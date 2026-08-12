#!/usr/bin/env python3
"""Unified UDA query-to-task materializer using the local Kimi CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from uda_materializer.pipeline import discover, run_one


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="one UDA query package or a tree containing packages")
    parser.add_argument("--output-root", type=Path, default=Path("output/materialization"))
    parser.add_argument("--task-id", action="append", default=[])
    parser.add_argument("--model", default="local/k3")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--kimi-timeout-seconds", type=int, default=900)
    args = parser.parse_args()
    packages = discover(args.input)
    if args.task_id:
        packages = [path for path in packages if path.name in set(args.task_id)]
    if not packages:
        parser.error(f"no UDA query packages found under {args.input}")
    args.output_root.mkdir(parents=True, exist_ok=True)
    results = [
        run_one(
            package,
            output_root=args.output_root,
            kimi_model=args.model,
            force=args.force,
            dry_run=args.dry_run,
            kimi_timeout_seconds=args.kimi_timeout_seconds,
        )
        for package in packages
    ]
    print(json.dumps({"backend": "aws", "results": results}, indent=2))
    return 0 if all(item["status"] in {"planned", "candidate"} for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
