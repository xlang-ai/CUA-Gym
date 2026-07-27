---
name: vs-code
description: "How to programmatically configure, modify, and verify VSCode settings, keybindings, extensions, and workspace files using Python. For setup-gen and reward-gen agents."
user-invocable: false
---

# VSCode — Python Manipulation Guide

This skill teaches **setup-gen** (create/modify configs) and **reward-gen** (read/verify configs) how to work with VSCode configuration files using pure Python code.

- Libraries: `json`, `os`, `subprocess`, `shutil`
- Config root: `~/.config/Code/User/` (Linux)

---

## 0. GUI Startup on VM (for setup-gen)

After preparing workspace/settings, setup-gen should open VSCode with the target folder or file for the GUI agent.

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

# Open workspace/folder
launch_gui('code "/home/user/workspace"', delay_sec=2.0)

# Or open a specific file
# launch_gui('code "/home/user/workspace/main.py"', delay_sec=2.0)
```

Guidelines:
- Use non-blocking launch (`Popen`) and short delays.
- For multi-app tasks, coordinate launch order explicitly.

---

## 1. Creating & Writing Files (setup-gen)

### Key File Paths

```python
import os, json, shutil, subprocess

HOME = os.path.expanduser("~")
VSCODE_USER = os.path.join(HOME, ".config", "Code", "User")
SETTINGS_PATH = os.path.join(VSCODE_USER, "settings.json")
KEYBINDINGS_PATH = os.path.join(VSCODE_USER, "keybindings.json")
SNIPPETS_DIR = os.path.join(VSCODE_USER, "snippets")
```

### Settings (settings.json)

```python
# Read existing settings (or start empty)
def load_settings():
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Write settings — merges with existing
def update_settings(updates: dict):
    settings = load_settings()
    settings.update(updates)
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=4)

# Examples
update_settings({
    "editor.fontSize": 16,
    "editor.wordWrap": "on",
    "workbench.colorTheme": "Visual Studio Dark",
    "debug.focusEditorOnBreak": False,
    "python.analysis.diagnosticSeverityOverrides": {
        "reportMissingImports": "none"
    }
})
```

### Nested Settings

```python
def update_nested_setting(key_path: list, value):
    """Set a deeply nested key like ["python", "analysis", "typeCheckingMode"]."""
    settings = load_settings()
    d = settings
    for key in key_path[:-1]:
        d = d.setdefault(key, {})
    d[key_path[-1]] = value
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=4)
```

### Keybindings (keybindings.json)

```python
def load_keybindings():
    """Load keybindings, handling the optional comment prefix line."""
    try:
        with open(KEYBINDINGS_PATH, "r") as f:
            content = f.read()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Skip first line (comment like "// Place your key bindings...")
            lines = content.split("\n", 1)
            if len(lines) > 1:
                return json.loads(lines[1])
            return []
    except FileNotFoundError:
        return []

def add_keybinding(key: str, command: str, when: str = None):
    bindings = load_keybindings()
    entry = {"key": key, "command": command}
    if when:
        entry["when"] = when
    bindings.append(entry)
    os.makedirs(os.path.dirname(KEYBINDINGS_PATH), exist_ok=True)
    with open(KEYBINDINGS_PATH, "w") as f:
        json.dump(bindings, f, indent=4)

# Examples
add_keybinding("ctrl+shift+t", "workbench.action.terminal.toggleTerminal")
add_keybinding("ctrl+k ctrl+c", "editor.action.addCommentLine", when="editorTextFocus")
```

### Workspace Files (.code-workspace)

```python
def create_workspace(workspace_path: str, folders: list, settings: dict = None):
    """Create a .code-workspace file."""
    workspace = {
        "folders": [{"path": p} for p in folders],
    }
    if settings:
        workspace["settings"] = settings
    with open(workspace_path, "w") as f:
        json.dump(workspace, f, indent=4)

# Example
create_workspace(
    "/home/user/project.code-workspace",
    ["/home/user/src", "/home/user/data1", "/home/user/data2"],
    settings={"editor.tabSize": 2}
)
```

### Extension Management

```python
# Install extension via CLI
def install_extension(extension_id: str):
    subprocess.run(["code", "--install-extension", extension_id], check=True)

# Uninstall extension
def uninstall_extension(extension_id: str):
    subprocess.run(["code", "--uninstall-extension", extension_id], check=True)

# List installed extensions
def list_extensions() -> str:
    result = subprocess.run(["code", "--list-extensions"], capture_output=True, text=True)
    return result.stdout

# Examples
install_extension("ms-python.python")
install_extension("esbenp.prettier-vscode")
```

### Text File Creation/Modification

```python
# Create a file for VSCode to open
def create_text_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

# Find and replace in a file
def find_replace_in_file(path: str, old: str, new: str):
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)

# Golden file: copy then modify
shutil.copy("/home/user/original.py", "/home/user/golden.py")
find_replace_in_file("/home/user/golden.py", "text", "test")
```

### Launching VSCode

```python
# Open VSCode with a file
subprocess.Popen(["code", "/home/user/document.txt"])

# Open VSCode with a folder
subprocess.Popen(["code", "/home/user/project/"])

# Open VSCode with a workspace
subprocess.Popen(["code", "/home/user/project.code-workspace"])
```

### Snippet Files

```python
def create_snippet(language: str, name: str, prefix: str, body: list, description: str = ""):
    snippet_path = os.path.join(SNIPPETS_DIR, f"{language}.json")
    os.makedirs(SNIPPETS_DIR, exist_ok=True)
    try:
        with open(snippet_path, "r") as f:
            snippets = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        snippets = {}
    snippets[name] = {"prefix": prefix, "body": body, "description": description}
    with open(snippet_path, "w") as f:
        json.dump(snippets, f, indent=4)
```

---

## 2. Reading & Verifying Files (reward-gen)

### Verifying Settings (Subset Check)

```python
def verify_settings_subset(expected: dict) -> bool:
    """Check that all expected key-value pairs exist in settings.json."""
    settings = load_settings()
    return _is_subset(expected, settings)

def _is_subset(expected, actual) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and _is_subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return expected == actual
    return expected == actual

# Example: check theme was changed
assert verify_settings_subset({"workbench.colorTheme": "Visual Studio Dark"})
# Nested check
assert verify_settings_subset({
    "python.analysis.diagnosticSeverityOverrides": {"reportMissingImports": "none"}
})
```

### Verifying Keybindings

```python
def verify_keybinding(expected_entry: dict) -> bool:
    """Check that expected keybinding exists in keybindings.json."""
    bindings = load_keybindings()
    return expected_entry in bindings

# Example
assert verify_keybinding({"key": "ctrl+shift+t", "command": "workbench.action.terminal.toggleTerminal"})
```

### Verifying Config with Containment

```python
def verify_config_containment(file_path: str, expected_json_str: str) -> bool:
    """Check JSON file contains expected structure (subset match)."""
    try:
        with open(file_path, "r") as f:
            actual = json.load(f)
        expected = json.loads(expected_json_str)
        return _is_subset(expected, actual)
    except (FileNotFoundError, json.JSONDecodeError):
        return False
```

### Verifying Text Files

```python
import re

def verify_text_file(actual_path: str, expected_path: str,
                     ignore_blanks=False, ignore_case=False) -> bool:
    with open(actual_path) as f:
        actual = f.read()
    with open(expected_path) as f:
        expected = f.read()
    if ignore_blanks:
        actual = re.sub(r'[\t\n]', ' ', actual).strip()
        actual = re.sub(r'\s+', ' ', actual)
        expected = re.sub(r'[\t\n]', ' ', expected).strip()
        expected = re.sub(r'\s+', ' ', expected)
    if ignore_case:
        actual = actual.lower()
        expected = expected.lower()
    return actual == expected
```

### Verifying Extensions

```python
def verify_extension_installed(extension_id: str) -> bool:
    result = subprocess.run(["code", "--list-extensions"], capture_output=True, text=True)
    return extension_id in result.stdout

def verify_extension_not_installed(extension_id: str) -> bool:
    return not verify_extension_installed(extension_id)
```

### Verifying Workspace Files

```python
def verify_workspace_folders(workspace_path: str, expected_folders: list) -> bool:
    with open(workspace_path, "r") as f:
        ws = json.load(f)
    actual_paths = [folder["path"] for folder in ws.get("folders", [])]
    return set(expected_folders) == set(actual_paths)
```

### Verifying Python Files by Test Suite

```python
import importlib.util, sys, uuid

def run_test_on_file(test_file: str, test_func_name: str = "test") -> float:
    """Load a test file and run its test function. Returns 0.0-1.0."""
    original_cwd = os.getcwd()
    original_path = sys.path.copy()
    module_name = f"test_{uuid.uuid4().hex[:8]}"
    try:
        test_dir = os.path.dirname(os.path.abspath(test_file))
        os.chdir(test_dir)
        if test_dir not in sys.path:
            sys.path.insert(0, test_dir)
        spec = importlib.util.spec_from_file_location(module_name, test_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        result = getattr(module, test_func_name)()
        if isinstance(result, bool):
            return 1.0 if result else 0.0
        return max(0.0, min(1.0, float(result)))
    except Exception:
        return 0.0
    finally:
        if module_name in sys.modules:
            del sys.modules[module_name]
        os.chdir(original_cwd)
        sys.path[:] = original_path
```

### Verifying ZIP/Archive Files

```python
import zipfile

def verify_zip_files(actual_zip: str, expected_zip: str) -> bool:
    with zipfile.ZipFile(actual_zip) as z1, zipfile.ZipFile(expected_zip) as z2:
        if set(z1.namelist()) != set(z2.namelist()):
            return False
        return all(z1.read(name) == z2.read(name) for name in z1.namelist())
```

---

## 3. Bitter Lessons

1. **keybindings.json may have a comment prefix line.** VSCode writes `// Place your key bindings in this file...` as the first line. `json.load()` fails. Always try direct load first, then skip the first line as fallback.

2. **settings.json uses `update` not `replace`.** Always load existing settings and merge. Overwriting the entire file destroys user settings that other setup steps depend on.

3. **`_is_subset` is the correct comparison for settings.** The evaluator checks that expected keys exist with correct values, NOT that settings.json is an exact match. Extra keys are fine.

4. **Workspace file is JSON, not settings.json.** `.code-workspace` files have a different schema (`folders`, `settings`, `extensions`). Don't confuse with `~/.config/Code/User/settings.json`.

5. **Extension IDs are case-insensitive but must be exact.** `ms-python.python` works; `Python` alone does not. Use `code --list-extensions` to get canonical IDs.

6. **`code` CLI may not be in PATH.** In headless/VM environments, VSCode may need to be launched via full path (`/usr/bin/code`) or the `code` symlink may not exist. Check with `which code` first.

7. **Text file comparison: `ignore_blanks` collapses tabs and newlines to spaces.** It replaces `[\t\n]` with space, then collapses multiple spaces. This means paragraph structure is lost. Use `ignore_blanks=False` when line structure matters.

8. **JSON settings with `//` comments are NOT valid JSON.** VSCode's `settings.json` supports JSONC (JSON with Comments). Python's `json` module cannot parse comments. Use regex to strip them: `re.sub(r'//.*$', '', content, flags=re.MULTILINE)` before parsing.

9. **`compare_config` defaults to containment mode.** The evaluator's `containment_ok=True` (default) means the expected JSON only needs to be a subset of the actual. Set `containment_ok=False` for strict equality.

10. **Python test suite runs in the test file's directory.** The evaluator `cd`s to the test file's parent directory before running. Relative paths in the test file resolve from there.

11. **Extension installation is async.** `code --install-extension` returns before the extension is fully activated. If subsequent steps depend on the extension, add a delay or restart VSCode.

12. **Workspace folders use exact paths.** `{"path": "/home/user/data1"}` is NOT equal to `{"path": "~/data1"}`. Always use fully expanded absolute paths when comparing.
