#!/usr/bin/env python3
"""Create OSWorld Desktop ECS (skill-owned Aliyun API, no utils/env.py)."""

from __future__ import annotations

import os
import sys

from _common import (
    REQUIRED_ALIYUN,
    build_vm_config,
    get_paths,
    load_dotenv,
    load_vm_config,
    provision_env_overrides,
    save_vm_config,
)
from vm_ops import VmOpsError, create_vm


def main() -> int:
    paths = get_paths()
    load_dotenv(paths=paths)
    for key, val in provision_env_overrides().items():
        os.environ[key] = val

    missing = [k for k in REQUIRED_ALIYUN if not os.environ.get(k, "").strip()]
    if missing:
        print(f"ERROR: Missing {', '.join(missing)} — run discover_and_fill.py first", file=sys.stderr)
        return 1

    existing = load_vm_config(paths)
    existing_id = (existing.get("instance_id") or "").strip()
    if existing_id:
        existing_ip = (existing.get("vm_ip") or "").strip() or "(unknown)"
        print(
            f"ERROR: desktop_vm.json already tracks instance {existing_id} ({existing_ip}).",
            file=sys.stderr,
        )
        print(
            "Run delete.py first to remove it, or discover_and_fill.py if reusing an existing VM.",
            file=sys.stderr,
        )
        return 1

    print("[PROVISION] Creating ECS (~2–5 min)...")
    print(f"  region={os.environ.get('ALIYUN_REGION')} type={os.environ.get('ALIYUN_INSTANCE_TYPE', 'ecs.g8a.xlarge')}")
    print(f"  env={paths.env_path}")
    try:
        instance_id, vm_ip = create_vm()
    except VmOpsError as e:
        print(str(e), file=sys.stderr)
        return 1

    config = build_vm_config(
        vm_ip=vm_ip,
        instance_id=instance_id,
        region=os.environ.get("ALIYUN_REGION"),
        image_id=os.environ.get("ALIYUN_IMAGE_ID"),
    )
    save_vm_config(paths, config)

    print(f"Done: {vm_ip} instance={instance_id}")
    print(f"Instance details: {paths.vm_path}")
    print(
        "NOTE: ECS is Running, but SSH (port 22) and Flask may need 1–3 min to start. "
        "Run verify.py next — it retries automatically."
    )
    print("Next: python scripts/verify.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
