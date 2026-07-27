---
name: os
description: "How to programmatically set up, modify, and verify OS-level configurations (files, GNOME settings, audio, permissions, system config) using Python. For setup-gen and reward-gen agents."
user-invocable: false
---

# OS — Python Manipulation Guide

This skill teaches **setup-gen** (create/modify system state) and **reward-gen** (read/verify system state) how to work with Linux OS tasks using Python.

- Libraries: `os`, `shutil`, `subprocess`, `json`, `stat`, `pathlib`
- Target: Ubuntu/GNOME desktop environment

---

## 0. GUI Startup on VM (for setup-gen)

For OS tasks, setup-gen should leave the required desktop apps/windows open at the end of `initial_setup.py`.

CRITICAL VM LIMIT: GUI launches must set `DISPLAY=:0`.

```python
import os
import shlex
import subprocess
import time

def launch_gui(command: str, delay_sec: float = 1.0):
    env = os.environ.copy()
    env["DISPLAY"] = ":0"
    subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    time.sleep(delay_sec)

# Examples
launch_gui('nautilus "/home/user"', delay_sec=1.5)
# launch_gui('gnome-control-center', delay_sec=1.5)
# launch_gui('gedit "/home/user/Desktop/notes.txt"', delay_sec=1.5)
```

Guidelines:
- Launch only apps needed by the task start state.
- For multi-app tasks, launch all required windows in deterministic order.

---

## 1. Creating & Writing Files (setup-gen)

### File & Directory Operations

```python
import os, shutil, subprocess, json, stat
from pathlib import Path

# Create directories
os.makedirs("/home/user/Desktop/project/src", exist_ok=True)

# Create files
Path("/home/user/Desktop/notes.txt").write_text("Hello World\n")

# Copy files/directories
shutil.copy2("/home/user/file1.txt", "/home/user/backup/file1.txt")  # preserves metadata
shutil.copytree("/home/user/src", "/home/user/dst")  # recursive copy

# Move / rename
shutil.move("/home/user/Desktop/todo_list_Jan_1", "/home/user/Desktop/todo_list_Jan_2")
os.rename("/home/user/old_name.txt", "/home/user/new_name.txt")

# Delete
os.remove("/home/user/temp.txt")           # single file
shutil.rmtree("/home/user/temp_dir")        # recursive directory

# File permissions
os.chmod("/home/user/script.sh", 0o755)     # rwxr-xr-x
# Recursive permission change for regular files
for root, dirs, files in os.walk("/home/user/testDir"):
    for f in files:
        os.chmod(os.path.join(root, f), 0o644)
```

### GNOME Desktop Settings (gsettings / dconf)

```python
# Set GNOME favorite apps
def set_favorite_apps(apps: list):
    """apps: list like ['thunderbird.desktop', 'google-chrome.desktop']"""
    apps_str = str(apps).replace("'", '"')  # gsettings expects double-quoted JSON-like
    subprocess.run(["gsettings", "set", "org.gnome.shell", "favorite-apps", apps_str], check=True)

# Text scaling factor (accessibility)
def set_text_scaling(factor: float):
    subprocess.run(["gsettings", "set", "org.gnome.desktop.interface",
                     "text-scaling-factor", str(factor)], check=True)

# Screen magnifier
def set_magnifier(enabled: bool):
    val = "true" if enabled else "false"
    subprocess.run(["gsettings", "set", "org.gnome.desktop.a11y.magnifier",
                     "mag-factor", "2.0" if enabled else "1.0"], check=True)

# Desktop wallpaper
def set_wallpaper(path: str):
    subprocess.run(["gsettings", "set", "org.gnome.desktop.background",
                     "picture-uri", f"file://{path}"], check=True)
    subprocess.run(["gsettings", "set", "org.gnome.desktop.background",
                     "picture-uri-dark", f"file://{path}"], check=True)

# Dark mode / theme
def set_dark_mode(enabled: bool):
    theme = "prefer-dark" if enabled else "default"
    subprocess.run(["gsettings", "set", "org.gnome.desktop.interface",
                     "color-scheme", theme], check=True)
```

### System Timezone

```python
# Set timezone to UTC
subprocess.run(["sudo", "timedatectl", "set-timezone", "UTC"], check=True)
# Set to specific timezone
subprocess.run(["sudo", "timedatectl", "set-timezone", "America/New_York"], check=True)
```

### Audio Volume (PulseAudio)

```python
# Set volume to max (100%)
subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%"], check=True)
# Set specific volume
subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "75%"], check=True)
# Mute / unmute
subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=True)  # unmute
```

### Terminal Configuration

```python
# Set default terminal size (GNOME Terminal profile via dconf)
subprocess.run(["dconf", "write", "/org/gnome/terminal/legacy/profiles:/:b1dcc9dd-5262-4d8d-a863-c897e6d979b9/default-size-columns", "132"], check=True)
subprocess.run(["dconf", "write", "/org/gnome/terminal/legacy/profiles:/:b1dcc9dd-5262-4d8d-a863-c897e6d979b9/default-size-rows", "43"], check=True)

# Persistent terminal size via .bashrc
def set_terminal_size_bashrc(cols: int, rows: int):
    bashrc = os.path.expanduser("~/.bashrc")
    with open(bashrc, "a") as f:
        f.write(f"\nstty columns {cols} rows {rows}\n")
```

### Package Installation

```python
# Install packages
subprocess.run(["sudo", "apt-get", "update"], check=True)
subprocess.run(["sudo", "apt-get", "install", "-y", "package-name"], check=True)

# Snap install
subprocess.run(["sudo", "snap", "install", "spotify"], check=True)
```

### Clipboard Operations

```python
# Set clipboard content (requires xclip or xsel)
def set_clipboard(text: str):
    proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
    proc.communicate(text.encode())

# Or via xdotool for GUI clipboard
subprocess.run(["xdotool", "key", "ctrl+c"])
```

### Shell Script Execution

```python
# Run a setup shell script
subprocess.run(["bash", "/home/user/setup.sh"], check=True, cwd="/home/user")

# Run with environment variables
env = os.environ.copy()
env["MY_VAR"] = "value"
subprocess.run(["bash", "-c", "echo $MY_VAR"], env=env, check=True)
```

---

## 2. Reading & Verifying Files (reward-gen)

### Verifying File/Directory Existence

```python
def verify_file_exists(path: str) -> bool:
    return os.path.isfile(path)

def verify_dir_exists(path: str) -> bool:
    return os.path.isdir(path)

def verify_file_content(path: str, expected: str) -> bool:
    try:
        return Path(path).read_text() == expected
    except FileNotFoundError:
        return False
```

### Verifying Directory Contents

```python
def verify_directory_files(dir_path: str, expected_files: set) -> bool:
    """Check that directory contains exactly the expected files."""
    try:
        actual = set(os.listdir(dir_path))
        return actual == expected_files
    except FileNotFoundError:
        return False

# Check JPGs were moved to target
def verify_moved_files(dir_path: str, expected_names: list) -> bool:
    actual = set(os.listdir(dir_path))
    return set(expected_names) == actual
```

### Verifying GNOME Settings

```python
def get_gsetting(schema: str, key: str) -> str:
    result = subprocess.run(["gsettings", "get", schema, key],
                            capture_output=True, text=True)
    return result.stdout.strip()

# Favorite apps
def verify_favorite_apps(expected: list) -> bool:
    raw = get_gsetting("org.gnome.shell", "favorite-apps")
    # Output is like: ['app1.desktop', 'app2.desktop']
    apps = eval(raw)
    return set(apps) == set(expected)

# Text scaling
def verify_text_enlarged() -> bool:
    factor = float(get_gsetting("org.gnome.desktop.interface", "text-scaling-factor"))
    return factor > 1.0

# Wallpaper
def verify_wallpaper(expected_path: str) -> bool:
    uri = get_gsetting("org.gnome.desktop.background", "picture-uri")
    return expected_path in uri
```

### Verifying Timezone

```python
def verify_utc_timezone() -> bool:
    result = subprocess.run(["timedatectl"], capture_output=True, text=True)
    lines = result.stdout.split("\n")
    for line in lines:
        if "Time zone" in line:
            return "+0000)" in line
    return False
```

### Verifying Audio Volume

```python
def get_volume() -> int:
    """Get current default sink volume as percentage."""
    result = subprocess.run(
        ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
        capture_output=True, text=True
    )
    # Output: "Volume: front-left: 65536 / 100% / ..."
    import re
    match = re.search(r'(\d+)%', result.stdout)
    return int(match.group(1)) if match else -1

assert get_volume() == 100
```

### Verifying File Permissions

```python
def verify_permissions(path: str, expected_mode: int) -> bool:
    """expected_mode as octal, e.g. 0o644."""
    actual = stat.S_IMODE(os.stat(path).st_mode)
    return actual == expected_mode

# Recursive check
def verify_all_file_permissions(dir_path: str, expected_mode: int) -> bool:
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            if not verify_permissions(os.path.join(root, f), expected_mode):
                return False
    return True
```

### Verifying Command Output (include/exclude)

```python
def verify_command_output(command: str, include: list = None, exclude: list = None) -> bool:
    """Run a shell command and check output contains/excludes strings."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = result.stdout + result.stderr
    if include and not all(s in output for s in include):
        return False
    if exclude and any(s in output for s in exclude):
        return False
    return True

# Examples
assert verify_command_output("which spotify", include=["spotify"], exclude=["not found"])
assert verify_command_output("stty size", include=["43 132"])
```

### Verifying Terminal Size

```python
def verify_terminal_size(expected_rows: int, expected_cols: int) -> bool:
    result = subprocess.run(["stty", "size"], capture_output=True, text=True)
    parts = result.stdout.strip().split()
    return len(parts) == 2 and int(parts[0]) == expected_rows and int(parts[1]) == expected_cols
```

### Verifying Package Installation

```python
def verify_package_installed(package_name: str) -> bool:
    result = subprocess.run(["which", package_name], capture_output=True, text=True)
    return result.returncode == 0 and package_name in result.stdout

def verify_apt_installed(package_name: str) -> bool:
    result = subprocess.run(["dpkg", "-l", package_name], capture_output=True, text=True)
    return result.returncode == 0
```

### Verifying File Content Patterns

```python
def verify_file_contains(path: str, expected_strings: list) -> bool:
    try:
        with open(path, "r") as f:
            content = f.read()
        return all(s in content for s in expected_strings)
    except FileNotFoundError:
        return False

def verify_text_file_match(actual: str, expected: str,
                           ignore_blanks=False, ignore_case=False) -> bool:
    """Compare two text files with optional normalization."""
    import re
    with open(actual) as f:
        a = f.read()
    with open(expected) as f:
        e = f.read()
    if ignore_blanks:
        a = re.sub(r'[\t\n]', ' ', a).strip()
        a = re.sub(r'\s+', ' ', a)
        e = re.sub(r'[\t\n]', ' ', e).strip()
        e = re.sub(r'\s+', ' ', e)
    if ignore_case:
        a, e = a.lower(), e.lower()
    return a == e
```

### Verifying JSON Configuration

```python
def verify_json_subset(file_path: str, expected: dict) -> bool:
    """Check that expected is a subset of the JSON file."""
    try:
        with open(file_path) as f:
            actual = json.load(f)
        return _is_subset(expected, actual)
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def _is_subset(expected, actual) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and _is_subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return expected == actual
    return expected == actual
```

---

## 3. Bitter Lessons

1. **`gsettings get` output is GVariant, not JSON.** It uses single quotes: `['app.desktop']`. Use `eval()` to parse Python-like syntax, or strip and parse manually. Do NOT use `json.loads()`.

2. **PulseAudio volume output format varies.** `pactl get-sink-volume` outputs `front-left: 65536 / 100% / 0.00 dB`. Extract the percentage with regex, don't split on spaces — the format changes across versions.

3. **`stty size` returns `rows cols`, NOT `cols rows`.** The output is `43 132` meaning 43 rows, 132 columns. Reversing them is a common error.

4. **File permission comparison must use `stat.S_IMODE`.** `os.stat().st_mode` includes file type bits. Always mask with `stat.S_IMODE()` to get just permission bits (e.g., 0o644).

5. **`subprocess.run` with `shell=True` vs argument list.** Use `shell=True` for pipes and redirects (`"ls | grep foo"`). Use argument list `["ls", "-la"]` for simple commands — safer and no shell injection risk.

6. **`timedatectl` timezone line format: `Time zone: Atlantic/Faroe (WET, +0000)`.** Parse the offset from the end of the line. Check for `+0000)` suffix for UTC verification, not just the timezone name (multiple zones map to UTC+0).

7. **GNOME dconf paths have UUIDs.** Terminal profile paths like `/org/gnome/terminal/legacy/profiles:/:b1dcc9dd-.../` contain a profile UUID that varies by system. Query the default profile first: `gsettings get org.gnome.terminal.legacy.profiles: default`.

8. **`shutil.copy` vs `shutil.copy2` vs `shutil.copytree`.** `copy` preserves only permissions. `copy2` preserves metadata (timestamps). `copytree` is for directories. Using the wrong one causes metadata-based verification to fail.

9. **`os.makedirs` needs `exist_ok=True`.** Without it, creating a directory that already exists raises `FileExistsError`. Always use `exist_ok=True` in setup scripts.

10. **`which` returns exit code 1 when not found.** Don't check `result.stdout` alone — also check `result.returncode == 0`. An empty stdout with returncode 0 is also possible if the binary has no output.

11. **Setup scripts using `sudo` may prompt for password.** In VM environments, configure `NOPASSWD` in sudoers or use `echo password | sudo -S`. Never assume passwordless sudo without checking.

12. **Snap-installed apps may not appear in `which`.** Snap uses `/snap/bin/` which may not be in PATH. Check `/snap/bin/<app>` directly or use `snap list` to verify.
