"""Playwright-backed browser controller for :class:`web_env.env.WebEnv`.

This module isolates every direct Playwright call behind a small interface
(`launch`, `goto`, `execute`, `screenshot`, `close`) so that:

1. :class:`web_env.env.WebEnv` never touches Playwright directly.
2. A different backend (e.g. a remote VM + pyautogui, à la
   ``utils/env.py``) could later be dropped in behind the same interface
   without changing ``WebEnv``.
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urljoin

import numpy as np

from web_env.actions import normalize_keys

logger = logging.getLogger("web_env.controller")

_DEFAULT_VIEWPORT = (1280, 800)


class ControllerError(Exception):
    """Raised for unrecoverable controller failures (e.g. launch failed)."""


class PlaywrightController:
    """Owns a Playwright instance, browser, context, and single active page.

    A single page is treated as "the" environment surface — computer-use
    agents operate one visible tab at a time, matching how screenshots and
    pixel-coordinate actions are interpreted.
    """

    def __init__(
        self,
        viewport: tuple[int, int] = _DEFAULT_VIEWPORT,
        headless: bool = True,
        cdp_url: Optional[str] = None,
    ):
        self.viewport = viewport
        self.headless = headless
        self.cdp_url = cdp_url

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._launched = False

    @property
    def page(self):
        if self._page is None:
            raise ControllerError("Controller has no active page. Call launch() first.")
        return self._page

    # --- lifecycle -----------------------------------------------------

    def launch(self) -> None:
        if self._launched:
            return
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        width, height = self.viewport

        if self.cdp_url:
            self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
            self._context = (
                self._browser.contexts[0] if self._browser.contexts else self._browser.new_context()
            )
        else:
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._context = self._browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1,
            )

        self._page = self._context.new_page()
        self._page.set_viewport_size({"width": width, "height": height})
        self._launched = True
        logger.info("PlaywrightController launched (headless=%s, cdp=%s)", self.headless, self.cdp_url)

    def close(self) -> None:
        if not self._launched:
            return
        try:
            if self._page is not None:
                self._page.close()
        except Exception:
            pass
        try:
            if self._context is not None and not self.cdp_url:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser is not None and not self.cdp_url:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright is not None:
                self._playwright.stop()
        except Exception:
            pass
        self._page = self._context = self._browser = self._playwright = None
        self._launched = False
        logger.info("PlaywrightController closed")

    # --- navigation ------------------------------------------------------

    def goto(self, url: str, wait_until: str = "load", timeout: int = 30_000) -> None:
        if not self._launched:
            self.launch()
        self.page.goto(url, wait_until=wait_until, timeout=timeout)

    def _resolve_relative(self, url: str) -> str:
        """Resolve relative goto URLs against the current page origin.

        Keeps the ``?sid=`` query alive across in-episode navigation the way
        SPA client-side routing normally would (e.g. ``{"type": "goto",
        "url": "/orders"}`` should reuse the current sid, not drop it).
        """
        if url.startswith("http://") or url.startswith("https://"):
            return url
        current = self.page.url
        if not current or current == "about:blank":
            return url
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        current_parsed = urlparse(current)
        target_parsed = urlparse(url)
        # Merge current query (e.g. sid) into the target if target has none.
        if not target_parsed.query:
            merged_query = current_parsed.query
        else:
            merged_query = target_parsed.query
        resolved_path = urljoin(current, target_parsed.path or current_parsed.path)
        resolved = urlunparse(
            (
                current_parsed.scheme,
                current_parsed.netloc,
                urlparse(resolved_path).path,
                "",
                merged_query,
                target_parsed.fragment,
            )
        )
        return resolved

    # --- observation -----------------------------------------------------

    def screenshot(self) -> np.ndarray:
        """Return the current viewport as an ``(H, W, 3)`` uint8 RGB array."""
        png_bytes = self.page.screenshot(type="png")
        return _png_bytes_to_rgb_array(png_bytes)

    def screenshot_bytes(self) -> bytes:
        return self.page.screenshot(type="png")

    def dom_snapshot(self, max_chars: int = 20_000) -> str:
        """Return a truncated HTML snapshot, useful for debugging/logging."""
        html = self.page.content()
        return html[:max_chars]

    def current_url(self) -> str:
        return self.page.url

    # --- action execution -------------------------------------------------

    def execute(self, action: dict) -> dict:
        """Execute a validated action dict. Never raises for user/page errors —
        returns ``{"ok": bool, "error": Optional[str]}`` so a rollout can keep
        going even if e.g. a selector wasn't found.
        """
        action_type = action["type"]
        try:
            handler = getattr(self, f"_do_{action_type}", None)
            if handler is None:
                return {"ok": False, "error": f"No handler for action type {action_type!r}"}
            handler(action)
            return {"ok": True, "error": None}
        except Exception as e:  # noqa: BLE001 - intentionally broad, reported not raised
            logger.warning("Action %s failed: %s", action, e)
            return {"ok": False, "error": str(e)}

    def _click_target(self, action: dict, click_kind: str) -> None:
        button = action.get("button", "left")
        selector = action.get("selector")
        if selector:
            if click_kind == "click":
                self.page.click(selector, button=button, timeout=10_000)
            elif click_kind == "double_click":
                self.page.dblclick(selector, button=button, timeout=10_000)
            elif click_kind == "right_click":
                self.page.click(selector, button="right", timeout=10_000)
            return
        x, y = action["x"], action["y"]
        if click_kind == "click":
            self.page.mouse.click(x, y, button=button)
        elif click_kind == "double_click":
            self.page.mouse.dblclick(x, y, button=button)
        elif click_kind == "right_click":
            self.page.mouse.click(x, y, button="right")

    def _do_click(self, action: dict) -> None:
        self._click_target(action, "click")

    def _do_double_click(self, action: dict) -> None:
        self._click_target(action, "double_click")

    def _do_right_click(self, action: dict) -> None:
        self._click_target(action, "right_click")

    def _do_type(self, action: dict) -> None:
        text = action["text"]
        selector = action.get("selector")
        if selector:
            self.page.fill(selector, text, timeout=10_000)
        else:
            self.page.keyboard.type(text)

    def _do_key(self, action: dict) -> None:
        keys = normalize_keys(action["keys"])
        self.page.keyboard.press(keys)

    def _do_scroll(self, action: dict) -> None:
        x, y = action.get("x"), action.get("y")
        if x is not None and y is not None:
            self.page.mouse.move(x, y)
        dx = action.get("dx", 0) or 0
        dy = action.get("dy", 0) or 0
        self.page.mouse.wheel(dx, dy)

    def _do_drag(self, action: dict) -> None:
        selector = action.get("selector")
        if selector:
            box = self.page.locator(selector).bounding_box(timeout=10_000)
            if box is None:
                raise ControllerError(f"Selector {selector!r} has no bounding box")
            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] / 2
        else:
            x, y = action["x"], action["y"]
        to_x, to_y = action["to_x"], action["to_y"]
        self.page.mouse.move(x, y)
        self.page.mouse.down()
        self.page.mouse.move(to_x, to_y, steps=10)
        self.page.mouse.up()

    def _do_hover(self, action: dict) -> None:
        selector = action.get("selector")
        if selector:
            self.page.hover(selector, timeout=10_000)
        else:
            self.page.mouse.move(action["x"], action["y"])

    def _do_goto(self, action: dict) -> None:
        url = self._resolve_relative(action["url"])
        self.page.goto(url, wait_until="load", timeout=30_000)

    def _do_wait(self, action: dict) -> None:
        self.page.wait_for_timeout(action.get("ms", 1000))

    def _do_terminate(self, action: dict) -> None:
        # No-op on the page itself; WebEnv.step() interprets this as done=True.
        pass


def _png_bytes_to_rgb_array(png_bytes: bytes) -> np.ndarray:
    from io import BytesIO

    from PIL import Image

    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    return np.array(img, dtype=np.uint8)
