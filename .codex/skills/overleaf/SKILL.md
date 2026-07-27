---
name: overleaf
description: "How to set up and manipulate Overleaf CE project state via HTTP APIs for CUA-Gym tasks. For setup-gen and reward-gen agents."
user-invocable: false
---

# Overleaf — Setup & Verification Guide

This skill teaches **setup-gen** and **reward-gen** how to create, manipulate, and verify Overleaf project state for LaTeX editing tasks. Unlike file-based domains, Overleaf tasks involve **HTTP state management** through a shared Overleaf CE instance — there are no local `.tex` files on the VM.

- Libraries: `requests`, `json`, `uuid`, `zipfile`, `io`, `re`
- Overleaf CE instance: `https://cua-gym-overleaf.xlang.ai`
- Admin account: `agent@cua-gym.local` (used only for user lifecycle management)

---

## 0. Architecture Overview

```
Admin creates session user  →  Session user logs in  →  Project created via ZIP upload
       ↓                              ↓                          ↓
  activate URL             CSRF + session cookie          CUA agent edits in browser
       ↓                              ↓                          ↓
  set password              setup-gen / reward-gen        reward-gen verifies via API
                                                                  ↓
                                                      User self-deletes account
```

**Key difference from mock_websites**: Overleaf uses **per-session user accounts** (not just per-session state IDs). Each training episode gets its own user, ensuring complete isolation. The user is created at setup and deleted after reward verification.

**Key difference from file-based domains**: There is no dual-VM pattern (initial_env / golden_env). Both initial and golden states exist as Overleaf projects under the same user on the shared instance. The reward script verifies by downloading and inspecting project content via HTTP.

---

## 1. Authentication API

All Overleaf API calls require session-cookie authentication. CSRF tokens are embedded in HTML pages as `<meta name="ol-csrfToken">` tags.

### 1.1 Extracting CSRF Token

```python
import re
import requests

OVERLEAF_URL = 'https://cua-gym-overleaf.xlang.ai'

session = requests.Session()

def get_csrf(session):
    """Extract CSRF token from any Overleaf page."""
    resp = session.get(f'{OVERLEAF_URL}/login', timeout=10)
    match = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', resp.text)
    if not match:
        raise RuntimeError('Cannot extract CSRF token')
    return match.group(1)
```

### 1.2 Login

```python
def login(session, email, password):
    """Login and establish session cookie."""
    csrf = get_csrf(session)
    resp = session.post(
        f'{OVERLEAF_URL}/login',
        json={'email': email, 'password': password, '_csrf': csrf},
        timeout=15,
        allow_redirects=False,
    )
    if resp.status_code not in (200, 302):
        raise RuntimeError(f'Login failed: {resp.status_code} {resp.text[:200]}')
    return session
```

### 1.3 CSRF for POST/PUT/DELETE Requests

There are two ways to pass CSRF tokens, depending on content type:

| Request Type | CSRF Method |
|---|---|
| `application/json` | Include `"_csrf": token` in JSON body |
| `multipart/form-data` (file upload) | Use `X-CSRF-Token` HTTP header |

```python
# JSON request
session.post(url, json={..., '_csrf': csrf})

# File upload (multipart) — CSRF must be in header, NOT in form data
session.post(url, files={...}, data={...}, headers={'X-CSRF-Token': csrf})
```

**CRITICAL**: For file uploads (ZIP upload, image upload), putting `_csrf` in the `data` dict returns 403 Forbidden. Always use the `X-CSRF-Token` header for multipart requests.

---

## 2. User Lifecycle API

Each training session requires an isolated user account. The admin account creates and manages session users.

### 2.1 Create Session User (Admin)

```python
def create_session_user(admin_session, email):
    """Admin creates a new user. Returns activate URL for password setup."""
    csrf = get_csrf(admin_session)
    resp = admin_session.post(
        f'{OVERLEAF_URL}/admin/register',
        json={'email': email, '_csrf': csrf},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    # Returns: {"email": "...", "setNewPasswordUrl": "https://.../user/activate?token=...&user_id=..."}
    return data['setNewPasswordUrl']
```

### 2.2 Set Password via Activate URL

The activate URL is a one-time link. A fresh (non-logged-in) session must visit it and POST the new password.

```python
def set_user_password(activate_url, new_password):
    """Set password for a newly created user via the activate URL."""
    pw_session = requests.Session()
    resp = pw_session.get(activate_url, timeout=10)

    csrf = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', resp.text).group(1)
    token = re.search(r'token=([a-f0-9]+)', activate_url).group(1)

    resp2 = pw_session.post(
        f'{OVERLEAF_URL}/user/password/set',
        json={
            'passwordResetToken': token,
            'password': new_password,
            '_csrf': csrf,
        },
        timeout=15,
        allow_redirects=False,
    )
    if resp2.status_code not in (200, 302):
        raise RuntimeError(f'Set password failed: {resp2.status_code}')
```

### 2.3 Delete Session User (Self-Delete)

After task completion and reward verification, the session user deletes their own account. This also removes all associated projects.

```python
def delete_own_account(session, password):
    """User deletes their own account and all projects."""
    csrf = get_csrf(session)
    resp = session.post(
        f'{OVERLEAF_URL}/user/delete',
        json={'password': password, '_csrf': csrf},
        timeout=15,
    )
    resp.raise_for_status()
```

### 2.4 Full User Lifecycle (Setup Helper)

```python
import uuid

def create_session_credentials():
    """Generate unique session email and password."""
    session_id = uuid.uuid4().hex[:12]
    email = f'session-{session_id}@cua-gym.local'
    password = f'cua-{uuid.uuid4().hex[:16]}'
    return email, password, session_id

def provision_session_user(admin_email, admin_password):
    """Full flow: admin creates user → set password → return logged-in session."""
    email, password, session_id = create_session_credentials()

    # Step 1: Admin creates user
    admin = requests.Session()
    login(admin, admin_email, admin_password)
    activate_url = create_session_user(admin, email)
    admin.post(f'{OVERLEAF_URL}/logout',
               json={'_csrf': get_csrf(admin)}, allow_redirects=False)

    # Step 2: Set password
    set_user_password(activate_url, password)

    # Step 3: Login as session user
    session = requests.Session()
    login(session, email, password)

    return session, email, password, session_id
```

---

## 3. Project API

### 3.1 Create Project from ZIP (Primary Method)

The most reliable way to create projects with arbitrary content. Build a ZIP in memory, upload it.

```python
import io
import zipfile

def build_project_zip(files: dict) -> bytes:
    """Build a ZIP from a dict of {filename: content_string}.

    Args:
        files: e.g., {'main.tex': '\\documentclass{article}...', 'refs.bib': '@article{...}'}
    Returns:
        ZIP bytes ready for upload.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buf.seek(0)
    return buf.read()

def create_project(session, name, zip_bytes):
    """Upload ZIP to create project. Returns project_id."""
    csrf = get_csrf(session)
    resp = session.post(
        f'{OVERLEAF_URL}/project/new/upload',
        files={'qqfile': (f'{name}.zip', zip_bytes, 'application/zip')},
        data={'name': name},
        headers={'X-CSRF-Token': csrf},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['project_id']
```

### 3.2 Create Blank Project

```python
def create_blank_project(session, name):
    """Create blank project with default main.tex. Returns project_id."""
    csrf = get_csrf(session)
    resp = session.post(
        f'{OVERLEAF_URL}/project/new',
        json={'projectName': name, '_csrf': csrf},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()['project_id']
```

### 3.3 Read Project File List (Entities)

```python
def get_file_list(session, project_id):
    """Get flat list of project files with paths.

    Returns: ['/main.tex', '/sections/intro.tex', '/figures/fig1.png', ...]
    """
    resp = session.get(
        f'{OVERLEAF_URL}/project/{project_id}/entities',
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    entities = data.get('entities', [])
    return [e['path'] for e in entities]
```

**Response format:**
```json
{
  "project_id": "abc123",
  "entities": [
    {"path": "/main.tex", "type": "doc"},
    {"path": "/references.bib", "type": "doc"},
    {"path": "/figures/plot.png", "type": "file"}
  ]
}
```

- `type: "doc"` = text file (.tex, .bib, .cls, .sty, .bst, .txt)
- `type: "file"` = binary file (images, PDFs, fonts)

### 3.4 Download Project as ZIP

```python
def download_project_zip(session, project_id):
    """Download entire project as ZIP. Returns bytes."""
    resp = session.get(
        f'{OVERLEAF_URL}/Project/{project_id}/download/zip',
        timeout=30,
    )
    resp.raise_for_status()
    return resp.content

def read_file_from_zip(zip_bytes, filename):
    """Extract a single file's content from project ZIP."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        return zf.read(filename).decode('utf-8')

def list_files_in_zip(zip_bytes):
    """List all files in project ZIP."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        return zf.namelist()
```

### 3.5 Compile Project

```python
def compile_project(session, project_id):
    """Compile project. Returns compile result with output file URLs.

    Returns: {
        'status': 'success' | 'failure' | 'timedout',
        'outputFiles': [{'path': 'output.pdf', 'url': '/project/.../output.pdf', 'build': '...', 'size': N}, ...]
    }
    """
    csrf = get_csrf(session)
    resp = session.post(
        f'{OVERLEAF_URL}/project/{project_id}/compile',
        json={'rootDoc_id': '', 'draft': False, 'check': 'silent', '_csrf': csrf},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()
```

### 3.6 Download Compiled PDF

**CRITICAL**: The PDF URL requires a build ID from the compile response. The simple path `/project/{id}/output/output.pdf` does NOT work.

```python
def download_pdf(session, project_id, compile_result):
    """Download compiled PDF. Must pass compile_result from compile_project()."""
    for f in compile_result.get('outputFiles', []):
        if f.get('path') == 'output.pdf':
            resp = session.get(f'{OVERLEAF_URL}{f["url"]}', timeout=30)
            resp.raise_for_status()
            return resp.content
    raise RuntimeError('No PDF in compile output')
```

### 3.7 Update Project Settings

```python
def update_settings(session, project_id, settings):
    """Update project settings.

    Supported settings:
        compiler: 'pdflatex' | 'xelatex' | 'lualatex' | 'latex'
        spellCheckLanguage: 'en' | 'fr' | 'de' | ...
    """
    csrf = get_csrf(session)
    resp = session.post(
        f'{OVERLEAF_URL}/project/{project_id}/settings',
        json={**settings, '_csrf': csrf},
        timeout=10,
    )
    resp.raise_for_status()
```

### 3.8 Word Count

```python
def get_wordcount(session, project_id):
    """Get word count of compiled document.

    Returns: {'texcount': {'textWords': N, 'headWords': N, 'mathInline': N, ...}}
    """
    resp = session.get(
        f'{OVERLEAF_URL}/project/{project_id}/wordcount',
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
```

### 3.9 Delete Project

```python
def delete_project(session, project_id):
    """Delete a project."""
    csrf = get_csrf(session)
    resp = session.delete(
        f'{OVERLEAF_URL}/Project/{project_id}',
        headers={'X-CSRF-Token': csrf},
        timeout=10,
    )
    resp.raise_for_status()
```

---

## 4. Task State Persistence

The state file `/tmp/task_overleaf_state` links `initial_setup.py`, `golden_patch.py`, and `reward.py` to the same user and project.

**State format:**
```json
{
    "project_id": "69b8f6ef24d927a869b834c4",
    "overleaf_url": "https://cua-gym-overleaf.xlang.ai",
    "session_email": "session-a1b2c3d4e5f6@cua-gym.local",
    "session_password": "cua-7f8e9d0c1b2a3456",
    "admin_email": "agent@cua-gym.local",
    "admin_password": "cua-gym-agent-2024"
}
```

```python
import json

STATE_FILE = '/tmp/task_overleaf_state'

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)
```

---

## 5. initial_setup.py Template

```python
"""
Initial Setup: <task_description>
Task ID: <task_id>
Domain: overleaf
"""
import io
import json
import os
import re
import shlex
import subprocess
import time
import uuid
import zipfile

import requests

# --- Config ---
OVERLEAF_URL = 'https://cua-gym-overleaf.xlang.ai'
ADMIN_EMAIL = 'agent@cua-gym.local'
ADMIN_PASSWORD = 'cua-gym-agent-2024'

# --- Helper functions (from Section 1-2) ---
def get_csrf(session):
    resp = session.get(f'{OVERLEAF_URL}/login', timeout=10)
    match = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', resp.text)
    return match.group(1)

def do_login(session, email, password):
    csrf = get_csrf(session)
    resp = session.post(f'{OVERLEAF_URL}/login',
        json={'email': email, 'password': password, '_csrf': csrf},
        timeout=15, allow_redirects=False)
    assert resp.status_code in (200, 302), f'Login failed: {resp.status_code}'

# --- Step 1: Create session user ---
session_id = uuid.uuid4().hex[:12]
session_email = f'session-{session_id}@cua-gym.local'
session_password = f'cua-{uuid.uuid4().hex[:16]}'

admin = requests.Session()
do_login(admin, ADMIN_EMAIL, ADMIN_PASSWORD)
csrf = get_csrf(admin)
resp = admin.post(f'{OVERLEAF_URL}/admin/register',
    json={'email': session_email, '_csrf': csrf}, timeout=15)
activate_url = resp.json()['setNewPasswordUrl']

# Set password
pw_session = requests.Session()
pw_resp = pw_session.get(activate_url, timeout=10)
pw_csrf = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', pw_resp.text).group(1)
pw_token = re.search(r'token=([a-f0-9]+)', activate_url).group(1)
pw_session.post(f'{OVERLEAF_URL}/user/password/set',
    json={'passwordResetToken': pw_token, 'password': session_password, '_csrf': pw_csrf},
    timeout=15, allow_redirects=False)

# --- Step 2: Login as session user ---
session = requests.Session()
do_login(session, session_email, session_password)

# --- Step 3: Build project ZIP ---
# Construct realistic LaTeX content for the task's initial state.
# The initial state should NOT contain the changes the task asks the agent to make.
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as zf:
    zf.writestr('main.tex', r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{graphicx}

\title{Quarterly Sales Report}
\author{Data Analytics Team}
\date{\today}

\begin{document}
\maketitle

\section{Introduction}
This report summarizes the quarterly sales performance across all regions.

\section{Results}
% TODO: Add results table here

\end{document}
""".strip())

    zf.writestr('references.bib', r"""
@article{smith2024,
    author = {Smith, John},
    title = {Sales Forecasting Methods},
    journal = {Journal of Business Analytics},
    year = {2024}
}
""".strip())
buf.seek(0)

# --- Step 4: Upload and create project ---
csrf = get_csrf(session)
resp = session.post(f'{OVERLEAF_URL}/project/new/upload',
    files={'qqfile': ('project.zip', buf.getvalue(), 'application/zip')},
    data={'name': 'Quarterly Sales Report'},
    headers={'X-CSRF-Token': csrf},
    timeout=30)
project_id = resp.json()['project_id']

# --- Step 5: Save state ---
state = {
    'project_id': project_id,
    'overleaf_url': OVERLEAF_URL,
    'session_email': session_email,
    'session_password': session_password,
    'admin_email': ADMIN_EMAIL,
    'admin_password': ADMIN_PASSWORD,
}
with open('/tmp/task_overleaf_state', 'w') as f:
    json.dump(state, f)

print(f'Project created: {project_id}')
print(f'URL: {OVERLEAF_URL}/project/{project_id}')

# --- Step 6: Launch browser ---
def launch_gui(command, delay_sec=1.0):
    env = os.environ.copy()
    env['DISPLAY'] = ':0'
    subprocess.Popen(shlex.split(command),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    time.sleep(delay_sec)

launch_gui(f'google-chrome "{OVERLEAF_URL}/project/{project_id}"', delay_sec=3.0)
print(f'GUI_READY: launched browser at {OVERLEAF_URL}/project/{project_id}')
```

---

## 6. golden_patch.py Template

**CRITICAL**: Unlike mock_websites, there is no `set_current` API. The golden state is created by uploading a new project with the expected final content under the **same user account**.

**Strategy**: Delete the initial project, create a new project with the golden content, and update the state file with the new project_id.

```python
"""
Golden Patch: <task_description>
Task ID: <task_id>
Domain: overleaf
Changes: <brief list of what this patch does>
"""
import io
import json
import re
import zipfile

import requests

# --- Config ---
OVERLEAF_URL = 'https://cua-gym-overleaf.xlang.ai'

# --- Load state ---
with open('/tmp/task_overleaf_state') as f:
    state = json.load(f)

def get_csrf(session):
    resp = session.get(f'{OVERLEAF_URL}/login', timeout=10)
    match = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', resp.text)
    return match.group(1)

def do_login(session, email, password):
    csrf = get_csrf(session)
    resp = session.post(f'{OVERLEAF_URL}/login',
        json={'email': email, 'password': password, '_csrf': csrf},
        timeout=15, allow_redirects=False)
    assert resp.status_code in (200, 302)

# --- Login as session user ---
session = requests.Session()
do_login(session, state['session_email'], state['session_password'])

# --- Delete old project ---
old_pid = state['project_id']
csrf = get_csrf(session)
session.delete(f'{OVERLEAF_URL}/Project/{old_pid}',
    headers={'X-CSRF-Token': csrf}, timeout=10)

# --- Build golden project ---
# Start from the SAME initial content, then apply the task's required changes.
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as zf:
    zf.writestr('main.tex', r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{graphicx}

\title{Quarterly Sales Report}
\author{Data Analytics Team}
\date{\today}

\begin{document}
\maketitle

\section{Introduction}
This report summarizes the quarterly sales performance across all regions.

\section{Results}
\begin{tabular}{|l|r|r|}
\hline
Region & Q1 Sales & Q2 Sales \\
\hline
North America & \$1.2M & \$1.5M \\
Europe & \$0.8M & \$0.9M \\
Asia Pacific & \$0.6M & \$0.7M \\
\hline
\textbf{Total} & \textbf{\$2.6M} & \textbf{\$3.1M} \\
\hline
\end{tabular}

\end{document}
""".strip())

    zf.writestr('references.bib', r"""
@article{smith2024,
    author = {Smith, John},
    title = {Sales Forecasting Methods},
    journal = {Journal of Business Analytics},
    year = {2024}
}
""".strip())
buf.seek(0)

# --- Upload golden project ---
csrf = get_csrf(session)
resp = session.post(f'{OVERLEAF_URL}/project/new/upload',
    files={'qqfile': ('project.zip', buf.getvalue(), 'application/zip')},
    data={'name': 'Quarterly Sales Report'},
    headers={'X-CSRF-Token': csrf},
    timeout=30)
new_pid = resp.json()['project_id']

# --- Update state ---
state['project_id'] = new_pid
with open('/tmp/task_overleaf_state', 'w') as f:
    json.dump(state, f)

print(f'Golden project created: {new_pid}')
```

---

## 7. reward.py Template

```python
"""
Reward Script: <task_description>
Task ID: <task_id>
Domain: overleaf
Scoring: <brief rubric>
"""
import io
import json
import re
import sys
import zipfile

import requests

# --- Load state ---
try:
    with open('/tmp/task_overleaf_state') as f:
        state = json.load(f)
except Exception as e:
    print(f'CRITICAL: Cannot read state: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

OVERLEAF_URL = state['overleaf_url']
PROJECT_ID = state['project_id']

# --- Login ---
def get_csrf(session):
    resp = session.get(f'{OVERLEAF_URL}/login', timeout=10)
    match = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', resp.text)
    return match.group(1)

try:
    session = requests.Session()
    csrf = get_csrf(session)
    resp = session.post(f'{OVERLEAF_URL}/login',
        json={'email': state['session_email'], 'password': state['session_password'], '_csrf': csrf},
        timeout=15, allow_redirects=False)
    assert resp.status_code in (200, 302)
except Exception as e:
    print(f'CRITICAL: Login failed: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

# --- Fetch project content ---
try:
    zip_resp = session.get(f'{OVERLEAF_URL}/Project/{PROJECT_ID}/download/zip', timeout=30)
    zip_resp.raise_for_status()
    project_zip = zip_resp.content
except Exception as e:
    print(f'CRITICAL: Cannot download project: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

def read_tex(filename):
    """Read a .tex file from the project ZIP."""
    with zipfile.ZipFile(io.BytesIO(project_zip)) as zf:
        return zf.read(filename).decode('utf-8')

def list_files():
    """List all files in the project ZIP."""
    with zipfile.ZipFile(io.BytesIO(project_zip)) as zf:
        return zf.namelist()

# --- Verification ---
def verify_task():
    total_score = 0.0

    # Component 1: <description> (X.X points)
    try:
        main_tex = read_tex('main.tex')
        # Example: check if Results section has a table
        if r'\begin{tabular}' in main_tex:
            print(f'PASS: Results table exists (0.4 pts)')
            total_score += 0.4
        else:
            print(f'FAIL: No table found in main.tex')
    except Exception as e:
        print(f'ERROR: Component 1 — {e}')

    # Component 2: <description> (X.X points)
    try:
        # Example: check compilation succeeds
        csrf = get_csrf(session)
        compile_resp = session.post(
            f'{OVERLEAF_URL}/project/{PROJECT_ID}/compile',
            json={'rootDoc_id': '', 'draft': False, 'check': 'silent', '_csrf': csrf},
            timeout=120)
        result = compile_resp.json()
        if result.get('status') == 'success':
            print(f'PASS: Compilation successful (0.3 pts)')
            total_score += 0.3
        else:
            print(f'FAIL: Compilation failed: {result.get("status")}')
    except Exception as e:
        print(f'ERROR: Component 2 — {e}')

    # Component 3: <description> (X.X points)
    try:
        # Example: check specific content
        main_tex = read_tex('main.tex')
        if 'North America' in main_tex and 'Europe' in main_tex:
            print(f'PASS: Regional data present (0.3 pts)')
            total_score += 0.3
        else:
            print(f'FAIL: Missing regional data')
    except Exception as e:
        print(f'ERROR: Component 3 — {e}')

    final_score = min(total_score, 1.0)
    print(f'\nScore: {total_score}/1.0')
    print(f'REWARD: {final_score}')
    return final_score

verify_task()
```

---

## 8. Cleanup Template

Every task must clean up after reward verification. Place this in the orchestrator or as a post-reward step.

```python
"""Cleanup: delete project and session user."""
import json
import re
import requests

with open('/tmp/task_overleaf_state') as f:
    state = json.load(f)

OVERLEAF_URL = state['overleaf_url']

def get_csrf(session):
    resp = session.get(f'{OVERLEAF_URL}/login', timeout=10)
    match = re.search(r'name="ol-csrfToken"\s+content="([^"]+)"', resp.text)
    return match.group(1)

# Login as session user
session = requests.Session()
csrf = get_csrf(session)
session.post(f'{OVERLEAF_URL}/login',
    json={'email': state['session_email'], 'password': state['session_password'], '_csrf': csrf},
    timeout=15, allow_redirects=False)

# Delete project
csrf = get_csrf(session)
session.delete(f'{OVERLEAF_URL}/Project/{state["project_id"]}',
    headers={'X-CSRF-Token': csrf}, timeout=10)

# Delete user (self-delete removes all remaining projects too)
csrf = get_csrf(session)
session.post(f'{OVERLEAF_URL}/user/delete',
    json={'password': state['session_password'], '_csrf': csrf},
    timeout=15)

print(f'Cleaned up: user={state["session_email"]}, project={state["project_id"]}')
```

---

## 9. Verification Techniques Reference

### 9.1 Content Verification (Text Matching)

```python
main_tex = read_tex('main.tex')

# Check section exists
has_section = r'\section{Related Work}' in main_tex

# Check command exists
has_package = r'\usepackage{hyperref}' in main_tex

# Check specific content with regex
import re
tables = re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}', main_tex, re.DOTALL)
num_tables = len(tables)

# Check bibliography entries
bib = read_tex('references.bib')
entries = re.findall(r'@\w+\{(\w+),', bib)
```

### 9.2 File Structure Verification

```python
files = list_files()

# Check specific files exist
assert 'main.tex' in files
assert 'figures/plot.png' in files

# Check directory structure
figure_files = [f for f in files if f.startswith('figures/')]
section_files = [f for f in files if f.startswith('sections/')]
```

### 9.3 Compilation Verification

```python
csrf = get_csrf(session)
result = session.post(f'{OVERLEAF_URL}/project/{PROJECT_ID}/compile',
    json={'rootDoc_id': '', 'draft': False, 'check': 'silent', '_csrf': csrf},
    timeout=120).json()

# Check compilation status
compile_ok = result.get('status') == 'success'

# Check for specific warnings/errors in log
for f in result.get('outputFiles', []):
    if f['path'] == 'output.log':
        log = session.get(f'{OVERLEAF_URL}{f["url"]}', timeout=30).text
        has_warnings = 'LaTeX Warning' in log
        has_errors = '! ' in log
```

### 9.4 PDF Content Verification

Download the compiled PDF and verify its content using PyMuPDF (fitz).

```python
# Download PDF
compile_result = compile_project(session, PROJECT_ID)
pdf_bytes = download_pdf(session, PROJECT_ID, compile_result)

# Verify with PyMuPDF (must be installed on VM)
import fitz  # PyMuPDF
doc = fitz.open(stream=pdf_bytes, filetype='pdf')

# Page count
num_pages = len(doc)

# Extract text
full_text = ''
for page in doc:
    full_text += page.get_text()

# Check specific content in rendered PDF
assert 'Quarterly Sales Report' in full_text
assert 'North America' in full_text

# Check for images
for page in doc:
    images = page.get_images()
    # images is a list of (xref, smask, width, height, ...) tuples

doc.close()
```

### 9.5 Word Count Verification

```python
wc = get_wordcount(session, PROJECT_ID)
text_words = wc['texcount']['textWords']
math_inline = wc['texcount']['mathInline']
math_display = wc['texcount']['mathDisplay']
```

### 9.6 Project Settings Verification

Project settings (compiler, language) can be checked via the entities API response or by inspecting the project page meta tags.

```python
# Check via entities API (project_id is in response)
resp = session.get(f'{OVERLEAF_URL}/project/{PROJECT_ID}/entities', timeout=10)
# Settings are not directly in entities — use compile behavior as proxy:
# If xelatex is required, compile with xelatex-only features and check success
```

---

## 10. Bitter Lessons

1. **CSRF in multipart uploads MUST use the `X-CSRF-Token` header.** Putting `_csrf` in the `data` dict for file uploads returns 403 Forbidden. This is the #1 integration bug.

2. **PDF download requires the full URL from compile results.** The simple path `/project/{id}/output/output.pdf` returns 404. You must compile first, then use the `url` field from the `outputFiles` array in the compile response.

3. **The entities API returns flat paths, not nested trees.** Format is `[{"path": "/main.tex", "type": "doc"}, ...]`. There are no folder IDs or doc IDs in this response. To get IDs for folder/doc operations, parse the project editor page's `ol-project` meta tag.

4. **Session users start as `holdingAccount: true`.** You MUST visit the activate URL and POST a password before the user can log in. Attempting to login before setting a password returns 401.

5. **User self-delete (`/user/delete`) removes everything.** All projects, history, and associated data are purged. This is the cleanest cleanup method and should always be used instead of deleting projects individually.

6. **CSRF tokens change after login.** The token obtained before login is invalidated when the session regenerates. Always call `get_csrf()` again after `login()`.

7. **Compilation is CPU-intensive and can take 30+ seconds.** Set `timeout=120` for compile requests. For documents with heavy packages (tikz, listings), compilation may take even longer.

8. **ZIP upload creates projects atomically.** All files in the ZIP are created at once. This is much more reliable than creating a blank project and adding files one by one (which requires folder IDs and multiple API calls).

9. **LaTeX content in Python strings needs raw strings or double backslashes.** Use `r"""\documentclass{article}..."""` or escape backslashes as `\\documentclass`. Forgetting this silently corrupts LaTeX source.

10. **Cloudflare has a 100-second WebSocket idle timeout.** Long-idle editor sessions may disconnect. This doesn't affect API calls but may impact the CUA agent's browser editing experience. Overleaf's built-in keepalive usually handles this.

11. **Each session user has independent project space.** User A cannot see or access User B's projects. This provides natural isolation between concurrent training episodes without any additional configuration.

12. **`/dev/csrf` may return HTML instead of plain text.** In some Overleaf versions, this endpoint returns the login page HTML. Always extract CSRF from the `ol-csrfToken` meta tag as a fallback.
