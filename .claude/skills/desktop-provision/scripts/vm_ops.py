"""Aliyun ECS create/delete for desktop-provision skill (self-contained, no utils/env.py)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from _common import collect_aliyun_env_vars, get_paths, python_bin

# Single instance type only; no fallback chain. No public Flask wait (use verify.py).
_VM_CREATE_SCRIPT = r'''
import os, sys, time, json

from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_tea_openapi import models as open_api_models

region = os.environ.get("ALIYUN_REGION", "cn-shenzhen")
itype = os.environ.get("ALIYUN_INSTANCE_TYPE", "ecs.g8a.xlarge")

api_cfg = open_api_models.Config(
    access_key_id=os.environ["ALIYUN_ACCESS_KEY_ID"],
    access_key_secret=os.environ["ALIYUN_ACCESS_KEY_SECRET"],
)
api_cfg.endpoint = f"ecs.{region}.aliyuncs.com"
client = EcsClient(api_cfg)

sys_disk = ecs_models.RunInstancesRequestSystemDisk(size="80", category="cloud_essd")
req = ecs_models.RunInstancesRequest(
    region_id=region,
    image_id=os.environ["ALIYUN_IMAGE_ID"],
    instance_type=itype,
    security_group_id=os.environ["ALIYUN_SECURITY_GROUP_ID"],
    v_switch_id=os.environ["ALIYUN_VSWITCH_ID"],
    instance_charge_type="PostPaid",
    internet_max_bandwidth_out=10,
    system_disk=sys_disk,
    amount=1,
)
rg = os.environ.get("ALIYUN_RESOURCE_GROUP_ID")
if rg:
    req.resource_group_id = rg

resp = client.run_instances(req)
print(f"INSTANCE_TYPE_USED={itype}", flush=True)
instance_id = resp.body.instance_id_sets.instance_id_set[0]
print(f"INSTANCE_ID={instance_id}", flush=True)

for i in range(60):
    time.sleep(5)
    d = ecs_models.DescribeInstancesRequest(
        region_id=region,
        instance_ids=json.dumps([instance_id]),
    )
    dr = client.describe_instances(d)
    insts = dr.body.instances.instance
    if insts and insts[0].status == "Running":
        inst = insts[0]
        break
    print(f"WAIT status={insts[0].status if insts else 'unknown'}", flush=True)
else:
    print("ERROR=timeout_waiting_for_running")
    sys.exit(1)

use_private = os.environ.get("ALIYUN_USE_PRIVATE_IP", "0") == "1"
ip = ""
if use_private and inst.vpc_attributes and inst.vpc_attributes.private_ip_address:
    ips = inst.vpc_attributes.private_ip_address.ip_address
    ip = ips[0] if ips else ""
else:
    if inst.public_ip_address:
        ips = inst.public_ip_address.ip_address
        ip = ips[0] if ips else ""
    if not ip and hasattr(inst, "eip_address") and inst.eip_address:
        ip = inst.eip_address.ip_address or ""

if not ip:
    print("ERROR=no_ip_found")
    sys.exit(1)

print(f"VM_IP={ip}", flush=True)
print("CREATION_COMPLETE", flush=True)
'''

_VM_DELETE_SCRIPT = r'''
import os, sys, time

from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_tea_openapi import models as open_api_models

region = os.environ.get("ALIYUN_REGION", "cn-shenzhen")
instance_id = os.environ["INSTANCE_ID"]

api_cfg = open_api_models.Config(
    access_key_id=os.environ["ALIYUN_ACCESS_KEY_ID"],
    access_key_secret=os.environ["ALIYUN_ACCESS_KEY_SECRET"],
)
api_cfg.endpoint = f"ecs.{region}.aliyuncs.com"
client = EcsClient(api_cfg)

for attempt in range(3):
    try:
        req = ecs_models.DeleteInstanceRequest(instance_id=instance_id, force=True)
        client.delete_instance(req)
        print(f"DELETED={instance_id}", flush=True)
        break
    except Exception as e:
        print(f"DELETE attempt {attempt+1} failed: {e}", flush=True)
        if attempt < 2:
            time.sleep(15)
else:
    print("ERROR=delete_failed_after_retries")
    sys.exit(1)
'''


class VmOpsError(RuntimeError):
    pass


def _run_script(script: str, env_vars: dict[str, str], *, timeout: int, cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update({k: str(v) for k, v in env_vars.items()})
    return subprocess.run(
        [python_bin(), "-"],
        input=script,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(cwd),
        env=env,
    )


def _parse_stdout(stdout: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in stdout.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def wait_until_deletable(instance_id: str, env_vars: dict[str, str] | None = None, timeout: int = 300) -> None:
    env_vars = env_vars or collect_aliyun_env_vars()
    region = env_vars.get("ALIYUN_REGION", "cn-shenzhen")
    from alibabacloud_ecs20140526.client import Client as EcsClient
    from alibabacloud_ecs20140526 import models as ecs_models
    from alibabacloud_tea_openapi import models as open_api_models

    cfg = open_api_models.Config(
        access_key_id=env_vars["ALIYUN_ACCESS_KEY_ID"],
        access_key_secret=env_vars["ALIYUN_ACCESS_KEY_SECRET"],
        region_id=region,
    )
    cfg.endpoint = f"ecs.{region}.aliyuncs.com"
    client = EcsClient(cfg)

    for i in range(timeout // 5):
        resp = client.describe_instances(
            ecs_models.DescribeInstancesRequest(
                region_id=region,
                instance_ids=json.dumps([instance_id]),
            )
        )
        insts = resp.body.instances.instance or []
        status = insts[0].status if insts else "Unknown"
        if status in ("Running", "Stopped"):
            if i:
                print(f"Instance ready for delete (status={status})")
            return
        print(f"Waiting for deletable status (current={status})...")
        time.sleep(5)
    print("WARN: Timed out waiting for Running/Stopped; attempting delete anyway")


def create_vm(env_vars: dict[str, str] | None = None, timeout: int = 420) -> tuple[str, str]:
    paths = get_paths()
    env_vars = env_vars or collect_aliyun_env_vars()
    result = _run_script(_VM_CREATE_SCRIPT, env_vars, timeout=timeout, cwd=paths.repo_root)
    if result.returncode != 0:
        raise VmOpsError(
            f"VM creation failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    parsed = _parse_stdout(result.stdout)
    instance_id = parsed.get("INSTANCE_ID")
    vm_ip = parsed.get("VM_IP")
    if not instance_id or not vm_ip:
        raise VmOpsError(f"Could not parse VM info:\n{result.stdout}")
    return instance_id, vm_ip


def delete_vm(instance_id: str, env_vars: dict[str, str] | None = None, timeout: int = 120) -> None:
    paths = get_paths()
    env_vars = dict(env_vars or collect_aliyun_env_vars())
    env_vars["INSTANCE_ID"] = instance_id
    result = _run_script(_VM_DELETE_SCRIPT, env_vars, timeout=timeout, cwd=paths.repo_root)
    if result.returncode != 0:
        raise VmOpsError(
            f"VM deletion failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
