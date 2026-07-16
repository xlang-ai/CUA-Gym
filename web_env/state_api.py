"""HTTP client for the CUA-Gym-Hub mock website state API.

Every mock exposes the same session-scoped state API (see ``hub/README.md``
and ``.claude/skills/mock_websites/SKILL.md``):

- ``POST /post?sid=<sid>``   — inject/update state (``set`` / ``set_current`` / ``reset``)
- ``GET  /go?sid=<sid>``     — ``{initial_state, current_state, state_diff}``
- ``GET  /state?sid=<sid>``  — raw ``{stored_state, has_custom_state, sid}``
- ``POST /upload?sid=<sid>`` — multipart file upload, returns ``{files:[...]}``

This module wraps those endpoints so :class:`web_env.env.WebEnv` and
:class:`web_env.task.WebTask` never construct raw HTTP calls themselves.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional, Union

import requests

_SID_SAFE_RE = re.compile(r"[^a-zA-Z0-9_-]")

_DEFAULT_TIMEOUT = 30


class StateApiError(Exception):
    """Raised when a mock's state API returns an unexpected response."""


def sanitize_sid(sid: str) -> str:
    """Mirror the server-side sid sanitization: keep only ``[a-zA-Z0-9_-]``."""
    return _SID_SAFE_RE.sub("", sid)


class StateApiClient:
    """Thin ``requests``-based client for one mock's state API."""

    def __init__(self, timeout: int = _DEFAULT_TIMEOUT):
        self.timeout = timeout

    # --- low-level helpers -------------------------------------------------

    def _post(self, base_url: str, path: str, sid: str, json_body: dict) -> dict:
        resp = requests.post(
            f"{base_url}{path}",
            params={"sid": sid},
            json=json_body,
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise StateApiError(
                f"POST {path} failed ({resp.status_code}) for sid={sid}: {resp.text}"
            )
        try:
            return resp.json()
        except ValueError:
            return {"raw": resp.text}

    def _get(self, base_url: str, path: str, sid: str) -> dict:
        resp = requests.get(f"{base_url}{path}", params={"sid": sid}, timeout=self.timeout)
        if resp.status_code != 200:
            raise StateApiError(
                f"GET {path} failed ({resp.status_code}) for sid={sid}: {resp.text}"
            )
        return resp.json()

    # --- public API ----------------------------------------------------

    def set_state(self, base_url: str, sid: str, state: dict, merge: bool = False) -> dict:
        """``action:"set"`` — writes both ``initial_state`` and ``current_state``.

        Used once per episode, before the browser loads the mock.
        """
        body: dict[str, Any] = {"action": "set", "state": state}
        if merge:
            body["merge"] = True
        return self._post(base_url, "/post", sid, body)

    def set_current(self, base_url: str, sid: str, state: dict, merge: bool = False) -> dict:
        """``action:"set_current"`` — writes ONLY ``current_state``.

        Used by golden-patch style helpers; never touches ``initial_state``.
        """
        body: dict[str, Any] = {"action": "set_current", "state": state}
        if merge:
            body["merge"] = True
        return self._post(base_url, "/post", sid, body)

    def reset(self, base_url: str, sid: str) -> dict:
        """``action:"reset"`` — deletes both initial and current state files."""
        return self._post(base_url, "/post", sid, {"action": "reset"})

    def go(self, base_url: str, sid: str) -> dict:
        """Returns ``{initial_state, current_state, state_diff}``."""
        return self._get(base_url, "/go", sid)

    def get_state(self, base_url: str, sid: str) -> dict:
        """Returns raw ``{stored_state, has_custom_state, sid}``."""
        return self._get(base_url, "/state", sid)

    def upload(
        self, base_url: str, sid: str, file_path: Union[str, Path], field_name: str = "file"
    ) -> dict:
        """Upload a local file, returns ``{success, files:[{url, original_name, ...}]}``."""
        file_path = Path(file_path)
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{base_url}/upload",
                params={"sid": sid},
                files={field_name: (file_path.name, f)},
                timeout=self.timeout,
            )
        if resp.status_code != 200:
            raise StateApiError(f"Upload failed ({resp.status_code}): {resp.text}")
        return resp.json()

    def verify_initial(self, base_url: str, sid: str) -> None:
        """Raise if ``initial_state`` wasn't actually persisted by :meth:`set_state`."""
        go = self.go(base_url, sid)
        if go.get("initial_state") is None:
            raise StateApiError(f"initial_state is None after injection for sid={sid}")


def build_episode_sid(task_id: str, suffix: Optional[str] = None) -> str:
    """Build a sanitized, unique-ish sid combining a task id and a random suffix."""
    import uuid

    suffix = suffix or uuid.uuid4().hex[:8]
    return sanitize_sid(f"{task_id}-{suffix}")
