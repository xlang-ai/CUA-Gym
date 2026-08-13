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
    required_software = runtime_data.get("required_software", []) if isinstance(runtime_data, dict) else []
    python_requirements = []
    for item in required_software if isinstance(required_software, list) else []:
        label = str(item).lower()
        if "python-chess" in label:
            python_requirements.append("chess")
        elif "playwright" in label:
            python_requirements.append("playwright")

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
    (bundle / "runtime_requirements.txt").write_text(
        "\n".join(sorted(set(python_requirements))) + ("\n" if python_requirements else "")
    )

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

    # Some query packages keep the browser payload only in the evaluator's
    # pristine copy.  If an asset lock declares the expected files, hydrate
    # the agent-visible context from that canonical copy instead of silently
    # producing a bundle that fails before gameplay is judged.  This remains
    # generic: non-browser tasks simply have no ``asset_lock``/
    # ``pristine_game`` topology and take the normal context-copy path.
    asset_lock = bundle / "hidden" / "asset_lock.json"
    pristine = bundle / "hidden" / "pristine_game"
    context_game = bundle / "exec" / "context" / "game"
    if asset_lock.is_file() and pristine.is_dir():
        locked = json.loads(asset_lock.read_text())
        expected = {
            str(item.get("path"))
            for item in locked.get("assets", [])
            if isinstance(item, dict) and item.get("path")
        }
        if not expected:
            expected = {
                str(path)
                for item in locked.get("assets", [])
                if isinstance(item, dict)
                for path in (item.get("source_files") or [])
            }
        if expected:
            context_game.mkdir(parents=True, exist_ok=True)
            for relative in sorted(expected):
                canonical = pristine / relative
                target = context_game / relative
                if canonical.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(canonical, target)

    _write_executable(bundle / "setup.sh", r"""
        #!/usr/bin/env bash
        set -euo pipefail
        BUNDLE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        WORKSPACE="${UDA_WORKSPACE:-/tmp_workspace}"
        mkdir -p "$WORKSPACE/results" "$WORKSPACE/context" "$WORKSPACE/.uda_hidden"
        if [[ -s "$BUNDLE_ROOT/runtime_requirements.txt" ]]; then
          python3 -m venv "$WORKSPACE/.uda_hidden/venv" 2>/dev/null || true
          if [[ -x "$WORKSPACE/.uda_hidden/venv/bin/python" ]]; then
            "$WORKSPACE/.uda_hidden/venv/bin/python" -m pip install --disable-pip-version-check --quiet -r "$BUNDLE_ROOT/runtime_requirements.txt"
          else
            python3 -m pip install --disable-pip-version-check --user --quiet -r "$BUNDLE_ROOT/runtime_requirements.txt"
          fi
        fi
        PYTHON_BIN="python3"
        if [[ -x "$WORKSPACE/.uda_hidden/venv/bin/python" ]]; then
          PYTHON_BIN="$WORKSPACE/.uda_hidden/venv/bin/python"
        fi
        printf '%s\n' "$PYTHON_BIN" >"$WORKSPACE/.uda_hidden/python_bin"
        cp -a "$BUNDLE_ROOT/exec/." "$WORKSPACE/"
        cp -a "$BUNDLE_ROOT/hidden/." "$WORKSPACE/.uda_hidden/"
        if [[ -f "$WORKSPACE/.uda_hidden/harness_server.py" ]]; then
          mkdir -p "$WORKSPACE/.uda_hidden/runtime"
          # Workers may be reused across UDA episodes. Stop only the
          # previous bundle-owned processes before checking readiness; an old
          # listener must not make a new task look healthy.
          if [[ -f "$WORKSPACE/.uda_hidden/runtime/harness.pid" ]]; then
            old_pid="$(cat "$WORKSPACE/.uda_hidden/runtime/harness.pid" 2>/dev/null || true)"
            [[ "$old_pid" =~ ^[0-9]+$ ]] && kill "$old_pid" 2>/dev/null || true
          fi
          if [[ -f "$WORKSPACE/.uda_hidden/runtime/browser.pid" ]]; then
            old_browser="$(cat "$WORKSPACE/.uda_hidden/runtime/browser.pid" 2>/dev/null || true)"
            [[ "$old_browser" =~ ^[0-9]+$ ]] && kill "$old_browser" 2>/dev/null || true
          fi
          # The first setup on a reused worker may predate our pid files.
          # Release only the task's dedicated listener port; do not match by
          # command name, which can accidentally terminate this setup shell.
          if command -v fuser >/dev/null 2>&1; then
            fuser -k "${UDA_GAME_PORT:-8317}/tcp" 2>/dev/null || true
          fi
          sleep 0.3
          rm -f "$WORKSPACE/.uda_hidden/runtime/harness.pid" "$WORKSPACE/.uda_hidden/runtime/browser.pid"
          "$PYTHON_BIN" "$WORKSPACE/.uda_hidden/harness_server.py" \
            --contract "$WORKSPACE/.uda_hidden/play_contract.json" \
            --root "$WORKSPACE/context/game" \
            --port "${UDA_GAME_PORT:-8317}" \
            --log "$WORKSPACE/.uda_hidden/runtime/move_log.jsonl" \
            >"$WORKSPACE/.uda_hidden/runtime/harness.log" 2>&1 &
          echo $! >"$WORKSPACE/.uda_hidden/runtime/harness.pid"
          harness_pid="$(cat "$WORKSPACE/.uda_hidden/runtime/harness.pid")"
          if ! kill -0 "$harness_pid" 2>/dev/null; then
            tail -40 "$WORKSPACE/.uda_hidden/runtime/harness.log" >&2 || true
            exit 1
          fi
          "$PYTHON_BIN" - "${UDA_GAME_PORT:-8317}" <<'PY'
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
          if [[ -d "$WORKSPACE/context/game" ]]; then
            profile="$WORKSPACE/.uda_hidden/chrome-profile"
            mkdir -p "$profile"
            game_url="http://127.0.0.1:${UDA_GAME_PORT:-8317}/"
            browser=""
            command -v google-chrome >/dev/null 2>&1 && browser="$(command -v google-chrome)"
            [[ -z "$browser" ]] && command -v chromium >/dev/null 2>&1 && browser="$(command -v chromium)"
            [[ -z "$browser" ]] && command -v chromium-browser >/dev/null 2>&1 && browser="$(command -v chromium-browser)"
            if [[ -n "$browser" ]]; then
              DISPLAY="${DISPLAY:-:0}" "$browser" --no-sandbox --no-first-run \
                --no-default-browser-check --disable-session-crashed-bubble \
                --disable-background-networking --user-data-dir="$profile" \
                --new-window "$game_url" >/dev/null 2>&1 &
              echo $! >"$WORKSPACE/.uda_hidden/runtime/browser.pid"
            fi
          fi
        fi
    """)

    _write_executable(bundle / "check.sh", r"""
        #!/usr/bin/env bash
        set -euo pipefail
        WORKSPACE="${UDA_WORKSPACE:-/tmp_workspace}"
        PYTHON_BIN="python3"
        if [[ -s "$WORKSPACE/.uda_hidden/python_bin" ]]; then
          PYTHON_BIN="$(cat "$WORKSPACE/.uda_hidden/python_bin")"
        fi
        if [[ -x "$WORKSPACE/.uda_hidden/verifier.py" || -f "$WORKSPACE/.uda_hidden/verifier.py" ]]; then
          TMP="$(mktemp -d)"
          trap 'rm -rf "$TMP"' EXIT
          cp -a "$WORKSPACE/.uda_hidden/." "$TMP/hidden/"
          cp "$WORKSPACE/.uda_hidden/asset_lock.json" "$TMP/asset_lock.json"
          set +e
          "$PYTHON_BIN" "$TMP/hidden/verifier.py" \
            --package "$TMP" \
            --log "$WORKSPACE/.uda_hidden/runtime/move_log.jsonl" \
            --context-dir "$WORKSPACE/context/game" \
            --pristine-dir "$TMP/hidden/pristine_game" >"$TMP/verifier.out" 2>&1
          verifier_rc=$?
          set -e
          cat "$TMP/verifier.out"
          "$PYTHON_BIN" - "$TMP/verifier.out" "$verifier_rc" <<'PY'
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
          "$PYTHON_BIN" - <<'PY'
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
