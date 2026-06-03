#!/usr/bin/env python3
"""Install repo vm_requirements.txt on the provisioned Desktop VM via SSH."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from _common import (
    SkillPaths,
    get_paths,
    load_dotenv,
    load_vm_config,
    run_ssh,
    save_vm_config,
    scp_to_vm,
    vm_requirements_path,
)

REMOTE_REQUIREMENTS = "/tmp/vm_requirements.txt"
BOOTSTRAP_PROBE = "python3 -c \"import openpyxl, flask, pandas\""


def _packages_present(vm_ip: str, password: str) -> bool:
    result = run_ssh(vm_ip, password, BOOTSTRAP_PROBE, timeout=30)
    return result.returncode == 0


def bootstrap_vm_requirements(
    paths: SkillPaths,
    *,
    force: bool = False,
    skip_if_installed: bool = True,
) -> bool:
    load_dotenv(paths=paths)
    data = load_vm_config(paths)
    vm_ip = (data.get("vm_ip") or "").strip()
    if not vm_ip:
        print("ERROR: vm_ip empty in desktop_vm.json", file=sys.stderr)
        return False

    password = os.environ.get("DESKTOP_SSH_PASSWORD", "").strip()
    if not password:
        print("ERROR: DESKTOP_SSH_PASSWORD required for bootstrap (SSH)", file=sys.stderr)
        return False

    req_path = vm_requirements_path(paths)
    if not req_path.is_file():
        print(f"ERROR: {req_path} not found", file=sys.stderr)
        return False

    if skip_if_installed and not force and data.get("vm_requirements_installed_at"):
        if _packages_present(vm_ip, password):
            print("BOOTSTRAP SKIP (vm_requirements already installed)")
            return True

    if skip_if_installed and not force and _packages_present(vm_ip, password):
        print("BOOTSTRAP SKIP (core packages already importable on VM)")
        data["vm_requirements_installed_at"] = data.get("vm_requirements_installed_at") or datetime.now().isoformat()
        save_vm_config(paths, data)
        return True

    print(f"[BOOTSTRAP] Uploading {req_path.name} to {vm_ip}…", file=sys.stderr)
    scp = scp_to_vm(req_path, vm_ip, password, REMOTE_REQUIREMENTS, timeout=120)
    if scp.returncode != 0:
        err = (scp.stderr or scp.stdout or "scp failed").strip()
        print(f"ERROR: scp failed: {err[:500]}", file=sys.stderr)
        return False

    print(
        "[BOOTSTRAP] Running pip3 install -r vm_requirements.txt on VM (may take several minutes)…",
        file=sys.stderr,
    )
    install_cmd = (
        f"pip3 install -r {REMOTE_REQUIREMENTS} --prefer-binary "
        "--quiet --disable-pip-version-check "
        "&& rm -f " + REMOTE_REQUIREMENTS
    )
    pip = run_ssh(vm_ip, password, install_cmd, timeout=900)
    if pip.returncode != 0:
        err = (pip.stderr or pip.stdout or "pip install failed").strip()
        print(f"ERROR: pip install failed on VM:\n{err[-2000:]}", file=sys.stderr)
        return False

    if not _packages_present(vm_ip, password):
        print("ERROR: pip finished but openpyxl/flask/pandas still not importable", file=sys.stderr)
        return False

    data["vm_requirements_installed_at"] = datetime.now().isoformat()
    save_vm_config(paths, data)
    print("BOOTSTRAP PASS (vm_requirements.txt installed on VM)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Install vm_requirements.txt on Desktop VM")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run pip install even if packages appear present",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Do not skip when vm_requirements_installed_at is set",
    )
    args = parser.parse_args()

    paths = get_paths()
    ok = bootstrap_vm_requirements(
        paths,
        force=args.force,
        skip_if_installed=not args.no_skip,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
