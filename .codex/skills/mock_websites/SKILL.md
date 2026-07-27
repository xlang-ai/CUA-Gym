---
name: mock_websites
description: "How to set up and manipulate mock web application state via HTTP APIs for CUA-Gym tasks. For setup-gen and reward-gen agents."
user-invocable: false
---

# Mock Websites — Setup & State Injection Guide

This skill teaches **setup-gen** how to create initial web app state and golden patches for mock website tasks. Unlike file-based domains, mock website tasks involve **HTTP state injection** — there are no local files on the VM.

- Libraries: `requests`, `json`, `uuid`
- All 16 mocks are deployed at `https://cua-gym-<name>.xlang.ai`

---

## 0. Mock Website Registry

All mocks are publicly deployed. The URL pattern is `https://cua-gym-<name>.xlang.ai` where `<name>` is the directory name without `_mock`, with underscores replaced by hyphens.

| Mock | Public URL | SCHEMA.md |
|------|-----------|-----------|
| asana_mock | `https://cua-gym-asana.xlang.ai` | `openrlvr-mock/asana_mock/SCHEMA.md` |
| aws_console_mock | `https://cua-gym-aws-console.xlang.ai` | `openrlvr-mock/aws_console_mock/SCHEMA.md` |
| discord_mock | `https://cua-gym-discord.xlang.ai` | `openrlvr-mock/discord_mock/SCHEMA.md` |
| docusign_mock | `https://cua-gym-docusign.xlang.ai` | `openrlvr-mock/docusign_mock/SCHEMA.md` |
| github_mock | `https://cua-gym-github.xlang.ai` | `openrlvr-mock/github_mock/SCHEMA.md` |
| gitlab_mock | `https://cua-gym-gitlab.xlang.ai` | `openrlvr-mock/gitlab_mock/SCHEMA.md` |
| gmail_mock | `https://cua-gym-gmail.xlang.ai` | `openrlvr-mock/gmail_mock/SCHEMA.md` |
| jira_mock | `https://cua-gym-jira.xlang.ai` | `openrlvr-mock/jira_mock/SCHEMA.md` |
| linkedin_mock | `https://cua-gym-linkedin.xlang.ai` | `openrlvr-mock/linkedin_mock/SCHEMA.md` |
| notion_mock | `https://cua-gym-notion.xlang.ai` | `openrlvr-mock/notion_mock/SCHEMA.md` |
| reddit_mock | `https://cua-gym-reddit.xlang.ai` | `openrlvr-mock/reddit_mock/SCHEMA.md` |
| salesforce_mock | `https://cua-gym-salesforce.xlang.ai` | `openrlvr-mock/salesforce_mock/SCHEMA.md` |
| slack_mock | `https://cua-gym-slack.xlang.ai` | `openrlvr-mock/slack_mock/SCHEMA.md` |
| trello_mock | `https://cua-gym-trello.xlang.ai` | `openrlvr-mock/trello_mock/SCHEMA.md` |
| twitter_mock | `https://cua-gym-twitter.xlang.ai` | `openrlvr-mock/twitter_mock/SCHEMA.md` |
| youtube_mock | `https://cua-gym-youtube.xlang.ai` | `openrlvr-mock/youtube_mock/SCHEMA.md` |

---

## 1. State API

### Hardened Default For New Tasks

For new UDA-style tasks, default to the hybrid hardened CUA-Gym-Hub flow on the normal public `cua-gym-*.xlang.ai` hosts:

- Setup and reward code read the admin token from `CUA_GYM_ADMIN_TOKEN`.
- On the Singapore deployment machine, the token source file is `/home/ubuntu/.cua-gym-hub-admin-token`.
- Do not hard-code the token value in generated scripts, prompts, skills, or git-tracked files.
- Use `X-CUA-Admin-Token` for `/post?sid=<sid>` and `/go?sid=<sid>`.
  Always include a browser-like `User-Agent` such as `Mozilla/5.0` on hidden
  setup/check API calls; several public mock hosts may reject Python/curl
  default user agents with Cloudflare 403/1010 even when the admin token is
  correct.
- Open Chrome to the one-time `launch_url` returned by `POST /post?sid=<sid>`, not to `/?sid=<sid>`.
- Do not rewrite DNS, edit `/etc/hosts`, use private IPs, or pass `--resolve` for normal tasks. The public mock hosts are compatible with both legacy no-token traffic and hardened token-authenticated traffic.
- Do not expose `CUA_GYM_ADMIN_TOKEN` to the agent process or write it to `/tmp_workspace/.env`; pass it only to hidden setup/check/reward harness code.
- Do not put the full mock state, seeded session JSON, sid, admin token, or verifier-only URL into `context/`, task instructions, or setup text. The agent should see the website in Chrome, not the fixture that seeded it.
- Do not instruct the agent to open `/tmp_workspace/context/cua_mock_session.json`, `mock.json`, `state.json`, or similar harness files. Task instructions should say that the seeded website is already open, or should name the public app URL only when the user workflow naturally requires opening it.
- The same public host supports legacy and hardened traffic. Legacy no-token traffic remains available for older tasks, while new UDA tasks should use the token-authenticated API in setup/reward and the one-time `launch_url` for the browser.
- Open the browser normally with `google-chrome "$BASE_URL$launch_url"`. Do not over-engineer browser navigation with `/etc/hosts`, `curl --resolve`, temporary redirect HTML, `about:blank`, or `xdotool` unless the task itself specifically requires GUI automation during setup.
- Setup must verify that Chrome actually opened. Use a durable launch such as
  `nohup setsid google-chrome --no-sandbox --disable-dev-shm-usage "$BASE_URL$launch_url" ... &`,
  then poll `pgrep` and, when available, `xdotool search --onlyvisible --class chrome`
  for a visible browser window. If Chrome did not open, print the launch log and
  exit nonzero. A setup script that merely backgrounds Chrome without checking it
  is not acceptable for UDA-Gym bundles.
- On EC2 desktop profiles, launch Chrome as the real desktop user with
  `sudo -u user env DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority
  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus ...`; a root-owned
  Chrome process can exist while the pre-rollout screenshot remains only the
  desktop. If setup creates a temporary Chrome profile as root, `chown -R
  user:user` before launching as `user`.
- After opening the one-time `launch_url`, perform an admin-token `/go?sid=...`
  readback and verify that the seeded app identity is still present. For
  example, Jira tasks should still show the injected project/key/statuses, not
  the default Kanban Project. If launch falls back to default state, fail setup
  so the bad session is caught before rollout.
- If an older UDA query package includes `context/cua_mock`, `context/warmup.sh`,
  or local mock/session JSON as source material, treat those as harness-only seed
  assets during materialization: move them to `hidden/`, never to `exec/context/`,
  and never mention them in `instruction.md`.
- If no deployed mock website fits and the task still needs a bespoke browser
  UI, switch to `.codex/skills/local_custom_ui/SKILL.md`. Do not implement the
  fallback as `exec/context/**/index.html`, visible app JavaScript, or
  source-visible local UI files for a UDA-critical surface.

Helper for setup/golden/reward code:

```python
import os

def cua_admin_headers():
    token = os.environ.get('CUA_GYM_ADMIN_TOKEN')
    if not token and os.path.exists('/home/ubuntu/.cua-gym-hub-admin-token'):
        with open('/home/ubuntu/.cua-gym-hub-admin-token') as f:
            token = f.read().strip()
    assert token, 'CUA_GYM_ADMIN_TOKEN is required for hardened CUA-Gym-Hub'
    return {
        'X-CUA-Admin-Token': token,
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    }
```

Every mock exposes identical HTTP endpoints:

### POST `/post?sid=<sid>` — State Injection

| Action | Body | Effect |
|--------|------|--------|
| `set` | `{"action":"set", "state":{...}}` | Writes current_state AND creates initial_state (if first write). Used by `initial_setup.py`. |
| `set_current` | `{"action":"set_current", "state":{...}}` | Writes ONLY current_state. Never touches initial_state. Used by `golden_patch.py`. |
| `reset` | `{"action":"reset"}` | Deletes both current and initial state files. |

All actions support `"merge": true` to deep-merge into existing state instead of replacing.

### GET `/go?sid=<sid>` — State Inspection

For new tasks, call this with `headers=cua_admin_headers()`.

Returns:
```json
{
  "initial_state": { ... },
  "current_state": { ... },
  "state_diff": { ... }
}
```

- `initial_state` = snapshot from first `action:"set"` call
- `current_state` = latest state (updated by UI interactions or `set_current`)
- `state_diff` = keys that changed between initial and current

### Hybrid Hardened Behavior

In hardened mode, `POST /post?sid=<sid>` returns:

```json
{
  "status": "ok",
  "launch_url": "/_cua_session?token=<one-time-token>",
  "public_sid": "__cua_session__"
}
```

Use this exactly as follows:

- Hidden setup/check/reward code keeps the real `sid` in a harness-owned
  metadata directory supplied by the adapter, preferably
  `$UDA_GYM_HARNESS_STATE_DIR/mock_sessions.json`.
- For new UDA-Gym bundles, generate a fresh randomized sid on every setup/run
  using `uuidgen`, Python `uuid.uuid4()`, or stronger randomness. Do not use a
  deterministic task-level sid: the same task will be rolled out repeatedly,
  and reusing a sid can leak stale server-side state between attempts.
- The adapter must pass `$UDA_GYM_HARNESS_STATE_DIR` only to hidden setup/check
  harness phases, not to the agent process. If the metadata is missing at
  check time, classify it as setup/harness failure; do not recompute or guess a
  sid from the task id.
- Hidden setup/check/reward code uses `X-CUA-Admin-Token` when calling `/post` and `/go` with the real `sid`.
- Hidden setup/check/reward code includes `User-Agent: Mozilla/5.0` on `/post`,
  `/go`, and `/upload` requests. Treat 403/1010 responses as verifier transport
  bugs to fix before rollout, not as task difficulty.
- Browser setup opens `BASE_URL + launch_url` in Chrome. The site consumes the one-time token, sets an HttpOnly session cookie, and redirects the agent to a clean app URL.
- The task instruction should never mention the real `sid`, the one-time token, `/post`, `/go`, admin APIs, local mock JSON, or hidden runtime files.
- A no-token request to `/go?sid=<real_sid>` must not reveal the hardened state. If it returns empty/default legacy state, that is expected.

### GET `/state?sid=<sid>` — Raw State Read

Returns `{stored_state, has_custom_state, sid}`.

### POST `/upload?sid=<sid>` — File Upload

Upload files (attachments, images, documents) to the mock server. Files are stored per-session and served via `/files/`.

**Request**: `multipart/form-data` with one or more file fields.

**Response**:
```json
{
  "success": true,
  "files": [
    {
      "original_name": "report.pdf",
      "stored_name": "a1b2c3d4_report.pdf",
      "size": 12345,
      "content_type": "application/pdf",
      "url": "/files/<sid>/a1b2c3d4_report.pdf"
    }
  ]
}
```

**Usage in initial_setup.py** — upload a file and reference its URL in state:
```python
import requests

# Upload a file
with open('/path/to/attachment.pdf', 'rb') as f:
    resp = requests.post(
        f'{BASE_URL}/upload?sid={sid}',
        files={'file': ('attachment.pdf', f, 'application/pdf')},
        timeout=30
    )
uploaded = resp.json()['files'][0]
file_url = uploaded['url']  # e.g., /files/<sid>/a1b2c3d4_attachment.pdf

# Reference it in state injection
state['messages']['general'].append({
    'messageId': 'msg_1',
    'content': 'Here is the report',
    'attachments': [{'name': 'attachment.pdf', 'url': file_url, 'size': uploaded['size']}],
    # ... other fields
})
```

### GET `/files/<sid>/<filename>` — Serve Uploaded Files

Returns the uploaded file with appropriate Content-Type header. Files are served with `Content-Disposition: attachment`.

---

## 2. Session ID (sid) Pattern

For native UDA-Gym bundles, the active sid pattern is:

1. The `uda-gym` driver creates a randomized per-rollout
   `$UDA_GYM_HARNESS_STATE_DIR` and passes it only to hidden `setup.sh` and
   `check.sh`.
2. `setup.sh` generates a fresh UUID sid for each mock, writes it to
   `$UDA_GYM_HARNESS_STATE_DIR/mock_sessions.json`, injects initial state with
   admin-token `/post`, and opens Chrome to the returned `launch_url`.
3. `check.sh` reads the same metadata file and fetches state with admin-token
   `/go?sid=<sid>`.
4. If the metadata file is missing, the task should be classified as
   setup/harness failure. Do not recompute a deterministic sid or read any
   agent-visible sid file.

The old CUA-Gym sid pattern below is legacy compatibility only. Do not use it
when generating new UDA-Gym bundles.

The sid links `initial_setup.py`, `golden_patch.py`, and `reward.py` to the same state.

**Flow:**
1. `initial_setup.py` generates a UUID sid → writes to `/tmp/task_web_sid` on the VM
2. `initial_setup.py` POSTs `action:"set"` with the sid → creates both initial and current state
3. `golden_patch.py` reads sid from `/tmp/task_web_sid` → POSTs `action:"set_current"` → updates ONLY current state
4. `reward.py` reads sid from `/tmp/task_web_sid` → GETs `/go?sid=<sid>` → compares initial vs current

```python
# Generate and persist sid (initial_setup.py)
import uuid
sid = str(uuid.uuid4())
with open('/tmp/task_web_sid', 'w') as f:
    f.write(sid)

# Read sid (golden_patch.py and reward.py)
with open('/tmp/task_web_sid') as f:
    sid = f.read().strip()
```

---

## 3. State Schemas

Each mock has a schema file documenting the full state shape, default IDs, and observable state changes. Schemas are stored locally in this skill directory.

**MANDATORY: Always read the schema before writing state injection code.** The schema tells you:
- Required top-level keys (e.g., `currentUser`, `channels`, `messages` for slack)
- Object shapes for each entity type
- Default IDs for users, channels, projects, etc.
- Which state fields change when the user performs specific actions

**To load the schema for a mock** (do this in Step 0, immediately after reading this SKILL.md):
```
Read: .codex/skills/mock_websites/schemas/<mock_name>.md
```

Example — for a Slack task:
```
Read: .codex/skills/mock_websites/schemas/slack_mock.md
```

For multi-mock tasks, read ALL schemas for every mock listed in `task_config.json`'s `domains` array.

**Available schemas:** asana_mock, aws_console_mock, discord_mock, docusign_mock, github_mock, gitlab_mock, gmail_mock, jira_mock, linkedin_mock, notion_mock, reddit_mock, salesforce_mock, slack_mock, trello_mock, twitter_mock, youtube_mock.

If no schema file exists for a mock, inspect the mock's default state via `GET /go?sid=nonexistent` to discover the state shape (it returns default data when no custom state is set).

---

## 4. initial_setup.py Template

```python
"""
Initial Setup: <task_description>
Task ID: <task_id>
Domain: mock_websites
Mock: <mock_name>
"""
import json
import os
import shlex
import subprocess
import time
import uuid

import requests

# --- Config ---
BASE_URL = 'https://cua-gym-<name>.xlang.ai'  # e.g., cua-gym-slack.xlang.ai
sid = str(uuid.uuid4())

def cua_admin_headers():
    token = os.environ.get('CUA_GYM_ADMIN_TOKEN')
    if not token and os.path.exists('/home/ubuntu/.cua-gym-hub-admin-token'):
        with open('/home/ubuntu/.cua-gym-hub-admin-token') as f:
            token = f.read().strip()
    assert token, 'CUA_GYM_ADMIN_TOKEN is required for hardened CUA-Gym-Hub'
    return {
        'X-CUA-Admin-Token': token,
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    }

# Persist sid for golden_patch.py and reward.py
with open('/tmp/task_web_sid', 'w') as f:
    f.write(sid)

# --- Build initial state ---
# Consult SCHEMA.md for the full state shape.
# Include ALL required top-level keys. Missing keys → blank UI or crash.
state = {
    # ... full state matching SCHEMA.md ...
}

# --- Inject state ---
resp = requests.post(
    f'{BASE_URL}/post?sid={sid}',
    json={'action': 'set', 'state': state},
    headers=cua_admin_headers(),
    timeout=30
)
assert resp.status_code == 200, f'State injection failed: {resp.text}'
launch_url = resp.json().get('launch_url')
assert launch_url, f'Hardened launch_url missing from response: {resp.text}'
print('State injected')

# --- Verify ---
go = requests.get(f'{BASE_URL}/go?sid={sid}', headers=cua_admin_headers(), timeout=10).json()
assert go['initial_state'] is not None, 'initial_state is None after injection'
print('Verified: initial_state and current_state are set')

# --- Launch browser ---
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

launch_gui(f'google-chrome "{BASE_URL}{launch_url}"', delay_sec=2.0)
print('GUI_READY: launched hardened browser session')
```

---

## 4.1 UDA-Gym Task Bundle Adaptation

When converting a UDA query into a runnable UDA-Gym-style task bundle, the same rules apply, but the files are usually named differently:

| UDA bundle file | Mock website responsibility |
|-----------------|-----------------------------|
| `setup.sh` or hidden setup script | Generate a fresh randomized sid for this rollout, inject initial state with `POST /post?sid=<sid>`, save sid in `$UDA_GYM_HARNESS_STATE_DIR/mock_sessions.json`, and open Chrome to `BASE_URL + launch_url`. |
| `check.sh` or hidden reward script | Read the randomized sid from `$UDA_GYM_HARNESS_STATE_DIR/mock_sessions.json`; fetch current state with admin-token `/go?sid=<sid>`, and compute a structured score from state plus any required local artifacts. Missing metadata is setup/harness failure, not a reason to guess a sid. |
| `context/` | Contains only user-visible exports/assets that would naturally exist for the task. It must not contain complete mock state, sid files, admin responses, or verifier fixtures. |
| `instruction` | Says the seeded site/dashboard/app is open in Chrome, or asks the agent to use the public website normally. It must not tell the agent to read mock session JSON or local seeded-state files. |
| `harness_env.tsv` or equivalent | May request `CUA_GYM_ADMIN_TOKEN` for hidden setup/check only. Do not stage this secret into agent-visible environment files. |

Minimal setup flow:

```python
import json
import os
import subprocess
import uuid
from pathlib import Path

import requests

task_id = '<task_id>'
mock_name = '<mock>'
sid = str(uuid.uuid4())
state_dir = Path(os.environ['UDA_GYM_HARNESS_STATE_DIR'])
state_dir.mkdir(parents=True, exist_ok=True)
state_dir.chmod(0o700)
session_file = state_dir / 'mock_sessions.json'
sessions = json.loads(session_file.read_text()) if session_file.exists() else {}
sessions[mock_name] = {'base_url': BASE_URL, 'sid': sid}
session_file.write_text(json.dumps(sessions))
session_file.chmod(0o600)

resp = requests.post(
    f'{BASE_URL}/post?sid={sid}',
    json={'action': 'set', 'state': state},
    headers=cua_admin_headers(),
    timeout=30,
)
resp.raise_for_status()
launch_url = resp.json()['launch_url']

subprocess.Popen(
    ['google-chrome', '--no-sandbox', '--disable-dev-shm-usage', f'{BASE_URL}{launch_url}'],
    env={**os.environ, 'DISPLAY': os.environ.get('DISPLAY', ':0')},
)
```

For multi-mock tasks, inject every mock first, then open every returned `launch_url` in Chrome. Use the same randomized per-rollout sid across mocks only when the verifier intentionally treats them as one cross-app task session.

---

## 5. golden_patch.py Template

**CRITICAL: Always use `action:"set_current"`. NEVER use `action:"set"` in golden_patch.py.**

Using `action:"set"` would overwrite `initial_state`, making `state_diff` empty and breaking reward evaluation entirely.

```python
"""
Golden Patch: <task_description>
Task ID: <task_id>
Domain: mock_websites
Mock: <mock_name>
Changes: <brief list of what this patch does>
"""
import copy
import json
import os

import requests

# --- Config ---
BASE_URL = 'https://cua-gym-<name>.xlang.ai'

# Read sid from initial_setup.py
with open('/tmp/task_web_sid') as f:
    sid = f.read().strip()

def cua_admin_headers():
    token = os.environ.get('CUA_GYM_ADMIN_TOKEN')
    if not token and os.path.exists('/home/ubuntu/.cua-gym-hub-admin-token'):
        with open('/home/ubuntu/.cua-gym-hub-admin-token') as f:
            token = f.read().strip()
    assert token, 'CUA_GYM_ADMIN_TOKEN is required for hardened CUA-Gym-Hub'
    return {
        'X-CUA-Admin-Token': token,
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    }

# --- Fetch current initial state ---
go = requests.get(f'{BASE_URL}/go?sid={sid}', headers=cua_admin_headers(), timeout=10).json()
state = copy.deepcopy(go['initial_state'])

# --- Apply ONLY the minimal changes the task requires ---
# Example: send a message in #general
# state['messages']['general'].append({
#     'messageId': 'msg_new_1',
#     'senderId': 'user_1',
#     'content': 'Hello world!',
#     'timestamp': '2024-06-15T14:30:00Z',
#     'threadId': None,
#     'reactions': [],
#     'attachments': [],
#     'isEdited': False
# })

# --- Write ONLY current_state (preserve initial_state) ---
resp = requests.post(
    f'{BASE_URL}/post?sid={sid}',
    json={'action': 'set_current', 'state': state},
    headers=cua_admin_headers(),
    timeout=30
)
assert resp.status_code == 200, f'set_current failed: {resp.text}'
print(f'Golden state applied via set_current: sid={sid}')

# --- Verify diff exists ---
go2 = requests.get(f'{BASE_URL}/go?sid={sid}', headers=cua_admin_headers(), timeout=10).json()
assert go2['state_diff'], 'state_diff is empty — golden state matches initial (no changes applied)'
print(f'Verified: state_diff is non-empty')
```

---

## 6. Multi-Mock Tasks

When `task_config.json` contains a `domains` list with multiple mocks:

```json
{
  "domains": ["slack_mock", "notion_mock"],
  "task_instruction": "Copy the meeting notes from Slack #general to a new Notion page"
}
```

Use the **same sid** across all mocks:

```python
# initial_setup.py — inject into ALL listed mocks
sid = str(uuid.uuid4())
with open('/tmp/task_web_sid', 'w') as f:
    f.write(sid)

mocks = {
    'slack_mock': 'https://cua-gym-slack.xlang.ai',
    'notion_mock': 'https://cua-gym-notion.xlang.ai',
}

launch_urls = []
for name, url in mocks.items():
    state = build_state_for(name)  # mock-specific state
    resp = requests.post(f'{url}/post?sid={sid}', json={'action': 'set', 'state': state}, headers=cua_admin_headers(), timeout=30)
    assert resp.status_code == 200
    launch_urls.append((name, url, resp.json()['launch_url']))

for name, url, launch_url in launch_urls:
    launch_gui(f'google-chrome "{url}{launch_url}"', delay_sec=1.0)
```

Golden patch similarly uses `set_current` on each mock that should change.

---

## 7. Sanity Check (for setup-gen Step 7)

Instead of `ls /home/user/`, use curl to verify state:

```bash
python3 scripts/env_cli.py -c "<workdir>/env_config_initial.json" execute \
  "sid=\$(cat /tmp/task_web_sid); curl -s -H \"X-CUA-Admin-Token: \$(cat /home/ubuntu/.cua-gym-hub-admin-token)\" 'https://cua-gym-slack.xlang.ai/go?sid='\$sid | python3 -m json.tool | head -60"
```

---

## 8. Bitter Lessons

1. **`action:"set"` in golden_patch.py is the #1 bug.** It overwrites initial_state, making state_diff empty. Reward scripts that compare initial vs current will always see 0 diff → reward = 0. ALWAYS use `action:"set_current"`.

2. **Missing state keys cause blank pages.** If you inject `{"channels": [...]}` without `currentUser`, `users`, `messages`, etc., the UI renders empty or crashes. Always provide ALL required top-level keys from SCHEMA.md.

3. **Array keys are replaced, not merged.** `deepMerge` treats arrays as atomic values. If you POST `{"messages": {"general": [msg1]}}` with `merge: true`, it replaces the entire `general` array. To add a message, fetch current state first, append, then write back.

4. **sid must be alphanumeric + hyphens + underscores.** The server sanitizes sid with `[^a-zA-Z0-9_-]`. UUIDs work perfectly. Do not use special characters.

5. **State is NOT persisted in the browser.** The browser fetches state from the server on page load via `?sid=xxx`. If you inject state after the browser loads, the user must refresh. Always inject state BEFORE launching the browser.

6. **`/go` without sid returns default state.** Always include `?sid=<sid>` in all API calls. Missing sid returns the app's built-in default data, not your injected state.

7. **Timestamps should be ISO 8601.** Most mocks expect `"2024-06-15T14:30:00Z"` format. Using Unix timestamps or other formats may cause rendering issues.

8. **IDs must be unique within their collection.** When adding new messages, channels, etc., generate unique IDs (e.g., `msg_new_1`, `ch_custom_1`). Duplicate IDs cause silent data corruption.

9. **golden_patch should copy initial_state and apply minimal changes.** Don't build golden state from scratch — start from `go['initial_state']`, deep-copy it, and modify only what the task requires. This ensures the state_diff accurately reflects task completion.

10. **HTTPS is required.** All mocks are served over HTTPS at `cua-gym-*.xlang.ai`. HTTP will not work.

11. **Do not leak the mock fixture into `context/`.** If the agent can read the complete seeded state from local files, the task becomes CLI-only and no longer tests GUI grounding. Only put natural user-facing exports in `context/`; keep full mock state under hidden setup inputs or server-side state.

12. **Do not ask the agent to open harness/session JSON.** Instructions like "open `/tmp_workspace/context/cua_mock_session.json`" are wrong for CUA-Gym-Hub. The harness injects the state; the user-facing instruction should say to use the already-open website or the public app URL.

13. **Do not bypass the public hybrid host.** The correct default is `https://cua-gym-<name>.xlang.ai` with admin-token API calls in hidden harness code. Avoid private IP deployments, `/etc/hosts`, `curl --resolve`, and split-horizon DNS unless debugging infrastructure itself.

14. **Open Chrome directly to the returned `launch_url`.** The one-time token URL is designed for setup. Avoid brittle setup automation such as `about:blank` plus `xdotool` or temporary redirect HTML; those can leave the page on the wrong URL and accidentally turn the task into a pure CLI task.

15. **Check that setup actually opened the seeded UI.** A valid setup should have a visible Chrome window titled for the target mock and reward/check should be able to read the injected server-side state with admin-token `/go`. If the browser is blank or default-state-only, stop and fix setup before rollout.

16. **Reward/check must read server-side authoritative state, not browser storage.** Browser storage is UI/session state. The verifier source of truth is admin-token `/go?sid=<sid>` plus explicit deliverable files.
