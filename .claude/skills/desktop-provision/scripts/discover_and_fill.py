#!/usr/bin/env python3
"""Discover Aliyun Desktop infra from AK/SK and backfill repo root .env."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from _common import (
    build_vm_config,
    ensure_aliyun_sdk,
    get_paths,
    load_dotenv,
    missing_access_keys,
    print_access_key_setup_guide,
    save_vm_config,
)

IMAGE_HINTS = ("cua-gym", "osworld", "ubuntu_osworld")
PREFERRED_REGION = "cn-shenzhen"
DEFAULT_INSTANCE_TYPE = "ecs.g8a.xlarge"


def _require_keys() -> None:
    load_dotenv()
    paths = get_paths()
    missing = missing_access_keys()
    if missing:
        if not paths.env_path.is_file():
            print(f"ERROR: Missing {paths.env_path}", file=sys.stderr)
            print("  Run: cp .env.example .env  (from repo root)", file=sys.stderr)
        for k in missing:
            print(f"ERROR: {k} required in {paths.env_path}", file=sys.stderr)
        print_access_key_setup_guide(env_path=paths.env_path, skill_dir=paths.skill_dir)
        sys.exit(1)


def _ecs_client(region: str):
    from alibabacloud_ecs20140526.client import Client as EcsClient
    from alibabacloud_tea_openapi import models as open_api_models

    cfg = open_api_models.Config(
        access_key_id=os.environ["ALIYUN_ACCESS_KEY_ID"],
        access_key_secret=os.environ["ALIYUN_ACCESS_KEY_SECRET"],
        region_id=region,
    )
    cfg.endpoint = f"ecs.{region}.aliyuncs.com"
    return EcsClient(cfg)


def _vpc_client(region: str):
    try:
        from alibabacloud_vpc20160428.client import Client as VpcClient
    except ImportError as e:
        raise RuntimeError(
            "pip install alibabacloud_vpc20160428  # needed to discover vSwitch"
        ) from e
    from alibabacloud_tea_openapi import models as open_api_models

    cfg = open_api_models.Config(
        access_key_id=os.environ["ALIYUN_ACCESS_KEY_ID"],
        access_key_secret=os.environ["ALIYUN_ACCESS_KEY_SECRET"],
        region_id=region,
    )
    cfg.endpoint = f"vpc.{region}.aliyuncs.com"
    return VpcClient(cfg)


def _image_matches(name: str) -> bool:
    lower = (name or "").lower()
    return any(h in lower for h in IMAGE_HINTS)


def _all_region_ids() -> list[str]:
    ecs0 = _ecs_client(PREFERRED_REGION)
    from alibabacloud_ecs20140526 import models as ecs_models

    rr = ecs0.describe_regions(ecs_models.DescribeRegionsRequest())
    return [r.region_id for r in (rr.body.regions.region or []) if r.region_id]


def _region_search_order(preferred: str | None) -> list[str]:
    all_regions = _all_region_ids()
    if not preferred:
        return all_regions
    rest = [r for r in all_regions if r != preferred]
    return [preferred] + rest


def _find_image_in_region(ecs, region: str):
    from alibabacloud_ecs20140526 import models as ecs_models

    req = ecs_models.DescribeImagesRequest(
        region_id=region,
        status="Available",
        image_owner_alias="self",
        page_size=100,
    )
    resp = ecs.describe_images(req)
    images = resp.body.images.image or []
    matches = [img for img in images if _image_matches(getattr(img, "image_name", "") or "")]
    if not matches:
        return None
    matches.sort(key=lambda i: getattr(i, "creation_time", "") or "", reverse=True)
    img = matches[0]
    return img.image_id, img.image_name or img.image_id


def _instance_type_available(ecs, region: str, zone_id: str, instance_type: str) -> bool:
    from alibabacloud_ecs20140526 import models as ecs_models

    req = ecs_models.DescribeAvailableResourceRequest(
        region_id=region,
        destination_resource="InstanceType",
        instance_type=instance_type,
        zone_id=zone_id,
    )
    try:
        resp = ecs.describe_available_resource(req)
        zones = resp.body.available_zones
        if not zones or not zones.available_zone:
            return False
        az = zones.available_zone[0]
        resources = az.available_resources
        if not resources or not resources.available_resource:
            return False
        supported = resources.available_resource[0].supported_resources.supported_resource or []
        return any(s.value == instance_type and s.status == "Available" for s in supported)
    except Exception:
        return False


def _instance_public_ip(inst) -> str:
    if inst.public_ip_address and inst.public_ip_address.ip_address:
        ips = inst.public_ip_address.ip_address
        if ips:
            return ips[0]
    eip = getattr(inst, "eip_address", None)
    if eip and getattr(eip, "ip_address", None):
        return eip.ip_address
    return ""


def _instance_private_ip(inst) -> str:
    vpc = getattr(inst, "vpc_attributes", None)
    if vpc and vpc.private_ip_address:
        ips = vpc.private_ip_address.ip_address
        if ips:
            return ips[0]
    return ""


def _use_private_ip_from_env() -> bool:
    return os.environ.get("ALIYUN_USE_PRIVATE_IP", "0").strip().lower() in ("1", "true", "yes")


def _find_reusable_instance(
    ecs, region: str, image_id: str, *, use_private_ip: bool
) -> tuple[str | None, str | None, list[str]]:
    """Return (instance_id, vm_ip, stopped_instance_ids) for same-image candidates."""
    from alibabacloud_ecs20140526 import models as ecs_models

    req = ecs_models.DescribeInstancesRequest(region_id=region, page_size=100)
    resp = ecs.describe_instances(req)
    running: list[tuple[Any, str]] = []
    stopped_ids: list[str] = []
    for inst in resp.body.instances.instance or []:
        if inst.image_id != image_id:
            continue
        if inst.status == "Stopped":
            stopped_ids.append(inst.instance_id)
            continue
        if inst.status != "Running":
            continue
        ip = _instance_private_ip(inst) if use_private_ip else _instance_public_ip(inst)
        if ip:
            running.append((inst, ip))
    if not running:
        return None, None, stopped_ids
    running.sort(key=lambda pair: pair[0].creation_time or "")
    inst, ip = running[0]
    return inst.instance_id, ip, stopped_ids


def _sg_allows_ports(ecs, region: str, sg_id: str) -> bool:
    from alibabacloud_ecs20140526 import models as ecs_models

    req = ecs_models.DescribeSecurityGroupAttributeRequest(
        region_id=region, security_group_id=sg_id
    )
    resp = ecs.describe_security_group_attribute(req)
    rules = resp.body.permissions.permission or []
    ports = set()
    for r in rules:
        if (r.port_range or "").startswith("22/") or r.port_range == "22/22":
            ports.add(22)
        if "5000" in (r.port_range or ""):
            ports.add(5000)
    return 22 in ports and 5000 in ports


def _pick_security_group(ecs, region: str, vpc_id: str | None):
    from alibabacloud_ecs20140526 import models as ecs_models

    req = ecs_models.DescribeSecurityGroupsRequest(region_id=region, page_size=50)
    if vpc_id:
        req.vpc_id = vpc_id
    resp = ecs.describe_security_groups(req)
    groups = resp.body.security_groups.security_group or []
    if not groups:
        return None, None
    for g in groups:
        if _sg_allows_ports(ecs, region, g.security_group_id):
            return g.security_group_id, g.vpc_id or vpc_id
    g = groups[0]
    return g.security_group_id, g.vpc_id or vpc_id


def _vswitch_zone_map(region: str, vpc_id: str) -> dict[str, str]:
    """Return vSwitch ID -> zone ID for a VPC."""
    zones: dict[str, str] = {}
    try:
        from alibabacloud_vpc20160428 import models as vpc_models

        vpc = _vpc_client(region)
        req = vpc_models.DescribeVSwitchesRequest(region_id=region, vpc_id=vpc_id, page_size=50)
        resp = vpc.describe_vswitches(req)
        for vs in resp.body.v_switches.v_switch or []:
            if vs.v_switch_id and vs.zone_id:
                zones[vs.v_switch_id] = vs.zone_id
    except ImportError:
        pass
    return zones


def _list_candidate_vswitches(ecs, region: str, vpc_id: str) -> list[tuple[str, str]]:
    """Return (vSwitch ID, zone ID) candidates, de-duplicated."""
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    zone_map = _vswitch_zone_map(region, vpc_id)

    from alibabacloud_ecs20140526 import models as ecs_models

    req = ecs_models.DescribeInstancesRequest(region_id=region, page_size=100)
    resp = ecs.describe_instances(req)
    for inst in resp.body.instances.instance or []:
        va = getattr(inst, "vpc_attributes", None)
        if not va:
            continue
        if vpc_id and getattr(va, "vpc_id", None) != vpc_id:
            continue
        vs = getattr(va, "v_switch_id", None)
        if not vs or vs in seen:
            continue
        seen.add(vs)
        zone = zone_map.get(vs) or getattr(inst, "zone_id", "") or ""
        out.append((vs, zone))

    for vs, zone in zone_map.items():
        if vs not in seen:
            seen.add(vs)
            out.append((vs, zone))

    return out


def _pick_network_for_instance_type(
    ecs, region: str, instance_type: str
) -> tuple[str, str, str, str] | None:
    """Pick SG + vSwitch where instance_type is available. Returns sg, vpc, vswitch, zone."""
    sg_id, vpc_id = _pick_security_group(ecs, region, None)
    if not sg_id or not vpc_id:
        return None

    candidates = _list_candidate_vswitches(ecs, region, vpc_id)
    if not candidates:
        raise RuntimeError(
            f"No vSwitch found for VPC {vpc_id} in {region}. "
            "Create a vSwitch in console or: pip install alibabacloud_vpc20160428"
        )

    for vswitch_id, zone_id in candidates:
        if not zone_id:
            continue
        if _instance_type_available(ecs, region, zone_id, instance_type):
            return sg_id, vpc_id, vswitch_id, zone_id
    return None


def _find_infra(preferred_region: str | None, instance_type: str):
    """
    Find region + image + network where instance_type can be provisioned.

    Search order: preferred region first, then every other region with an OSWorld image.
    Within each region, pick a vSwitch zone that supports instance_type.
    """
    warnings: list[str] = []
    image_regions: list[tuple[str, str, str, object]] = []

    for region in _region_search_order(preferred_region):
        ecs = _ecs_client(region)
        found = _find_image_in_region(ecs, region)
        if found:
            image_regions.append((region, found[0], found[1], ecs))

    if not image_regions:
        return None, warnings

    skipped: list[str] = []
    for region, image_id, image_name, ecs in image_regions:
        try:
            net = _pick_network_for_instance_type(ecs, region, instance_type)
        except RuntimeError as e:
            warnings.append(str(e))
            continue
        if net:
            sg_id, vpc_id, vswitch_id, zone_id = net
            if preferred_region and region != preferred_region:
                warnings.append(
                    f"Switched region {preferred_region} → {region} "
                    f"(OSWorld image + {instance_type} available in zone {zone_id})"
                )
            elif preferred_region == region:
                # Same region but may have skipped incompatible zones silently
                pass
            return {
                "region": region,
                "image_id": image_id,
                "image_name": image_name,
                "ecs": ecs,
                "sg_id": sg_id,
                "vpc_id": vpc_id,
                "vswitch_id": vswitch_id,
                "zone_id": zone_id,
            }, warnings

        skipped.append(region)

    if skipped:
        warnings.append(
            f"{instance_type} is not available in any zone/vSwitch under regions with "
            f"OSWorld image: {', '.join(skipped)}. "
            "Import the image to another region, create a vSwitch in a supporting zone, "
            "or change ALIYUN_INSTANCE_TYPE in .env."
        )
    return None, warnings


def _update_env(updates: dict[str, str]) -> None:
    env_path = get_paths().env_path
    lines: list[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    keys_done = set()
    out: list[str] = []
    pat = re.compile(r"^([A-Z0-9_]+)=")
    for line in lines:
        m = pat.match(line.strip())
        if m and m.group(1) in updates:
            key = m.group(1)
            out.append(f"{key}={updates[key]}")
            keys_done.add(key)
        else:
            out.append(line)
    for key, val in updates.items():
        if key not in keys_done:
            out.append(f"{key}={val}")
    env_path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def main(*, install_deps: bool = False) -> int:
    if not ensure_aliyun_sdk(auto_install=True if install_deps else None):
        return 1
    _require_keys()
    paths = get_paths()
    preferred_region = os.environ.get("ALIYUN_REGION", "").strip() or None
    instance_type = os.environ.get("ALIYUN_INSTANCE_TYPE", "").strip() or DEFAULT_INSTANCE_TYPE

    infra, warnings = _find_infra(preferred_region, instance_type)
    for w in warnings:
        print(f"WARN: {w}")

    if not infra:
        if preferred_region:
            ecs = _ecs_client(preferred_region)
            if not _find_image_in_region(ecs, preferred_region):
                print(
                    f"ERROR: No OSWorld/cua-gym custom image in region {preferred_region}.",
                    file=sys.stderr,
                )
                print(
                    "Discover scanned all regions — import image or clear ALIYUN_REGION to auto-pick.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"ERROR: Image found in {preferred_region} but {instance_type} is unavailable "
                    "in every zone/vSwitch there.",
                    file=sys.stderr,
                )
                print(
                    "Try another region (re-import image) or set ALIYUN_INSTANCE_TYPE to a "
                    "supported type.",
                    file=sys.stderr,
                )
        else:
            print("ERROR: No matching OSWorld/cua-gym custom image in any region.", file=sys.stderr)
        print("See onboarding.md in this skill directory.", file=sys.stderr)
        return 1

    region = infra["region"]
    image_id = infra["image_id"]
    image_name = infra["image_name"]
    ecs = infra["ecs"]
    sg_id = infra["sg_id"]
    vswitch_id = infra["vswitch_id"]
    zone_id = infra["zone_id"]

    print(f"Region:  {region}")
    print(f"Image:   {image_id} ({image_name})")
    print(f"Type:    {instance_type} (zone {zone_id})")

    reuse_id, reuse_ip, stopped_ids = _find_reusable_instance(
        ecs, region, image_id, use_private_ip=_use_private_ip_from_env()
    )
    if stopped_ids and not reuse_id:
        ids = ", ".join(stopped_ids[:3])
        suffix = f" (+{len(stopped_ids) - 3} more)" if len(stopped_ids) > 3 else ""
        print(
            f"WARN: Stopped instance(s) with same image: {ids}{suffix}. "
            "Start in Aliyun console or run delete.py, then re-run discover.",
            file=sys.stderr,
        )
    if reuse_id:
        save_vm_config(
            paths,
            build_vm_config(
                vm_ip=reuse_ip or "",
                instance_id=reuse_id,
                region=region,
                image_id=image_id,
            ),
        )
        ip_mode = "private" if _use_private_ip_from_env() else "public"
        print(f"REUSE instance_id={reuse_id} vm_ip={reuse_ip} ({ip_mode})")
        print(f"Instance details: {paths.vm_path}")
        print("Skip provision.py — run verify.py (SSH/Flask may need 1–3 min if instance just started).")

    updates = {
        "ALIYUN_REGION": region,
        "ALIYUN_IMAGE_ID": image_id,
        "ALIYUN_VSWITCH_ID": vswitch_id,
        "ALIYUN_SECURITY_GROUP_ID": sg_id,
        "ALIYUN_INSTANCE_TYPE": instance_type,
        "ALIYUN_USE_PRIVATE_IP": os.environ.get("ALIYUN_USE_PRIVATE_IP", "0") or "0",
    }
    _update_env(updates)
    print(f"vSwitch: {vswitch_id}")
    print(f"SG:      {sg_id}")
    print(f"Updated: {paths.env_path}")
    if os.environ.get("ALIYUN_USE_PRIVATE_IP", "0").strip() in ("1", "true", "yes"):
        print("TIP: Set ALIYUN_USE_PRIVATE_IP=0 in .env when provisioning from Mac (public IP)")
    if not reuse_id:
        print("Next: set DESKTOP_SSH_PASSWORD if empty, then follow SKILL.md § Provision")
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Discover Aliyun Desktop infra and backfill .env")
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Auto-install missing Aliyun Python SDK (no prompt)",
    )
    args = parser.parse_args()
    raise SystemExit(main(install_deps=args.install_deps))
