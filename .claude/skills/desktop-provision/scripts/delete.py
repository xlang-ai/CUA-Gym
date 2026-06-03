#!/usr/bin/env python3
"""Delete OSWorld Desktop ECS and clear local config."""

from __future__ import annotations

import sys

from _common import clear_vm_config, collect_aliyun_env_vars, get_paths, load_dotenv, load_vm_config
from vm_ops import VmOpsError, delete_vm, wait_until_deletable


def _env_for_instance(config: dict) -> dict[str, str]:
    env_vars = collect_aliyun_env_vars()
    region = (config.get("region") or "").strip()
    if region:
        env_vars["ALIYUN_REGION"] = region
    return env_vars


def main() -> int:
    paths = get_paths()
    load_dotenv(paths=paths)

    config = load_vm_config(paths)
    instance_id = (config.get("instance_id") or "").strip()
    vm_ip = (config.get("vm_ip") or "").strip()
    if not instance_id:
        print("ERROR: No instance_id in desktop_vm.json", file=sys.stderr)
        return 1

    env_vars = _env_for_instance(config)
    region = env_vars.get("ALIYUN_REGION", "")
    print(f"[DELETE] instance={instance_id} ip={vm_ip or '(unknown)'} region={region or '(from .env)'}")
    wait_until_deletable(instance_id, env_vars=env_vars)
    try:
        delete_vm(instance_id, env_vars=env_vars)
    except VmOpsError as e:
        print(str(e), file=sys.stderr)
        return 1

    clear_vm_config(paths)
    print(f"Deleted {instance_id} and cleared {paths.vm_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
