#!/usr/bin/env python3
"""Post-materialization audit for native UDA-Gym bundles.

The audit is intentionally generic: it checks bundle hygiene, hidden-data
boundaries, runtime/profile declarations, template contract preservation, and
rollout evidence without embedding per-domain verifier logic.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


FORBIDDEN_RUNTIME_KEYS = {
    "ami",
    "ami_id",
    "launch_template",
    "launch_template_id",
    "subnet",
    "subnet_id",
    "security_group",
    "security_group_ids",
    "iam_instance_profile",
    "aws_profile",
}

INSTRUCTION_LEAK_PATTERNS = [
    r"\bhidden\b",
    r"\bgt/",
    r"/tmp_workspace/gt\b",
    r"\.uda_hidden",
    r"task_contract",
    r"golden_export",
    r"reference_manifest",
    r"\bstart_sec\b",
    r"\bend_sec\b",
    r"\btolerance_sec\b",
    r"\bsid=",
    r"/post\?sid",
    r"/go\?sid",
]

SENSITIVE_VISIBLE_NAMES = {
    "task_contract.json",
    "reference_manifest.json",
    "golden_export.mp4",
    "verification_contract.yaml",
}

CLI_SURFACE_TOOLS = {
    "bash",
    "cat",
    "ffmpeg",
    "ffprobe",
    "grep",
    "node",
    "python",
    "python3",
    "rg",
    "sed",
    "sh",
}

VISIBLE_UI_SOURCE_SUFFIXES = {".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".map"}
SOURCE_VISIBLE_UI_REALIZATIONS = {"browser_app", "dashboard_app", "mock_saas", "local_custom_ui"}
BROWSER_STORAGE_PATTERNS = [
    "localstorage",
    "indexeddb",
    "cookies",
    "history",
    "chrome sqlite",
    "default/history",
    "default/cookies",
    "leveldb",
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> Any:
    import yaml  # type: ignore

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _nonempty(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def _iter_files(root: Path):
    if not root.exists():
        return
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if any(part in {"__pycache__", ".pytest_cache", "node_modules"} for part in path.parts):
            continue
        yield path


def _surface_nodes(bundle: Path) -> list[tuple[str, dict[str, Any]]]:
    surface_path = bundle / "surface.yaml"
    if not surface_path.exists():
        return []
    try:
        surface = _load_yaml(surface_path)
    except Exception:
        return []
    surfaces = surface.get("surfaces") if isinstance(surface, dict) else None
    if not isinstance(surfaces, dict):
        return []
    nodes: list[tuple[str, dict[str, Any]]] = []
    for name, node in surfaces.items():
        if isinstance(node, dict):
            nodes.append((str(name), node))
    return nodes


def _surface_has_local_custom_ui(bundle: Path) -> bool:
    for _name, node in _surface_nodes(bundle):
        if str(node.get("realized_as") or "") == "local_custom_ui":
            return True
    check_path = bundle / "check.yaml"
    return check_path.exists() and "local_custom_ui://" in _read_text(check_path)


def _source_visible_ui_entrypoints(bundle: Path) -> list[str]:
    offenders: list[str] = []
    for name, node in _surface_nodes(bundle):
        if str(node.get("realized_as") or "") not in SOURCE_VISIBLE_UI_REALIZATIONS:
            continue
        entrypoints = node.get("entrypoints")
        if not isinstance(entrypoints, list):
            continue
        for entry in entrypoints:
            entry_s = str(entry).split()[0].strip("'\"")
            if entry_s.startswith("/tmp_workspace/context/") and Path(entry_s).suffix.lower() in VISIBLE_UI_SOURCE_SUFFIXES:
                offenders.append(f"{name}: {entry}")
    return offenders


def _add(report: dict[str, Any], severity: str, code: str, message: str, evidence: str | None = None) -> None:
    item = {"severity": severity, "code": code, "message": message}
    if evidence:
        item["evidence"] = evidence
    report["issues"].append(item)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="ignore")


def _extract_runtime(bundle: Path) -> dict[str, Any]:
    meta_path = bundle / "meta.json"
    if not meta_path.exists():
        return {}
    meta = _load_json(meta_path)
    if not isinstance(meta, dict):
        return {}
    runtime = meta.get("runtime")
    return runtime if isinstance(runtime, dict) else {}


def _extract_spec_primitives(bundle: Path) -> list[str]:
    spec_path = bundle / "spec.yaml"
    if not spec_path.exists():
        return []
    try:
        spec = _load_yaml(spec_path)
    except Exception:
        return []
    primitives = spec.get("primitives") if isinstance(spec, dict) else None
    if not isinstance(primitives, list):
        return []
    return [str(item) for item in primitives]


def _commands_from_rollout(rollout: Path) -> list[str]:
    commands: list[str] = []
    for path in rollout.rglob("codex.jsonl"):
        for line in _read_text(path).splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = event.get("item") if isinstance(event, dict) else None
            if isinstance(item, dict) and item.get("type") == "command_execution":
                command = item.get("command")
                if isinstance(command, str):
                    commands.append(command)
    return commands


def _rollout_score(rollout: Path) -> float | None:
    candidates = [
        rollout / "reward.json",
        rollout / "reward_stdout.json",
        rollout / "score.json",
        *rollout.rglob("reward.json"),
        *rollout.rglob("metadata.json"),
    ]
    for path in candidates:
        if not _nonempty(path):
            continue
        try:
            payload = _load_json(path)
        except Exception:
            continue
        stack = [payload]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                for key in ("overall_score", "reward", "score", "total_score"):
                    candidate = value.get(key)
                    if isinstance(candidate, (int, float)):
                        return float(candidate)
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
    return None


def _rollout_execution_issues(rollout: Path) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    seen_messages: set[str] = set()
    for path in rollout.rglob("trajectory.json"):
        if not _nonempty(path):
            continue
        try:
            payload = _load_json(path)
        except Exception:
            continue
        status = str(payload.get("status") or "").strip().lower()
        if status and status not in {"success", "resolved", "completed", "done"}:
            message = f"trajectory status is {status!r}"
            if message not in seen_messages:
                issues.append((message, _rel(path, rollout)))
                seen_messages.add(message)

    failure_patterns = [
        "agent run failed",
        "NonZeroAgentExitCodeError",
        "Operation timed out",
        "Command failed (exit -1)",
    ]
    for path in rollout.rglob("trial.log"):
        text = _read_text(path)
        for pattern in failure_patterns:
            if pattern in text:
                issues.append((f"trial log contains {pattern!r}", _rel(path, rollout)))
                break
    return issues


def audit_workspace(workspace: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    bundle = workspace / "bundle"
    source = workspace / "source" / "uda_package"
    rollout = workspace / "rollout"
    report: dict[str, Any] = {
        "workspace": str(workspace),
        "bundle": str(bundle),
        "issues": [],
        "summary": {"errors": 0, "warnings": 0},
    }

    required_files = ["meta.json", "instruction.md", "setup.sh", "check.sh"]
    required_dirs = ["exec", "hidden", "gt"]
    for name in required_files:
        if not (bundle / name).is_file():
            _add(report, "error", "missing_bundle_file", f"bundle/{name} is required")
    for name in required_dirs:
        if not (bundle / name).is_dir():
            _add(report, "error", "missing_bundle_dir", f"bundle/{name}/ is required")

    instruction = bundle / "instruction.md"
    if instruction.exists():
        text = _read_text(instruction)
        for pattern in INSTRUCTION_LEAK_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                _add(
                    report,
                    "error",
                    "instruction_hidden_leak",
                    f"agent-facing instruction appears to leak /{pattern}/",
                    "bundle/instruction.md",
                )

    exec_dir = bundle / "exec"
    for path in _iter_files(exec_dir) or []:
        rel = _rel(path, exec_dir)
        if rel.split("/", 1)[0] in {"hidden", "gt"} or path.name in SENSITIVE_VISIBLE_NAMES:
            _add(report, "error", "sensitive_file_in_exec", "sensitive verifier artifact is visible", f"bundle/exec/{rel}")

    source_visible_entries = _source_visible_ui_entrypoints(bundle)
    for entry in source_visible_entries:
        _add(
            report,
            "error",
            "source_visible_custom_ui_entrypoint",
            "UDA-critical browser surface points at agent-visible local UI source",
            entry,
        )

    local_custom_ui = _surface_has_local_custom_ui(bundle)
    exec_ui_sources = [
        path for path in (_iter_files(exec_dir / "context") or []) if path.suffix.lower() in VISIBLE_UI_SOURCE_SUFFIXES
    ]
    if local_custom_ui and exec_ui_sources:
        examples = ", ".join(_rel(path, bundle) for path in exec_ui_sources[:5])
        _add(
            report,
            "error",
            "agent_visible_custom_ui_source",
            "local_custom_ui bundle exposes UI source under exec/context",
            examples,
        )

    try:
        runtime = _extract_runtime(bundle)
    except Exception as exc:
        _add(report, "error", "bad_meta_json", f"bundle/meta.json is not valid JSON: {exc}")
        runtime = {}
    primitives = _extract_spec_primitives(bundle)
    if primitives:
        has_gui = any(name.startswith("uda-gui-") for name in primitives)
        has_cli = any(name.startswith("uda-cli-") for name in primitives)
        if not has_gui or not has_cli:
            _add(
                report,
                "error",
                "primitive_axis_missing",
                "from-primitive UDA tasks must include both GUI and CLI primitives",
                f"bundle/spec.yaml primitives={primitives!r}",
            )
    for key in sorted(FORBIDDEN_RUNTIME_KEYS.intersection(runtime)):
        _add(
            report,
            "error",
            "runtime_deployment_leak",
            f"runtime.{key} is deployment detail; keep task metadata declarative",
            "bundle/meta.json",
        )

    for name in ("runtime.yaml", "template_contract.yaml", "verification_contract.yaml", "asset_lock.json", "synthesis_report.yaml"):
        if (source / name).exists() and not (bundle / name).exists():
            _add(report, "error", "source_contract_not_preserved", f"source {name} was not copied into bundle")

    setup_text = _read_text(bundle / "setup.sh") if (bundle / "setup.sh").exists() else ""
    check_text = _read_text(bundle / "check.sh") if (bundle / "check.sh").exists() else ""
    if local_custom_ui:
        if "/opt/uda_apps" not in setup_text or "UDA_GYM_HARNESS_STATE_DIR" not in setup_text:
            _add(
                report,
                "error",
                "custom_ui_setup_not_isolated",
                "local_custom_ui setup must use /opt/uda_apps and harness-owned metadata",
                "bundle/setup.sh",
            )
        if "custom_ui.json" not in check_text or "UDA_GYM_HARNESS_STATE_DIR" not in check_text:
            _add(
                report,
                "error",
                "custom_ui_reward_no_server_state",
                "local_custom_ui check must read server-side state through harness metadata",
                "bundle/check.sh",
            )
        lowered_check = check_text.lower()
        for pattern in BROWSER_STORAGE_PATTERNS:
            if pattern in lowered_check:
                _add(
                    report,
                    "error",
                    "custom_ui_browser_storage_reward",
                    "local_custom_ui reward must not use browser storage or Chrome DBs as truth",
                    f"bundle/check.sh contains {pattern!r}",
                )
                break
    gt_names = {path.name for path in _iter_files(bundle / "gt") or []}
    for path in _iter_files(bundle / "hidden") or []:
        rel = _rel(path, bundle / "hidden")
        if path.name not in setup_text and path.name not in check_text and path.name not in gt_names:
            _add(
                report,
                "error",
                "orphan_hidden_fixture",
                "final hidden fixture is not referenced by setup/check and is not mirrored in gt",
                f"bundle/hidden/{rel}",
            )

    for script in ("setup.sh", "check.sh"):
        path = bundle / script
        if path.exists():
            proc = subprocess.run(["bash", "-n", str(path)], text=True, capture_output=True)
            if proc.returncode != 0:
                _add(report, "error", "shell_syntax_error", f"bundle/{script} failed bash -n", proc.stderr.strip())

    if rollout.exists():
        score = _rollout_score(rollout)
        commands = _commands_from_rollout(rollout)
        for message, evidence in _rollout_execution_issues(rollout):
            _add(
                report,
                "warning",
                "rollout_execution_failed",
                message,
                f"rollout/{evidence}",
            )
        if score is None:
            _add(report, "warning", "missing_rollout_score", "rollout exists but no parseable reward/score was found")
        if not commands and any(rollout.iterdir()):
            _add(report, "warning", "missing_agent_command_trace", "rollout exists but no Codex command trace was found")
        required_software = runtime.get("required_software") if isinstance(runtime, dict) else None
        required = {str(item).lower() for item in required_software or []}
        command_text = "\n".join(commands).lower()
        gui_required = sorted(required - CLI_SURFACE_TOOLS)
        gui_touched = any(tool in command_text for tool in gui_required)
        computer_use_trace = any(path.name.endswith(".jsonl") and "computer" in _read_text(path).lower() for path in rollout.rglob("*.jsonl"))
        if score is not None and score >= 0.95 and gui_required and not gui_touched and not computer_use_trace:
            _add(
                report,
                "warning",
                "high_score_without_declared_software_use",
                "rollout scored high without evidence of declared professional GUI/software use",
                f"required_software={gui_required}, score={score}",
            )
    else:
        _add(report, "warning", "missing_rollout_dir", "workspace has no rollout/ directory to audit")

    report["summary"]["errors"] = sum(1 for issue in report["issues"] if issue["severity"] == "error")
    report["summary"]["warnings"] = sum(1 for issue in report["issues"] if issue["severity"] == "warning")
    report["ok"] = report["summary"]["errors"] == 0
    return report


def write_audit_artifacts(workspace: Path) -> dict[str, Any]:
    report = audit_workspace(workspace)
    (workspace / "MATERIALIZATION_AUDIT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "## Verdict: " + ("PASS" if report["ok"] else "FAIL"),
        "",
        f"errors: {report['summary']['errors']}",
        f"warnings: {report['summary']['warnings']}",
        "",
    ]
    for issue in report["issues"]:
        evidence = f" ({issue['evidence']})" if issue.get("evidence") else ""
        lines.append(f"- {issue['severity'].upper()} {issue['code']}: {issue['message']}{evidence}")
    (workspace / "MATERIALIZATION_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace")
    args = parser.parse_args()
    report = write_audit_artifacts(Path(args.workspace))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
