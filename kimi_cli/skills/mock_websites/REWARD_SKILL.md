---
name: mock_websites_reward
description: "How to write reward.py scripts that verify mock web application state for CUA-Gym tasks. For reward-gen agent."
user-invocable: false
---

# Mock Websites — Reward Script Guide

This skill teaches **reward-gen** how to write `reward.py` scripts that verify task completion against mock web application state. Unlike file-based domains, there are no local artifacts — state is fetched via HTTP.

For new UDA-Gym-style bundles, prefer `check.sh` and the hardened public hybrid
flow in Section 2. Legacy references to `initial_setup.py`, `reward.py`, and
`/tmp/task_web_sid` are compatibility patterns for old CUA-Gym tasks; UDA-Gym
bundles must use the randomized `$UDA_GYM_HARNESS_STATE_DIR/mock_sessions.json`
contract supplied by the uda-gym driver, and must never expose
sid/token/state fixtures to the agent.

---

## 1. Reading the Session ID

For native UDA-Gym bundles, read the randomized rollout sid from the
driver-owned metadata file:

```python
import json
import os
import sys
from pathlib import Path

mock_name = '<mock>'
state_dir = os.environ.get('UDA_GYM_HARNESS_STATE_DIR')
if not state_dir:
    print(json.dumps({
        'overall_score': 0.0,
        'subscores': {},
        'errors': ['setup_fail: UDA_GYM_HARNESS_STATE_DIR missing'],
    }))
    sys.exit(0)

session_file = Path(state_dir) / 'mock_sessions.json'
try:
    sessions = json.loads(session_file.read_text())
    sid = sessions[mock_name]['sid']
except Exception as exc:
    print(json.dumps({
        'overall_score': 0.0,
        'subscores': {},
        'errors': [f'setup_fail: cannot read mock session metadata: {exc}'],
    }))
    sys.exit(0)
```

The legacy pattern below is for old CUA-Gym tasks only. Do not use it when
writing new UDA-Gym `check.sh` evaluators.

The sid was written by `initial_setup.py` to `/tmp/task_web_sid`. Fail early if not found.

```python
import sys

try:
    with open('/tmp/task_web_sid') as f:
        sid = f.read().strip()
    if not sid:
        raise ValueError('sid is empty')
except Exception as e:
    print(f'CRITICAL: Cannot read sid from /tmp/task_web_sid: {e}')
    print('REWARD: 0.0')
    sys.exit(0)
```

---

## 2. Fetching State from the Mock Server

For new UDA-style tasks, default to the hybrid hardened CUA-Gym-Hub flow on the
normal public `cua-gym-*.xlang.ai` hosts. Reward code must read the admin token
from `CUA_GYM_ADMIN_TOKEN`; on the Singapore deployment machine the fallback
token source file is `/home/ubuntu/.cua-gym-hub-admin-token`. Do not hard-code
the token value in generated scripts, prompts, skills, or git-tracked files.
Do not use private IPs, `/etc/hosts`, DNS rewrites, or `curl --resolve`; public
hosts are compatible with both legacy no-token traffic and hardened
token-authenticated traffic. Always include a browser-like `User-Agent` such as
`Mozilla/5.0` on hidden setup/check API calls; several public mock hosts may
reject Python/curl default user agents with Cloudflare 403/1010 even when the
admin token is correct.

Reward/check scripts must treat the mock server as the authoritative state
source. Do not read browser SQLite databases, Chrome local storage, seeded
fixture JSON, `context/cua_mock_session.json`, or any local mock-state dump as
the verifier source of truth. Those files either do not exist in real tasks or
are agent-visible artifacts that would make the task hackable. The verifier
should read only:

- harness-owned sid metadata such as `$UDA_GYM_HARNESS_STATE_DIR/mock_sessions.json`
- admin-token `/go?sid=<sid>` state from the public `cua-gym-*.xlang.ai` host
- explicit user deliverables under paths named by the task
- ordinary context exports/assets only when the task spec says they are part of the user-visible evidence

For new UDA-Gym bundles, setup must generate a fresh randomized sid for every
rollout and write it to harness-owned metadata such as
`$UDA_GYM_HARNESS_STATE_DIR/mock_sessions.json`. Check/reward must read that
metadata. Do not recompute a deterministic sid from the task id, and do not
guess a sid when the metadata is missing; missing harness metadata is a
setup/harness failure because guessing risks reading stale state from a
previous rollout. The sid remains non-agent-visible because setup/check are
hidden and the browser opens only the returned one-time `launch_url`.

```python
import os
import requests

BASE_URL = 'https://cua-gym-<name>.xlang.ai'  # e.g., cua-gym-slack.xlang.ai

def cua_admin_headers():
    token = os.environ.get('CUA_GYM_ADMIN_TOKEN')
    if not token and os.path.exists('/home/ubuntu/.cua-gym-hub-admin-token'):
        with open('/home/ubuntu/.cua-gym-hub-admin-token') as f:
            token = f.read().strip()
    if not token:
        raise RuntimeError('CUA_GYM_ADMIN_TOKEN is required for hardened CUA-Gym-Hub')
    return {
        'X-CUA-Admin-Token': token,
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    }

try:
    resp = requests.get(f'{BASE_URL}/go?sid={sid}', headers=cua_admin_headers(), timeout=15)
    resp.raise_for_status()
    data = resp.json()
except Exception as e:
    print(f'CRITICAL: Cannot fetch state from {BASE_URL}/go?sid={sid}: {e}')
    print('REWARD: 0.0')
    sys.exit(0)

initial_state = data.get('initial_state', {})
current_state = data.get('current_state', {})
state_diff = data.get('state_diff', {})
```

**Key insight**: `initial_state` is the pre-task snapshot. `current_state` is what the agent (or golden_patch) produced. Your reward script scores how well `current_state` matches the expected post-task state.

For UDA-Gym-style task bundles, the same logic usually lives in `check.sh`
instead of `reward.py`. Keep the same security boundary: `CUA_GYM_ADMIN_TOKEN`
is a harness-only environment variable for setup/check, never an agent-visible
env var or file in `/tmp_workspace`.

---

## 3. Reward Script Template (Programmatic Verification)

For tasks with clearly defined, checkable success criteria:

```python
"""
Reward Script: <task_description>
Task ID: <task_id>
Domain: mock_websites
Mock: <mock_name>
Scoring: <brief rubric>
"""
import json
import os
import sys

import requests

# --- Read sid ---
try:
    with open('/tmp/task_web_sid') as f:
        sid = f.read().strip()
except Exception:
    print('REWARD: 0.0')
    sys.exit(0)

BASE_URL = 'https://cua-gym-<name>.xlang.ai'

def cua_admin_headers():
    token = os.environ.get('CUA_GYM_ADMIN_TOKEN')
    if not token and os.path.exists('/home/ubuntu/.cua-gym-hub-admin-token'):
        with open('/home/ubuntu/.cua-gym-hub-admin-token') as f:
            token = f.read().strip()
    if not token:
        raise RuntimeError('CUA_GYM_ADMIN_TOKEN is required for hardened CUA-Gym-Hub')
    return {
        'X-CUA-Admin-Token': token,
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    }

# --- Fetch state ---
try:
    data = requests.get(f'{BASE_URL}/go?sid={sid}', headers=cua_admin_headers(), timeout=15).json()
except Exception:
    print('REWARD: 0.0')
    sys.exit(0)

initial = data.get('initial_state', {})
current = data.get('current_state', {})

def verify_task():
    total_score = 0.0

    # Component 1: <description> (X.X points)
    try:
        # Example: check if a new message was sent in #general
        initial_msgs = initial.get('messages', {}).get('general', [])
        current_msgs = current.get('messages', {}).get('general', [])
        if len(current_msgs) > len(initial_msgs):
            new_msgs = current_msgs[len(initial_msgs):]
            if any('hello' in m.get('content', '').lower() for m in new_msgs):
                print(f'PASS: New message containing "hello" found ({0.5} pts)')
                total_score += 0.5
            else:
                print(f'FAIL: New messages exist but none contain "hello"')
        else:
            print(f'FAIL: No new messages in #general')
    except Exception as e:
        print(f'ERROR: Component 1 — {e}')

    # Component 2: <description> (X.X points)
    try:
        # ... another check ...
        pass
    except Exception as e:
        print(f'ERROR: Component 2 — {e}')

    final_score = min(total_score, 1.0)
    print(f'\nScore: {total_score}/1.0')
    print(f'REWARD: {final_score}')
    return final_score

verify_task()
```

---

## 4. LLM-as-Judge (Constrained Usage)

For task components where success cannot be verified programmatically (e.g., semantic equivalence like "SD-USA" ≈ "San Diego", or subjective quality like "write a professional reply"), use the pre-deployed LLM judge helper.

### Budget Rule

- **≥ 60%** of total score MUST come from programmatic checks (§3 pattern)
- **≤ 40%** MAY use LLM judge via `call_llm_judge()`
- Every LLM judge call MUST have a `# JUSTIFICATION:` comment

### Usage Pattern

```python
import json
import os
import sys

import requests

# --- Read sid ---
try:
    with open('/tmp/task_web_sid') as f:
        sid = f.read().strip()
except Exception:
    print('REWARD: 0.0')
    sys.exit(0)

BASE_URL = 'https://cua-gym-<name>.xlang.ai'

def cua_admin_headers():
    token = os.environ.get('CUA_GYM_ADMIN_TOKEN')
    if not token and os.path.exists('/home/ubuntu/.cua-gym-hub-admin-token'):
        with open('/home/ubuntu/.cua-gym-hub-admin-token') as f:
            token = f.read().strip()
    if not token:
        raise RuntimeError('CUA_GYM_ADMIN_TOKEN is required for hardened CUA-Gym-Hub')
    return {
        'X-CUA-Admin-Token': token,
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    }

# --- Fetch state ---
try:
    data = requests.get(f'{BASE_URL}/go?sid={sid}', headers=cua_admin_headers(), timeout=15).json()
except Exception:
    print('REWARD: 0.0')
    sys.exit(0)

initial = data.get('initial_state', {})
current = data.get('current_state', {})

# --- Import LLM judge helper (pre-deployed by orchestrator to /tmp/) ---
sys.path.insert(0, '/tmp')
from reward_judge import call_llm_judge

def verify_task():
    total_score = 0.0

    # Component 1 (0.4 pts) — PROGRAMMATIC: message count check
    try:
        initial_msgs = initial.get('messages', {}).get('general', [])
        current_msgs = current.get('messages', {}).get('general', [])
        if len(current_msgs) > len(initial_msgs):
            print(f'PASS: New message(s) found in #general (0.4 pts)')
            total_score += 0.4
        else:
            print(f'FAIL: No new messages in #general')
    except Exception as e:
        print(f'ERROR: Component 1 — {e}')

    # Component 2 (0.3 pts) — PROGRAMMATIC: sender is correct user
    try:
        initial_msgs = initial.get('messages', {}).get('general', [])
        current_msgs = current.get('messages', {}).get('general', [])
        new_msgs = current_msgs[len(initial_msgs):]
        if new_msgs and new_msgs[-1].get('sender') == 'user_1':
            print(f'PASS: Message sent by correct user (0.3 pts)')
            total_score += 0.3
        else:
            print(f'FAIL: Message not sent by user_1')
    except Exception as e:
        print(f'ERROR: Component 2 — {e}')

    # Component 3 (0.3 pts) — LLM JUDGE: message content quality
    # JUSTIFICATION: Task asks agent to "write a professional greeting".
    # No single correct phrasing exists — semantic evaluation needed.
    try:
        initial_msgs = initial.get('messages', {}).get('general', [])
        current_msgs = current.get('messages', {}).get('general', [])
        new_msgs = current_msgs[len(initial_msgs):]
        if new_msgs:
            llm_score = call_llm_judge(
                task_instruction='Write a professional greeting in #general',
                success_criteria='The message is a professional, appropriate greeting',
                state_excerpt=json.dumps(new_msgs[-1]),
            )
            total_score += 0.3 * llm_score
            print(f'LLM JUDGE: Component 3 — {0.3 * llm_score:.2f} pts')
        else:
            print(f'FAIL: Component 3 — no message to evaluate')
    except Exception as e:
        print(f'ERROR: Component 3 — {e}')

    final_score = min(total_score, 1.0)
    print(f'\nScore: {total_score}/1.0')
    print(f'REWARD: {final_score}')
    return final_score

verify_task()
```

### FORBIDDEN — Do NOT use raw OpenAI SDK

```python
# FORBIDDEN — bypasses locked-down model/temperature/system_prompt
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(model='gpt-4o-mini', ...)
```

Always use `from reward_judge import call_llm_judge`. The helper is deployed to `/tmp/reward_judge.py` by the orchestrator with fixed parameters you cannot override.

---

## 5. Composite Scoring (Web + Other Checks)

For hybrid tasks that involve both web state and local file changes:

```python
# Weight allocation
WEB_WEIGHT = 0.7
FILE_WEIGHT = 0.3

# Web state score
web_score = verify_web_state()  # uses pattern from §3

# File score
file_score = verify_local_file()  # standard file verification

final = web_score * WEB_WEIGHT + file_score * FILE_WEIGHT
print(f'REWARD: {min(final, 1.0)}')
```

---

## 6. Multi-Mock Reward

When the task involves multiple mocks, fetch `/go` from each and score the combined state:

```python
mocks = {
    'slack': 'https://cua-gym-slack.xlang.ai',
    'notion': 'https://cua-gym-notion.xlang.ai',
}

states = {}
for name, url in mocks.items():
    try:
        data = requests.get(f'{url}/go?sid={sid}', headers=cua_admin_headers(), timeout=15).json()
        states[name] = data
    except Exception as e:
        print(f'ERROR: Cannot fetch {name}: {e}')
        print('REWARD: 0.0')
        sys.exit(0)

# Score each mock's state independently, then combine
slack_score = verify_slack(states['slack'])
notion_score = verify_notion(states['notion'])
final = slack_score * 0.5 + notion_score * 0.5
print(f'REWARD: {min(final, 1.0)}')
```

---

## 7. Writing success_criteria (for LLM Judge)

Good success criteria are:
- **Specific**: "A message with content containing 'quarterly report' was posted in #marketing"
- **Observable**: Reference state fields the judge can check in the JSON
- **Negative-aware**: "No messages were deleted from #general" (if relevant)

Bad success criteria:
- **Vague**: "The task was completed" — gives the LLM nothing to verify
- **Implementation-focused**: "The POST request succeeded" — describes how, not what
- **Uncheckable**: "The user felt satisfied" — not observable in state

---

## 8. State Schemas

To understand the state structure for each mock, read the schema file:

```
Read: kimi_cli/skills/mock_websites/schemas/<mock_name>.md
```

The schema documents all required top-level keys, entity shapes, and which fields change for specific user actions. Use it to design accurate verification checks.

**Available schemas:** asana_mock, aws_console_mock, discord_mock, docusign_mock, github_mock, gitlab_mock, gmail_mock, jira_mock, linkedin_mock, notion_mock, reddit_mock, salesforce_mock, slack_mock, trello_mock, twitter_mock, youtube_mock.

For mocks without a schema file, fetch default state via `GET /go?sid=nonexistent` to discover the structure.

---

## 9. Information Barrier Reminder

As the reward-gen agent (discriminator), you MUST NOT:
- Read `initial_setup.py` or `golden_patch.py`
- Derive verification logic from setup-gen's implementation
- Use the initial_state from `/go` to "cheat" (e.g., hardcoding expected values from the golden state)

Your reward script must be derivable purely from `task_config.json` (task description + success criteria). Explore the VMs to understand what changed, but design scoring based on task requirements.

---

## 10. REWARD: X.X Format

The **last printed line** of reward.py MUST be `REWARD: X.X` where X.X is a float between 0.0 and 1.0.

```python
# Always end with this pattern
print(f'REWARD: {final_score}')
```

The pipeline parses this line to extract the reward value. Any other format will cause evaluation failure.

---

## 11. Error Handling Checklist

Your reward.py MUST handle these failure modes gracefully (print `REWARD: 0.0` and exit):

| Failure | Cause | Handling |
|---------|-------|----------|
| `/tmp/task_web_sid` not found | initial_setup.py didn't run | `REWARD: 0.0` |
| sid is empty | File exists but empty | `REWARD: 0.0` |
| `/go?sid=<sid>` returns 4xx/5xx | Server error or wrong URL | `REWARD: 0.0` |
| `/go?sid=<sid>` times out | Server unreachable | `REWARD: 0.0` |
| `current_state` is None | No state was injected for this sid | `REWARD: 0.0` |
| `initial_state == current_state` | No changes made (agent did nothing) | `REWARD: 0.0` |
| LLM judge API fails | OpenAI key missing or rate limited | `REWARD: 0.0` |
| JSON parse error | Malformed response | `REWARD: 0.0` |

**Never let reward.py crash without printing `REWARD: X.X`.** Wrap everything in try/except.

---

## 12. UDA Mock Website Pitfalls To Avoid

These came from real rollout failures and should be treated as hard rules when
batch-converting UDA queries into runnable task bundles:

1. **Do not put the seeded mock state in `context/`.** If the agent can read the complete state JSON directly, the task stops measuring GUI/browser skill and becomes a file-reading task.

2. **Do not mention mock session files in the task instruction.** Phrases like "open `/tmp_workspace/context/cua_mock_session.json`" are wrong. The harness should inject and open the website; the user instruction should say the dashboard/app is already open in Chrome or ask the agent to use the normal public website.

3. **Use the public hybrid host.** Hidden setup/check code should call `https://cua-gym-<name>.xlang.ai/post` and `/go` with `X-CUA-Admin-Token` plus `User-Agent: Mozilla/5.0`. Do not verify against private IPs, `/etc/hosts`, DNS rewrites, or `curl --resolve`. Treat 403/1010 responses as verifier transport bugs to fix before rollout, not as task difficulty.

4. **Verify server-side state, not browser-local state.** The authoritative verifier state is admin-token `/go?sid=<sid>`. Chrome history, cookies, IndexedDB, localStorage, and bundled JS are not reward truth.

5. **Keep the admin token out of the agent environment.** Use harness-only env injection such as `harness_env.tsv` or runner-level secret passing. Never write the token to `/tmp_workspace/.env`, task instructions, context files, or generated code visible to the agent.

6. **Expect no-token `/go?sid=<real_sid>` to show empty/default state.** That is the hardened behavior. If a no-token request reveals the seeded task state, the website deployment is misconfigured.

7. **Score structured deliverables, not free-form summaries.** For UDA tasks, prefer exact JSON/CSV/GeoJSON/etc. fields plus mock state checks. Avoid requiring a free-form markdown summary as the main deliverable because it is hard to verify and easy to game.

8. **Do not reward setup success.** A passing verifier must prove the agent produced the requested final state or deliverable. `POST /post` success, Chrome launch success, or the presence of a sid file are setup checks, not task completion.
