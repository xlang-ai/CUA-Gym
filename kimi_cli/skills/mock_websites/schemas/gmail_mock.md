# gmail_mock Schema

**Deploy order**: 18 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8017)
**Base URL**: `http://172.17.46.46:8017/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**State endpoint**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Current user: `{userId, username, email, avatar}` |
| `emails` | array | All emails across all folders (see Email fields below) |
| `labels` | array | User-defined labels: `[{id, name, color}]` |
| `drafts` | array | Draft emails (same shape as email objects) |

### Email Object Fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique email ID (e.g. `"email_1"`) |
| `threadId` | string | Groups emails into threads |
| `from` | object | `{name, email, avatar}` |
| `to` | array | `[{name, email}]` |
| `cc` | array | `[{name, email}]` |
| `bcc` | array | `[{name, email}]` |
| `subject` | string | Email subject line |
| `body` | string | HTML body content |
| `snippet` | string | Plain-text preview (auto-derived from body if omitted) |
| `timestamp` | string | ISO 8601 datetime |
| `read` | boolean | Read status |
| `starred` | boolean | Starred flag |
| `important` | boolean | Important flag |
| `labels` | array | Label IDs (e.g. `["l1", "l2"]`) |
| `category` | string | Tab: `"primary"`, `"social"`, or `"promotions"` |
| `folder` | string | `"inbox"`, `"sent"`, `"drafts"`, `"spam"`, `"trash"` |
| `attachments` | array | `[{id, name, size, type, url}]` |

### Default Labels

| ID | Name | Color |
|----|------|-------|
| `l1` | Work | `#ef4444` (red) |
| `l2` | Personal | `#3b82f6` (blue) |
| `l3` | Travel | `#22c55e` (green) |
| `l4` | Finance | `#eab308` (yellow) |

### Default User

```json
{"userId": "u1", "username": "Demo User", "email": "demo@example.com"}
```

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8017/",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {"userId": "u1", "username": "Demo User", "email": "demo@example.com"},
        "emails": [
          {
            "id": "email_1",
            "threadId": "thread_1",
            "from": {"name": "Alice Smith", "email": "alice@company.com"},
            "to": [{"name": "Demo User", "email": "demo@example.com"}],
            "subject": "Q4 Project Roadmap Update",
            "body": "Please review the attached roadmap.",
            "timestamp": "2026-02-09T11:30:00Z",
            "read": false,
            "starred": true,
            "important": true,
            "labels": ["l1"],
            "category": "primary",
            "folder": "inbox",
            "attachments": []
          }
        ],
        "labels": [
          {"id": "l1", "name": "Work", "color": "#ef4444"},
          {"id": "l2", "name": "Personal", "color": "#3b82f6"}
        ],
        "drafts": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Read an email | `emails[i].read: false → true` |
| Star/unstar email | `emails[i].starred` toggled |
| Mark as important | `emails[i].important` toggled |
| Move to trash | `emails[i].folder: "inbox" → "trash"` |
| Move to spam | `emails[i].folder: "inbox" → "spam"` |
| Archive email | `emails[i].folder: "inbox" → "archive"` |
| Send reply/compose | New email object added to `emails` with `folder: "sent"` |
| Save draft | New email object added to `drafts` array |
| Add/remove label | `emails[i].labels` array modified |
| Delete permanently | Email ID removed from `emails` array (appears in `state_diff.deletedEmails`) |

### state_diff Structure

```json
{
  "newEmails": ["email_id_1"],
  "deletedEmails": ["email_id_2"],
  "modifiedEmails": {
    "email_1": {
      "read": {"from": false, "to": true},
      "folder": {"from": "inbox", "to": "trash"}
    }
  },
  "labels": [...]
}
```
