---
name: penpot
description: "How to set up and manipulate Penpot design tool state via HTTP APIs for CUA-Gym UI design tasks. For setup-gen and reward-gen agents."
user-invocable: false
---

# Penpot — Setup & Verification Guide

This skill teaches **setup-gen** and **reward-gen** how to create, manipulate, and verify Penpot project state for UI design tasks. Like Overleaf, Penpot tasks involve **HTTP state management** through a shared Penpot instance — there are no local design files on the VM.

- Libraries: `requests`, `json`, `uuid`, `re`, `zipfile`, `io`
- Penpot instance: `https://cua-gym-figma.xlang.ai`

---

## 0. Architecture Overview

```
Register temp user  →  Login (session cookie)  →  Create project
       ↓                       ↓                       ↓
  No email verif       API returns JSON         Import template (.penpot ZIP)
                               ↓                       ↓
                        setup-gen configures     CUA agent operates in browser
                               ↓                       ↓
                        reward-gen reads          get-file / get-page
                        shape tree                     ↓
                               ↓               Score 0.0–1.0
                        delete-profile (cleanup)
```

**Key difference from mock_websites**: Penpot uses **per-session user accounts** (not session IDs). Each training episode gets its own user for isolation. The user is created at setup and deleted after reward verification.

**Key difference from Overleaf**: No CSRF tokens needed. No admin account required — users self-register. API uses JSON RPC, not REST. Must set `Accept: application/json` header or responses return Transit+JSON (Clojure serialization).

---

## 1. Authentication API

All Penpot API calls use session-cookie authentication. The base endpoint is `/api/rpc/command/<method>`.

### 1.1 API Call Pattern

```python
import requests

PENPOT_URL = 'https://cua-gym-figma.xlang.ai'

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',  # CRITICAL: without this, responses are Transit+JSON
})

def rpc(session, method, payload=None):
    """Call Penpot RPC API."""
    resp = session.post(
        f'{PENPOT_URL}/api/rpc/command/{method}',
        json=payload or {},
    )
    return resp
```

### 1.2 Register User

Registration is a two-step process: prepare → confirm.

```python
def register_user(session, email, password, fullname):
    """Register a new user. Returns profile dict."""
    # Step 1: Prepare
    resp = rpc(session, 'prepare-register-profile', {
        'email': email,
        'password': password,
        'fullname': fullname,
    })
    resp.raise_for_status()
    token = resp.json()['token']

    # Step 2: Complete
    resp = rpc(session, 'register-profile', {'token': token})
    resp.raise_for_status()
    return resp.json()  # {'id': '...', 'email': '...', 'fullname': '...'}
```

### 1.3 Login

```python
def login(session, email, password):
    """Login and establish session cookie. Returns profile with team/project IDs."""
    resp = rpc(session, 'login-with-password', {
        'email': email,
        'password': password,
    })
    resp.raise_for_status()
    return resp.json()
    # Returns: {
    #   'id': '...',
    #   'defaultTeamId': '...',
    #   'defaultProjectId': '...',
    #   'email': '...',
    #   ...
    # }
```

### 1.4 Delete User (Self-Delete)

```python
def delete_profile(session):
    """Delete the logged-in user and ALL their data."""
    resp = rpc(session, 'delete-profile', {})
    # Returns 204 No Content on success
    return resp.status_code in (200, 204)
```

---

## 2. User Lifecycle

Each training episode creates and destroys an isolated user.

```python
import uuid

def create_session_credentials():
    """Generate unique session email and password."""
    sid = uuid.uuid4().hex[:12]
    email = f'session-{sid}@cua-gym.local'
    password = f'cua-{uuid.uuid4().hex[:16]}'
    return email, password, sid

def provision_session(penpot_url):
    """Full flow: register → login → return session with team info."""
    email, password, sid = create_session_credentials()

    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })

    register_user(session, email, password, 'CUA Agent')
    profile = login(session, email, password)

    return session, {
        'email': email,
        'password': password,
        'session_id': sid,
        'team_id': profile['defaultTeamId'],
        'default_project_id': profile['defaultProjectId'],
    }
```

---

## 3. Project & File API

### 3.1 Create Project

```python
def create_project(session, team_id, name):
    """Create a project. Returns project dict with 'id'."""
    resp = rpc(session, 'create-project', {
        'teamId': team_id,
        'name': name,
    })
    resp.raise_for_status()
    return resp.json()
```

### 3.2 Create Empty File

```python
def create_file(session, project_id, name):
    """Create an empty design file. Returns file dict with 'id'.
    New files have 1 page with 1 root frame."""
    resp = rpc(session, 'create-file', {
        'projectId': project_id,
        'name': name,
    })
    resp.raise_for_status()
    return resp.json()
```

### 3.3 Import Template (.penpot ZIP)

**CRITICAL**: The `import-binfile` endpoint expects **ZIP format** (starts with `PK` header). Files exported from Penpot's web UI in newer versions may use a v2 binary format (header `010b1a86`) which is NOT compatible with this API. Always use templates that were exported via the API's `export-binfile` method.

```python
def import_template(session, project_id, name, zip_bytes):
    """Import a .penpot ZIP file into a project.
    Returns SSE stream with progress events.
    """
    from io import BytesIO
    # MUST remove Content-Type for multipart
    saved_ct = session.headers.pop('Content-Type', None)
    resp = session.post(
        f'{PENPOT_URL}/api/rpc/command/import-binfile',
        data={
            'name': name,
            'project-id': project_id,  # NOTE: kebab-case for multipart
        },
        files={
            'file': ('template.penpot', BytesIO(zip_bytes), 'application/octet-stream'),
        },
        headers={'Accept': 'application/json'},
        timeout=180,
    )
    if saved_ct:
        session.headers['Content-Type'] = saved_ct
    return resp

def import_template_from_path(session, project_id, name, filepath):
    """Import from a local file path."""
    with open(filepath, 'rb') as f:
        zip_bytes = f.read()
    return import_template(session, project_id, name, zip_bytes)
```

### 3.4 Export File as ZIP

Export is an SSE (Server-Sent Events) stream that returns a download URL.

```python
import re

def export_file(session, file_id):
    """Export a file as ZIP. Returns ZIP bytes."""
    resp = rpc(session, 'export-binfile', {
        'fileId': file_id,
        'includeLibraries': False,
        'embedAssets': True,
    })

    # Parse SSE to find download URL
    download_url = None
    for line in resp.text.strip().split('\n'):
        if line.startswith('data: ') and '~#uri' in line:
            match = re.search(r'"(https?://[^"]+)"', line)
            if match:
                download_url = match.group(1)

    if not download_url:
        raise RuntimeError('No download URL in export response')

    dl_resp = session.get(download_url, timeout=60)
    dl_resp.raise_for_status()
    return dl_resp.content  # ZIP bytes
```

### 3.5 List Project Files

```python
def get_project_files(session, project_id):
    """List all files in a project."""
    resp = rpc(session, 'get-project-files', {'projectId': project_id})
    resp.raise_for_status()
    return resp.json()  # [{'id': '...', 'name': '...', ...}, ...]
```

### 3.6 Delete File / Project

```python
def delete_file(session, file_id):
    rpc(session, 'delete-file', {'id': file_id})  # 204

def delete_project(session, project_id):
    rpc(session, 'delete-project', {'id': project_id})  # 204
```

---

## 4. Reading Design State (for Reward Verification)

### 4.1 Get File Data

```python
def get_file(session, file_id):
    """Get full file data including pages index, components, colors, typographies."""
    resp = rpc(session, 'get-file', {'id': file_id})
    resp.raise_for_status()
    return resp.json()
    # Returns: {
    #   'id': '...',
    #   'name': '...',
    #   'data': {
    #     'pagesIndex': {'<page-id>': {'name': '...', ...}, ...},
    #     'components': {'<comp-id>': {...}, ...},
    #     'colors': {'<color-id>': {'name': '...', 'color': '#hex', ...}, ...},
    #     'typographies': {'<typo-id>': {'name': '...', 'fontFamily': '...', ...}, ...},
    #   }
    # }
```

### 4.2 Get Page Shape Tree

```python
def get_page(session, file_id, page_id):
    """Get all shapes on a page. Returns objects dict keyed by shape ID."""
    resp = rpc(session, 'get-page', {
        'fileId': file_id,
        'pageId': page_id,
    })
    resp.raise_for_status()
    return resp.json()
    # Returns: {
    #   'objects': {
    #     '<shape-id>': {
    #       'type': 'frame' | 'rect' | 'circle' | 'text' | 'path' | 'image' | 'group',
    #       'name': 'Button',
    #       'x': 100, 'y': 200,
    #       'width': 300, 'height': 50,
    #       'fills': [{'fillColor': '#3498db', 'fillOpacity': 1}],
    #       'strokes': [...],
    #       'children': ['child-id-1', 'child-id-2'],
    #       'parentId': 'parent-id',
    #       ...
    #     },
    #     ...
    #   }
    # }
```

### 4.3 Shape Properties Reference

Each shape object may contain:

| Property | Type | Description |
|----------|------|-------------|
| `type` | string | `frame`, `rect`, `circle`, `text`, `path`, `image`, `group`, `bool`, `svg-raw` |
| `name` | string | User-visible layer name |
| `x`, `y` | number | Position |
| `width`, `height` | number | Dimensions |
| `rotation` | number | Rotation in degrees |
| `fills` | array | `[{fillColor: '#hex', fillOpacity: N}, ...]` |
| `strokes` | array | `[{strokeColor: '#hex', strokeWidth: N, strokeAlignment: 'center'|'inner'|'outer'}, ...]` |
| `shadow` | array | Shadow effects |
| `blur` | object | Blur effect |
| `opacity` | number | 0.0 – 1.0 |
| `hidden` | boolean | Visibility |
| `blocked` | boolean | Locked state |
| `children` | array | Child shape IDs (for frames/groups) |
| `parentId` | string | Parent shape ID |
| `content` | object | Text content (for `type: text`) |
| `selrect` | object | Selection rectangle |
| `constraints` | object | Responsive constraints |
| `interactions` | array | Prototype interactions |
| `componentId` | string | Link to component (if instance) |
| `componentFile` | string | Source file for component |

### 4.4 Helper: Inspect All Pages

```python
def inspect_file_shapes(session, file_id):
    """Get complete shape tree for all pages. Returns structured summary."""
    file_data = get_file(session, file_id)
    data = file_data.get('data', {})
    pages_index = data.get('pagesIndex', {})

    result = {
        'components': len(data.get('components', {})),
        'colors': len(data.get('colors', {})),
        'typographies': len(data.get('typographies', {})),
        'pages': [],
    }

    for pid in pages_index:
        pname = pages_index[pid]
        if isinstance(pname, dict):
            pname = pname.get('name', pid)

        page = get_page(session, file_id, pid)
        objects = page.get('objects', {})

        type_counts = {}
        for obj in objects.values():
            if isinstance(obj, dict):
                t = obj.get('type', 'unknown')
                type_counts[t] = type_counts.get(t, 0) + 1

        result['pages'].append({
            'id': pid,
            'name': pname,
            'objectCount': len(objects),
            'typeCounts': type_counts,
        })

    return result
```

---

## 5. Task State Persistence

The state file `/tmp/task_penpot_state` links `initial_setup.py`, `golden_patch.py`, and `reward.py`.

```json
{
    "penpot_url": "https://cua-gym-figma.xlang.ai",
    "session_email": "session-a1b2c3d4e5f6@cua-gym.local",
    "session_password": "cua-7f8e9d0c1b2a3456",
    "team_id": "...",
    "project_id": "...",
    "file_id": "...",
    "file_url": "https://cua-gym-figma.xlang.ai/view/..."
}
```

```python
import json

STATE_FILE = '/tmp/task_penpot_state'

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)
```

---

## 6. initial_setup.py Template

```python
"""
Initial Setup: <task_description>
Task ID: <task_id>
Domain: penpot
"""
import json
import os
import shlex
import subprocess
import time
import uuid

import requests

# --- Config ---
PENPOT_URL = 'https://cua-gym-figma.xlang.ai'

# --- Helper functions ---
def rpc(session, method, payload=None):
    resp = session.post(f'{PENPOT_URL}/api/rpc/command/{method}', json=payload or {})
    return resp

# --- Step 1: Create session user ---
session_id = uuid.uuid4().hex[:12]
session_email = f'session-{session_id}@cua-gym.local'
session_password = f'cua-{uuid.uuid4().hex[:16]}'

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
})

# Register
resp = rpc(session, 'prepare-register-profile', {
    'email': session_email,
    'password': session_password,
    'fullname': 'CUA Agent',
})
token = resp.json()['token']
rpc(session, 'register-profile', {'token': token})

# Login
profile = rpc(session, 'login-with-password', {
    'email': session_email,
    'password': session_password,
}).json()
team_id = profile['defaultTeamId']

# --- Step 2: Create project ---
project = rpc(session, 'create-project', {
    'teamId': team_id,
    'name': 'Design Task',
}).json()
project_id = project['id']

# --- Step 3: Create or import initial design ---

# OPTION A: Import a pre-made template
# Template must be in ZIP format (exported via API, NOT from Penpot web UI)
# template_path = '/path/to/template.penpot'
# saved_ct = session.headers.pop('Content-Type', None)
# with open(template_path, 'rb') as f:
#     resp = session.post(
#         f'{PENPOT_URL}/api/rpc/command/import-binfile',
#         data={'name': 'Task Design', 'project-id': project_id},
#         files={'file': ('template.penpot', f, 'application/octet-stream')},
#         headers={'Accept': 'application/json'},
#         timeout=180,
#     )
# if saved_ct:
#     session.headers['Content-Type'] = saved_ct
# # Get imported file ID
# files = rpc(session, 'get-project-files', {'projectId': project_id}).json()
# file_id = files[0]['id']

# OPTION B: Create empty file (for "create from scratch" tasks)
file_data = rpc(session, 'create-file', {
    'projectId': project_id,
    'name': 'Task Design',
}).json()
file_id = file_data['id']

# --- Step 4: Save state ---
state = {
    'penpot_url': PENPOT_URL,
    'session_email': session_email,
    'session_password': session_password,
    'team_id': team_id,
    'project_id': project_id,
    'file_id': file_id,
}
with open('/tmp/task_penpot_state', 'w') as f:
    json.dump(state, f)

print(f'Project created: {project_id}')
print(f'File created: {file_id}')
file_url = f'{PENPOT_URL}/view/{file_id}'

# --- Step 5: Launch browser ---
def launch_gui(command, delay_sec=1.0):
    env = os.environ.copy()
    env['DISPLAY'] = ':0'
    subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    time.sleep(delay_sec)

# Open workspace editor (not viewer)
workspace_url = f'{PENPOT_URL}/#/workspace/{project_id}/{file_id}'
launch_gui(f'google-chrome "{workspace_url}"', delay_sec=3.0)
print(f'GUI_READY: launched browser at {workspace_url}')
```

---

## 7. golden_patch.py Template

**Strategy**: Export the initial file as a template, then create a new file with the expected final state, replacing the initial file in the state.

For Penpot tasks, the golden patch creates the expected completed design either by:
- (A) Creating a new file with the expected content via import
- (B) Modifying state file reference to point to a pre-built golden template

```python
"""
Golden Patch: <task_description>
Task ID: <task_id>
Domain: penpot
Changes: <brief list of what this patch does>
"""
import json
import re

import requests

# --- Config ---
PENPOT_URL = 'https://cua-gym-figma.xlang.ai'

# --- Load state ---
with open('/tmp/task_penpot_state') as f:
    state = json.load(f)

def rpc(session, method, payload=None):
    resp = session.post(f'{PENPOT_URL}/api/rpc/command/{method}', json=payload or {})
    return resp

# --- Login ---
session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
})
rpc(session, 'login-with-password', {
    'email': state['session_email'],
    'password': state['session_password'],
})

# --- Delete initial file ---
rpc(session, 'delete-file', {'id': state['file_id']})

# --- Create golden file ---
# OPTION A: Import golden template
# golden_template = '/path/to/golden_template.penpot'
# saved_ct = session.headers.pop('Content-Type', None)
# with open(golden_template, 'rb') as f:
#     resp = session.post(
#         f'{PENPOT_URL}/api/rpc/command/import-binfile',
#         data={'name': 'Task Design', 'project-id': state['project_id']},
#         files={'file': ('golden.penpot', f, 'application/octet-stream')},
#         headers={'Accept': 'application/json'},
#         timeout=180,
#     )
# if saved_ct:
#     session.headers['Content-Type'] = saved_ct

# OPTION B: Create file with expected content
file_data = rpc(session, 'create-file', {
    'projectId': state['project_id'],
    'name': 'Task Design',
}).json()
new_file_id = file_data['id']

# TODO: Use update-file to add expected shapes/components
# This is the most complex part — see Section 9 for shape manipulation

# --- Update state ---
state['file_id'] = new_file_id
with open('/tmp/task_penpot_state', 'w') as f:
    json.dump(state, f)

print(f'Golden file created: {new_file_id}')
```

---

## 8. reward.py Template

```python
"""
Reward Script: <task_description>
Task ID: <task_id>
Domain: penpot
Scoring: <brief rubric>
"""
import json
import sys

import requests

# --- Load state ---
try:
    with open('/tmp/task_penpot_state') as f:
        state = json.load(f)
except Exception as e:
    print(f'CRITICAL: Cannot read state: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

PENPOT_URL = state['penpot_url']
FILE_ID = state['file_id']

def rpc(session, method, payload=None):
    resp = session.post(f'{PENPOT_URL}/api/rpc/command/{method}', json=payload or {})
    return resp

# --- Login ---
try:
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })
    resp = rpc(session, 'login-with-password', {
        'email': state['session_email'],
        'password': state['session_password'],
    })
    assert resp.status_code == 200, f'Login failed: {resp.status_code}'
except Exception as e:
    print(f'CRITICAL: Login failed: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

# --- Fetch design state ---
try:
    file_data = rpc(session, 'get-file', {'id': FILE_ID}).json()
    data = file_data.get('data', {})
    pages_index = data.get('pagesIndex', {})
    components = data.get('components', {})
    colors = data.get('colors', {})
    typographies = data.get('typographies', {})

    # Get first page shapes
    page_ids = list(pages_index.keys())
    all_shapes = {}
    for pid in page_ids:
        page = rpc(session, 'get-page', {'fileId': FILE_ID, 'pageId': pid}).json()
        all_shapes[pid] = page.get('objects', {})
except Exception as e:
    print(f'CRITICAL: Cannot read file: {e}')
    print('REWARD: 0.0')
    sys.exit(0)


# --- Verification ---
def verify_task():
    total_score = 0.0

    # Component 1: <description> (X.X points)
    try:
        # Example: check that a rectangle shape exists
        first_page_shapes = all_shapes[page_ids[0]]
        rect_shapes = [
            s for s in first_page_shapes.values()
            if isinstance(s, dict) and s.get('type') == 'rect'
        ]
        if len(rect_shapes) >= 1:
            print(f'PASS: Rectangle shape exists ({len(rect_shapes)} found) (0.3 pts)')
            total_score += 0.3
        else:
            print('FAIL: No rectangle shapes found')
    except Exception as e:
        print(f'ERROR: Component 1 — {e}')

    # Component 2: <description> (X.X points)
    try:
        # Example: check fill color
        for s in rect_shapes:
            fills = s.get('fills', [])
            if fills and fills[0].get('fillColor', '').lower() == '#3498db':
                print(f'PASS: Correct fill color #3498db (0.3 pts)')
                total_score += 0.3
                break
        else:
            print('FAIL: No shape with expected fill color #3498db')
    except Exception as e:
        print(f'ERROR: Component 2 — {e}')

    # Component 3: <description> (X.X points)
    try:
        # Example: check shape dimensions
        for s in rect_shapes:
            w = s.get('width', 0)
            h = s.get('height', 0)
            if abs(w - 200) < 5 and abs(h - 100) < 5:
                print(f'PASS: Shape dimensions ~200x100 (0.2 pts)')
                total_score += 0.2
                break
        else:
            print('FAIL: No shape with expected dimensions')
    except Exception as e:
        print(f'ERROR: Component 3 — {e}')

    # Component 4: <description> (X.X points)
    try:
        # Example: check text content
        text_shapes = [
            s for s in first_page_shapes.values()
            if isinstance(s, dict) and s.get('type') == 'text'
        ]
        if text_shapes:
            print(f'PASS: Text element exists ({len(text_shapes)} found) (0.2 pts)')
            total_score += 0.2
        else:
            print('FAIL: No text elements found')
    except Exception as e:
        print(f'ERROR: Component 4 — {e}')

    final_score = min(total_score, 1.0)
    print(f'\nScore: {total_score}/1.0')
    print(f'REWARD: {final_score}')
    return final_score

verify_task()
```

---

## 9. Verification Techniques Reference

### 9.1 Shape Count & Type Verification

```python
# Count shapes by type on a page
type_counts = {}
for obj in page_shapes.values():
    if isinstance(obj, dict):
        t = obj.get('type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1

# Verify minimum counts
assert type_counts.get('rect', 0) >= 3, 'Need at least 3 rectangles'
assert type_counts.get('text', 0) >= 2, 'Need at least 2 text elements'
```

### 9.2 Shape Property Verification

```python
# Find shape by name
def find_shape_by_name(shapes, name):
    for sid, s in shapes.items():
        if isinstance(s, dict) and s.get('name') == name:
            return s
    return None

button = find_shape_by_name(page_shapes, 'Submit Button')
if button:
    # Check position
    assert abs(button['x'] - 100) < 10
    assert abs(button['y'] - 200) < 10

    # Check size
    assert abs(button['width'] - 150) < 5
    assert abs(button['height'] - 40) < 5

    # Check fill
    fills = button.get('fills', [])
    assert len(fills) > 0
    assert fills[0].get('fillColor', '').lower() == '#2ecc71'

    # Check stroke
    strokes = button.get('strokes', [])
    if strokes:
        assert strokes[0].get('strokeWidth', 0) == 2
```

### 9.3 Layer Hierarchy Verification

```python
# Check parent-child relationships
def get_children(shapes, parent_id):
    parent = shapes.get(parent_id)
    if not parent or not isinstance(parent, dict):
        return []
    child_ids = parent.get('children', [])
    return [shapes[cid] for cid in child_ids if cid in shapes]

# Verify a frame contains expected children
frame = find_shape_by_name(page_shapes, 'Card Component')
children = get_children(page_shapes, frame_id)
child_types = [c.get('type') for c in children]
assert 'text' in child_types, 'Card must contain text'
assert 'rect' in child_types, 'Card must contain rectangle background'
```

### 9.4 Component Library Verification

```python
# Check components defined in file
file_data = get_file(session, file_id)
components = file_data['data'].get('components', {})

# Verify component exists
comp_names = [c.get('name', '') for c in components.values() if isinstance(c, dict)]
assert 'Button' in comp_names, 'Button component must exist'
assert 'Card' in comp_names, 'Card component must exist'
```

### 9.5 Color & Typography Verification

```python
# Check colors in design system
colors = file_data['data'].get('colors', {})
color_values = [c.get('color', '') for c in colors.values() if isinstance(c, dict)]
assert '#3498db' in [c.lower() for c in color_values], 'Primary blue must be defined'

# Check typographies
typographies = file_data['data'].get('typographies', {})
font_families = [t.get('fontFamily', '') for t in typographies.values() if isinstance(t, dict)]
assert 'Inter' in font_families or 'Roboto' in font_families
```

### 9.6 Multi-Page Verification

```python
# Verify page count and names
pages_index = file_data['data'].get('pagesIndex', {})
page_names = []
for pinfo in pages_index.values():
    if isinstance(pinfo, dict):
        page_names.append(pinfo.get('name', ''))
    else:
        page_names.append(str(pinfo))

assert len(page_names) >= 3, 'Need at least 3 pages'
assert 'Home' in page_names, 'Must have Home page'
assert 'About' in page_names, 'Must have About page'
```

### 9.7 Visual Comparison (Fuzzy)

For tasks where exact property matching is insufficient, compare shape counts and approximate positions.

```python
def shapes_similar(expected_shapes, actual_shapes, tolerance=20):
    """Check if actual design roughly matches expected layout."""
    score = 0.0
    total = len(expected_shapes)

    for exp in expected_shapes:
        best_match = None
        best_dist = float('inf')
        for act in actual_shapes.values():
            if not isinstance(act, dict):
                continue
            if act.get('type') != exp['type']:
                continue
            dx = abs(act.get('x', 0) - exp['x'])
            dy = abs(act.get('y', 0) - exp['y'])
            dist = (dx**2 + dy**2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_match = act
        if best_match and best_dist < tolerance:
            score += 1.0

    return score / total if total > 0 else 0.0
```

---

## 10. Cleanup Template

```python
"""Cleanup: delete project and session user."""
import json
import requests

with open('/tmp/task_penpot_state') as f:
    state = json.load(f)

PENPOT_URL = state['penpot_url']

session = requests.Session()
session.headers.update({
    'Content-Type': 'application/json',
    'Accept': 'application/json',
})

# Login
session.post(f'{PENPOT_URL}/api/rpc/command/login-with-password', json={
    'email': state['session_email'],
    'password': state['session_password'],
})

# Delete profile (cascades to all projects and files)
session.post(f'{PENPOT_URL}/api/rpc/command/delete-profile', json={})

print(f'Cleaned up: user={state["session_email"]}')
```

---

## 11. Preparing Template Files

Since the `import-binfile` API requires ZIP format, templates must be prepared via the API export flow:

1. **Manual setup**: Open Penpot web UI → create a design → add shapes/components
2. **Export via API**: Login via API → `export-binfile` → download ZIP from URL
3. **Store**: Save ZIP as `.penpot` in `templates/` directory

```python
# Script to export a template from an existing Penpot file
import re, requests

PENPOT_URL = 'https://cua-gym-figma.xlang.ai'
session = requests.Session()
session.headers.update({'Content-Type': 'application/json', 'Accept': 'application/json'})

# Login with the account that owns the template
session.post(f'{PENPOT_URL}/api/rpc/command/login-with-password',
    json={'email': 'your@email.com', 'password': 'your-pass'})

# Export
resp = session.post(f'{PENPOT_URL}/api/rpc/command/export-binfile',
    json={'fileId': 'TARGET_FILE_ID', 'includeLibraries': True, 'embedAssets': True})

for line in resp.text.strip().split('\n'):
    if 'uri' in line:
        url = re.search(r'"(https?://[^"]+)"', line).group(1)
        data = session.get(url).content
        with open('templates/my_template.penpot', 'wb') as f:
            f.write(data)
        print(f'Saved {len(data)} bytes')
```

---

## 12. Bitter Lessons

1. **`Accept: application/json` is mandatory.** Without it, Penpot returns Transit+JSON (Clojure's serialization format: `["^ ", "~:key", "value"]`), which standard JSON parsers cannot handle. ALWAYS set this header on every session.

2. **Import expects ZIP format, not v2 binary.** Files exported from Penpot's web UI (newer versions) use a proprietary binary format (header `010b1a86` with zstd compression). The `import-binfile` API only accepts ZIP format. Always prepare templates via the API's `export-binfile` method.

3. **Multipart params use kebab-case.** For `import-binfile`, use `project-id` (NOT `projectId`) in multipart form data. JSON RPC calls use camelCase.

4. **Export is SSE, not direct download.** `export-binfile` returns a `text/event-stream` with progress events. The actual file URL is in the `end` event's `~#uri` field. You must parse the stream and make a second GET request.

5. **Delete returns 204, not 200.** `delete-file`, `delete-project`, `delete-profile` all return `204 No Content`. Don't treat this as an error.

6. **New files have 1 page with 1 root frame.** The root frame (`type: frame`, `name: Root Frame`) is always present. It's the container for all other shapes on the page. Don't count it as a user-created shape.

7. **`delete-profile` cascades to everything.** Deleting the user removes all their teams, projects, files, and data. This is the cleanest cleanup — no need to delete individual files or projects first.

8. **Registration is two-step.** `prepare-register-profile` returns a token, then `register-profile` completes it. Both must succeed. The token is a JWT valid for a limited time.

9. **Login returns essential IDs.** The `defaultTeamId` and `defaultProjectId` from login are needed for creating projects. Don't skip the login step even if you just registered (registration doesn't return these).

10. **Shape IDs are UUIDs.** All shapes, pages, files, projects use UUID format (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`). When verifying shapes, always match by `name` or `type` rather than ID (IDs change on each import).

11. **Concurrent episodes need separate users.** Each CUA training episode must have its own registered user. Never share users between episodes — shapes would collide and verification would be unreliable.

12. **No CSRF tokens needed.** Unlike Overleaf, Penpot uses session cookies only. No need to extract CSRF from HTML pages. This simplifies the API client significantly.
