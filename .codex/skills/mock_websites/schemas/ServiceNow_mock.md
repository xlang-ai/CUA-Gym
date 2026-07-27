# ServiceNow_mock Schema

**Deploy order**: 44 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8044)
**Base URL**: `http://172.17.46.46:8044/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Merge**: `POST /post?sid=<sid>` with body `{"action":"set","merge":true,"state":{...}}`
**Upload**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Files**: `GET /files/<sid>/<filename>` → file content

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | `User` | Logged-in user object. Default: u1 (System Administrator) |
| `users` | `User[]` | All system users. Default: 8 users (u1-u8) |
| `groups` | `Group[]` | Assignment groups. Default: 5 groups (g1-g5) |
| `incidents` | `Incident[]` | Incident records. Default: 15 incidents (inc1-inc15) |
| `problems` | `Problem[]` | Problem records. Default: 4 problems (prb1-prb4) |
| `changeRequests` | `ChangeRequest[]` | Change request records. Default: 5 changes (chg1-chg5) |
| `catalog` | `Catalog` | Service catalog definition. Default: cat1 |
| `catalogCategories` | `CatalogCategory[]` | Catalog categories. Default: 6 categories (scc1-scc6) |
| `catalogItems` | `CatalogItem[]` | Catalog items available for order. Default: 12 items (sci1-sci12) |
| `requests` | `Request[]` | Service requests (orders). Default: 3 requests (req1-req3) |
| `requestedItems` | `RequestedItem[]` | Individual requested items (RITMs). Default: 4 items (ritm1-ritm4) |
| `kbCategories` | `KBCategory[]` | Knowledge base categories. Default: 10 categories (kbc1-kbc10) |
| `kbArticles` | `KBArticle[]` | Knowledge base articles. Default: 10 articles (kb1-kb10) |
| `cmdbItems` | `CMDBItem[]` | Configuration items (CMDB). Default: 8 items (ci1-ci8) |
| `journal` | `JournalEntry[]` | Activity log entries (comments + work notes). Default: 12 entries (j1-j12) |
| `notifications` | `Notification[]` | User notifications. Default: 8 notifications (notif1-notif8; notif1-notif3 unread) |
| `shoppingCart` | `CartItem[]` | Current shopping cart contents. Default: `[]` (empty) |
| `navigatorFilter` | `string` | Text filter for the left navigator panel. Default: `""` |
| `navigatorExpandedSections` | `string[]` | Expanded navigator sections. Default: `["Incident"]` |
| `activeModule` | `string` | Currently active navigator module. Default: `"dashboard"` |
| `favorites` | `Favorite[]` | User-bookmarked navigation items. Default: `[]` |
| `history` | `HistoryEntry[]` | Navigation history (max 15). Default: `[]` |
| `currentListFilters` | `object` | Currently applied list filters. Default: `{}` |
| `currentSortColumn` | `string|null` | Active sort column. Default: `null` |
| `currentSortDirection` | `string` | Sort direction. Default: `"asc"` |

---

### User fields

`{ sys_id, user_name, first_name, last_name, email, title, department, phone, avatar, role, active, vip }`

- `sys_id`: `string` — Unique identifier (e.g., `"u1"`)
- `role`: `"admin" | "itil" | "user"`
- `avatar`: `string` — 2-letter initials (e.g., `"SA"`, `"BA"`)
- `active`: `boolean`
- `vip`: `boolean`

**Default users**:
| sys_id | user_name | Name | Role | Department |
|--------|-----------|------|------|------------|
| u1 | admin | System Administrator | admin | IT |
| u2 | beth.anglin | Beth Anglin | itil | IT Service Desk |
| u3 | david.loo | David Loo | itil | IT Service Desk |
| u4 | fred.luddy | Fred Luddy | itil | IT Network |
| u5 | luke.wilson | Luke Wilson | itil | IT Database |
| u6 | bud.richman | Bud Richman | user | Sales |
| u7 | don.goodliffe | Don Goodliffe | user | Human Resources |
| u8 | abel.tuter | Abel Tuter | user | Finance |

---

### Group fields

`{ sys_id, name, description, manager, members, type, active }`

- `sys_id`: `string` — Unique identifier (e.g., `"g1"`)
- `manager`: `string` — User sys_id
- `members`: `string[]` — Array of user sys_ids
- `type`: `"itil"`

**Default groups**:
| sys_id | name | Manager | Members |
|--------|------|---------|---------|
| g1 | Service Desk | u2 | u2, u3 |
| g2 | Network | u4 | u4 |
| g3 | Database | u5 | u5 |
| g4 | Hardware | u4 | u4, u5 |
| g5 | Software | u2 | u2, u3, u5 |

---

### Incident fields

`{ sys_id, number, caller_id, category, subcategory, contact_type, short_description, description, state, impact, urgency, priority, assignment_group, assigned_to, opened_at, opened_by, resolved_at, resolved_by, closed_at, closed_by, close_code, close_notes, updated_at, sla_due, cmdb_ci, knowledge }`

- `sys_id`: `string` — Unique identifier (e.g., `"inc1"`)
- `number`: `string` — Display number (e.g., `"INC0010001"`)
- `caller_id`: `string` — User sys_id of the person reporting
- `category`: `"Inquiry / Help" | "Software" | "Hardware" | "Network" | "Database"`
- `subcategory`: `string` — Depends on category (e.g., `"VPN"`, `"Email"`, `"Printer"`, `"Oracle"`)
- `contact_type`: `"Phone" | "Email" | "Self-service" | "Walk-in"`
- `state`: `number` — `1` (New), `2` (In Progress), `3` (On Hold), `6` (Resolved), `7` (Closed), `8` (Cancelled)
- `impact`: `number` — `1` (High), `2` (Medium), `3` (Low)
- `urgency`: `number` — `1` (High), `2` (Medium), `3` (Low)
- `priority`: `number` — Auto-calculated from impact x urgency matrix: `1` (Critical), `2` (High), `3` (Moderate), `4` (Low), `5` (Planning)
- `assignment_group`: `string` — Group sys_id
- `assigned_to`: `string|null` — User sys_id
- `opened_at`, `resolved_at`, `closed_at`, `updated_at`, `sla_due`: `string|null` — ISO 8601 timestamps
- `opened_by`, `resolved_by`, `closed_by`: `string|null` — User sys_ids
- `close_code`: `"" | "Solved (Permanently)" | "Solved (Workaround)" | "Not Solved" | "Closed/Resolved by Caller"`
- `cmdb_ci`: `string|null` — Configuration item sys_id
- `knowledge`: `boolean`

**Priority matrix** (impact x urgency):
| | Urgency 1 | Urgency 2 | Urgency 3 |
|---|---|---|---|
| Impact 1 | 1 - Critical | 2 - High | 3 - Moderate |
| Impact 2 | 2 - High | 3 - Moderate | 4 - Low |
| Impact 3 | 3 - Moderate | 4 - Low | 5 - Planning |

**Default incidents**: 15 records (inc1-inc15) with states: 4 New (1), 4 In Progress (2), 1 On Hold (3), 3 Resolved (6), 3 Closed (7), 1 Cancelled (8)

---

### Problem fields

`{ sys_id, number, short_description, description, state, priority, impact, urgency, assignment_group, assigned_to, opened_at, opened_by, resolved_at, closed_at, cause_notes, fix_notes, known_error, related_incidents, updated_at, cmdb_ci }`

- `sys_id`: `string` — (e.g., `"prb1"`)
- `number`: `string` — (e.g., `"PRB0040001"`)
- `state`: `number` — `1` (New), `2` (Assess), `3` (Root Cause Analysis), `4` (Fix in Progress), `5` (Resolved), `6` (Closed)
- `known_error`: `boolean`
- `related_incidents`: `string[]` — Array of incident sys_ids
- `cause_notes`: `string` — Root cause analysis notes
- `fix_notes`: `string` — Fix/resolution notes

**Default problems**: 4 records (prb1-prb4) with states: New (1), Assess (2), Root Cause Analysis (3), Resolved (5)

---

### ChangeRequest fields

`{ sys_id, number, type, short_description, description, state, priority, impact, risk, category, assignment_group, assigned_to, requested_by, opened_at, opened_by, start_date, end_date, close_code, close_notes, updated_at, cmdb_ci, approval, conflict_status }`

- `sys_id`: `string` — (e.g., `"chg1"`)
- `number`: `string` — (e.g., `"CHG0030001"`)
- `type`: `"Normal" | "Standard" | "Emergency"`
- `state`: `number` — `-5` (New), `-4` (Assess), `-3` (Authorize), `-2` (Scheduled), `-1` (Implement), `0` (Review), `3` (Closed), `4` (Cancelled)
- `risk`: `"High" | "Moderate" | "Low"`
- `approval`: `"Not Yet Requested" | "Requested" | "Approved"`
- `conflict_status`: `"Not Run" | "No Conflicts"`
- `close_code`: `"" | "Successful" | "Unsuccessful" | "Cancelled"`
- `start_date`, `end_date`: `string` — ISO 8601 timestamps for planned schedule

**Default change requests**: 5 records (chg1-chg5) with types: 3 Normal, 1 Standard, 1 Emergency

---

### Catalog fields

`{ sys_id, title, description, active }`

Single catalog record. Default: `{ sys_id: "cat1", title: "Service Catalog" }`

---

### CatalogCategory fields

`{ sys_id, title, description, icon, parent, catalog, active, order }`

- `icon`: `string` — Emoji icon
- `parent`: `string|null` — Parent category sys_id (null for top-level)
- `catalog`: `string` — Catalog sys_id

**Default categories**: 6 top-level categories (scc1-scc6): Hardware, Software, Services, Office, Can We Help You?, Peripherals

---

### CatalogItem fields

`{ sys_id, name, short_description, description, category, price, delivery_time, active, order, popular, picture }`

- `category`: `string` — CatalogCategory sys_id
- `price`: `string` — Display price (e.g., `"$1,200"`, `"$15/mo"`, `"Free"`)
- `delivery_time`: `string` — (e.g., `"5 business days"`)
- `popular`: `boolean` — Shown in "Top Requests" sidebar
- `picture`: `string` — Emoji icon
- `description`: `string` — HTML content

**Default items**: 12 items (sci1-sci12) across 5 categories

---

### Request fields

`{ sys_id, number, requested_for, opened_at, opened_by, state, stage, items, updated_at }`

- `number`: `string` — (e.g., `"REQ0010001"`)
- `requested_for`: `string` — User sys_id
- `state`: `"Open" | "Closed Complete"`
- `stage`: `"Requested" | "Delivery" | "Completed"`
- `items`: `string[]` — Array of RequestedItem sys_ids

**Default requests**: 3 records (req1-req3)

---

### RequestedItem fields

`{ sys_id, number, request, cat_item, state, assigned_to, assignment_group, quantity, opened_at, updated_at, short_description }`

- `number`: `string` — (e.g., `"RITM0010001"`)
- `request`: `string` — Request sys_id
- `cat_item`: `string` — CatalogItem sys_id
- `state`: `"Open" | "Work in Progress" | "Closed Complete"`
- `quantity`: `number`

**Default requested items**: 4 records (ritm1-ritm4)

---

### KBCategory fields

`{ sys_id, label, parent_id, description, active, article_count }`

- `parent_id`: `string|null` — Parent category sys_id (null for top-level)

**Default KB categories**: 10 categories (kbc1-kbc10). Top-level: Applications, Email, Hardware, Network, Operating Systems, Policies. Child categories: Outlook (under Email), Gmail (under Email), Windows (under OS), Mac OS X (under OS)

---

### KBArticle fields

`{ sys_id, number, short_description, text, category, author, published, workflow_state, rating, view_count, helpful_count, updated_at }`

- `number`: `string` — (e.g., `"KB0010001"`)
- `text`: `string` — HTML content of the article
- `category`: `string` — KBCategory sys_id
- `author`: `string` — User sys_id
- `workflow_state`: `"Published"`
- `rating`: `number` — Float (e.g., `4.5`)
- `view_count`: `number`
- `helpful_count`: `number`

**Default articles**: 10 articles (kb1-kb10) covering VPN, passwords, email, printers, wireless, software, policies

---

### CMDBItem fields

`{ sys_id, name, sys_class_name, status, environment, category, assigned_to, department, location, ip_address, serial_number, manufacturer, model }`

- `sys_class_name`: `"cmdb_ci_netgear" | "cmdb_ci_server" | "cmdb_ci_database" | "cmdb_ci_app_server"`
- `status`: `"Installed" | "In Maintenance"`
- `environment`: `"Production" | "Development"`
- `category`: `"Network" | "Hardware" | "Software"`

**Default CMDB items**: 8 items (ci1-ci8): VPN gateway, mail server, production DB, web server, access point, dev DB, file server, backup server

---

### JournalEntry fields

`{ sys_id, element_id, element, value, sys_created_by, sys_created_on, name }`

- `element_id`: `string` — sys_id of the parent record (incident, problem, or change)
- `element`: `"comments" | "work_notes"` — Type of journal entry
- `value`: `string` — The text content
- `sys_created_by`: `string` — User sys_id who wrote it
- `sys_created_on`: `string` — ISO 8601 timestamp
- `name`: `"incident" | "problem" | "change_request"` — Parent table name

**Default entries**: 12 entries (j1-j12) across incidents inc1, inc3, inc4, inc6, inc8

---

### Notification fields

`{ sys_id, type, target_table, target_id, target_number, message, created_at, read, actor }`

- `type`: `"assignment" | "comment" | "approval" | "state_change" | "sla_warning"`
- `target_table`: `"incident" | "change_request" | "sc_req_item" | "sc_request"`
- `target_id`: `string` — sys_id of the target record
- `target_number`: `string` — Display number of the target
- `read`: `boolean`
- `actor`: `string` — User sys_id who triggered the notification

**Default notifications**: 8 records (notif1-notif8). 3 unread (notif1-notif3), 5 read (notif4-notif8)

---

### CartItem fields (shoppingCart array)

`{ item: CatalogItem, quantity: number }`

- `item`: Full CatalogItem object
- `quantity`: `number` (1-10)

---

### Favorite fields

`{ label: string, route: string }`

### HistoryEntry fields

`{ label: string, route: string, timestamp: string }`

---

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Dashboard | Welcome page with stats + assigned work |
| `/go` | StateInspector | State inspection endpoint (JSON) |
| `/incident/list` | IncidentList | Incident list with filters and sorting |
| `/incident/create` | IncidentForm | Create new incident |
| `/incident/:id` | IncidentForm | View/edit existing incident |
| `/problem/list` | ProblemList | Problem list with filters |
| `/problem/create` | ProblemForm | Create new problem |
| `/problem/:id` | ProblemForm | View/edit existing problem |
| `/change/list` | ChangeList | Change request list with filters |
| `/change/create` | ChangeForm | Create new change request (type selector) |
| `/change/:id` | ChangeForm | View/edit existing change request |
| `/catalog` | ServiceCatalog | Browse catalog categories + top requests |
| `/catalog/category/:id` | CatalogCategory | Items in a specific category |
| `/catalog/item/:id` | CatalogItemDetail | Item detail + add to cart |
| `/catalog/cart` | ShoppingCart | View cart + submit order |
| `/knowledge` | KnowledgeBase | Browse/search KB articles by category |
| `/knowledge/article/:id` | KnowledgeArticle | Read KB article + helpfulness vote |
| `/cmdb/list` | CMDBList | Configuration items list |
| `/cmdb/:id` | CMDBDetail | CI detail + related incidents |
| `/reports` | Reports | Charts: incidents by priority + state |
| `/search` | GlobalSearch | Cross-table text search (q= param) |

**Incident list filters** (via `?filter=` query param): `assigned_to_me`, `open`, `open_unassigned`, `resolved`, `closed`
**Problem list filters**: `open`
**Change list filters**: `open`, `closed`

---

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8044/",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": { "sys_id": "u1", "user_name": "admin", "first_name": "System", "last_name": "Administrator", "email": "admin@example.com", "title": "System Administrator", "department": "IT", "phone": "555-0100", "avatar": "SA", "role": "admin", "active": true, "vip": false },
        "users": [
          { "sys_id": "u1", "user_name": "admin", "first_name": "System", "last_name": "Administrator", "email": "admin@example.com", "title": "System Administrator", "department": "IT", "phone": "555-0100", "avatar": "SA", "role": "admin", "active": true, "vip": false },
          { "sys_id": "u2", "user_name": "beth.anglin", "first_name": "Beth", "last_name": "Anglin", "email": "beth.anglin@example.com", "title": "Service Desk Agent", "department": "IT Service Desk", "phone": "555-0201", "avatar": "BA", "role": "itil", "active": true, "vip": false }
        ],
        "groups": [
          { "sys_id": "g1", "name": "Service Desk", "description": "Front-line support", "manager": "u2", "members": ["u2"], "type": "itil", "active": true }
        ],
        "incidents": [
          { "sys_id": "inc1", "number": "INC0010001", "caller_id": "u1", "category": "Network", "subcategory": "VPN", "contact_type": "Phone", "short_description": "Cannot connect to VPN", "description": "VPN shows error 619.", "state": 1, "impact": 2, "urgency": 2, "priority": 3, "assignment_group": "g1", "assigned_to": null, "opened_at": "2026-03-01T09:00:00.000Z", "opened_by": "u2", "resolved_at": null, "resolved_by": null, "closed_at": null, "closed_by": null, "close_code": "", "close_notes": "", "updated_at": "2026-03-01T09:00:00.000Z", "sla_due": "2026-03-03T09:00:00.000Z", "cmdb_ci": null, "knowledge": false }
        ],
        "problems": [],
        "changeRequests": [],
        "catalog": { "sys_id": "cat1", "title": "Service Catalog", "description": "Browse and order IT services and equipment", "active": true },
        "catalogCategories": [
          { "sys_id": "scc1", "title": "Hardware", "description": "Hardware requests", "icon": "\uD83D\uDDA5\uFE0F", "parent": null, "catalog": "cat1", "active": true, "order": 1 }
        ],
        "catalogItems": [
          { "sys_id": "sci1", "name": "Standard Laptop", "short_description": "Dell Latitude 5540", "description": "<p>Standard business laptop.</p>", "category": "scc1", "price": "$1,200", "delivery_time": "5 business days", "active": true, "order": 1, "popular": true, "picture": "\uD83D\uDCBB" }
        ],
        "requests": [],
        "requestedItems": [],
        "kbCategories": [],
        "kbArticles": [],
        "cmdbItems": [],
        "journal": [],
        "notifications": [],
        "shoppingCart": [],
        "navigatorFilter": "",
        "navigatorExpandedSections": ["Incident"],
        "activeModule": "dashboard",
        "favorites": [],
        "history": [],
        "currentListFilters": {},
        "currentSortColumn": null,
        "currentSortDirection": "asc"
      }
    }
  }
}
```

---

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Create new incident | `incidents` (new entry appended with auto-generated sys_id + INC number) |
| Update incident fields (state, priority, assignment, description, etc.) | `incidents[*].*`, `incidents[*].updated_at` |
| Resolve incident | `incidents[*].state` → `6`, `incidents[*].resolved_at`, `incidents[*].resolved_by` |
| Delete incident | `incidents` (entry removed) |
| Add comment to incident | `journal` (new entry with `element: "comments"`, `name: "incident"`) |
| Add work note to incident | `journal` (new entry with `element: "work_notes"`, `name: "incident"`) |
| Create new problem | `problems` (new entry appended with PRB number) |
| Update problem fields | `problems[*].*`, `problems[*].updated_at` |
| Create new change request | `changeRequests` (new entry appended with CHG number) |
| Update change request fields | `changeRequests[*].*`, `changeRequests[*].updated_at` |
| Add work note to problem/change | `journal` (new entry with `name: "problem"` or `"change_request"`) |
| Add item to shopping cart | `shoppingCart` (new CartItem appended, or existing quantity incremented) |
| Remove item from cart | `shoppingCart` (entry removed) |
| Empty cart | `shoppingCart` → `[]` |
| Submit order (from cart) | `requests` (new Request), `requestedItems` (new RITMs), `notifications` (new notif), `shoppingCart` → `[]` |
| Mark notification as read | `notifications[*].read` → `true` |
| Mark all notifications as read | `notifications[*].read` → `true` (all entries) |
| Toggle navigator section expand/collapse | `navigatorExpandedSections` (section added/removed) |
| Filter navigator | `navigatorFilter` → new filter text |
| Navigate to module | `history` (new entry prepended, max 15), `activeModule` updated |
| Add favorite | `favorites` (new entry appended) |
| Remove favorite | `favorites` (entry removed) |
| Change incident impact/urgency | `incidents[*].impact`, `incidents[*].urgency`, `incidents[*].priority` (auto-calculated) |
