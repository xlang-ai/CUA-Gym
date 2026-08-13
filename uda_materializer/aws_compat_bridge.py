"""Bridge the generic UDA Gym protocol to an AWS ``uda_compat_server``.

The EC2 AMI exposes desktop primitives under ``/v1/*`` rather than the
benchmark-facing ``/reset``/``/step``/``/evaluate`` contract.  This small
local proxy keeps that provider detail out of the materializer and teacher
harness.  It is intentionally bundle-agnostic: task-specific behavior stays
inside the native bundle and its scripts.
"""

from __future__ import annotations

import argparse
import base64
import http.server
import json
import os
import shlex
import socketserver
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _request(base: str, path: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> Any:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        base.rstrip("/") + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        raw = response.read()
    return json.loads(raw) if raw else None


class AwsCompatBridge:
    def __init__(self, compat_url: str, bundle_root: Path, remote_root: str) -> None:
        self.compat_url = compat_url.rstrip("/")
        self.bundle_root = bundle_root.resolve()
        self.remote_root = remote_root.rstrip("/")
        self.active_task: str | None = None
        self.deployed: set[str] = set()

    def _shell(self, command: str, *, cwd: str | None = None, timeout: int = 900) -> dict[str, Any]:
        payload: dict[str, Any] = {"command": command, "timeout": timeout}
        if cwd:
            payload["exec_dir"] = cwd
        result = _request(self.compat_url, "/v1/shell/exec", method="POST", payload=payload)
        return result.get("data", result) if isinstance(result, dict) else {}

    def _deploy(self, task: str) -> str:
        bundle = (self.bundle_root / task / "bundle").resolve()
        if self.bundle_root not in bundle.parents or not bundle.is_dir():
            raise ValueError(f"bundle not found: {task}")
        remote = f"{self.remote_root}/{task}"
        if task in self.deployed:
            return remote
        archive = Path("/tmp") / f"uda-bundle-{task.replace('/', '_')}-{os.getpid()}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for path in sorted(bundle.rglob("*")):
                tar.add(path, arcname=path.relative_to(bundle).as_posix())
        archive_bytes = archive.read_bytes()
        remote_archive = "/tmp/uda-bundle.tar.gz"
        chunk_size = 48 * 1024
        for offset in range(0, len(archive_bytes), chunk_size):
            chunk = base64.b64encode(archive_bytes[offset : offset + chunk_size]).decode("ascii")
            result = _request(
                self.compat_url,
                "/v1/file/write",
                method="POST",
                payload={
                    "file": remote_archive,
                    "content": chunk,
                    "encoding": "base64",
                    "append": offset > 0,
                },
            )
            if isinstance(result, dict) and result.get("success") is False:
                raise RuntimeError(f"remote archive chunk upload failed at {offset}")
        command = (
            f"mkdir -p {shlex.quote(remote)}; "
            f"tar -xzf {shlex.quote(remote_archive)} -C {shlex.quote(remote)}; "
            f"chmod +x {shlex.quote(remote + '/setup.sh')} {shlex.quote(remote + '/check.sh')}"
        )
        result = self._shell(command, timeout=900)
        archive.unlink(missing_ok=True)
        if int(result.get("returncode", result.get("exit_code", 1))) != 0:
            raise RuntimeError(f"remote bundle upload failed: {result}")
        self.deployed.add(task)
        return remote

    def _screenshot(self) -> str:
        result = _request(
            self.compat_url,
            "/v1/computer-use/action",
            method="POST",
            payload={"action": "screenshot"},
        )
        if isinstance(result, dict):
            return str(result.get("base64_image") or result.get("data", {}).get("base64_image") or "")
        return ""

    def reset(self, task: str) -> dict[str, Any]:
        remote = self._deploy(task)
        command = (
            f"export UDA_WORKSPACE=/tmp_workspace; "
            f"mkdir -p /tmp_workspace; "
            f"bash {shlex.quote(remote + '/setup.sh')}"
        )
        result = self._shell(command, cwd=remote, timeout=240)
        if int(result.get("returncode", result.get("exit_code", 1))) != 0:
            raise RuntimeError(str(result))
        self.active_task = task
        for _ in range(30):
            shot = self._screenshot()
            if shot:
                return {"obs": {"pixels_b64": shot}, "task_id": task}
            time.sleep(0.5)
        raise RuntimeError("AWS desktop screenshot unavailable after setup")

    @staticmethod
    def _map_action(action: dict[str, Any]) -> dict[str, Any]:
        kind = str(action.get("action_type", "")).upper()
        if kind == "CLICK":
            return {"action": "left_click", "coordinate": [action["x"], action["y"]]}
        if kind == "DOUBLE_CLICK":
            return {"action": "double_click", "coordinate": [action["x"], action["y"]]}
        if kind == "RIGHT_CLICK":
            return {"action": "right_click", "coordinate": [action["x"], action["y"]]}
        if kind == "MOVE_TO":
            return {"action": "mouse_move", "coordinate": [action["x"], action["y"]]}
        if kind == "DRAG_TO":
            return {
                "action": "left_click_drag",
                "start_coordinate": [action["x"], action["y"]],
                "coordinate": [action["end_x"], action["end_y"]],
            }
        if kind == "TYPING":
            return {"action": "type", "text": action.get("text", "")}
        if kind == "PRESS":
            key = str(action.get("key", ""))
            key = {"ArrowLeft": "left", "ArrowRight": "right", "ArrowUp": "up", "ArrowDown": "down", "Enter": "Return"}.get(key, key)
            return {"action": "key", "key": key, "text": key}
        if kind == "HOTKEY":
            keys = action.get("keys", [])
            return {"action": "key", "key": "+".join(str(k) for k in keys), "text": "+".join(str(k) for k in keys)}
        if kind == "WAIT":
            return {"action": "wait", "duration": 1}
        if kind == "EXECUTE_CODE":
            raise ValueError("EXECUTE_CODE is not allowed through the AWS bridge")
        raise ValueError(f"unsupported UDA action type: {kind}")

    def step(self, action: dict[str, Any]) -> dict[str, Any]:
        mapped = self._map_action(action)
        result = _request(self.compat_url, "/v1/computer-use/action", method="POST", payload=mapped)
        if isinstance(result, dict) and result.get("error"):
            raise RuntimeError(str(result["error"]))
        shot = str(result.get("base64_image") or result.get("data", {}).get("base64_image") or "")
        return {"obs": {"pixels_b64": shot}, "action": action}

    def evaluate(self) -> dict[str, Any]:
        if not self.active_task:
            raise RuntimeError("no active AWS UDA task")
        remote = f"{self.remote_root}/{self.active_task}"
        result = self._shell(
            f"export UDA_WORKSPACE=/tmp_workspace; bash {shlex.quote(remote + '/check.sh')}",
            cwd=remote,
            timeout=900,
        )
        output = str(result.get("output", ""))
        payload = None
        for line in reversed(output.splitlines()):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                payload = value
                break
        if payload is None:
            raise RuntimeError("AWS UDA check emitted no JSON result")
        score = payload.get("score", payload.get("reward", payload.get("overall_score")))
        if not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
            raise RuntimeError(f"AWS UDA check emitted invalid score: {payload}")
        return {"is_successful": float(score), "evaluation_result": payload, "raw_output": output}


class Handler(http.server.BaseHTTPRequestHandler):
    bridge: AwsCompatBridge

    def _send(self, payload: dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        if self.path == "/health":
            try:
                _request(self.bridge.compat_url, "/v1/sandbox")
                self._send({"status": "ok", "backend": "aws-compat"})
            except Exception as exc:
                self._send({"status": "degraded", "error": str(exc)}, 503)
            return
        if self.path == "/tool/screenshot":
            self._send({"pixels_b64": self.bridge._screenshot()})
            return
        self._send({"error": "not found"}, 404)

    def do_POST(self) -> None:
        try:
            body = self._body()
            if self.path == "/reset":
                task = str(body.get("task_name") or body.get("task_id"))
                self._send(self.bridge.reset(task)); return
            if self.path == "/step":
                self._send(self.bridge.step(body.get("json_action") or {})); return
            if self.path == "/evaluate":
                self._send(self.bridge.evaluate()); return
            if self.path == "/tool/screenshot":
                self._send({"pixels_b64": self.bridge._screenshot()}); return
            if self.path == "/tool/exec":
                data = self.bridge._shell(str(body.get("script", "")), timeout=int(body.get("timeout", 180)))
                self._send({"output": data.get("output", ""), "error": data.get("error", ""), "returncode": data.get("returncode", data.get("exit_code", 1))}); return
            if self.path == "/tool/file/read":
                path = body.get("path") or body.get("file")
                result = _request(self.bridge.compat_url, "/v1/file/read", method="POST", payload={"file": path})
                content = result.get("data", {}).get("content", "")
                self._send({"content_b64": base64.b64encode(content.encode()).decode()}); return
            if self.path == "/tool/file/write":
                path = body.get("path") or body.get("file")
                raw = base64.b64decode(body.get("content_b64", ""), validate=True)
                # The EC2 compatibility endpoint accepts small text writes,
                # but long Kimi memory snapshots can exceed its single-call
                # body limit. Preserve byte-exact UTF-8 content while using
                # the same append protocol as bundle deployment.
                chunk_size = 32 * 1024
                chunks = [raw[i:i + chunk_size] for i in range(0, len(raw), chunk_size)] or [b""]
                for index, chunk in enumerate(chunks):
                    result = _request(
                        self.bridge.compat_url,
                        "/v1/file/write",
                        method="POST",
                        payload={
                            "file": path,
                            "content": chunk.decode("utf-8"),
                            "append": bool(body.get("append", False)) or index > 0,
                        },
                    )
                    if isinstance(result, dict) and result.get("success") is False:
                        raise RuntimeError(f"AWS file write failed at chunk {index}")
                self._send({"ok": bool(result)}); return
            self._send({"error": "not found"}, 404)
        except Exception as exc:
            self._send({"error": str(exc)}, 500)

    def log_message(self, *_args: Any) -> None:
        return


def serve(compat_url: str, bundle_root: Path, port: int, remote_root: str) -> None:
    bridge = AwsCompatBridge(compat_url, bundle_root, remote_root)
    handler = type("AwsBridgeHandler", (Handler,), {"bridge": bridge})
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as server:
        server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compat-url", default=os.environ.get("UDA_AWS_COMPAT_URL", "http://127.0.0.1:8080"))
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=18731)
    parser.add_argument("--remote-root", default="/home/user/uda_tasks")
    args = parser.parse_args()
    serve(args.compat_url, args.bundle_root, args.port, args.remote_root)


if __name__ == "__main__":
    main()
