---
name: desktop-provision
description: >-
  Discover Aliyun ECS resources from AccessKey, backfill repo root .env,
  provision or reuse OSWorld Desktop VM. If Aliyun SDK missing, ask user to install
  (or run discover/preflight with --install-deps). If no AccessKey, guide via onboarding.md.
  Use when user provides Aliyun key, desktop provision, ECS VM, or OSWorld VM setup.
user-invocable: true
---

# Desktop Provision — Aliyun ECS (OSWorld Desktop)

Self-contained skill for **creating, verifying, and deleting** OSWorld Desktop VMs on Aliyun ECS. All Aliyun API logic lives in `scripts/vm_ops.py` — does **not** depend on or modify `utils/env.py`.

**State file:** `desktop_vm.json` (local, gitignored). Harness reads it for Desktop task runs.

Do **not** ask users to paste AccessKey in chat — only local `.env`.

---

## Quick start

```bash
cd <path-to>/desktop-provision

# First time: cp repo .env.example → .env, fill AK/SK + DESKTOP_SSH_PASSWORD
python scripts/discover_and_fill.py
python scripts/preflight.py
python scripts/provision.py    # skip if discover printed REUSE
python scripts/verify.py       # Flask health + auto-install vm_requirements.txt on VM
# when idle:
python scripts/delete.py
```

First-time Aliyun account → [onboarding.md](onboarding.md).

---

## Layout

```
<repo>/.env                          # credentials (gitignored)
<skill_dir>/
  desktop_vm.json                    # VM state (gitignored; see .example)
  desktop_vm.json.example            # empty schema template
  .gitignore
  scripts/
    _common.py                       # paths, dotenv, VM JSON helpers
    vm_ops.py                        # Aliyun create/delete
    discover_and_fill.py             # scan infra + backfill .env; REUSE existing VM
    preflight.py                     # pre-flight checks
    provision.py                     # create ECS
    verify.py                        # Flask health check (+ cold-start retries)
    bootstrap_vm.py                  # pip install repo vm_requirements.txt on VM (also run by verify)
    delete.py                        # delete ECS + clear desktop_vm.json
  SKILL.md
  onboarding.md
```

---

## Path resolution

Scripts use `get_paths()` in `scripts/_common.py`:

| What | Default |
|------|---------|
| Skill dir | Parent of `scripts/` |
| Repo root | Walk up for `.env` or `pyproject.toml` |
| `.env` | `<repo_root>/.env` |
| `desktop_vm.json` | `<skill_dir>/desktop_vm.json` |

**Overrides** (optional env vars):

| Env var | Purpose |
|---------|---------|
| `DESKTOP_PROVISION_SKILL_DIR` | Skill root |
| `DESKTOP_PROVISION_REPO_ROOT` | Repository root |
| `DESKTOP_PROVISION_ENV_FILE` | Credentials file |
| `DESKTOP_PROVISION_VM_JSON` | VM state file |

Run scripts from any cwd — paths are resolved automatically.

---

## Prerequisites

### `.env` fields

| User fills | Filled by `discover_and_fill.py` |
|------------|----------------------------------|
| `ALIYUN_ACCESS_KEY_ID` | `ALIYUN_REGION` |
| `ALIYUN_ACCESS_KEY_SECRET` | `ALIYUN_IMAGE_ID` |
| `ALIYUN_INSTANCE_TYPE` (default `ecs.g8a.xlarge`) | `ALIYUN_VSWITCH_ID` |
| `DESKTOP_SSH_PASSWORD` | `ALIYUN_SECURITY_GROUP_ID` |

Mac / local dev: `ALIYUN_USE_PRIVATE_IP=0` (public IP).

No AccessKey yet → [onboarding.md — Create AccessKey](onboarding.md#create-accesskey).

### Python SDK

On Mac (Homebrew Python, PEP 668), system-wide `pip install` may fail. Use either:

```bash
cd .claude/skills/desktop-provision
python3 -m venv .venv
.venv/bin/pip install alibabacloud_ecs20140526 alibabacloud_tea_openapi alibabacloud_vpc20160428
.venv/bin/python scripts/discover_and_fill.py
```

Or pass `--install-deps` — scripts auto-create `.venv` and re-exec when system pip is locked.

If missing, scripts prompt to install or accept `--install-deps`. **Agent:** ask user, then run e.g. `python scripts/preflight.py --install-deps`.

### System tools

| Tool | Used by | Install |
|------|---------|---------|
| `sshpass` | `verify.py` (SSH tunnel on Mac) | `brew install sshpass` / `apt install sshpass` |
| `ssh` | tunnel | usually preinstalled |

`preflight.py` checks for `sshpass`.

---

## Scripts reference

| Script | Purpose | Typical output |
|--------|---------|----------------|
| `discover_and_fill.py` | Find OSWorld image + VPC; backfill `.env`; REUSE running instance | `REUSE …` or infra IDs |
| `preflight.py` | Validate `.env`, SDK, instance type in zone, `sshpass` | `PREFLIGHT PASS` |
| `provision.py` | Create PostPaid ECS (~2–5 min); write `desktop_vm.json` | `Done: <ip> instance=<id>` |
| `verify.py` | Check Flask `:5000` (direct or SSH tunnel); retries on cold start; then **install `vm_requirements.txt` on VM** | `VERIFY PASS` + `BOOTSTRAP PASS` |
| `bootstrap_vm.py` | SSH + `pip3 install -r <repo>/vm_requirements.txt` (standalone; verify calls this by default) | `BOOTSTRAP PASS` |
| `delete.py` | Delete ECS; clear `desktop_vm.json` | `Deleted and cleared local config` |

All scripts support `--install-deps` where SDK is needed (`discover`, `preflight`).

---

## Workflow details

### REUSE

If `discover_and_fill.py` finds a **Running** instance with the same image **and a usable IP**, it writes `desktop_vm.json` and prints `REUSE`. Skip `provision.py`; run `verify.py` directly.

| `ALIYUN_USE_PRIVATE_IP` | REUSE requires |
|-------------------------|----------------|
| `0` (Mac / local dev) | Running + **public** IP |
| `1` (VPC-only) | Running + **private** IP |

**Not reused:** Stopped instances (WARN printed — start in console or `delete.py` first). Running instances without the required IP are skipped.

### Cold start (important)

Aliyun ECS **Running ≠ VM services ready**.

| Phase | What happens |
|-------|----------------|
| `provision.py` done | ECS Running + public IP assigned |
| +1–3 min | `sshd` on **:22**, then `osworld_server` (Flask **:5000**) |
| `verify.py` | Retries automatically (default 8× every 15s ≈ up to 2 min) |

`provision.py` waits only for ECS Running — **not** SSH or Flask.

**Agent — tell the user explicitly:**

| When | Message |
|------|---------|
| After provision | 「实例已创建，SSH 和 Desktop 服务通常还需 1–3 分钟启动；正在自动 verify，请稍候。」 |
| Verify retrying | 「正常冷启动，不是配置错误，等待服务就绪…」 |
| Verify PASS | 「实例已就绪。详情见 `desktop_vm.json`。」 |

Do **not** treat first `Connection refused` as provision failure.

**After verify PASS** (optional detail):

> 实例已就绪。详细信息见 `.claude/skills/desktop-provision/desktop_vm.json`（`vm_ip`、`instance_id`、`port`、`region` 等）。

Do not dump all JSON fields unless the user asks.

### Mac connectivity

Public `:5000` is often blocked from Mac. `verify.py` and harness fall back to **SSH tunnel** using `DESKTOP_SSH_PASSWORD`.

### VM Python packages (`vm_requirements.txt`)

After Flask verify passes, `verify.py` **automatically** SSHes into the VM and runs:

```bash
pip3 install -r <repo_root>/vm_requirements.txt
```

This installs the Desktop task baseline (openpyxl, Flask, pandas, …) so tasks do not fail on missing imports. Skip with `verify.py --no-bootstrap`; re-run with `bootstrap_vm.py --force`.

| When | What happens |
|------|----------------|
| First verify on new VM | Upload + pip install (~2–10 min depending on network) |
| REUSE / already installed | Skips if `openpyxl`, `flask`, `pandas` import on VM |
| Manual only | `python scripts/bootstrap_vm.py` |

Records `vm_requirements_installed_at` in `desktop_vm.json` on success.

---

## Harness integration

After `verify.py` passes, run Desktop tasks from harness — **no `--provision`**:

```bash
cd envs/cua-gym/harness
python cuagym_harness.py --modal desktop --mode reset_only --task <uuid>
```

Harness reads VM endpoint from `.claude/skills/desktop-provision/desktop_vm.json` by default. Override: `DESKTOP_VM_JSON` or `--vm-ip`.

See [`envs/cua-gym/harness/README.md`](../../../envs/cua-gym/harness/README.md).

---

## Error handbook

| Symptom / API code | Action |
|--------------------|--------|
| Missing Aliyun SDK | `pip install …` or `python scripts/preflight.py --install-deps` |
| Missing `ALIYUN_ACCESS_KEY_*` | [Create RAM AccessKey](onboarding.md#create-accesskey) → `.env` → re-run discover |
| Missing `sshpass` | `brew install sshpass` (Mac) or `apt install sshpass` |
| `NotEnoughBalance` | Recharge Aliyun account |
| `InvalidResourceType.NotSupported` | Re-run `discover_and_fill.py` |
| No image in region | Import qcow2 ([onboarding.md](onboarding.md)) or clear `ALIYUN_REGION` |
| Public `:5000` unreachable (Mac) | Normal — SSH tunnel used automatically |
| `Connection refused` right after provision | **Cold start** — wait; `verify.py` retries |
| `VERIFY FAIL` after all retries | Check `DESKTOP_SSH_PASSWORD`, SG TCP 22/5000; `systemctl status osworld_server` on VM |
| `BOOTSTRAP FAIL` / pip errors on VM | Re-run `python scripts/bootstrap_vm.py --force`; check VM outbound network; `vm_requirements.txt` uses `psycopg2-binary` (not source `psycopg2`) |
| Missing `<repo>/vm_requirements.txt` | File must exist at repo root (CUA-Gym manifest for VM Python deps) |
| `provision.py`: instance already in `desktop_vm.json` | Run `delete.py` first, or `discover_and_fill.py` for REUSE |
| Stopped instance with same image (WARN) | Start in Aliyun console, or `delete.py` then provision |
| `IncorrectInstanceStatus.Initializing` on delete | `delete.py` waits for Running/Stopped; uses `region` from `desktop_vm.json` |

---

## Security

- Never commit `.env` or `desktop_vm.json`
- Delete instance when idle (PostPaid billing)

---

## `desktop_vm.json` schema

Written by `provision.py` / `discover_and_fill.py` (REUSE). Read by `verify.py`, `delete.py`, harness.

Template: [`desktop_vm.json.example`](desktop_vm.json.example)

```json
{
  "vm_ip": "47.x.x.x",
  "instance_id": "i-xxx",
  "port": 5000,
  "region": "cn-shenzhen",
  "image_id": "m-xxx",
  "created_at": "2026-06-03T11:49:51",
  "provider_name": "aliyun",
  "vm_requirements_installed_at": "2026-06-03T11:52:10"
}
```
