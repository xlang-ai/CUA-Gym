"""``WebEnv`` — a Gymnasium environment over the CUA-Gym-Hub mock websites.

Architecture recap (see ``web_env/README.md`` for the full picture):

- **Backend**: a headless/headed Chromium tab driven by Playwright
  (:class:`web_env.controller.PlaywrightController`). Screenshots and pixel
  actions are 1:1 in coordinate space (fixed viewport, ``device_scale_factor=1``).
- **Action space**: hybrid pixel-coordinate + DOM-selector dicts
  (:mod:`web_env.actions`).
- **World state**: each mock website exposes an HTTP state API
  (``/post``, ``/go``) namespaced by a per-episode session id (``sid``).
  ``reset()`` injects a :class:`web_env.task.WebTask`'s ``initial_state()``
  via this API *before* navigating the browser there (state must exist
  before the SPA's first load). ``evaluate()`` reads back ``/go`` and asks
  the task to score ``current_state`` against ``initial_state``/``state_diff``.
"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Optional, Union

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from web_env import actions as action_utils
from web_env import registry
from web_env.controller import PlaywrightController
from web_env.state_api import StateApiClient, build_episode_sid
from web_env.task import WebTask

logger = logging.getLogger("web_env.env")

_DEFAULT_VIEWPORT = (1280, 800)


class WebEnv(gym.Env):
    """Gymnasium environment wrapping one CUA-Gym-Hub mock website episode.

    Example:
        >>> from web_env import WebEnv
        >>> from web_env.tasks.task_12306_book_pay import Book12306Task
        >>> env = WebEnv(url_mode="public", headless=True)
        >>> obs = env.reset(task_config=Book12306Task())
        >>> obs, reward, terminated, truncated, info = env.step(
        ...     {"type": "click", "selector": "text=预订"}
        ... )
        >>> score = env.evaluate()
        >>> env.close()
    """

    metadata = {"render_modes": ["rgb_array", "human"]}

    def __init__(
        self,
        url_mode: str = "public",
        host: Optional[str] = None,
        viewport: tuple[int, int] = _DEFAULT_VIEWPORT,
        headless: bool = True,
        cdp_url: Optional[str] = None,
        pause_default: float = 2.0,
        keep_state_on_close: bool = False,
    ):
        """
        Args:
            url_mode: ``"public"`` to use the hosted ``cua-gym-*.xlang.ai``
                mocks, or ``"local"`` for a self-hosted deployment.
            host: local deployment host/IP (only used when ``url_mode="local"``).
            viewport: ``(width, height)`` of the browser viewport; observation
                screenshots are exactly this size.
            headless: whether to launch Chromium headless.
            cdp_url: if set, connect to an already-running Chromium instance
                over CDP instead of launching a new one (e.g.
                ``"http://localhost:9222"``).
            pause_default: default settle time (seconds) after each action,
                used when ``step(..., pause=None)``.
            keep_state_on_close: if False (default), ``close()`` also deletes
                the episode's server-side state via ``/post {"action":"reset"}``.
        """
        super().__init__()
        self.url_mode = url_mode
        self.host = host
        self.viewport = viewport
        self.headless = headless
        self.cdp_url = cdp_url
        self.pause_default = pause_default
        self.keep_state_on_close = keep_state_on_close

        self.controller = PlaywrightController(
            viewport=viewport, headless=headless, cdp_url=cdp_url
        )
        self.state_client = StateApiClient()

        self.current_task: Optional[WebTask] = None
        self.base_url: Optional[str] = None
        self.sid: Optional[str] = None
        self._step_count = 0
        self._terminated = False
        self._closed = False
        self._last_screenshot: Optional[np.ndarray] = None

        width, height = viewport
        self.observation_space = spaces.Dict(
            {
                "screenshot": spaces.Box(low=0, high=255, shape=(height, width, 3), dtype=np.uint8),
            }
        )
        # The action space is a structured dict validated at runtime by
        # web_env.actions.validate(); Gymnasium's typed Dict/Discrete spaces
        # can't cleanly express "x/y OR selector" unions, so we declare a
        # permissive Dict space here purely for introspection/documentation
        # purposes and rely on actions.validate() as the real contract.
        self.action_space = spaces.Dict(
            {
                "type": spaces.Text(max_length=32),
            }
        )

    # --- task / URL resolution --------------------------------------------

    def _resolve_task(self, task_config: Optional[Union[WebTask, dict, str, Path]]) -> WebTask:
        if task_config is None:
            if self.current_task is None:
                raise ValueError(
                    "reset() requires task_config on the first call (no current_task set)."
                )
            return self.current_task
        if isinstance(task_config, WebTask):
            return task_config
        return WebTask.from_config(task_config)

    def base_url_for(self, mock_name: str) -> str:
        """Resolve the base URL for any mock (primary or ``related_apps``)."""
        return registry.base_url(mock_name, mode=self.url_mode, host=self.host)

    # --- Gym API: reset ----------------------------------------------------

    def reset(
        self,
        task_config: Optional[Union[WebTask, dict, str, Path]] = None,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Reset the environment to a task's initial state.

        Args:
            task_config: a :class:`WebTask` instance, a dict / JSON path
                understood by ``WebTask.from_config``, or ``None`` to re-run
                the currently loaded task with a fresh episode/sid.
            seed: seeds Python/NumPy RNG (Gymnasium convention) for any
                task-side randomization.
            options: reserved for future use (e.g. per-reset overrides);
                unused fields are ignored.

        Returns:
            The initial observation dict, ``{"screenshot": np.ndarray, "url": str}``.
        """
        super().reset(seed=seed)
        options = options or {}

        task = self._resolve_task(task_config)
        self.current_task = task

        self.base_url = self.base_url_for(task.mock)
        self.sid = build_episode_sid(task.task_id)

        state = task.initial_state() or {}
        self.state_client.set_state(self.base_url, self.sid, state)
        self.state_client.verify_initial(self.base_url, self.sid)

        task.setup(self)

        self.controller.launch()
        entry_url = f"{self.base_url}/?sid={self.sid}"
        self.controller.goto(entry_url)

        self._step_count = 0
        self._terminated = False
        time.sleep(options.get("pause", self.pause_default))

        return self._observe()

    def reset_gym(
        self,
        task_config: Optional[Union[WebTask, dict, str, Path]] = None,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
    ) -> tuple[dict[str, Any], dict]:
        """Strict-Gymnasium-compliant wrapper returning ``(obs, info)``.

        ``reset()`` returns just the observation dict per this package's
        primary API; use this wrapper if you need to plug ``WebEnv`` into
        infrastructure that expects the standard Gymnasium ``reset`` contract.
        """
        obs = self.reset(task_config=task_config, seed=seed, options=options)
        info = {"sid": self.sid, "base_url": self.base_url, "task": repr(self.current_task)}
        return obs, info

    # --- Gym API: step -------------------------------------------------

    def step(self, action: dict, pause: float = 2):
        """Execute one action and advance the episode.

        Args:
            action: an action dict (see :mod:`web_env.actions`) — hybrid
                pixel-coordinate or DOM-selector targeting, e.g.
                ``{"type": "click", "x": 640, "y": 380}`` or
                ``{"type": "click", "selector": "#submit-order"}``.
            pause: seconds to sleep after executing the action, to let the
                SPA settle (state updates, animations, network) before the
                next observation/evaluation. Mirrors the mock websites' own
                async state-update patterns.

        Returns:
            ``(observation, reward, terminated, truncated, info)`` — the
            standard Gymnasium 5-tuple. ``reward`` is ``0.0`` unless the
            action is ``{"type": "terminate"}``, in which case it equals
            ``self.evaluate()``. ``truncated`` is always ``False`` (no step
            limit is enforced by the environment itself).
        """
        if self.controller is None or self.sid is None:
            raise RuntimeError("Call reset() before step().")

        validated = action_utils.validate(action)
        result = self.controller.execute(validated)

        time.sleep(pause if pause is not None else self.pause_default)
        self._step_count += 1

        terminated = action_utils.is_terminal(validated)
        self._terminated = self._terminated or terminated

        obs = self._observe()
        reward = self.evaluate() if terminated else 0.0

        info = {
            "action": validated,
            "action_result": result,
            "sid": self.sid,
            "url": self.controller.current_url(),
            "steps": self._step_count,
        }
        truncated = False
        return obs, reward, terminated, truncated, info

    # --- observation -------------------------------------------------------

    def _observe(self) -> dict[str, Any]:
        screenshot = self.controller.screenshot()
        self._last_screenshot = screenshot
        return {"screenshot": screenshot, "url": self.controller.current_url()}

    # --- evaluation ----------------------------------------------------

    def evaluate(self) -> float:
        """Score the current episode against ``self.current_task``'s rubric.

        Returns:
            A float in ``[0.0, 1.0]``. ``0.0`` if no task is loaded.
        """
        if self.current_task is None or self.base_url is None or self.sid is None:
            return 0.0
        go = self.state_client.go(self.base_url, self.sid)
        score = self.current_task.evaluate(self, go)
        return max(0.0, min(1.0, float(score)))

    # --- rendering -----------------------------------------------------

    def render(self, mode: str = "rgb_array"):
        """Render the current browser viewport.

        Args:
            mode: ``"rgb_array"`` returns an ``(H, W, 3)`` uint8 array
                (re-screenshots the live page). ``"human"`` additionally
                writes the screenshot to a temp PNG and returns its path,
                for quick visual inspection.
        """
        if self.controller is None:
            return None
        screenshot = self.controller.screenshot()
        self._last_screenshot = screenshot
        if mode == "rgb_array":
            return screenshot
        if mode == "human":
            from PIL import Image

            tmp = Path(tempfile.gettempdir()) / f"web_env_render_{self.sid or 'noepisode'}.png"
            Image.fromarray(screenshot).save(tmp)
            return str(tmp)
        raise ValueError(f"Unsupported render mode: {mode!r}")

    # --- lifecycle -----------------------------------------------------

    def close(self):
        """Release browser resources and (optionally) server-side episode state."""
        if self._closed:
            return
        self._closed = True
        try:
            if not self.keep_state_on_close and self.base_url and self.sid:
                self.state_client.reset(self.base_url, self.sid)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to reset server-side state on close: %s", e)
        self.controller.close()

    def __enter__(self) -> "WebEnv":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
