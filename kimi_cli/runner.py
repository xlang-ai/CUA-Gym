"""Small, documented adapter around the installed Kimi Code CLI."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
from pathlib import Path
from typing import Iterable


def command(
    *,
    workspace: Path,
    prompt: str,
    model: str | None = None,
    skills_dir: Path | None = None,
    agent_file: Path | None = None,
    add_dirs: Iterable[Path] = (),
) -> list[str]:
    """Build the official non-interactive Kimi command.

    Keeping command construction here makes the materializer backend-neutral
    and gives tests one place to assert the CLI contract.
    """
    # Kimi Code uses the process cwd as the workspace. `--work-dir` belongs
    # to the retired kimi-cli documentation and is intentionally not used.
    argv = ["kimi"]
    for path in add_dirs:
        argv.extend(("--add-dir", str(path)))
    if skills_dir:
        argv.extend(("--skills-dir", str(skills_dir)))
    if agent_file:
        argv.extend(("--agent-file", str(agent_file)))
    if model:
        argv.extend(("--model", model))
    argv.extend(("--prompt", prompt, "--output-format", "stream-json"))
    return argv


def run(
    *,
    workspace: Path,
    prompt: str,
    model: str | None = None,
    skills_dir: Path | None = None,
    agent_file: Path | None = None,
    add_dirs: Iterable[Path] = (),
    log_path: Path | None = None,
    timeout_seconds: int | None = None,
    kimi_code_home: Path | None = None,
) -> int:
    argv = command(
        workspace=workspace,
        prompt=prompt,
        model=model,
        skills_dir=skills_dir,
        agent_file=agent_file,
        add_dirs=add_dirs,
    )
    env = os.environ.copy()
    env.setdefault("KIMI_OUTPUT_FORMAT", "stream-json")
    if kimi_code_home:
        # Kimi Code resolves config.toml from KIMI_CODE_HOME.  Keeping this
        # optional lets a materialization use an isolated provider endpoint
        # without mutating the user's global CLI configuration.
        env["KIMI_CODE_HOME"] = str(kimi_code_home)
    output = log_path.open("w", encoding="utf-8") if log_path else None
    process = subprocess.Popen(
        argv,
        cwd=workspace,
        env=env,
        stdout=output,
        stderr=subprocess.STDOUT if output else None,
        start_new_session=True,
    )
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        return 124
    finally:
        if output:
            output.close()
    return process.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--skills-dir", type=Path, default=None)
    parser.add_argument("--agent-file", type=Path, default=None)
    parser.add_argument("--add-dir", type=Path, action="append", default=[])
    parser.add_argument("--log", type=Path, default=None)
    parser.add_argument("--timeout-seconds", type=int, default=None)
    parser.add_argument("--kimi-code-home", type=Path, default=None)
    args = parser.parse_args()
    return run(
        workspace=args.workspace,
        prompt=args.prompt,
        model=args.model,
        skills_dir=args.skills_dir,
        agent_file=args.agent_file,
        add_dirs=args.add_dir,
        log_path=args.log,
        timeout_seconds=args.timeout_seconds,
        kimi_code_home=args.kimi_code_home,
    )


if __name__ == "__main__":
    raise SystemExit(main())
