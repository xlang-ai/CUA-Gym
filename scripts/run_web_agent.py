#!/usr/bin/env python3
"""Run a basic Qwen-VL agent against a WebEnv task.

Example:
    # Ensure .env is filled in (see .env.example), then:
    python scripts/run_web_agent.py --max-steps 30
    python scripts/run_web_agent.py --url-mode local --host 163.7.16.44 --headed
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Repo root on sys.path so `web_env` imports work without an editable install.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _load_dotenv() -> None:
    env_path = _REPO_ROOT / ".env"
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
    except ImportError:
        # Minimal fallback: KEY=VALUE lines, no interpolation.
        if not env_path.exists():
            return
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("'").strip('"')
            os.environ.setdefault(key, value)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run QwenVLAgent on a WebEnv task")
    p.add_argument("--url-mode", choices=["public", "local"], default=None,
                   help="Override WEBENV_URL_MODE from .env")
    p.add_argument("--host", default=None, help="Local mock host (url-mode=local)")
    p.add_argument("--headed", action="store_true", help="Show the browser window")
    p.add_argument("--max-steps", type=int, default=None,
                   help="Override WEBENV_MAX_STEPS")
    p.add_argument("--pause", type=float, default=2.0,
                   help="Seconds to wait after each action")
    p.add_argument("--model", default=None, help="Override WEBENV_MODEL")
    p.add_argument("--message-cache-dir", default="./draft/message_cache",
                   help="Directory to dump sanitized LLM messages for debugging")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main() -> int:
    _load_dotenv()
    args = build_parser().parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("run_web_agent")

    from web_env import WebEnv
    from web_env.agents import QwenVLAgent
    from web_env.tasks import Book12306Task

    url_mode = args.url_mode or os.getenv("WEBENV_URL_MODE", "public")
    host = args.host or os.getenv("WEBENV_LOCAL_HOST") or None
    max_steps = args.max_steps or int(os.getenv("WEBENV_MAX_STEPS", "30"))
    headless = not args.headed and os.getenv("WEBENV_HEADLESS", "1") != "0"

    task = Book12306Task()
    agent = QwenVLAgent(
        model=args.model,
        message_cache_dir=args.message_cache_dir,
    )
    agent.reset(logger)

    env = WebEnv(url_mode=url_mode, host=host, headless=headless, pause_default=args.pause)
    logger.info(
        "Starting task=%s mock=%s url_mode=%s model=%s base_url=%s",
        task.task_id,
        task.mock,
        url_mode,
        agent.model,
        agent.base_url,
    )

    try:
        obs = env.reset(task_config=task)
        logger.info("Instruction: %s", task.instruction)
        logger.info("Opened %s", obs.get("url"))

        steps_done = 0
        terminated = False
        for step_idx in range(1, max_steps + 1):
            response, actions = agent.predict(task.instruction, obs)
            if not actions:
                logger.warning("Step %d: model returned no parseable actions. Raw:\n%s",
                               step_idx, response)
                # Force a wait so we don't spin hot on empty parses.
                actions = [{"type": "wait", "ms": 1000}]

            for action in actions:
                logger.info("Step %d action: %s", step_idx, action)
                obs, reward, terminated, _truncated, info = env.step(
                    action, pause=args.pause
                )
                steps_done = info.get("steps", step_idx)
                logger.info(
                    "  -> ok=%s reward=%.2f terminated=%s url=%s",
                    info.get("action_result", {}).get("ok"),
                    reward,
                    terminated,
                    info.get("url"),
                )
                if terminated:
                    break

            if terminated:
                break

        score = env.evaluate()
        logger.info("Final score: %.2f (steps=%d)", score, steps_done)
        return 0 if score >= 1.0 else 1
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
