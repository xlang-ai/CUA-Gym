"""One generic UDA query -> native task bundle pipeline.

Task-specific behavior stays in the query package and is interpreted by Kimi;
this module only owns discovery, isolation, invocation, and publication gates.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import textwrap
from pathlib import Path
from typing import Any

from kimi_cli.runner import run as run_kimi


REQUIRED_QUERY_FILES = ("query.md", "check.yaml", "surface.yaml")
REQUIRED_BUNDLE_FILES = ("meta.json", "instruction.md", "setup.sh", "check.sh")


def is_query_package(path: Path) -> bool:
    return path.is_dir() and all((path / name).is_file() for name in REQUIRED_QUERY_FILES)


def discover(root: Path) -> list[Path]:
    root = root.expanduser().resolve()
    if is_query_package(root):
        return [root]
    if not root.is_dir():
        return []
    ignored = {".git", "__pycache__", ".pytest_cache", "node_modules", "build", "dist"}
    result = []
    for query in sorted(root.rglob("query.md")):
        if any(part in ignored for part in query.relative_to(root).parts):
            continue
        if is_query_package(query.parent):
            result.append(query.parent)
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"))


def prepare(package: Path, output_root: Path, *, force: bool) -> tuple[Path, dict[str, Any]]:
    task_id = package.name
    workspace = output_root / task_id
    if workspace.exists() and force:
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    source = workspace / "source" / "uda_package"
    if not source.exists():
        copy_tree(package, source)
    for name in ("bundle/exec", "bundle/hidden", "bundle/gt", "rollout"):
        (workspace / name).mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": task_id,
        "source_package": str(package),
        "workspace": str(workspace),
        "query_sha256": sha256(package / "query.md"),
        "runtime_backend": "aws",
        "teacher_model": "moonshotai/Kimi-K3",
    }
    (workspace / "task_config.json").write_text(json.dumps(payload, indent=2) + "\n")
    return workspace, payload


def _yaml_mapping(path: Path) -> dict[str, Any]:
    """Read a small optional manifest without making YAML a hard dependency."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    value = yaml.safe_load(path.read_text()) if path.is_file() else {}
    return value if isinstance(value, dict) else {}


def _copy_contents(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for child in src.iterdir():
        target = dst / child.name
        if child.is_dir():
            shutil.copytree(child, target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        else:
            shutil.copy2(child, target)


def _write_executable(path: Path, content: str) -> None:
    path.write_text(textwrap.dedent(content).lstrip())
    path.chmod(0o755)


def scaffold_native_bundle(package: Path, workspace: Path, payload: dict[str, Any]) -> None:
    """Create a conservative generic bundle before Kimi's review pass.

    This is deliberately driven by package topology, not by a game/task name.
    Kimi remains responsible for semantic review and bounded repairs, while a
    transient model/tool failure cannot leave an empty materialization tree.
    """
    bundle = workspace / "bundle"
    source = workspace / "source" / "uda_package"
    runtime = _yaml_mapping(source / "runtime.yaml")
    runtime_data = runtime.get("runtime") if isinstance(runtime.get("runtime"), dict) else runtime
    profile = runtime_data.get("profile", "general-root") if isinstance(runtime_data, dict) else "general-root"

    (bundle / "exec").mkdir(parents=True, exist_ok=True)
    (bundle / "hidden").mkdir(parents=True, exist_ok=True)
    (bundle / "gt").mkdir(parents=True, exist_ok=True)
    (bundle / "instruction.md").write_text((source / "query.md").read_text())
    (bundle / "meta.json").write_text(json.dumps({
        "id": payload["task_id"],
        "task_family": "uda",
        "driver": "uda-gym",
        "timeout_seconds": 1800,
        "runtime": {"type": "ec2", "profile": profile},
        "source_query_sha256": payload["query_sha256"],
    }, indent=2) + "\n")

    _copy_contents(source / "context", bundle / "exec" / "context")
    _copy_contents(source / "hidden", bundle / "hidden")
    _copy_contents(source / "gt", bundle / "gt")
    # Verifiers commonly resolve these manifests relative to their package
    # root. Keep them hidden/evaluator-owned rather than agent-visible.
    for name in (
        "asset_lock.json", "spec.yaml", "surface.yaml", "check.yaml",
        "runtime.yaml", "verification_contract.yaml", "template_contract.yaml",
    ):
        src = source / name
        if src.is_file():
            shutil.copy2(src, bundle / "hidden" / name)

    _write_executable(bundle / "setup.sh", r"""
        #!/usr/bin/env bash
        set -euo pipefail
        BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        WORKSPACE="${UDA_WORKSPACE:-/tmp_workspace}"
        mkdir -p "$WORKSPACE/results" "$WORKSPACE/context" "$WORKSPACE/.uda_hidden"
        cp -a "$BUNDLE_ROOT/exec/." "$WORKSPACE/"
        cp -a "$BUNDLE_ROOT/hidden/." "$WORKSPACE/.uda_hidden/"
        if [[ -f "$WORKSPACE/.uda_hidden/harness_server.py" ]]; then
          mkdir -p "$WORKSPACE/.uda_hidden/runtime"
          python3 "$WORKSPACE/.uda_hidden/harness_server.py" \
            --contract "$WORKSPACE/.uda_hidden/play_contract.json" \
            --root "$WORKSPACE/context/game" \
            --port "${UDA_GAME_PORT:-8317}" \
            --log "$WORKSPACE/.uda_hidden/runtime/move_log.jsonl" \
            >"$WORKSPACE/.uda_hidden/runtime/harness.log" 2>&1 &
          echo $! >"$WORKSPACE/.uda_hidden/runtime/harness.pid"
          python3 - "${UDA_GAME_PORT:-8317}" <<'PY'
        import socket
        import sys
        import time
        port = int(sys.argv[1])
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise SystemExit("UDA harness did not become ready")
        PY
        fi
    """)

    _write_executable(bundle / "check.sh", r"""
        #!/usr/bin/env bash
        set -euo pipefail
        WORKSPACE="${UDA_WORKSPACE:-/tmp_workspace}"
        if [[ -x "$WORKSPACE/.uda_hidden/verifier.py" || -f "$WORKSPACE/.uda_hidden/verifier.py" ]]; then
          TMP="$(mktemp -d)"
          trap 'rm -rf "$TMP"' EXIT
          cp -a "$WORKSPACE/.uda_hidden/." "$TMP/hidden/"
          cp "$WORKSPACE/.uda_hidden/asset_lock.json" "$TMP/asset_lock.json"
          set +e
          python3 "$TMP/hidden/verifier.py" \
            --package "$TMP" \
            --log "$WORKSPACE/.uda_hidden/runtime/move_log.jsonl" \
            --context-dir "$WORKSPACE/context/game" \
            --pristine-dir "$TMP/hidden/pristine_game" >"$TMP/verifier.out" 2>&1
          verifier_rc=$?
          set -e
          cat "$TMP/verifier.out"
          python3 - "$TMP/verifier.out" "$verifier_rc" <<'PY'
        import json
        import sys
        text = open(sys.argv[1], encoding="utf-8").read()
        rc = int(sys.argv[2])
        verdict = "PASS" if rc == 0 and "verdict: PASS" in text else "FAIL"
        print(json.dumps({"score": 1.0 if verdict == "PASS" else 0.0,
                          "overall_score": 1.0 if verdict == "PASS" else 0.0,
                          "verdict": verdict, "verifier_exit_code": rc}))
        PY
        else
          python3 - <<'PY'
        import json
        print(json.dumps({"overall_score": 0.0, "subscores": {}, "errors": ["no generic verifier supplied"]}))
        PY
        fi
    """)
    (workspace / "REVIEW.md").write_text(
        "# Static materialization review\n\n"
        "## Verdict: PENDING\n\n"
        "The generic scaffold was created from source topology. Kimi's review "
        "must validate every check.yaml criterion, hidden boundary, and setup/check contract.\n"
    )
    (workspace / "SANITY.md").write_text(
        "# Runtime sanity\n\n## Verdict: PENDING\n\n"
        "No runtime PASS is allowed until a real AWS worker setup and Kimi teacher rollout "
        "produce trajectory, numeric score, alignment, feedback, and screenshot evidence.\n"
    )


def prompt(payload: dict[str, Any]) -> str:
    return f"""Review and finish the already-scaffolded UDA bundle in this workspace.

Workspace: {payload['workspace']}
Task id: {payload['task_id']}
Runtime backend: AWS EC2 worker (not SimCloud)
Teacher: Kimi hybrid harness using moonshotai/Kimi-K3

The Python stage has already copied assets and created the native contract.
Inspect bundle/ first, then inspect only the source manifest needed to validate
semantic correctness. Keep source/uda_package immutable. Map every check.yaml
criterion into check.sh; do not replace a replay/state verifier with a weaker
heuristic. Repair only concrete gaps, and write/update REVIEW.md and SANITY.md.
Run bash -n and a static contract audit before returning.

There is no need to search the parent repository or invent infrastructure. Do
not reread the entire source tree. If UDA_AWS_GYM_URL is configured, run
the real AWS teacher controller and persist all evidence under rollout/. If it
is not configured, write an explicit pending runtime record and leave SANITY
pending; never claim rollout success from static checks. Do not modify the
source copy or create a per-game materializer.
"""


def bundle_complete(bundle: Path) -> bool:
    return (
        all((bundle / name).is_file() for name in REQUIRED_BUNDLE_FILES)
        and all((bundle / name).is_dir() for name in ("exec", "hidden", "gt"))
    )


def run_one(
    package: Path,
    *,
    output_root: Path,
    kimi_model: str,
    force: bool,
    dry_run: bool,
    kimi_timeout_seconds: int | None = None,
    kimi_code_home: Path | None = None,
) -> dict[str, Any]:
    workspace, payload = prepare(package, output_root, force=force)
    scaffold_native_bundle(package, workspace, payload)
    result: dict[str, Any] = {"task_id": package.name, "workspace": str(workspace)}
    if dry_run:
        result["status"] = "planned"
        return result
    log_path = workspace / "kimi.jsonl"
    rc = run_kimi(
        workspace=workspace,
        prompt=prompt(payload),
        model=kimi_model,
        skills_dir=Path(__file__).resolve().parents[1] / "kimi_cli" / "skills",
        agent_file=Path(__file__).resolve().parents[1] / "kimi_cli" / "agents" / "orchestrator.md",
        add_dirs=(package.parent,),
        log_path=log_path,
        timeout_seconds=kimi_timeout_seconds,
        kimi_code_home=kimi_code_home,
    )
    result["kimi_exit_code"] = rc
    result["bundle_complete"] = bundle_complete(workspace / "bundle")
    result["status"] = "candidate" if result["bundle_complete"] else "failed"
    (workspace / "materialization_result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
