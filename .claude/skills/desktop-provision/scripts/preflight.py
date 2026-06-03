#!/usr/bin/env python3
"""Pre-flight checks before discover / provision."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys

from _common import (
    ALIYUN_SDK_PACKAGES,
    REQUIRED_ALIYUN,
    ensure_aliyun_sdk,
    get_paths,
    load_dotenv,
    missing_access_keys,
    print_access_key_setup_guide,
    vm_requirements_path,
)


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"OK: {msg}")


def _check_instance_type_zone() -> list[str]:
    issues: list[str] = []
    region = os.environ.get("ALIYUN_REGION", "").strip()
    vswitch = os.environ.get("ALIYUN_VSWITCH_ID", "").strip()
    itype = os.environ.get("ALIYUN_INSTANCE_TYPE", "ecs.g8a.xlarge").strip()
    if not (region and vswitch):
        return issues

    try:
        from alibabacloud_ecs20140526.client import Client as EcsClient
        from alibabacloud_ecs20140526 import models as ecs_models
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_vpc20160428.client import Client as VpcClient
        from alibabacloud_vpc20160428 import models as vpc_models
    except ImportError as e:
        return [str(e)]

    cfg = open_api_models.Config(
        access_key_id=os.environ["ALIYUN_ACCESS_KEY_ID"],
        access_key_secret=os.environ["ALIYUN_ACCESS_KEY_SECRET"],
        region_id=region,
    )
    cfg.endpoint = f"ecs.{region}.aliyuncs.com"
    ecs = EcsClient(cfg)

    vcfg = open_api_models.Config(
        access_key_id=os.environ["ALIYUN_ACCESS_KEY_ID"],
        access_key_secret=os.environ["ALIYUN_ACCESS_KEY_SECRET"],
        region_id=region,
    )
    vcfg.endpoint = f"vpc.{region}.aliyuncs.com"
    vpc = VpcClient(vcfg)
    vs_resp = vpc.describe_vswitches(
        vpc_models.DescribeVSwitchesRequest(region_id=region, v_switch_id=vswitch)
    )
    switches = vs_resp.body.v_switches.v_switch or []
    if not switches:
        issues.append(f"vSwitch {vswitch} not found in {region}")
        return issues
    zone = switches[0].zone_id

    req = ecs_models.DescribeAvailableResourceRequest(
        region_id=region,
        destination_resource="InstanceType",
        instance_type=itype,
        zone_id=zone,
    )
    resp = ecs.describe_available_resource(req)
    zones = resp.body.available_zones
    if not zones or not zones.available_zone:
        issues.append(f"{itype} not available in zone {zone} — re-run discover_and_fill.py")
        return issues
    supported = (
        zones.available_zone[0]
        .available_resources.available_resource[0]
        .supported_resources.supported_resource
        or []
    )
    if not any(s.value == itype and s.status == "Available" for s in supported):
        issues.append(f"{itype} not available in zone {zone} — re-run discover_and_fill.py")
    else:
        _ok(f"{itype} available in zone {zone}")
    return issues


def main(*, install_deps: bool = False) -> int:
    if not ensure_aliyun_sdk(auto_install=True if install_deps else None):
        return 1

    paths = get_paths()
    if not paths.env_path.is_file():
        _fail(f"Missing {paths.env_path} — copy from .env.example or set DESKTOP_PROVISION_ENV_FILE")
        print("  Run from repo root: cp .env.example .env", file=sys.stderr)
        print_access_key_setup_guide(env_path=paths.env_path, skill_dir=paths.skill_dir)
        return 1

    load_dotenv(paths=paths)
    issues: list[str] = []

    if missing_access_keys():
        for var in ("ALIYUN_ACCESS_KEY_ID", "ALIYUN_ACCESS_KEY_SECRET"):
            if not os.environ.get(var, "").strip():
                issues.append(f"Missing {var}")
        print_access_key_setup_guide(env_path=paths.env_path, skill_dir=paths.skill_dir)

    if not os.environ.get("DESKTOP_SSH_PASSWORD", "").strip():
        issues.append("Missing DESKTOP_SSH_PASSWORD (needed for SSH verify / tunnel)")

    if shutil.which("sshpass"):
        _ok("sshpass installed")
    else:
        issues.append("sshpass not found (brew install sshpass / apt install sshpass)")

    for pkg in ALIYUN_SDK_PACKAGES:
        if importlib.util.find_spec(pkg):
            _ok(pkg)
        else:
            issues.append(f"{pkg} not installed")

    post_discover = all(os.environ.get(k, "").strip() for k in REQUIRED_ALIYUN[2:])
    if post_discover:
        _ok("Discover fields present in .env")
        issues.extend(_check_instance_type_zone())
    else:
        missing = [k for k in REQUIRED_ALIYUN[2:] if not os.environ.get(k, "").strip()]
        print(f"INFO: Run discover_and_fill.py to fill: {', '.join(missing)}")

    use_private = os.environ.get("ALIYUN_USE_PRIVATE_IP", "0").strip()
    if use_private == "1":
        print("WARN: ALIYUN_USE_PRIVATE_IP=1 — use 0 when provisioning from Mac (public IP)")
    else:
        _ok("ALIYUN_USE_PRIVATE_IP=0 (public IP for Mac)")

    req = vm_requirements_path(paths)
    if req.is_file():
        _ok(f"vm_requirements.txt present ({req})")
    else:
        issues.append(f"Missing {req} — required for verify/bootstrap pip install on VM")

    if issues:
        for i in issues:
            _fail(i)
        return 1

    print("PREFLIGHT PASS")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-flight checks for desktop-provision")
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Auto-install missing Aliyun Python SDK (no prompt)",
    )
    args = parser.parse_args()
    raise SystemExit(main(install_deps=args.install_deps))
