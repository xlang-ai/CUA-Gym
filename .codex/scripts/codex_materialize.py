#!/usr/bin/env python3
"""
Codex-native UDA-Gym materialization harness.

This mirrors the Claude batch pipeline at a small scale:

1. load UDA-Gym query packages from a gen/ tree or one package dir;
2. prepare one isolated per-task workspace under output/codex_workspaces/;
3. copy .codex/ and .agents/ infrastructure into that workspace;
4. run Codex CLI non-interactively with the uda-gym-materializer skill;
5. accept only native UDA-Gym bundles with REVIEW.md PASS and SANITY.md PASS.

The existing Claude pipeline remains untouched.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_nanorollout_root() -> Path:
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


NANOROLLOUT_ROOT = _resolve_nanorollout_root()
UDA_EC2_USAGE_DOC = (
    NANOROLLOUT_ROOT
    / "nanorollout"
    / "envs"
    / "uda_env"
    / "ec2_runtime"
    / "UDA_ENV_EC2_USAGE.md"
)
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CODEX_WORKSPACE_DIR = PROJECT_ROOT / "output" / "codex_workspaces"
CODEX_LOG_DIR = PROJECT_ROOT / "output" / "codex_logs"
CODEX_FINAL_DIR = PROJECT_ROOT / "output" / "codex_final"

sys.path.insert(0, str(SCRIPTS_DIR))
import batch_orchestrator as bo  # noqa: E402
from uda_materialization_audit import write_audit_artifacts  # noqa: E402


def _copytree_clean(src: Path, dst: Path) -> None:
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


def _install_codex_infra(workspace: Path) -> None:
    for name in (".codex", ".agents", ".claude"):
        src = PROJECT_ROOT / name
        if src.exists():
            _copytree_clean(src, workspace / name)
    if UDA_EC2_USAGE_DOC.exists():
        context_dir = workspace / ".codex" / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(UDA_EC2_USAGE_DOC, context_dir / "UDA_ENV_EC2_USAGE.md")


def prepare_workspace(task: dict, *, force: bool) -> tuple[Path, dict]:
    task_id = task["task_id"]
    workspace = CODEX_WORKSPACE_DIR / task_id
    if force and workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "bundle" / "exec").mkdir(parents=True, exist_ok=True)
    (workspace / "bundle" / "hidden").mkdir(parents=True, exist_ok=True)
    (workspace / "bundle" / "gt").mkdir(parents=True, exist_ok=True)
    (workspace / "reward_sandbox").mkdir(parents=True, exist_ok=True)
    (workspace / "rollout").mkdir(parents=True, exist_ok=True)
    _install_codex_infra(workspace)
    payload = bo._workspace_payload(task, workspace)
    return workspace, payload


def verdict_passes(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return "## Verdict: PASS" in path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False


def sanity_static_keys_present(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8").lower()
    except UnicodeDecodeError:
        return False
    reward_strictness_present = (
        "reward strictness:" in text
        or "## reward strictness" in text
        or "reward strictness and solution multiplicity" in text
        or "covers all criteria from `check.yaml`" in text
    )
    solution_multiplicity_present = (
        "solution multiplicity:" in text
        or "## solution multiplicity" in text
        or "solution multiplicity" in text
    )
    return reward_strictness_present and solution_multiplicity_present


def bundle_complete(bundle: Path) -> bool:
    return (
        (bundle / "meta.json").exists()
        and (bundle / "instruction.md").exists()
        and (bundle / "setup.sh").exists()
        and (bundle / "check.sh").exists()
        and (bundle / "exec").is_dir()
        and (bundle / "hidden").is_dir()
        and (bundle / "gt").is_dir()
    )


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


def _latest_mtime(path: Path) -> float:
    if path.is_file():
        return path.stat().st_mtime
    latest = path.stat().st_mtime if path.exists() else 0.0
    if path.is_dir():
        for child in path.rglob("*"):
            try:
                latest = max(latest, child.stat().st_mtime)
            except OSError:
                pass
    return latest


def _find_nro_run_dirs(rollout: Path, task_id: str) -> list[Path]:
    """Find NanoRollout run dirs even when agents use noncanonical output names."""
    if not rollout.exists():
        return []
    run_dirs: list[Path] = []
    for candidate in rollout.rglob(task_id):
        if not candidate.is_dir():
            continue
        for child in candidate.iterdir():
            if child.is_dir() and (
                (child / "reward.json").exists()
                or (child / "result.txt").exists()
                or (child / "trial.log").exists()
                or (child / "agent").is_dir()
            ):
                run_dirs.append(child)
    # Prefer complete/latest runs and de-duplicate by resolved path.
    unique: dict[Path, Path] = {}
    for path in run_dirs:
        try:
            unique[path.resolve()] = path
        except OSError:
            unique[path] = path
    return sorted(unique.values(), key=_latest_mtime)


def _copy_if_present(src: Path, dst: Path) -> bool:
    if _nonempty_file(src):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    return False


def canonicalize_rollout_artifacts(workspace: Path, task_id: str) -> dict[str, Any]:
    """Normalize NanoRollout outputs into stable rollout/* files before gating.

    This is intentionally outside the agent loop. Agents may name the output
    directory `nro_results`, `nro_results_2`, or `nro_output`; the harness should
    not reject an otherwise valid rollout because stable artifact copy-out was
    skipped or used a noncanonical path.
    """
    rollout = workspace / "rollout"
    summary: dict[str, Any] = {
        "task_id": task_id,
        "canonicalized": False,
        "run_dir": None,
        "score": None,
        "resolved_status": None,
        "error": None,
        "classification": "missing_rollout",
        "artifacts": [],
    }
    run_dirs = _find_nro_run_dirs(rollout, task_id)
    if not run_dirs:
        (rollout / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    def run_rank(path: Path) -> tuple[int, float]:
        completeness = sum(
            1
            for rel in (
                "reward.json",
                "result.txt",
                "metadata.json",
                "trial.log",
                "trajectory.json",
                "agent/codex.jsonl",
                "agent/trajectory.json",
            )
            if _nonempty_file(path / rel)
        )
        return completeness, _latest_mtime(path)

    run_dir = max(run_dirs, key=run_rank)
    summary["run_dir"] = str(run_dir.relative_to(workspace))

    copied: list[str] = []
    for src_rel, dst_rel in (
        ("trial.log", "setup.log"),
        ("trial.log", "reward.log"),
        ("agent/codex.jsonl", "agent_trajectory.jsonl"),
        ("trajectory.json", "trajectory.json"),
        ("agent/trajectory.json", "agent_trajectory.json"),
        ("agent/last-message.txt", "agent_last_message.txt"),
        ("result.txt", "result.txt"),
        ("reward.json", "reward_stdout.json"),
        ("reward.json", "reward.json"),
        ("metadata.json", "run_metadata.json"),
        ("screenshots/pre_rollout.png", "screenshots/pre_rollout.png"),
        ("screenshots/pre_rollout.json", "screenshots/pre_rollout.json"),
    ):
        if _copy_if_present(run_dir / src_rel, rollout / dst_rel):
            copied.append(dst_rel)

    # Preserve a canonical nro_output tree for downstream gates. If the agent
    # used e.g. rollout/nro_results_2, copy that whole tree into rollout/nro_output.
    if not (rollout / "nro_output").is_dir():
        for ancestor in run_dir.parents:
            if ancestor.parent == rollout and ancestor.name.startswith("nro"):
                shutil.copytree(ancestor, rollout / "nro_output")
                copied.append("nro_output/")
                break

    reward_path = run_dir / "reward.json"
    if _nonempty_file(reward_path):
        try:
            reward_payload = _read_json(reward_path)
            if isinstance(reward_payload, dict):
                summary["score"] = _find_score(reward_payload)
                summary["resolved_status"] = (
                    reward_payload.get("resolved_status")
                    or reward_payload.get("resolved")
                )
                summary["error"] = reward_payload.get("error")
        except Exception as exc:
            summary["error"] = f"reward_json_error: {exc}"

    metadata_path = rollout / "run_metadata.json"
    if not _nonempty_file(metadata_path):
        metadata = {"instance_id": task_id, "run_dir": summary["run_dir"]}
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        copied.append("run_metadata.json")

    summary["canonicalized"] = bool(copied)
    summary["artifacts"] = copied
    summary["classification"] = classify_workspace(workspace, codex_rc=0, fallback_summary=summary)
    (rollout / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _collect_text(paths: list[Path], max_chars: int = 200_000) -> str:
    chunks: list[str] = []
    remaining = max_chars
    for path in paths:
        if remaining <= 0 or not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        chunks.append(text[:remaining])
        remaining -= len(chunks[-1])
    return "\n".join(chunks)


def classify_workspace(
    workspace: Path,
    *,
    codex_rc: int | None,
    fallback_summary: dict[str, Any] | None = None,
) -> str:
    """Separate harness/infra failures from task validity and agent score."""
    rollout = workspace / "rollout"
    texts = _collect_text(
        [
            workspace / "codex_last_message.txt",
            workspace / "SANITY.md",
            rollout / "run_summary.json",
            *list(rollout.rglob("trial.log"))[-5:],
        ]
    ).lower()

    if "operation timed out" in texts or "codex agent run failed" in texts or "chmod 700" in texts:
        return "infra_fail"
    if "stalled timeout" in texts or "without log heartbeat" in texts:
        return "harness_timeout"
    if codex_rc == 124:
        return "harness_timeout"
    if codex_rc not in (None, 0):
        return "harness_orchestrator_failed"
    if "setup failed" in texts or "chrome did not open" in texts or "gui_ready" in texts and "missing" in texts:
        return "setup_fail"
    if "http error 403" in texts or "error code: 1010" in texts or "cloudflare" in texts:
        return "reward_transport_fail"

    score = None
    if fallback_summary:
        score = fallback_summary.get("score")
    if score is None and _nonempty_file(rollout / "reward_stdout.json"):
        try:
            score = _find_score(_read_json(rollout / "reward_stdout.json"))
        except Exception:
            score = None
    if isinstance(score, (int, float)):
        if verdict_passes(workspace / "REVIEW.md") and verdict_passes(workspace / "SANITY.md"):
            if score >= 0.999:
                return "task_valid_agent_full"
            return "task_valid_agent_partial"
    if "not valid json" in texts or "evaluator" in texts and "failed" in texts:
        return "reward_fail"
    if not verdict_passes(workspace / "REVIEW.md"):
        return "review_fail"
    if not verdict_passes(workspace / "SANITY.md"):
        return "sanity_fail"
    return "task_valid_score_unknown"


def _nonempty_file(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def _screenshot_quality_issue(path: Path) -> str | None:
    """Return a blocking reason when a rollout screenshot is blank/black."""
    try:
        from PIL import Image, ImageStat
    except Exception:
        return None

    try:
        with Image.open(path) as image:
            image = image.convert("RGB")
            width, height = image.size
            if width <= 0 or height <= 0:
                return "pre-rollout screenshot has invalid dimensions"

            stat = ImageStat.Stat(image)
            mean_luma = sum(stat.mean) / 3.0

            pixels = image.load()
            sampled = 0
            nonblack = 0
            step_x = max(1, width // 160)
            step_y = max(1, height // 90)
            for y in range(0, height, step_y):
                for x in range(0, width, step_x):
                    sampled += 1
                    if max(pixels[x, y]) > 24:
                        nonblack += 1
            nonblack_ratio = nonblack / sampled if sampled else 0.0
    except Exception as exc:
        return f"pre-rollout screenshot could not be inspected: {exc}"

    if mean_luma < 3.0 or nonblack_ratio < 0.005:
        return (
            "pre-rollout screenshot is nearly black/blank "
            f"(mean_luma={mean_luma:.2f}, nonblack_ratio={nonblack_ratio:.4f})"
        )
    return None


def rollout_complete(workspace: Path, task_id: str | None = None) -> tuple[bool, list[str]]:
    rollout = workspace / "rollout"
    reasons: list[str] = []
    if task_id:
        canonicalize_rollout_artifacts(workspace, task_id)

    # NanoRollout is the authoritative runtime gate. It does not always emit the
    # older Claude-style stable filenames, so accept the canonical NRO evidence
    # the orchestrator copies out while keeping the full rollout/nro_output tree.
    evidence_groups = {
        "setup/runtime log": [
            rollout / "setup.log",
            rollout / "reward.log",
        ],
        "agent trajectory": [
            rollout / "agent_trajectory.jsonl",
            rollout / "trajectory.json",
        ],
        "agent transcript/summary": [
            rollout / "agent_transcript.md",
            rollout / "agent_last_message.txt",
            rollout / "result.txt",
        ],
        "run metadata": [
            rollout / "run_metadata.json",
        ],
    }
    for label, paths in evidence_groups.items():
        if not any(_nonempty_file(path) for path in paths):
            formatted = " or ".join(str(path.relative_to(workspace)) for path in paths)
            reasons.append(f"missing {label} evidence ({formatted})")

    if not (rollout / "nro_output").is_dir():
        reasons.append("missing rollout/nro_output NanoRollout tree")

    pre_rollout_screenshot = rollout / "screenshots" / "pre_rollout.png"
    if not _nonempty_file(pre_rollout_screenshot):
        reasons.append("missing pre-rollout screenshot evidence (rollout/screenshots/pre_rollout.png)")
    else:
        screenshot_issue = _screenshot_quality_issue(pre_rollout_screenshot)
        if screenshot_issue:
            reasons.append(screenshot_issue)

    reward_candidates = [
        rollout / "reward_stdout.json",
        rollout / "reward.json",
        rollout / "score.json",
    ]
    reward_path = next((path for path in reward_candidates if _nonempty_file(path)), None)
    if reward_path is None:
        reasons.append("missing or empty rollout/reward_stdout.json")
    else:
        try:
            reward_payload = _read_json(reward_path)
        except Exception as exc:
            reasons.append(f"{reward_path.relative_to(workspace)} is not valid JSON: {exc}")
        else:
            score = _find_score(reward_payload)
            if score is None:
                reasons.append(f"{reward_path.relative_to(workspace)} has no numeric score")
            elif not 0.0 <= score <= 1.0:
                reasons.append(
                    f"{reward_path.relative_to(workspace)} score {score} is outside [0, 1]"
                )

    try:
        metadata = _read_json(rollout / "run_metadata.json")
    except Exception as exc:
        reasons.append(f"rollout/run_metadata.json is not valid JSON: {exc}")
    else:
        if not isinstance(metadata, dict):
            reasons.append("rollout/run_metadata.json must be a JSON object")

    return not reasons, reasons


def workspace_complete(workspace: Path) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not verdict_passes(workspace / "REVIEW.md"):
        reasons.append("REVIEW.md missing ## Verdict: PASS")
    if not verdict_passes(workspace / "SANITY.md"):
        reasons.append("SANITY.md missing ## Verdict: PASS")
    elif not sanity_static_keys_present(workspace / "SANITY.md"):
        reasons.append("SANITY.md missing reward strictness and solution multiplicity static checks")
    if not bundle_complete(workspace / "bundle"):
        reasons.append("bundle is missing required native UDA-Gym files/directories")

    try:
        audit = write_audit_artifacts(workspace)
    except Exception as exc:
        reasons.append(f"materialization audit failed to run: {exc}")
    else:
        for issue in audit.get("issues", []):
            if issue.get("severity") == "error":
                code = issue.get("code", "audit_error")
                message = issue.get("message", "")
                evidence = issue.get("evidence")
                suffix = f" ({evidence})" if evidence else ""
                reasons.append(f"{code}: {message}{suffix}")

    task_id = workspace.name
    canonicalize_rollout_artifacts(workspace, task_id)
    rollout_ok, rollout_reasons = rollout_complete(workspace, task_id)
    if not rollout_ok:
        reasons.extend(rollout_reasons)

    return not reasons, reasons


def publish_final(task_id: str, workspace: Path) -> None:
    final = CODEX_FINAL_DIR / task_id
    if final.exists():
        shutil.rmtree(final)
    final.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(workspace / "bundle", final)


def write_materialization_result(
    workspace: Path,
    task_id: str,
    *,
    codex_rc: int,
    complete: bool,
    reasons: list[str],
) -> dict[str, Any]:
    rollout_summary = None
    rollout_summary_path = workspace / "rollout" / "run_summary.json"
    if _nonempty_file(rollout_summary_path):
        try:
            loaded = _read_json(rollout_summary_path)
            if isinstance(loaded, dict):
                rollout_summary = loaded
        except Exception:
            rollout_summary = None

    classification = classify_workspace(
        workspace,
        codex_rc=codex_rc,
        fallback_summary=rollout_summary,
    )
    if not complete and reasons:
        reason_text = "\n".join(reasons).lower()
        if any(
            marker in reason_text
            for marker in (
                "orphan_hidden_fixture",
                "leaked",
                "audit",
                "forbidden",
                "answer",
                "sid",
                "admin token",
            )
        ):
            classification = "audit_fail"
        elif "missing" in reason_text or "bundle" in reason_text:
            classification = "artifact_gate_fail"
        elif "rollout/" in reason_text or "reward_stdout" in reason_text:
            classification = "rollout_artifact_fail"
        else:
            classification = "final_gate_fail"

    result = {
        "task_id": task_id,
        "complete": complete,
        "classification": classification,
        "codex_exit_code": codex_rc,
        "reasons": reasons,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    (workspace / "materialization_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result


def build_prompt(task: dict, payload: dict, workspace: Path) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
    return (
        "Use $uda-gym-materializer.\n"
        "Run the Codex UDA-Gym materialization pipeline end to end.\n\n"
        f"Input task id: {task['task_id']}\n"
        f"Task workspace root: {workspace}\n"
        "Codex has been launched with this task workspace as cwd.\n"
        "Treat cwd as the only visible mutable workspace.\n"
        "Use only relative generated paths: task_config.json, bundle/, reward_sandbox/, rollout/, REVIEW.md, SANITY.md.\n"
        "The source UDA package has been copied under source/uda_package/ inside cwd.\n\n"
        "The UDA EC2 usage guide has been copied under .codex/context/UDA_ENV_EC2_USAGE.md when available.\n\n"
        "Selected task payload (authoritative):\n"
        f"{payload_json}\n\n"
        "IMPORTANT:\n"
        "- Read .codex/skills/uda-gym-materializer/SKILL.md first.\n"
        "- Noninteractive mode: do NOT spawn custom agents or call wait. Instead, run the roles serially in this main Codex process.\n"
        "- Read .codex/agents/prompts/setup-gen.md and use it as the setup-gen checklist when producing instruction.md, meta.json, exec/, hidden/, and setup.sh.\n"
        "- Then read .codex/agents/prompts/reward-gen.md and use it as the reward-gen checklist when producing check.sh, gt/, and REVIEW.md.\n"
        "- Then use .codex/agents/prompts/orchestrator.md as the SANITY.md/static+runtime rollout checklist.\n"
        "- Keep role boundaries explicit in REVIEW.md and SANITY.md, but do not use spawn_agent/wait because noninteractive subagent waits are not reliable in this harness.\n"
        "- Do NOT read or write parent project directories.\n"
        "- Do NOT ask clarifying questions.\n"
        "- Do NOT generate old CUA-Gym config.json, initial_setup.py, golden_patch.py, or reward.py.\n"
        f"- Runtime rollout must use {NANOROLLOUT_ROOT} with BENCH=uda-gym and examples/eval/uda/run_codex_oauth.sh.\n"
        "- In bundle runtime metadata, runtime.type is the execution provider. Use ec2 for EC2 profile rollout; if an older source runtime.yaml says uda-gym, normalize it to ec2 in bundle/meta.json and bundle/runtime.yaml.\n"
        "- Runtime profile must match required software: finance/spreadsheet/BI/notebook/openpyxl/pandas/Metabase/Grafana tasks use datascience; multimedia/video use multimedia; Blender 5.x uses multimedia-blender5 and is non-rollout-ready until validated; plain office/browser/file may use general-root.\n"
        "- If bundle/task.yaml is present, its instruction must be absent or mirror bundle/instruction.md; never preserve placeholder text such as 'See query.md' or 'See instruction.md'.\n"
        f"- Prefix NanoRollout runs with PATH={NANOROLLOUT_ROOT / '.venv' / 'bin'}:$PATH so the wrapper resolves nro.\n"
        "- Do NOT hand-roll rollout with boto3, SSH, direct /v1/* sandbox APIs, or local-only checker simulations; fail SANITY.md if NanoRollout cannot run.\n"
        "- Before the agent begins the rollout, capture the initialized desktop/browser/app state after setup and save it as ./rollout/screenshots/pre_rollout.png. This screenshot is required rollout evidence.\n"
        "- Accepted output must include ./bundle/, ./REVIEW.md with ## Verdict: PASS, ./SANITY.md with ## Verdict: PASS, and real rollout artifacts under ./rollout/.\n"
        "- Local checker smoke tests are useful diagnostics but can never replace the required UDA EC2 rollout."
    )


def _observed_size(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        try:
            total += path.stat().st_size
        except OSError:
            pass
    return total


def _terminate_process_group(proc: subprocess.Popen, stderr_log: Path, reason: str) -> None:
    with stderr_log.open("a", encoding="utf-8") as f:
        f.write(f"\n[uda-materializer] terminating Codex process: {reason}\n")
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        with stderr_log.open("a", encoding="utf-8") as f:
            f.write("[uda-materializer] SIGTERM timed out; sending SIGKILL\n")
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        except OSError:
            proc.kill()
        proc.wait(timeout=15)


def run_codex(
    task: dict,
    payload: dict,
    workspace: Path,
    timeout_min: int,
    stalled_timeout_min: int,
    model: str | None,
) -> int:
    CODEX_LOG_DIR.mkdir(parents=True, exist_ok=True)
    task_id = task["task_id"]
    prompt_path = workspace / "codex_prompt.txt"
    prompt_path.write_text(build_prompt(task, payload, workspace), encoding="utf-8")
    json_log = CODEX_LOG_DIR / f"{task_id}.jsonl"
    stderr_log = CODEX_LOG_DIR / f"{task_id}.stderr.log"
    last_message = workspace / "codex_last_message.txt"

    model_arg = f" --model {shlex.quote(model)}" if model else ""
    command = (
        "source ~/.zshrc >/dev/null 2>&1 || true; "
        "nvm use 22 >/dev/null; "
        f"codex -a never --sandbox danger-full-access exec --json "
        f"--cd {shlex.quote(str(workspace))}{model_arg} "
        f"--output-last-message {shlex.quote(str(last_message))} "
        f"- < {shlex.quote(str(prompt_path))} "
        f"> {shlex.quote(str(json_log))} "
        f"2> {shlex.quote(str(stderr_log))}"
    )

    started = time.time()
    proc = subprocess.Popen(
        ["zsh", "-lc", command],
        cwd=str(PROJECT_ROOT),
        start_new_session=True,
    )
    last_output_at = started
    # Treat only Codex's structured stream and final-message file as liveness.
    # Plugin-manifest warnings can keep stderr growing forever while the
    # orchestrator is actually stuck waiting on a subagent.
    heartbeat_paths = [json_log, last_message]
    last_size = _observed_size(heartbeat_paths)
    exit_code: int | None = None
    while True:
        exit_code = proc.poll()
        if exit_code is not None:
            break

        now = time.time()
        if now - started > timeout_min * 60:
            _terminate_process_group(proc, stderr_log, f"overall timeout {timeout_min}m")
            exit_code = 124
            break

        current_size = _observed_size(heartbeat_paths)
        if current_size != last_size:
            last_size = current_size
            last_output_at = now
        elif stalled_timeout_min > 0 and now - last_output_at > stalled_timeout_min * 60:
            _terminate_process_group(
                proc,
                stderr_log,
                f"stalled timeout {stalled_timeout_min}m without log heartbeat",
            )
            exit_code = 124
            break

        time.sleep(5)

    elapsed = time.time() - started
    print(f"  Codex exit={exit_code} elapsed={elapsed/60:.1f}m")
    print(f"  JSON log: {json_log}")
    print(f"  stderr:   {stderr_log}")
    return int(exit_code)


def select_tasks(files: list[str], task_id: str | None, contains: str | None) -> list[dict]:
    tasks = bo.load_tasks(files)
    if task_id:
        tasks = [task for task in tasks if task["task_id"] == task_id]
    if contains:
        tasks = [task for task in tasks if contains in task["task_id"]]
    return tasks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="UDA-Gym gen/ tree, package dir, or queries.jsonl")
    parser.add_argument("--task-id", help="Run exactly one task id")
    parser.add_argument("--filter", help="Run tasks whose id contains this string")
    parser.add_argument("--force", action="store_true", help="Reset existing Codex workspace")
    parser.add_argument("--dry-run", action="store_true", help="Prepare nothing; print selected tasks")
    parser.add_argument("--timeout", type=int, default=90, help="Codex timeout in minutes")
    parser.add_argument(
        "--stalled-timeout",
        type=int,
        default=20,
        help="Kill Codex if JSON/stderr/last-message logs do not change for this many minutes; 0 disables",
    )
    parser.add_argument("--model", help="Optional Codex model override")
    args = parser.parse_args()
    os.environ["NANOROLLOUT_ROOT"] = str(NANOROLLOUT_ROOT)

    tasks = select_tasks(args.files, args.task_id, args.filter)
    if not tasks:
        print("No matching UDA tasks.")
        return 0

    print("=" * 60)
    print("Codex UDA Materializer")
    print("=" * 60)
    print(f"Tasks:   {len(tasks)}")
    print(f"Timeout: {args.timeout} min/task")
    print(f"Stall:   {args.stalled_timeout} min without log heartbeat")
    print(f"Model:   {args.model or '(default)'}")
    print(f"Started: {datetime.now().isoformat(timespec='seconds')}")

    if args.dry_run:
        for task in tasks:
            print(f"  DRY {task['task_id']} from {task['source_file']}[{task['index']}]")
        return 0

    failures: list[str] = []
    for task in tasks:
        task_id = task["task_id"]
        print(f"\nSTART {task_id}")
        workspace, payload = prepare_workspace(task, force=args.force)
        rc = run_codex(task, payload, workspace, args.timeout, args.stalled_timeout, args.model)
        complete, reasons = workspace_complete(workspace)
        result = write_materialization_result(
            workspace,
            task_id,
            codex_rc=rc,
            complete=complete,
            reasons=reasons,
        )
        if rc == 0 and complete:
            publish_final(task_id, workspace)
            print(f"PASS  {task_id} [{result['classification']}]")
            print(f"Final: {CODEX_FINAL_DIR / task_id}")
        else:
            failures.append(task_id)
            print(f"FAIL  {task_id} [{result['classification']}]")
            if rc != 0:
                print(f"  - codex exited with {rc}")
            for reason in reasons:
                print(f"  - {reason}")
            print(f"Workspace: {workspace}")

    if failures:
        print("\nFailed tasks:")
        for task_id in failures:
            print(f"  - {task_id}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
