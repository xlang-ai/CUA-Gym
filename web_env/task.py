"""Task base class for :class:`web_env.env.WebEnv`.

A :class:`WebTask` bundles together the three things a task needs to define:

1. ``instruction`` — the natural-language goal shown to the agent.
2. ``initial_state`` (+ optional ``setup``) — the world state injected into
   the mock website(s) via the state API before the episode starts.
3. ``evaluate`` — a rubric-based scoring function returning ``0.0..1.0``,
   consuming the live ``/go`` response (``{initial_state, current_state,
   state_diff}``) so partial credit can be awarded for partially-completed
   multi-step goals — mirroring the OSWorld-style task pattern in
   ``desktop_env.task_base.BaseTask`` (see e.g. the reference
   ``task_001.py``), adapted to the mock-website state-diff model instead of
   file/VM state.

Subclasses target one mock (``mock``) by default; multi-site tasks can list
extra mocks in ``related_apps`` and inject/evaluate them via ``env.state_client``
and ``env.base_url_for(name)`` from within ``setup``/``evaluate``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from web_env.env import WebEnv


class WebTask:
    """Base class for a single evaluable task against one or more mocks.

    Subclass and override ``instruction``, ``mock``, ``initial_state()``, and
    ``evaluate()`` at minimum. See ``web_env/tasks/task_12306_book_pay.py``
    for a concrete example.
    """

    #: Unique task identifier, used to build the episode ``sid``.
    task_id: str = "unnamed_task"
    #: Registry key of the primary mock this task targets, e.g. "12306_mock".
    mock: str = ""
    #: Natural-language instruction shown to the agent.
    instruction: str = ""
    #: Additional mock names involved in multi-site tasks (state is injected
    #: into these too if `setup()` is overridden to do so).
    related_apps: list[str] = []

    def __init__(self, **overrides: Any):
        for key, value in overrides.items():
            setattr(self, key, value)

    # --- setup -------------------------------------------------------------

    def initial_state(self) -> dict:
        """Return the JSON-serializable state to inject via ``action:"set"``
        into ``self.mock`` before the browser navigates. Consult the target
        mock's ``SCHEMA.md`` (under ``hub/websites/<mock>/SCHEMA.md``) for the
        required top-level keys — omitting required keys causes a blank or
        crashing UI.
        """
        return {}

    def setup(self, env: "WebEnv") -> None:
        """Optional hook for extra setup beyond a single ``initial_state()``
        injection: uploading files via ``env.state_client.upload(...)``,
        injecting state into ``related_apps`` for multi-mock tasks, etc.
        Called after the primary state injection, before the browser
        navigates to the mock.
        """
        return None

    # --- evaluation ----------------------------------------------------

    def evaluate(self, env: "WebEnv", go: dict) -> float:
        """Score the current episode in ``[0.0, 1.0]``.

        Args:
            env: the live :class:`WebEnv`, in case the task needs to read
                further server state (e.g. for ``related_apps``) or the
                current page URL.
            go: the primary mock's ``/go?sid=...`` response —
                ``{"initial_state": ..., "current_state": ..., "state_diff": ...}``.

        Subclasses should award partial credit for partially-completed
        multi-step tasks rather than a strict binary pass/fail, e.g.:

            score = 0.0
            if <sub-goal 1 met>:
                score += 0.5
            if <sub-goal 2 met>:
                score += 0.5
            return score
        """
        raise NotImplementedError("Subclasses must implement evaluate()")

    # --- config loading --------------------------------------------------

    @classmethod
    def from_config(cls, cfg: Union[dict, str, Path]) -> "WebTask":
        """Instantiate from a dict, or a path to a JSON config file.

        The config's keys are applied as attribute overrides on top of the
        class defaults (``task_id``, ``mock``, ``instruction``, plus any
        subclass-specific fields).
        """
        if isinstance(cfg, (str, Path)):
            with open(cfg, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        if not isinstance(cfg, dict):
            raise TypeError(f"task_config must be a dict, path, or WebTask, got {type(cfg)!r}")
        return cls(**cfg)

    # --- rubric helpers for subclasses --------------------------------

    @staticmethod
    def _clamp01(score: float) -> float:
        return max(0.0, min(1.0, float(score)))

    @staticmethod
    def current_state(go: dict) -> dict:
        return go.get("current_state") or {}

    @staticmethod
    def initial_state_from_go(go: dict) -> dict:
        return go.get("initial_state") or {}

    @staticmethod
    def state_diff(go: dict) -> dict:
        return go.get("state_diff") or {}

    @staticmethod
    def find_by(items: Optional[list], **fields) -> Optional[dict]:
        """Return the first dict in ``items`` whose fields match all
        ``fields`` (equality). Convenience for rubric checks like
        ``find_by(orders, trainNo="G7", seatClass="secondClassSeat")``.
        """
        for item in items or []:
            if all(item.get(k) == v for k, v in fields.items()):
                return item
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(task_id={self.task_id!r}, mock={self.mock!r})"
