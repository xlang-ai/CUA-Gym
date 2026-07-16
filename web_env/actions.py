"""Hybrid pixel/DOM action schema for :class:`web_env.env.WebEnv`.

An action is a plain ``dict`` (JSON-serializable, so it can come straight out
of a vision-language model's tool call). Every action has a ``"type"`` key
selecting the verb; targeting is either:

- **pixel-based** — ``x``/``y`` (and ``to_x``/``to_y`` for drags) in viewport
  pixel coordinates. These coordinates are 1:1 with the screenshot returned
  by :meth:`WebEnv.render`/observations, since the controller pins
  ``device_scale_factor=1`` and keeps the viewport size equal to the
  screenshot size. This is what a vision model grounds on after looking at
  a screenshot.
- **DOM-based** — ``selector`` (a Playwright selector: CSS like ``"#id"``,
  ``"css=.class"``, text like ``"text=Submit"``, or role-based like
  ``"role=button[name='Submit']"``). This is useful when the caller (e.g. a
  scripted task, or a model with accessibility-tree access) knows the exact
  element to target and doesn't want to rely on pixel grounding.

Supported ``type`` values:

    click, double_click, right_click, type, key, scroll, drag, hover,
    goto, wait, terminate

See ``web_env/README.md`` for the full reference and examples.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

VALID_TYPES = frozenset(
    {
        "click",
        "double_click",
        "right_click",
        "type",
        "key",
        "scroll",
        "drag",
        "hover",
        "goto",
        "wait",
        "terminate",
    }
)

# Verbs that may target a pixel coordinate.
_POINT_VERBS = frozenset({"click", "double_click", "right_click", "scroll", "drag", "hover"})
# Verbs that may target a DOM selector instead of / in addition to a point.
_SELECTOR_VERBS = frozenset(
    {"click", "double_click", "right_click", "type", "hover", "drag"}
)

VALID_BUTTONS = frozenset({"left", "right", "middle"})


@dataclass
class Action:
    """Typed convenience wrapper around the action dict.

    Not required to use :class:`WebEnv` (plain dicts work fine) — provided so
    callers who prefer typed construction/validation can do
    ``Action(type="click", x=10, y=20).to_dict()``.
    """

    type: str
    x: Optional[float] = None
    y: Optional[float] = None
    to_x: Optional[float] = None
    to_y: Optional[float] = None
    dx: Optional[float] = None
    dy: Optional[float] = None
    selector: Optional[str] = None
    text: Optional[str] = None
    keys: Optional[Union[str, list]] = None
    button: str = "left"
    url: Optional[str] = None
    ms: Optional[int] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {"type": self.type}
        for key in (
            "x", "y", "to_x", "to_y", "dx", "dy", "selector", "text",
            "keys", "url", "ms",
        ):
            value = getattr(self, key)
            if value is not None:
                d[key] = value
        if self.button != "left":
            d["button"] = self.button
        d.update(self.extra)
        return d


def _has_point(action: dict) -> bool:
    return action.get("x") is not None and action.get("y") is not None


def _has_selector(action: dict) -> bool:
    return bool(action.get("selector"))


def validate(action: Union[dict, Action]) -> dict:
    """Validate (and normalize to a plain dict) an action.

    Raises ``ValueError`` for structurally invalid actions (unknown type,
    missing required fields, no valid target for a verb that needs one).
    Does NOT check whether a selector actually matches an element on the
    page, or whether the pixel coordinates are within the viewport — those
    are runtime concerns handled by :class:`web_env.controller.PlaywrightController`.
    """
    if isinstance(action, Action):
        action = action.to_dict()
    if not isinstance(action, dict):
        raise ValueError(f"Action must be a dict or Action, got {type(action)!r}")

    action_type = action.get("type")
    if action_type not in VALID_TYPES:
        raise ValueError(
            f"Unknown action type {action_type!r}. Valid types: {sorted(VALID_TYPES)}"
        )

    if action_type in _POINT_VERBS and not (_has_point(action) or _has_selector(action)):
        raise ValueError(
            f"Action type '{action_type}' requires either x/y or selector"
        )

    if action_type == "drag":
        has_dest = action.get("to_x") is not None and action.get("to_y") is not None
        if not has_dest:
            raise ValueError("'drag' action requires to_x and to_y")

    if action_type == "type":
        if action.get("text") is None:
            raise ValueError("'type' action requires 'text'")

    if action_type == "key":
        if not action.get("keys"):
            raise ValueError("'key' action requires 'keys' (str or list of str)")

    if action_type == "goto":
        if not action.get("url"):
            raise ValueError("'goto' action requires 'url'")

    if action_type == "wait":
        if action.get("ms") is None:
            action = {**action, "ms": 1000}

    button = action.get("button", "left")
    if button not in VALID_BUTTONS:
        raise ValueError(f"Invalid button {button!r}. Valid: {sorted(VALID_BUTTONS)}")

    return action


def normalize_keys(keys: Union[str, list]) -> str:
    """Convert a keys spec (``"Control+A"`` or ``["Control", "a"]``) to a
    Playwright ``page.keyboard.press`` compatible string."""
    if isinstance(keys, str):
        return keys
    return "+".join(str(k) for k in keys)


def is_terminal(action: dict) -> bool:
    return action.get("type") == "terminate"
