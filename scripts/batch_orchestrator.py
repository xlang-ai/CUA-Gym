#!/usr/bin/env python3
"""
Batch Orchestrator Runner for CUA-Gym

Processes UDA-Gym query packages through the orchestrator agent in parallel,
with concurrency control, progress tracking, and auto-resume. This runner is
UDA-Gym-bundle-only; the old CUA-Gym task-generation JSON protocol is not
accepted.

Usage:
    # Run every valid UDA query package under a gen/ tree
    python3 scripts/batch_orchestrator.py "$UDA_GYM_ROOT/gen"

    # Higher concurrency (limited by VM budget)
    python3 scripts/batch_orchestrator.py -c 5 "$UDA_GYM_ROOT/gen"

    # Filter specific tasks
    python3 scripts/batch_orchestrator.py --filter "wandb" "$UDA_GYM_ROOT/gen"

    # Dry run (see what would be processed)
    python3 scripts/batch_orchestrator.py --dry-run "$UDA_GYM_ROOT/gen"

    # Retry only failed tasks
    python3 scripts/batch_orchestrator.py --retry-failed "$UDA_GYM_ROOT/gen"

    # Specific task by ID
    python3 scripts/batch_orchestrator.py --task-id uda_20260629_p002_ml_runs "$UDA_GYM_ROOT/gen"

    # Run UDA-Gym generated queries from a JSONL manifest or a single package
    python3 scripts/batch_orchestrator.py "$UDA_GYM_ROOT/gen/queries.jsonl"
    python3 scripts/batch_orchestrator.py "$UDA_GYM_ROOT/gen/20260625_849781"
"""

import argparse
import asyncio
import json
import os
import shutil
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from uda_materialization_audit import write_audit_artifacts

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = PROJECT_ROOT / "output" / "batch_status.json"
LOG_DIR = PROJECT_ROOT / "output" / "logs"
FINAL_DIR = PROJECT_ROOT / "output" / "final"
WORKSPACE_DIR = PROJECT_ROOT / "output" / "workspaces"
ENV_FILE = PROJECT_ROOT / ".env"


def resolve_nanorollout_root() -> Path:
    """Find the NanoRollout checkout used for authoritative runtime sanity."""
    configured = os.environ.get("NANOROLLOUT_ROOT")
    candidates = [
        Path(configured).expanduser() if configured else None,
        PROJECT_ROOT.parent / "UDA-Gym" / "NanoRollout",
        PROJECT_ROOT.parent / "NanoRollout",
    ]
    for candidate in candidates:
        if candidate and (candidate / "examples" / "eval" / "uda" / "run_codex_oauth.sh").is_file():
            return candidate.resolve()
    attempted = ", ".join(str(path) for path in candidates if path)
    raise FileNotFoundError(
        "NanoRollout checkout not found. Set NANOROLLOUT_ROOT or use a sibling "
        f"checkout. Tried: {attempted}"
    )


def install_nanorollout_context(workspace: Path, nanorollout_root: Path) -> None:
    usage_doc = (
        nanorollout_root
        / "nanorollout"
        / "envs"
        / "uda_env"
        / "ec2_runtime"
        / "UDA_ENV_EC2_USAGE.md"
    )
    if not usage_doc.is_file():
        return
    context_dir = workspace / ".claude" / "context"
    context_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(usage_doc, context_dir / "UDA_ENV_EC2_USAGE.md")


# Prepend osworld venv to PATH so all agent `python3` calls use it
_VENV_BIN = os.path.expanduser("~/.venvs/osworld-py312/bin")
if _VENV_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _VENV_BIN + ":" + os.environ.get("PATH", "")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def task_workspace(task_id: str) -> Path:
    """Return the single active workspace for a task."""
    return WORKSPACE_DIR / task_id


def _copytree_clean(src: Path, dst: Path):
    """Copy a read-only source tree into the per-task Claude workspace."""
    ignored_names = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "dist",
        "build",
        ".DS_Store",
    }

    if dst.exists():
        shutil.rmtree(dst)

    def ignore(_dir: str, names: list[str]) -> list[str]:
        return [name for name in names if name in ignored_names]

    shutil.copytree(src, dst, ignore=ignore)


def _install_workspace_claude_files(workspace: Path):
    """Install only the local agents and skills needed by the harness."""
    claude_dir = workspace / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    for name in ("agents", "skills"):
        src = PROJECT_ROOT / ".claude" / name
        dst = claude_dir / name
        if src.exists():
            _copytree_clean(src, dst)


def _workspace_payload(task: dict, workspace: Path) -> dict:
    """Rewrite UDA source paths to the copy staged inside the task workspace."""
    payload = json.loads(json.dumps(task["task_payload"]))
    source_pkg = Path(payload["context"]["uda_package"]["package_dir"]).resolve()
    local_source = workspace / "source" / "uda_package"
    _copytree_clean(source_pkg, local_source)

    uda = payload["context"]["uda_package"]
    uda["original_package_dir"] = str(source_pkg)
    uda["package_dir"] = str(local_source)
    uda["query_md_path"] = str(local_source / "query.md")
    uda["check_yaml_path"] = str(local_source / "check.yaml")
    uda["surface_yaml_path"] = str(local_source / "surface.yaml")

    for key, filename in (
        ("spec_yaml_path", "spec.yaml"),
        ("runtime_yaml_path", "runtime.yaml"),
        ("template_contract_path", "template_contract.yaml"),
        ("verification_contract_path", "verification_contract.yaml"),
        ("asset_lock_path", "asset_lock.json"),
        ("synthesis_report_path", "synthesis_report.yaml"),
        ("calibration_path", "calibration.yaml"),
    ):
        path = local_source / filename
        uda[key] = str(path) if path.exists() else None

    context_dir = local_source / "context"
    uda["context_dir"] = str(context_dir) if context_dir.exists() else None
    uda["context_manifest"] = _manifest_for(context_dir)
    for key, dirname in (("hidden_dir", "hidden"), ("gt_dir", "gt")):
        path = local_source / dirname
        uda[key] = str(path) if path.exists() else None
        uda[f"{key}_manifest"] = _manifest_for(path)
    return payload


def prepare_task_workspace(task: dict, *, reset: bool) -> tuple[Path, dict]:
    """Prepare one isolated Claude cwd and return the rewritten payload."""
    workspace = task_workspace(task["task_id"])
    if reset and workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "bundle" / "exec").mkdir(parents=True, exist_ok=True)
    (workspace / "bundle" / "hidden").mkdir(parents=True, exist_ok=True)
    (workspace / "bundle" / "gt").mkdir(parents=True, exist_ok=True)
    (workspace / "reward_sandbox").mkdir(parents=True, exist_ok=True)
    (workspace / "rollout").mkdir(parents=True, exist_ok=True)
    _install_workspace_claude_files(workspace)
    return workspace, _workspace_payload(task, workspace)

def load_env():
    """Load .env file into os.environ (simple key=value parser)."""
    if not ENV_FILE.exists():
        return
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip 'export ' prefix if present
            if line.startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            os.environ[key] = value


def _is_uda_query_dir(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "query.md").exists()
        and (path / "check.yaml").exists()
        and (path / "surface.yaml").exists()
    )


def _find_uda_query_dirs(root: Path) -> list[Path]:
    """Find UDA-Gym query package directories under a gen/ tree."""
    if _is_uda_query_dir(root):
        return [root]
    if not root.is_dir():
        return []

    ignored = {".git", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}
    packages: list[Path] = []
    for candidate in sorted(p for p in root.rglob("query.md") if p.is_file()):
        if any(part in ignored for part in candidate.relative_to(root).parts):
            continue
        package_dir = candidate.parent
        if _is_uda_query_dir(package_dir):
            packages.append(package_dir)
    return packages


def _manifest_for(root: Path) -> list[dict]:
    if not root.exists():
        return []
    ignored_dirs = {"__pycache__", ".pytest_cache", "node_modules", "dist", "build"}
    ignored_files = {".DS_Store"}
    manifest = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel_parts = path.relative_to(root).parts
        if any(part in ignored_dirs for part in rel_parts) or path.name in ignored_files:
            continue
        manifest.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
        })
    return manifest


def _load_uda_task_from_dir(package_dir: Path, source_path: Path, index: int, row: dict | None = None) -> dict:
    """Build a CUA task payload that points directly at a UDA-Gym gen/<id> dir."""
    package_dir = package_dir.resolve()
    row = row or {}
    uda_id = row.get("id") or package_dir.name
    query_path = package_dir / "query.md"
    check_path = package_dir / "check.yaml"
    surface_path = package_dir / "surface.yaml"
    spec_path = package_dir / "spec.yaml"
    runtime_path = package_dir / "runtime.yaml"
    template_contract_path = package_dir / "template_contract.yaml"
    verification_contract_path = package_dir / "verification_contract.yaml"
    asset_lock_path = package_dir / "asset_lock.json"
    synthesis_report_path = package_dir / "synthesis_report.yaml"
    calibration_path = package_dir / "calibration.yaml"
    context_dir = package_dir / "context"
    hidden_dir = package_dir / "hidden"
    gt_dir = package_dir / "gt"

    missing = [p.name for p in (query_path, check_path, surface_path) if not p.exists()]
    if missing:
        raise FileNotFoundError(f"UDA query package {package_dir} missing: {', '.join(missing)}")

    task_payload = {
        "task_id": f"uda_{uda_id}",
        "domain": "uda_cross_interface",
        "task_instruction": query_path.read_text(encoding="utf-8").strip(),
        "context": {
            "uda_package": {
                "id": uda_id,
                "package_dir": str(package_dir),
                "query_md_path": str(query_path),
                "check_yaml_path": str(check_path),
                "surface_yaml_path": str(surface_path),
                "spec_yaml_path": str(spec_path) if spec_path.exists() else None,
                "runtime_yaml_path": str(runtime_path) if runtime_path.exists() else None,
                "template_contract_path": (
                    str(template_contract_path) if template_contract_path.exists() else None
                ),
                "verification_contract_path": (
                    str(verification_contract_path) if verification_contract_path.exists() else None
                ),
                "asset_lock_path": str(asset_lock_path) if asset_lock_path.exists() else None,
                "synthesis_report_path": (
                    str(synthesis_report_path) if synthesis_report_path.exists() else None
                ),
                "calibration_path": str(calibration_path) if calibration_path.exists() else None,
                "context_dir": str(context_dir) if context_dir.exists() else None,
                "context_manifest": _manifest_for(context_dir),
                "hidden_dir": str(hidden_dir) if hidden_dir.exists() else None,
                "hidden_dir_manifest": _manifest_for(hidden_dir),
                "gt_dir": str(gt_dir) if gt_dir.exists() else None,
                "gt_dir_manifest": _manifest_for(gt_dir),
                "index_row": row,
            },
            "runtime_contract": {
                "copy_context_to_vm": "/tmp_workspace/context",
                "results_dir": "/tmp_workspace/results",
                "run_warmup_if_present": "/tmp_workspace/context/warmup.sh",
                "do_not_modify_source_package": True,
            },
        },
        "difficulty": "hard",
        "source": "uda_gym",
        "metadata": {
            "uda_id": uda_id,
            "family": row.get("family"),
            "pattern": row.get("pattern"),
            "primitives": row.get("primitives", []),
            "locations": row.get("locations"),
            "source": row.get("source", "primitives"),
        },
    }
    return {
        "source_file": str(source_path),
        "index": index,
        "task_id": task_payload["task_id"],
        "domain": "uda_cross_interface",
        "task_payload": task_payload,
    }


def _load_uda_jsonl(path: Path) -> list[dict]:
    """Load UDA-Gym gen/queries.jsonl rows as direct package references."""
    tasks = []
    # For /path/to/UDA-Gym/gen/queries.jsonl, rows with "dir": "gen/<id>"
    # are relative to /path/to/UDA-Gym.
    uda_root = path.parent.parent if path.parent.name == "gen" else path.parent
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        row = json.loads(line)
        row_dir = row.get("dir")
        if not row_dir:
            print(f"[WARN] Skipping UDA row without dir at {path}:{i + 1}")
            continue
        package_dir = (uda_root / row_dir).resolve()
        if not _is_uda_query_dir(package_dir):
            print(f"[WARN] Skipping legacy/non-surface UDA package: {package_dir}")
            continue
        tasks.append(_load_uda_task_from_dir(package_dir, path, i, row=row))
    return tasks


def load_tasks(file_paths: list[str]) -> list[dict]:
    """Load only UDA-Gym query packages/jsonl inputs."""
    tasks = []
    for fp in file_paths:
        path = Path(fp).expanduser()
        if path.is_dir():
            if _is_uda_query_dir(path):
                tasks.append(_load_uda_task_from_dir(path, path, 0))
            else:
                packages = _find_uda_query_dirs(path)
                if not packages:
                    print(f"[WARN] Skipping directory that is not a UDA query package/tree: {path}")
                    continue
                for i, package_dir in enumerate(packages):
                    tasks.append(_load_uda_task_from_dir(package_dir, path, i))
            continue

        fp = str(path)
        if path.suffix == ".jsonl":
            tasks.extend(_load_uda_jsonl(path))
            continue

        print(f"[WARN] Skipping non-UDA input: {path}")
    return tasks


def load_status() -> dict:
    """Load batch status from disk."""
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            return json.load(f)
    return {}


def save_status(status: dict):
    """Save batch status to disk."""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATUS_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(status, f, indent=2)
    tmp.rename(STATUS_FILE)


def task_is_complete(task_id: str, status: dict) -> bool:
    """Check if a task completed the adversarial generator/discriminator loop."""
    # Check status file
    if (
        status.get(task_id, {}).get("status") == "completed"
        and is_workspace_complete(task_id)
    ):
        return True
    # Also check if accepted workspace outputs exist on disk. A standalone
    # final/ directory is not enough: orchestrator is forbidden from direct
    # bundle authoring, so completion must be grounded in REVIEW.md and
    # SANITY.md PASS.
    if is_workspace_complete(task_id):
        return True
    return False


def is_bundle_complete(bundle: Path) -> bool:
    """Accept only native UDA-Gym bundle output."""
    if not bundle.exists():
        return False

    uda_required = [
        "meta.json",
        "instruction.md",
        "setup.sh",
        "check.sh",
    ]
    if all((bundle / name).exists() for name in uda_required):
        # exec/hidden/gt are part of the UDA-Gym style contract. They may be
        # empty, but the directories should exist so the runner can stage them
        # deterministically.
        return all((bundle / name).is_dir() for name in ("exec", "hidden", "gt"))

    return False


def is_final_complete(final: Path) -> bool:
    """Check final publication directory shape."""
    return is_bundle_complete(final)


def _verdict_passes(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return "## Verdict: PASS" in path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False


def _sanity_static_keys_present(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8").lower()
    except UnicodeDecodeError:
        return False
    return "reward strictness:" in text and "solution multiplicity:" in text


def _read_json(path: Path) -> object:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"{path} is empty")
    return json.loads(text)


def _find_score(value: object) -> float | None:
    if isinstance(value, dict):
        for key in ("overall_score", "score", "reward", "total_score"):
            candidate = value.get(key)
            if isinstance(candidate, (int, float)):
                return float(candidate)
            if isinstance(candidate, str):
                try:
                    return float(candidate)
                except ValueError:
                    pass
        for nested in value.values():
            score = _find_score(nested)
            if score is not None:
                return score
    elif isinstance(value, list):
        for nested in value:
            score = _find_score(nested)
            if score is not None:
                return score
    return None


def _nonempty_file(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def rollout_complete(work_dir: Path) -> bool:
    """Require concrete evidence of a real UDA rollout before publishing."""
    rollout = work_dir / "rollout"
    evidence_groups = (
        (rollout / "setup.log", rollout / "reward.log"),
        (rollout / "agent_trajectory.jsonl", rollout / "trajectory.json"),
        (rollout / "agent_transcript.md", rollout / "agent_last_message.txt", rollout / "result.txt"),
        (rollout / "run_metadata.json",),
    )
    for group in evidence_groups:
        if not any(_nonempty_file(path) for path in group):
            return False
    if not (rollout / "nro_output").is_dir():
        return False

    try:
        reward_payload = _read_json(rollout / "reward_stdout.json")
        metadata = _read_json(rollout / "run_metadata.json")
    except Exception:
        return False

    score = _find_score(reward_payload)
    if score is None or not 0.0 <= score <= 1.0:
        return False
    return isinstance(metadata, dict)


def is_workspace_complete(task_id: str) -> bool:
    """Require discriminator PASS, sanity PASS, rollout evidence, and bundle."""
    work_dir = task_workspace(task_id)
    try:
        audit = write_audit_artifacts(work_dir)
    except Exception:
        return False
    if audit.get("summary", {}).get("errors", 1):
        return False
    return (
        _verdict_passes(work_dir / "REVIEW.md")
        and _verdict_passes(work_dir / "SANITY.md")
        and _sanity_static_keys_present(work_dir / "SANITY.md")
        and is_bundle_complete(work_dir / "bundle")
        and rollout_complete(work_dir)
    )


def publish_final(task_id: str) -> bool:
    """Publish the accepted workspace bundle to output/final/<task_id>."""
    work_dir = task_workspace(task_id)
    bundle = work_dir / "bundle"
    final = FINAL_DIR / task_id
    if not is_workspace_complete(task_id):
        return False
    final.parent.mkdir(parents=True, exist_ok=True)
    if final.exists():
        shutil.rmtree(final)
    shutil.copytree(bundle, final)
    return is_final_complete(final)

# ---------------------------------------------------------------------------
# Core: run one task
# ---------------------------------------------------------------------------

async def run_task(
    task: dict,
    semaphore: asyncio.Semaphore,
    status: dict,
    args: argparse.Namespace,
):
    """Run orchestrator for a single task."""
    task_id = task["task_id"]
    domain = task["domain"]
    source = task["source_file"]
    index = task["index"]
    task_payload = task["task_payload"]

    # Skip completed
    if task_is_complete(task_id, status) and not args.force:
        return "skipped"

    # Skip non-failed if retry_failed mode
    if args.retry_failed:
        prev = status.get(task_id, {}).get("status", "")
        if prev not in ("failed", "error", "timeout"):
            return "skipped"

    async with semaphore:
        ts_start = datetime.now()
        print(f"  [{ts_start.strftime('%H:%M:%S')}] START  {task_id}  "
              f"(from {source}[{index}])")

        if args.dry_run:
            print(f"  [DRY]   {task_id} — would run orchestrator")
            return "dry_run"

        workspace, task_payload = prepare_task_workspace(task, reset=args.force)
        nanorollout_root = Path(args.nanorollout_root)
        install_nanorollout_context(workspace, nanorollout_root)

        # Update status
        status[task_id] = {
            "status": "running",
            "source_file": source,
            "index": index,
            "domain": domain,
            "started_at": ts_start.isoformat(),
            "attempt": status.get(task_id, {}).get("attempt", 0) + 1,
        }
        save_status(status)

        # Construct prompt:
        # Pass the selected task payload directly to avoid expensive reads of
        # large task_generation JSON files inside the agent session.
        task_payload_json = json.dumps(task_payload, ensure_ascii=False, indent=2)
        prompt = (
            f"Process tasks for domain: {domain}\n"
            f"Input file: {source}\n"
            f"Task index: {index}\n\n"
            f"Task workspace root: {workspace}\n"
            "Claude has been launched with this task workspace as cwd.\n"
            "Treat cwd as the only visible mutable workspace.\n"
            "Use only relative generated paths: task_config.json, bundle/, reward_sandbox/, rollout/, REVIEW.md, SANITY.md.\n"
            "The source UDA package has been copied under source/uda_package/ inside cwd.\n\n"
            "Selected task payload (authoritative):\n"
            f"{task_payload_json}\n\n"
            "IMPORTANT:\n"
            "- Use the task payload above as the selected task.\n"
            "- Do NOT read or write parent project directories.\n"
            "- Do NOT read output/task_generation/*.json files.\n"
            "- Do NOT ask clarifying questions.\n"
            "- Execute the full orchestrator pipeline immediately.\n\n"
            "UDA-GYM BUNDLE MODE IS THE ONLY SUPPORTED MODE:\n"
            "- The selected payload points at a UDA-Gym query package.\n"
            "- Read the source package directly from task_config.context.uda_package.\n"
            "- Run the generator/discriminator subagent loop over native UDA-Gym bundle files.\n"
            "- You are only the orchestrator: write task_config.json, spawn setup-gen, spawn reward-gen, inspect REVIEW.md, run a strong-model rollout, and write SANITY.md.\n"
            f"- Runtime rollout must use {nanorollout_root} with BENCH=uda-gym and examples/eval/uda/run_codex_oauth.sh.\n"
            f"- Prefix NanoRollout runs with PATH={nanorollout_root / '.venv' / 'bin'}:$PATH so the wrapper resolves nro.\n"
            "- Do NOT hand-roll rollout with boto3, SSH, direct /v1/* sandbox APIs, or local-only checker simulations; fail SANITY.md if NanoRollout cannot run.\n"
            "- Do NOT directly write or edit bundle files such as instruction.md, meta.json, setup.sh, check.sh, hidden/, gt/, or exec/.\n"
            "- Do NOT write output/final/<task_id>/ yourself; the runner publishes final only after REVIEW.md and SANITY.md PASS.\n"
            "- Accepted output must be ./bundle/, ./REVIEW.md with ## Verdict: PASS, and ./SANITY.md with ## Verdict: PASS.\n"
            "- Do NOT generate old CUA-Gym config.json, initial_setup.py, golden_patch.py, or reward.py."
        )

        # Build command
        cmd = [
            "claude",
            "--agent", "orchestrator",
            "-p", prompt,
            "--max-turns", str(args.max_turns),
            "--output-format", "stream-json",
            "--verbose",
        ]
        if args.model:
            cmd += ["--model", args.model]
        if args.dangerously_skip_permissions:
            cmd += ["--permission-mode", "dontAsk"]
        else:
            # Agent is the Claude Code tool name for spawning setup/reward subagents.
            cmd += ["--allowedTools",
                    "Agent,Bash,Read,Write,Edit,Glob,Grep,WebSearch,WebFetch"]

        # Log file (stream-json for full trace, readable summary separate)
        log_file = LOG_DIR / f"{task_id}.jsonl"
        err_file = LOG_DIR / f"{task_id}.stderr.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        result_status = "failed"
        max_retries = args.api_retries
        for attempt_num in range(max_retries + 1):
            if attempt_num > 0:
                wait_secs = min(30 * attempt_num, 120)
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] RETRY  {task_id}  "
                      f"(attempt {attempt_num + 1}/{max_retries + 1}, "
                      f"waiting {wait_secs}s)")
                await asyncio.sleep(wait_secs)

            # Use attempt-suffixed log files so each attempt is preserved
            if attempt_num == 0:
                attempt_log = log_file
                attempt_err = err_file
            else:
                attempt_log = LOG_DIR / f"{task_id}.attempt{attempt_num}.jsonl"
                attempt_err = LOG_DIR / f"{task_id}.attempt{attempt_num}.stderr.log"

            try:
                with open(attempt_log, "w") as lf, open(attempt_err, "w") as ef:
                    ef.write(f"=== {task_id} (attempt {attempt_num + 1}/{max_retries + 1}) ===\n")
                    ef.write(f"Command: {cmd[0]} {cmd[1]} {cmd[2]} -p '...'\n")
                    ef.write(f"Cwd: {workspace}\n")
                    ef.write(f"Prompt: {prompt}\n")
                    ef.write(f"Started: {ts_start.isoformat()}\n")
                    ef.write("=" * 60 + "\n\n")
                    ef.flush()

                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=lf,
                        stderr=ef,
                        cwd=str(workspace),
                    )

                    try:
                        await asyncio.wait_for(
                            proc.wait(),
                            timeout=args.timeout * 60,  # minutes → seconds
                        )
                    except asyncio.TimeoutError:
                        proc.kill()
                        await proc.wait()
                        result_status = "timeout"
                        ef.write(f"\n\n=== TIMEOUT after {args.timeout} minutes ===\n")

                # Check result
                if result_status == "timeout":
                    break  # Don't retry on timeout

                if is_workspace_complete(task_id) and publish_final(task_id):
                    result_status = "completed"
                    break  # Success — stop retrying
                else:
                    result_status = "failed"
                    status[task_id]["exit_code"] = proc.returncode
                    # Read stderr for error details
                    try:
                        stderr_content = Path(attempt_err).read_text()
                        # Extract last meaningful lines
                        lines = [l for l in stderr_content.strip().split('\n')
                                 if l.strip() and not l.startswith('===')]
                        if lines:
                            status[task_id]["last_error"] = '\n'.join(lines[-5:])
                    except Exception:
                        pass
                    # Symlink latest attempt logs for easy access
                    if attempt_num > 0:
                        for src, dst in [(attempt_log, log_file), (attempt_err, err_file)]:
                            try:
                                dst.unlink(missing_ok=True)
                                dst.symlink_to(src.name)
                            except Exception:
                                pass

            except Exception as e:
                result_status = "error"
                status[task_id]["error"] = str(e)
                break  # Don't retry on unexpected exceptions

        ts_end = datetime.now()
        duration = (ts_end - ts_start).total_seconds()
        status[task_id]["status"] = result_status
        status[task_id]["finished_at"] = ts_end.isoformat()
        status[task_id]["duration_seconds"] = round(duration)
        save_status(status)

        # Print error hint on failure
        if result_status in ("failed", "error", "timeout"):
            hint = status[task_id].get("last_error", status[task_id].get("error", ""))
            if hint:
                # Show last line of error
                last_line = hint.strip().split('\n')[-1][:120]
                print(f"          └─ {last_line}")
            print(f"          └─ Log: {err_file}")

        icon = {"completed": "✓", "failed": "✗", "timeout": "⏰", "error": "!"}.get(
            result_status, "?"
        )
        print(f"  [{ts_end.strftime('%H:%M:%S')}] {icon} {result_status.upper():9s} "
              f"{task_id}  ({duration:.0f}s)")

        return result_status

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(
        description="Batch orchestrator runner for CUA-Gym",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "files", nargs="*",
        help="UDA-Gym gen/ directory, query package directory, or queries.jsonl",
    )
    parser.add_argument(
        "-c", "--concurrency", type=int, default=3,
        help="Max parallel tasks (default: 3, limited by VM budget)",
    )
    parser.add_argument(
        "--max-turns", type=int, default=200,
        help="Max Claude turns per task (default: 200)",
    )
    parser.add_argument(
        "--timeout", type=int, default=240,
        help="Timeout per task in minutes (default: 45)",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="Model to use (default: inherit from project)",
    )
    parser.add_argument(
        "--filter", type=str, default=None,
        help="Only run tasks whose task_id contains this string",
    )
    parser.add_argument(
        "--task-id", type=str, default=None,
        help="Run only this specific task_id",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be processed without running",
    )
    parser.add_argument(
        "--retry-failed", action="store_true",
        help="Only retry tasks with failed/error/timeout status",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-run even completed tasks",
    )
    parser.add_argument(
        "--api-retries", type=int, default=3,
        help="Max retries per task on API failure (default: 3, 0 to disable)",
    )
    parser.add_argument(
        "--dangerously-skip-permissions", action="store_true",
        help="Skip all Claude permission prompts (use with caution)",
    )
    args = parser.parse_args()

    # Load environment
    load_env()
    nanorollout_root = resolve_nanorollout_root()
    args.nanorollout_root = str(nanorollout_root)
    os.environ["NANOROLLOUT_ROOT"] = str(nanorollout_root)

    if not args.files:
        print("Error: specify a UDA-Gym gen/ tree, query package directory, or queries.jsonl.")
        print('Example: python scripts/batch_orchestrator.py "$UDA_GYM_ROOT/gen"')
        sys.exit(1)

    # Load tasks
    tasks = load_tasks(args.files)

    # Apply filters
    if args.task_id:
        tasks = [t for t in tasks if t["task_id"] == args.task_id]
    elif args.filter:
        tasks = [t for t in tasks if args.filter in t["task_id"]]

    if not tasks:
        print("No tasks match the filter criteria.")
        sys.exit(0)

    # Load status
    status = load_status()

    # Count
    total = len(tasks)
    already_done = sum(1 for t in tasks if task_is_complete(t["task_id"], status))
    pending = total - already_done

    # Summary
    sources = sorted(set(t["source_file"] for t in tasks))
    print("=" * 60)
    print("CUA-Gym Batch Orchestrator")
    print("=" * 60)
    print(f"  Task files:    {len(sources)}")
    print(f"  Total tasks:   {total}")
    print(f"  Completed:     {already_done}")
    print(f"  Pending:       {pending}")
    print(f"  Concurrency:   {args.concurrency}")
    print(f"  Timeout:       {args.timeout} min/task")
    print(f"  API retries:   {args.api_retries}")
    print(f"  Max turns:     {args.max_turns}")
    print(f"  Model:         {args.model or '(default)'}")
    print(f"  NanoRollout:   {nanorollout_root}")
    print(f"  Status file:   {STATUS_FILE}")
    print(f"  Log dir:       {LOG_DIR}")
    if args.dry_run:
        print(f"  Mode:          DRY RUN")
    if args.retry_failed:
        print(f"  Mode:          RETRY FAILED ONLY")
    print("=" * 60)

    if pending == 0 and not args.force and not args.retry_failed:
        print("\nAll tasks already completed! Use --force to re-run.")
        sys.exit(0)

    # Run
    print(f"\nStarting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    semaphore = asyncio.Semaphore(args.concurrency)
    t0 = time.time()

    results = await asyncio.gather(*[
        run_task(t, semaphore, status, args) for t in tasks
    ])

    elapsed = time.time() - t0

    # Final summary
    from collections import Counter
    counts = Counter(results)
    print("\n" + "=" * 60)
    print("BATCH COMPLETE")
    print("=" * 60)
    print(f"  Completed:  {counts.get('completed', 0)}")
    print(f"  Failed:     {counts.get('failed', 0)}")
    print(f"  Timeout:    {counts.get('timeout', 0)}")
    print(f"  Error:      {counts.get('error', 0)}")
    print(f"  Skipped:    {counts.get('skipped', 0)}")
    print(f"  Dry run:    {counts.get('dry_run', 0)}")
    print(f"  Elapsed:    {elapsed/60:.1f} minutes")
    print(f"  Status:     {STATUS_FILE}")

    # List failures
    failed_ids = [
        t["task_id"] for t, r in zip(tasks, results)
        if r in ("failed", "error", "timeout")
    ]
    if failed_ids:
        print(f"\nFailed tasks ({len(failed_ids)}):")
        for tid in failed_ids[:20]:
            reason = status.get(tid, {}).get("status", "unknown")
            print(f"  - {tid} ({reason})")
        if len(failed_ids) > 20:
            print(f"  ... and {len(failed_ids) - 20} more")
        print(f"\nRetry with: python3 scripts/batch_orchestrator.py --retry-failed {' '.join(args.files)}")


if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def _sigint(sig, frame):
        print("\n\nInterrupted! Progress saved to batch_status.json")
        sys.exit(130)
    signal.signal(signal.SIGINT, _sigint)

    asyncio.run(main())
