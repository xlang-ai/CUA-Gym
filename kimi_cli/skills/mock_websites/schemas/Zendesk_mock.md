# Zendesk_mock Schema

**Deploy order**: 60 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8060)
**Base URL**: `http://172.17.46.46:8060/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → stored state JSON
**Upload files**: `POST /upload?sid=<sid>` (multipart) → `{files: [{url, original_name, stored_name, size}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | The currently logged-in agent (same shape as an item in `users[]` with `role: "agent"`) |
| `users` | array | All users (both agents and end-users); see User object below |
| `organizations` | array | Customer organizations; see Organization object below |
| `groups` | array | Support groups/teams; see Group object below |
| `tickets` | array | All support tickets; see Ticket object below |
| `comments` | object | Keyed by ticket ID (number) → array of Comment objects |
| `views` | array | Saved ticket views/filters; see View object below |
| `macros` | array | Automation macros; see Macro object below |
| `tags` | array | Global list of available tag strings |
| `ui` | object | UI state; see UI object below |

---

### User Object

Each element in `users[]` (also the shape of `currentUser`):

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique user ID. Agents: 1-5. End-users: 101-110 |
| `name` | string | Full name |
| `email` | string | Email address |
| `role` | string | `"agent"` or `"end-user"` |
| `phone` | string\|null | Phone number |
| `photo` | string\|null | Avatar URL (null by default) |
| `organization_id` | number\|null | FK to organization. Agents have null |
| `group_id` | number\|null | FK to group (agents only, end-users have null) |
| `time_zone` | string | IANA timezone (e.g. `"America/New_York"`) |
| `locale` | string | Locale code (e.g. `"en-US"`) |
| `signature` | string | Agent email signature |
| `notes` | string | Internal notes about user |
| `suspended` | boolean | Whether user is suspended |
| `verified` | boolean | Whether email is verified |
| `active` | boolean | Whether user is active |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |
| `last_login_at` | string | ISO 8601 timestamp |
| `initials` | string | Two-letter initials for avatar display |

### Organization Object

Each element in `organizations[]`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique org ID (1-5) |
| `name` | string | Organization name |
| `domain_names` | string[] | Associated domain names |
| `details` | string | Description |
| `notes` | string | Internal notes |
| `group_id` | number | Default support group |
| `shared_tickets` | boolean | Whether tickets are shared |
| `shared_comments` | boolean | Whether comments are shared |
| `tags` | string[] | Organization tags |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |

### Group Object

Each element in `groups[]`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique group ID (1-4) |
| `name` | string | Group name (e.g. `"Tier 1 Support"`) |
| `description` | string | Group description |
| `default` | boolean | Whether this is the default group |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |

### Ticket Object

Each element in `tickets[]`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique ticket ID (1001-1015 default) |
| `subject` | string | Ticket subject line |
| `description` | string | Initial ticket description |
| `status` | string | One of: `"new"`, `"open"`, `"pending"`, `"hold"`, `"solved"`, `"closed"` |
| `type` | string\|null | One of: `"question"`, `"incident"`, `"problem"`, `"task"`, or null |
| `priority` | string\|null | One of: `"urgent"`, `"high"`, `"normal"`, `"low"`, or null |
| `requester_id` | number | FK to user who submitted the ticket |
| `submitter_id` | number | FK to user who created the ticket |
| `assignee_id` | number\|null | FK to agent assigned, or null if unassigned |
| `group_id` | number | FK to support group |
| `organization_id` | number\|null | FK to organization |
| `collaborator_ids` | number[] | User IDs of collaborators (CC'd) |
| `follower_ids` | number[] | Agent IDs following this ticket |
| `tags` | string[] | Ticket tags |
| `via` | object | `{channel: string}` — channel is `"email"` or `"web"` |
| `satisfaction_rating` | object\|null | `{score: string, comment: string}` or null. Score: `"good"` or `"bad"` |
| `due_at` | string\|null | ISO 8601 due date or null |
| `is_public` | boolean | Whether ticket is public |
| `custom_fields` | array | Custom field values (empty by default) |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |
| `comment_count` | number | Number of comments on ticket |
| `sla` | object | SLA tracking object (see below) |

#### SLA Sub-Object (`ticket.sla`)

| Field | Type | Description |
|-------|------|-------------|
| `first_reply_at` | string\|null | ISO 8601 timestamp of first agent reply, or null if not yet replied |
| `next_reply_due` | string\|null | ISO 8601 timestamp when next reply is due, or null |
| `breached` | boolean | Whether the SLA has been breached |

### Comment Object

Each element in `comments[ticketId]`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique comment ID (5001+) |
| `ticket_id` | number | FK to parent ticket |
| `author_id` | number | FK to user who wrote the comment |
| `body` | string | Plain text body |
| `html_body` | string | HTML formatted body |
| `public` | boolean | `true` for public replies, `false` for internal notes |
| `type` | string | Always `"Comment"` |
| `attachments` | array | File attachments (empty by default) |
| `created_at` | string | ISO 8601 timestamp |

### View Object

Each element in `views[]`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique view ID (1-8) |
| `title` | string | View name displayed in sidebar |
| `description` | string | View description |
| `active` | boolean | Whether view is active |
| `position` | number | Sort position |
| `type` | string | `"standard"`, `"shared"`, or `"personal"` |
| `conditions` | object | Filter conditions: `{all: Condition[], any: Condition[]}` |

#### View Condition Object

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | Field to match: `"assignee_id"`, `"status"`, `"priority"`, `"updated_at"` |
| `operator` | string | `"is"`, `"is_not"`, `"less_than"`, `"within"` |
| `value` | string\|number\|null | Value to match. `"current_user"` resolves to `currentUser.id` |

### Macro Object

Each element in `macros[]`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique macro ID (1-6) |
| `title` | string | Macro name |
| `description` | string | What the macro does |
| `active` | boolean | Whether macro is active |
| `position` | number | Sort position |
| `actions` | object[] | Array of actions: `{field: string, value: string\|number}` |
| `restriction` | null | Access restriction (null = no restriction) |

#### Macro Action Fields

Supported `field` values in macro actions:
- `"status"` → sets ticket status
- `"priority"` → sets ticket priority
- `"group_id"` → reassigns to group
- `"assignee_id"` → assigns to agent (`"current_user"` resolves to currentUser.id)
- `"comment_mode"` → `"public"` or `"internal"` (used with `comment_value`)
- `"comment_value"` → text body of comment to add

### UI Object (`ui`)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `activeView` | number | `1` | Currently selected view ID |
| `openTicketTabs` | number[] | `[]` | Ticket IDs open as tabs in the header |
| `activeTicketId` | number\|null | `null` | Currently active/focused ticket tab |
| `searchQuery` | string | `""` | Current search query text |
| `selectedTicketIds` | number[] | `[]` | Ticket IDs selected for bulk operations |
| `replyMode` | string | `"public"` | Default reply mode: `"public"` or `"internal"` |
| `sidebarCollapsed` | boolean | `false` | Whether sidebar is collapsed |

---

## Default IDs Reference

### Agents (users with `role: "agent"`)
| ID | Name | Group |
|----|------|-------|
| 1 | Sarah Chen | Tier 1 Support (group 1) |
| 2 | Marcus Johnson | Tier 1 Support (group 1) |
| 3 | Emily Rodriguez | Tier 2 Support (group 2) |
| 4 | David Kim | Billing (group 3) |
| 5 | Priya Patel | Engineering (group 4) |

### End-Users (users with `role: "end-user"`)
| ID | Name | Organization |
|----|------|--------------|
| 101 | Alex Thompson | Acme Corp (org 1) |
| 102 | Jordan Lee | TechStart Inc (org 2) |
| 103 | Maria Garcia | Global Retail (org 3) |
| 104 | Sam Wilson | Acme Corp (org 1) |
| 105 | Nina Patel | TechStart Inc (org 2) |
| 106 | Chris Brown | DesignHub Co (org 4) |
| 107 | Lisa Wang | Global Retail (org 3) |
| 108 | Tom Anderson | (none) |
| 109 | Rachel Kim | EduTech Foundation (org 5) |
| 110 | Mike Davis | Acme Corp (org 1) |

### Organizations
| ID | Name | Domain |
|----|------|--------|
| 1 | Acme Corp | acmecorp.com |
| 2 | TechStart Inc | techstart.io |
| 3 | Global Retail | globalretail.com |
| 4 | DesignHub Co | designhub.co |
| 5 | EduTech Foundation | edutech.org |

### Groups
| ID | Name |
|----|------|
| 1 | Tier 1 Support |
| 2 | Tier 2 Support |
| 3 | Billing |
| 4 | Engineering |

### Default Ticket IDs
1001 through 1015 (15 tickets with varying statuses, types, priorities, and assignments)

### Default Views
| ID | Title | Type |
|----|-------|------|
| 1 | Your unsolved tickets | standard |
| 2 | Unassigned tickets | standard |
| 3 | All unsolved tickets | standard |
| 4 | Recently updated tickets | standard |
| 5 | Recently solved tickets | standard |
| 6 | Pending tickets | standard |
| 7 | New tickets | shared |
| 8 | Urgent & High priority | personal |

### Default Macros
| ID | Title |
|----|-------|
| 1 | Close and redirect to FAQ |
| 2 | Escalate to Tier 2 |
| 3 | Request more information |
| 4 | Assign to me |
| 5 | Downgrade priority -- resolved |
| 6 | Transfer to Billing |

---

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8060/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": 1, "name": "Sarah Chen", "email": "sarah.chen@company.com",
          "role": "agent", "phone": "+1-555-0101", "photo": null,
          "organization_id": null, "group_id": 1,
          "time_zone": "America/New_York", "locale": "en-US",
          "signature": "Best regards,\nSarah Chen", "notes": "",
          "suspended": false, "verified": true, "active": true,
          "created_at": "2023-06-15T10:00:00Z", "updated_at": "2025-01-01T00:00:00Z",
          "last_login_at": "2025-01-01T00:00:00Z", "initials": "SC"
        },
        "users": [
          {"id": 1, "name": "Sarah Chen", "email": "sarah.chen@company.com", "role": "agent", "phone": "+1-555-0101", "photo": null, "organization_id": null, "group_id": 1, "time_zone": "America/New_York", "locale": "en-US", "signature": "", "notes": "", "suspended": false, "verified": true, "active": true, "created_at": "2023-06-15T10:00:00Z", "updated_at": "2025-01-01T00:00:00Z", "last_login_at": "2025-01-01T00:00:00Z", "initials": "SC"},
          {"id": 101, "name": "Alex Thompson", "email": "alex.t@acmecorp.com", "role": "end-user", "phone": "+1-555-1001", "photo": null, "organization_id": 1, "group_id": null, "time_zone": "America/New_York", "locale": "en-US", "signature": "", "notes": "VIP customer", "suspended": false, "verified": true, "active": true, "created_at": "2024-03-10T10:00:00Z", "updated_at": "2025-01-01T00:00:00Z", "last_login_at": "2025-01-01T00:00:00Z", "initials": "AT"}
        ],
        "organizations": [
          {"id": 1, "name": "Acme Corp", "domain_names": ["acmecorp.com"], "details": "Enterprise customer", "notes": "", "group_id": 1, "shared_tickets": false, "shared_comments": false, "tags": ["enterprise"], "created_at": "2023-01-15T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z"}
        ],
        "groups": [
          {"id": 1, "name": "Tier 1 Support", "description": "Front-line support", "default": true, "created_at": "2023-01-01T00:00:00Z", "updated_at": "2024-06-01T00:00:00Z"}
        ],
        "tickets": [
          {
            "id": 2001, "subject": "Cannot access dashboard", "description": "Getting a 403 error when trying to access the main dashboard.",
            "status": "new", "type": "problem", "priority": "high",
            "requester_id": 101, "submitter_id": 101, "assignee_id": null,
            "group_id": 1, "organization_id": 1,
            "collaborator_ids": [], "follower_ids": [],
            "tags": ["access", "dashboard"], "via": {"channel": "email"},
            "satisfaction_rating": null, "due_at": null, "is_public": true, "custom_fields": [],
            "created_at": "2025-01-01T10:00:00Z", "updated_at": "2025-01-01T10:00:00Z",
            "comment_count": 1,
            "sla": {"first_reply_at": null, "next_reply_due": "2025-01-01T14:00:00Z", "breached": false}
          }
        ],
        "comments": {
          "2001": [
            {"id": 9001, "ticket_id": 2001, "author_id": 101, "body": "Getting a 403 error when trying to access the main dashboard.", "html_body": "<p>Getting a 403 error when trying to access the main dashboard.</p>", "public": true, "type": "Comment", "attachments": [], "created_at": "2025-01-01T10:00:00Z"}
          ]
        },
        "views": [
          {"id": 1, "title": "Your unsolved tickets", "description": "Tickets assigned to you that are not yet solved", "active": true, "position": 0, "type": "standard", "conditions": {"all": [{"field": "assignee_id", "operator": "is", "value": "current_user"}, {"field": "status", "operator": "less_than", "value": "solved"}], "any": []}},
          {"id": 2, "title": "Unassigned tickets", "description": "Tickets with no assignee", "active": true, "position": 1, "type": "standard", "conditions": {"all": [{"field": "assignee_id", "operator": "is", "value": null}, {"field": "status", "operator": "less_than", "value": "solved"}], "any": []}}
        ],
        "macros": [
          {"id": 1, "title": "Close and redirect to FAQ", "description": "Closes ticket and sends FAQ link", "active": true, "position": 0, "actions": [{"field": "status", "value": "solved"}, {"field": "comment_mode", "value": "public"}, {"field": "comment_value", "value": "This is covered in our FAQ."}], "restriction": null}
        ],
        "tags": ["access", "dashboard", "login", "billing"],
        "ui": {
          "activeView": 1,
          "openTicketTabs": [],
          "activeTicketId": null,
          "searchQuery": "",
          "selectedTicketIds": [],
          "replyMode": "public",
          "sidebarCollapsed": false
        }
      }
    }
  }
}
```

---

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Assign ticket to agent | `tickets[i].assignee_id` updated |
| Change ticket status | `tickets[i].status` updated |
| Change ticket priority | `tickets[i].priority` updated |
| Change ticket type | `tickets[i].type` updated |
| Change ticket group | `tickets[i].group_id` updated |
| Add tag to ticket | `tickets[i].tags` array grows |
| Remove tag from ticket | `tickets[i].tags` array shrinks |
| Add follower to ticket | `tickets[i].follower_ids` array grows |
| Remove follower from ticket | `tickets[i].follower_ids` array shrinks |
| Submit public reply | `comments[ticketId]` grows by 1 (with `public: true`); `tickets[i].comment_count` incremented; `tickets[i].status` may change |
| Submit internal note | `comments[ticketId]` grows by 1 (with `public: false`); `tickets[i].comment_count` incremented; `tickets[i].status` may change |
| Create new ticket | `tickets` array grows by 1; `comments[newTicketId]` initialized with first comment; `ui.openTicketTabs` grows |
| Delete ticket | `tickets` array shrinks; ticket removed from `ui.openTicketTabs`, `ui.activeTicketId`, `ui.selectedTicketIds` |
| Apply macro to ticket | `tickets[i]` fields updated per macro actions; `comments[ticketId]` may grow if macro includes comment |
| Open ticket tab | `ui.openTicketTabs` grows (if not already present); `ui.activeTicketId` set to ticket ID |
| Close ticket tab | `ui.openTicketTabs` shrinks; `ui.activeTicketId` may change to last remaining tab or null |
| Switch active ticket tab | `ui.activeTicketId` changes |
| Switch view | `ui.activeView` changes to new view ID |
| Search tickets | `ui.searchQuery` updated |
| Select tickets (checkbox) | `ui.selectedTicketIds` grows |
| Deselect tickets | `ui.selectedTicketIds` shrinks or becomes empty |
| Select all tickets | `ui.selectedTicketIds` set to all visible ticket IDs |
| Bulk update tickets | Multiple `tickets[i]` updated with same changes; `ui.selectedTicketIds` cleared |

---

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Dashboard | Home dashboard with summary cards and recent tickets |
| `/views/:viewId` | ViewsPage | Ticket list filtered by view conditions |
| `/tickets/new` | NewTicket | New ticket creation form |
| `/tickets/:ticketId` | TicketDetail | Ticket detail with conversation, properties, and context |
| `/customers` | CustomersPage | List of all end-user customers |
| `/customers/:userId` | CustomerDetail | Customer profile with ticket history |
| `/organizations` | OrganizationsPage | List of all organizations |
| `/organizations/:orgId` | OrganizationDetail | Organization detail with members and tickets |
| `/reporting` | ReportingPage | Charts and agent leaderboard (read-only, does not modify state) |
| `/search` | SearchPage | Search results for tickets (query param `q`) |
| `/go` | Go | State inspection endpoint (JSON output) |

---

## Reducer Actions Reference

| Action Type | Payload | Effect |
|-------------|---------|--------|
| `SET_STATE` | `{...state}` | Replaces entire state |
| `UPDATE_TICKET` | `{id: number, changes: {...}}` | Updates single ticket fields |
| `ADD_TICKET` | `{...ticketObject}` | Adds new ticket to array |
| `DELETE_TICKET` | `ticketId: number` | Removes ticket; cleans up UI state |
| `ADD_COMMENT` | `{ticketId: number, comment: {...}}` | Adds comment; increments `comment_count` |
| `UPDATE_COMMENT` | `{ticketId: number, commentId: number, changes: {...}}` | Updates existing comment fields |
| `APPLY_MACRO` | `{ticketId: number, macro: {...}}` | Applies macro actions to ticket |
| `SET_ACTIVE_VIEW` | `viewId: number` | Sets `ui.activeView` |
| `OPEN_TICKET_TAB` | `ticketId: number` | Adds to `ui.openTicketTabs`; sets `ui.activeTicketId` |
| `CLOSE_TICKET_TAB` | `ticketId: number` | Removes from `ui.openTicketTabs`; adjusts `ui.activeTicketId` |
| `SET_ACTIVE_TICKET` | `ticketId: number` | Sets `ui.activeTicketId` |
| `SET_SEARCH_QUERY` | `query: string` | Sets `ui.searchQuery` |
| `TOGGLE_SELECTED_TICKET` | `ticketId: number` | Toggles ticket in `ui.selectedTicketIds` |
| `SELECT_ALL_TICKETS` | `ticketIds: number[]` | Sets `ui.selectedTicketIds` |
| `DESELECT_ALL_TICKETS` | (none) | Clears `ui.selectedTicketIds` |
| `BULK_UPDATE_TICKETS` | `{ids: number[], changes: {...}}` | Updates multiple tickets; clears selection |
| `SET_UI` | `{...uiChanges}` | Merges into `ui` object |
