#!/usr/bin/env python3
"""Verify that Kimi has a complete one-for-one materialization asset mirror."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def rels(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    checks = [
        (ROOT / ".codex" / "skills", ROOT / "kimi_cli" / "skills"),
        (ROOT / ".claude" / "agents", ROOT / "kimi_cli" / "agents"),
        (ROOT / ".claude" / "commands", ROOT / "kimi_cli" / "commands"),
    ]
    failures: list[str] = []
    for source, target in checks:
        source_files, target_files = rels(source), rels(target)
        if source_files != target_files:
            failures.append(f"topology mismatch: {source} -> {target}")
            missing, extra = source_files - target_files, target_files - source_files
            if missing:
                failures.append(f"  missing: {sorted(missing)}")
            if extra:
                failures.append(f"  extra: {sorted(extra)}")
    if failures:
        print("\n".join(failures))
        return 1
    print("Kimi asset mirror topology: PASS")
    print(f"skills={len(rels(checks[0][0]))} agents={len(rels(checks[1][0]))} commands={len(rels(checks[2][0]))}")
    print("Adapted runtime files: kimi_cli/agents/orchestrator.md, kimi_cli/skills/uda-gym-materializer/SKILL.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
