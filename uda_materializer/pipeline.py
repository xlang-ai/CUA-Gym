"""One generic UDA query -> native task bundle pipeline.

Task-specific behavior stays in the query package and is interpreted by Kimi;
this module only owns discovery, isolation, invocation, and publication gates.
"""

from __future__ import annotations

import hashlib
import json
import shutil
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


def prompt(payload: dict[str, Any]) -> str:
    return f"""Materialize the single UDA query in source/uda_package into bundle/.

Workspace: {payload['workspace']}
Task id: {payload['task_id']}
Runtime backend: AWS EC2 worker (not SimCloud)
Teacher: Kimi hybrid harness using moonshotai/Kimi-K3

Follow the unified uda-materializer skill and do not create task/game-specific
materializer code. Read the source manifests and query, then immediately use
Bash/Write to produce the native bundle contract:
  bundle/meta.json, instruction.md, setup.sh, check.sh,
  bundle/exec/, bundle/hidden/, bundle/gt/, REVIEW.md, and SANITY.md.
Keep source/uda_package immutable. Map every check.yaml criterion into check.sh;
do not replace a replay/state verifier with a weaker heuristic. Copy visible
assets to exec and setup/reward-only assets to hidden/gt according to the
skill. Run bash -n and a static contract audit before returning.

There is no need to search the parent repository or invent infrastructure. Do
not spend additional turns rereading already-read files: write the files now,
then inspect only the generated bundle. If UDA_AWS_GYM_URL is configured, run
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
