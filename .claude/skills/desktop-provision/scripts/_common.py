"""Shared helpers for desktop-provision skill scripts."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REQUIRED_ALIYUN = (
    "ALIYUN_ACCESS_KEY_ID",
    "ALIYUN_ACCESS_KEY_SECRET",
    "ALIYUN_REGION",
    "ALIYUN_IMAGE_ID",
    "ALIYUN_VSWITCH_ID",
    "ALIYUN_SECURITY_GROUP_ID",
)

OPTIONAL_ALIYUN = (
    "ALIYUN_INSTANCE_TYPE",
    "ALIYUN_RESOURCE_GROUP_ID",
    "ALIYUN_USE_PRIVATE_IP",
    "DESKTOP_SSH_PASSWORD",
)

ALIYUN_SDK_PACKAGES = (
    "alibabacloud_ecs20140526",
    "alibabacloud_tea_openapi",
    "alibabacloud_vpc20160428",
)


@dataclass(frozen=True)
class SkillPaths:
    skill_dir: Path
    repo_root: Path
    env_path: Path
    vm_path: Path


EMPTY_VM_CONFIG: dict = {"vm_ip": "", "instance_id": "", "port": 5000}


def _find_repo_root(start: Path) -> Path | None:
    """Walk upward looking for a project root (.env or pyproject.toml)."""
    for directory in (start, *start.parents):
        if (directory / ".env").is_file():
            return directory
        if (directory / "pyproject.toml").is_file():
            return directory
    return None


def get_paths() -> SkillPaths:
    """
    Resolve skill paths. Agent may override via environment:

    - DESKTOP_PROVISION_SKILL_DIR — skill root (default: parent of this scripts/ dir)
    - DESKTOP_PROVISION_REPO_ROOT — repo root (default: walk up from skill dir for .env)
    - DESKTOP_PROVISION_ENV_FILE — credentials file (default: <repo_root>/.env)
    - DESKTOP_PROVISION_VM_JSON — desktop_vm.json path (default: <skill_dir>/desktop_vm.json)
    """
    skill_dir = Path(
        os.environ.get("DESKTOP_PROVISION_SKILL_DIR", Path(__file__).resolve().parents[1])
    ).resolve()

    repo_root = os.environ.get("DESKTOP_PROVISION_REPO_ROOT", "").strip()
    if repo_root:
        repo = Path(repo_root).resolve()
    else:
        found = _find_repo_root(skill_dir)
        if not found:
            found = _find_repo_root(Path.cwd())
        repo = found or skill_dir

    env_path = Path(os.environ.get("DESKTOP_PROVISION_ENV_FILE", repo / ".env")).resolve()
    vm_path = Path(
        os.environ.get("DESKTOP_PROVISION_VM_JSON", skill_dir / "desktop_vm.json")
    ).resolve()

    return SkillPaths(
        skill_dir=skill_dir,
        repo_root=repo,
        env_path=env_path,
        vm_path=vm_path,
    )


def vm_port(data: dict) -> int:
    return int(data.get("port") or 5000)


def load_vm_config(paths: SkillPaths) -> dict:
    if not paths.vm_path.is_file():
        return dict(EMPTY_VM_CONFIG)
    data = json.loads(paths.vm_path.read_text(encoding="utf-8"))
    data.setdefault("port", vm_port(data))
    return data


def save_vm_config(paths: SkillPaths, data: dict) -> None:
    payload = {
        "vm_ip": data.get("vm_ip", ""),
        "instance_id": data.get("instance_id", ""),
        "port": vm_port(data),
    }
    for key in ("region", "image_id", "created_at", "provider_name", "vm_requirements_installed_at"):
        if data.get(key):
            payload[key] = data[key]
    paths.vm_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def vm_requirements_path(paths: SkillPaths | None = None) -> Path:
    paths = paths or get_paths()
    return paths.repo_root / "vm_requirements.txt"


SSH_OPTS = ("-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null")


def run_ssh(
    vm_ip: str,
    password: str,
    remote_cmd: str,
    *,
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "sshpass",
        "-p",
        password,
        "ssh",
        *SSH_OPTS,
        f"root@{vm_ip}",
        remote_cmd,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def scp_to_vm(
    local_path: Path,
    vm_ip: str,
    password: str,
    remote_path: str,
    *,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "sshpass",
        "-p",
        password,
        "scp",
        *SSH_OPTS,
        str(local_path),
        f"root@{vm_ip}:{remote_path}",
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def clear_vm_config(paths: SkillPaths) -> None:
    save_vm_config(paths, dict(EMPTY_VM_CONFIG))


def build_vm_config(
    *,
    vm_ip: str,
    instance_id: str,
    port: int = 5000,
    region: str | None = None,
    image_id: str | None = None,
    provider_name: str = "aliyun",
) -> dict:
    return {
        "vm_ip": vm_ip,
        "instance_id": instance_id,
        "port": port,
        "region": region,
        "image_id": image_id,
        "created_at": datetime.now().isoformat(),
        "provider_name": provider_name,
    }


def load_dotenv(*, apply: bool = True, paths: SkillPaths | None = None) -> dict[str, str]:
    paths = paths or get_paths()
    values: dict[str, str] = {}
    if not paths.env_path.is_file():
        return values
    for line in paths.env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:]
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    if apply:
        for key, value in values.items():
            os.environ[key] = value
    return values


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def skill_venv_python() -> Path:
    return skill_dir() / ".venv" / "bin" / "python"


def _venv_has_aliyun_sdk(venv_py: Path) -> bool:
    for pkg in ALIYUN_SDK_PACKAGES:
        result = subprocess.run(
            [str(venv_py), "-c", f"import {pkg}"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return False
    return True


def _create_skill_venv() -> Path:
    venv_dir = skill_dir() / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    return skill_venv_python()


def _pip_install_packages(py: str, packages: list[str]) -> bool:
    cmd = [py, "-m", "pip", "install", *packages]
    print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, check=False)
    return result.returncode == 0


def python_bin() -> str:
    """Prefer skill .venv when it has the Aliyun SDK (Mac PEP 668–safe)."""
    venv_py = skill_venv_python()
    if venv_py.is_file() and _venv_has_aliyun_sdk(venv_py):
        return str(venv_py)
    return sys.executable


def collect_aliyun_env_vars() -> dict[str, str]:
    keys = [
        "ALIYUN_ACCESS_KEY_ID",
        "ALIYUN_ACCESS_KEY_SECRET",
        "ALIYUN_REGION",
        "ALIYUN_IMAGE_ID",
        "ALIYUN_INSTANCE_TYPE",
        "ALIYUN_VSWITCH_ID",
        "ALIYUN_SECURITY_GROUP_ID",
        "ALIYUN_RESOURCE_GROUP_ID",
        "ALIYUN_USE_PRIVATE_IP",
    ]
    return {k: os.environ[k] for k in keys if k in os.environ}


def provision_env_overrides() -> dict[str, str]:
    """Mac-friendly defaults; skill-owned — does not touch utils/env.py."""
    use_private = os.environ.get("ALIYUN_USE_PRIVATE_IP", "0").strip() or "0"
    return {"ALIYUN_USE_PRIVATE_IP": use_private}


def missing_access_keys() -> list[str]:
    return [
        k
        for k in ("ALIYUN_ACCESS_KEY_ID", "ALIYUN_ACCESS_KEY_SECRET")
        if not os.environ.get(k, "").strip()
    ]


def print_access_key_setup_guide(*, env_path: Path, skill_dir: Path) -> None:
    """Print console steps when AK/SK are missing. Agent: point user here, never ask for keys in chat."""
    doc = skill_dir / "onboarding.md"
    print("\n── Aliyun AccessKey required ──", file=sys.stderr)
    print("Do NOT paste AccessKey in chat. Add to your local .env only.\n", file=sys.stderr)
    print("Create a RAM AccessKey (recommended over root account key):", file=sys.stderr)
    print("  1. Open RAM AccessKey console:", file=sys.stderr)
    print("     https://ram.console.aliyun.com/manage/ak", file=sys.stderr)
    print("  2. Sign in to your Aliyun account", file=sys.stderr)
    print("  3. Prefer: RAM → Users → create user → enable「OpenAPI AccessKey」", file=sys.stderr)
    print("     Attach policies: AliyunECSFullAccess + AliyunVPCReadOnlyAccess", file=sys.stderr)
    print("     (or AliyunECSFullAccess alone for minimal setup)", file=sys.stderr)
    print("  4. Create AccessKey → copy AccessKey ID and AccessKey Secret once", file=sys.stderr)
    print("  5. Add to .env (repo root):", file=sys.stderr)
    print(f"       {env_path}", file=sys.stderr)
    print("       ALIYUN_ACCESS_KEY_ID=<your-id>", file=sys.stderr)
    print("       ALIYUN_ACCESS_KEY_SECRET=<your-secret>", file=sys.stderr)
    print(f"  6. Full walkthrough: {doc} (section「Create AccessKey」)", file=sys.stderr)
    print("  7. Re-run: python scripts/discover_and_fill.py\n", file=sys.stderr)


def missing_aliyun_sdk() -> list[str]:
    return [pkg for pkg in ALIYUN_SDK_PACKAGES if importlib.util.find_spec(pkg) is None]


def print_aliyun_sdk_install_guide() -> None:
    spec = " ".join(ALIYUN_SDK_PACKAGES)
    venv_py = skill_venv_python()
    print("\n── Aliyun Python SDK not installed ──", file=sys.stderr)
    print(f"Missing packages: {', '.join(missing_aliyun_sdk())}", file=sys.stderr)
    print(f"\nInstall manually:\n  {sys.executable} -m pip install {spec}\n", file=sys.stderr)
    print(
        "On Mac (PEP 668), use the skill venv instead:\n"
        f"  cd {skill_dir()}\n"
        "  python3 -m venv .venv && .venv/bin/pip install " + spec + "\n"
        f"  .venv/bin/python scripts/discover_and_fill.py\n",
        file=sys.stderr,
    )
    if venv_py.is_file():
        print(f"Or re-run with existing venv:\n  {venv_py} scripts/…\n", file=sys.stderr)
    print("Or re-run with:  --install-deps  (auto-creates .venv if system pip is locked)\n", file=sys.stderr)


def ensure_aliyun_sdk(*, auto_install: bool | None = None, reexec: bool = True) -> bool:
    """
    Ensure Aliyun SDK is importable in the current interpreter.

    If system pip is PEP 668–locked, installs into skill/.venv and re-execs the script.

    auto_install:
      True  — run pip install without prompting
      False — print guide and return False
      None  — if interactive TTY, ask user; else print guide and return False
    """
    venv_py = skill_venv_python()
    if venv_py.is_file() and _venv_has_aliyun_sdk(venv_py):
        if missing_aliyun_sdk() and reexec and Path(sys.executable).resolve() != venv_py.resolve():
            os.execv(str(venv_py), [str(venv_py), *sys.argv])
        if not missing_aliyun_sdk():
            return True

    if not missing_aliyun_sdk():
        return True

    print_aliyun_sdk_install_guide()

    do_install = auto_install
    if do_install is None and sys.stdin.isatty():
        try:
            answer = input("Install Aliyun SDK packages now? [y/N] ").strip().lower()
            do_install = answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            do_install = False
    elif do_install is None:
        print(
            "Non-interactive session: ask the user, then run with --install-deps "
            "or pip install manually.",
            file=sys.stderr,
        )
        return False

    if not do_install:
        return False

    to_install = missing_aliyun_sdk()

    if _pip_install_packages(sys.executable, to_install) and not missing_aliyun_sdk():
        print("OK: Aliyun SDK installed", file=sys.stderr)
        return True

    if not venv_py.is_file():
        print(f"Creating skill virtualenv at {venv_py.parent.parent} …", file=sys.stderr)
        venv_py = _create_skill_venv()

    if not _pip_install_packages(str(venv_py), to_install):
        print("ERROR: pip install failed (system pip locked? use skill .venv)", file=sys.stderr)
        return False

    if not _venv_has_aliyun_sdk(venv_py):
        print("ERROR: SDK still missing after install in .venv", file=sys.stderr)
        return False

    print(f"OK: Aliyun SDK installed in {venv_py.parent.parent}", file=sys.stderr)
    if reexec:
        os.execv(str(venv_py), [str(venv_py), *sys.argv])
    print(f"Re-run with: {venv_py} {' '.join(sys.argv)}", file=sys.stderr)
    return False
