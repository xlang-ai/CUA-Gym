#!/usr/bin/env python3
"""Verify OSWorld Flask server on provisioned VM."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from _common import get_paths, load_dotenv, load_vm_config, vm_port
from bootstrap_vm import bootstrap_vm_requirements

DEFAULT_RETRIES = 8
DEFAULT_INTERVAL_SEC = 15


def _curl(url: str, timeout: int = 15) -> tuple[int, str]:
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        return resp.status, "ok"
    except urllib.error.HTTPError as e:
        return e.code, "http_error"
    except Exception as e:
        return 0, str(e)


def _verify_direct(vm_ip: str, port: int) -> tuple[bool, str]:
    last_detail = "no response"
    for path in ("/screenshot", "/"):
        status, detail = _curl(f"http://{vm_ip}:{port}{path}")
        last_detail = detail
        if status == 200:
            return True, f"direct {path} HTTP {status}"
        if status in (404, 405):
            return True, f"direct {path} HTTP {status} (server up)"
    return False, f"direct unreachable ({last_detail})"


def _verify_ssh_tunnel(vm_ip: str, port: int, password: str) -> tuple[bool, str]:
    if not password:
        return False, "DESKTOP_SSH_PASSWORD missing for SSH tunnel"

    sock = socket.socket()
    sock.bind(("", 0))
    local_port = sock.getsockname()[1]
    sock.close()

    cmd = [
        "sshpass", "-p", password,
        "ssh", "-N",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ExitOnForwardFailure=yes",
        "-L", f"{local_port}:127.0.0.1:{port}",
        f"root@{vm_ip}",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for _ in range(20):
            time.sleep(0.5)
            if proc.poll() is not None:
                err = (proc.stderr.read() if proc.stderr else b"").decode()
                return False, f"SSH tunnel failed: {err[:200]}"
            status, _ = _curl(f"http://127.0.0.1:{local_port}/screenshot")
            if status == 200:
                return True, f"ssh_tunnel /screenshot HTTP {status}"
            status, _ = _curl(f"http://127.0.0.1:{local_port}/")
            if status in (200, 404, 405):
                return True, f"ssh_tunnel HTTP {status} (server up)"
        return False, "SSH tunnel up but Flask not responding"
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def _verify_once(vm_ip: str, port: int, password: str) -> tuple[bool, str]:
    ok, mode = _verify_direct(vm_ip, port)
    if not ok:
        ok, mode = _verify_ssh_tunnel(vm_ip, port, password)
    return ok, mode


def _is_cold_start(detail: str) -> bool:
    cold = (
        "Connection refused",
        "Connection timed out",
        "No route to host",
        "Flask not responding",
        "direct unreachable",
    )
    lower = detail.lower()
    return any(c.lower() in lower for c in cold)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify OSWorld Flask on provisioned VM")
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"Max attempts when VM is still booting (default {DEFAULT_RETRIES})",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL_SEC,
        help=f"Seconds between attempts (default {DEFAULT_INTERVAL_SEC})",
    )
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Skip pip install of repo vm_requirements.txt after verify passes",
    )
    parser.add_argument(
        "--force-bootstrap",
        action="store_true",
        help="Re-run pip install even if packages already appear on VM",
    )
    args = parser.parse_args()

    paths = get_paths()
    load_dotenv(paths=paths)
    data = load_vm_config(paths)
    vm_ip = (data.get("vm_ip") or "").strip()
    port = vm_port(data)
    if not vm_ip:
        print("ERROR: vm_ip empty in desktop_vm.json", file=sys.stderr)
        return 1

    password = os.environ.get("DESKTOP_SSH_PASSWORD", "").strip()
    last_mode = ""

    print(
        f"[VERIFY] Checking {vm_ip}:{port} — SSH/Flask may need 1–3 min after provision "
        f"(up to {args.retries} attempts, {args.interval}s apart)",
        file=sys.stderr,
    )

    for attempt in range(1, args.retries + 1):
        ok, last_mode = _verify_once(vm_ip, port, password)
        if ok:
            if attempt > 1:
                print(f"VM ready after {attempt} attempt(s)", file=sys.stderr)
            print(f"VERIFY PASS ({last_mode})")
            if args.no_bootstrap:
                return 0
            if bootstrap_vm_requirements(
                paths,
                force=args.force_bootstrap,
            ):
                return 0
            return 1

        if attempt < args.retries and _is_cold_start(last_mode):
            wait = args.interval
            print(
                f"[VERIFY] Attempt {attempt}/{args.retries} — VM still booting "
                f"({last_mode[:80]}). Waiting {wait}s…",
                file=sys.stderr,
            )
            time.sleep(wait)
            continue
        break

    print(f"VERIFY FAIL: {last_mode}", file=sys.stderr)
    print(
        "Hints: right after provision, SSH/Flask may need 1–3 min — re-run verify.py or "
        f"use --retries {DEFAULT_RETRIES} --interval {DEFAULT_INTERVAL_SEC} (defaults).",
        file=sys.stderr,
    )
    print(
        "Mac: public :5000 often blocked; verify uses SSH tunnel. "
        "Check DESKTOP_SSH_PASSWORD and SG TCP 22/5000.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
