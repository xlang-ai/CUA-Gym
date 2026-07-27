# hubspot_mock Schema

**Deploy order**: 22 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8022)
**Base URL**: `http://172.17.46.46:8022/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Set Current Only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Merge**: `POST /post?sid=<sid>` with body `{"action":"set","merge":true,"state":{...}}`
**Upload Files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Serve Files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## State Management

Uses React Context (`StoreContext`) with `useReducer`. State is persisted to localStorage under `hubspot_mock_db` (or `hubspot_mock_db_<sid>` for session-specific state). Initial state snapshot stored under `hubspot_mock_db_initial` (or `hubspot_mock_db_initial_<sid>`). State is also synced to the server-side file store on every change via `POST /post` with `set_current` action.

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Dashboard | Overview with stat cards, deal pipeline chart, activity trends chart, recent activity feed |
| `/contacts` | Contacts | Contacts table with search, filters, sort, pagination, CRUD |
| `/companies` | Companies | Companies table with search, sort, pagination, CRUD |
| `/deals` | Deals | Deal pipeline board (drag-and-drop) or list view, CRUD |
| `/tickets` | Tickets | Service tickets table with search, status filter, sort, pagination, CRUD |
| `/tasks` | Tasks | Tasks table with status/type filters, sort, completion toggle, CRUD |
| `/templates` | Templates | Email template cards with create, edit, duplicate, delete |
| `/meetings` | Meetings | Meeting list with create, edit, delete |
| `/forms` | Forms | Form cards with create, status toggle (active/inactive) |
| `/go` | Go | State inspector showing `{initial_state, current_state, state_diff}` |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `contacts` | Contact[] | CRM contacts; default 12 records (c1..c12) |
| `companies` | Company[] | CRM companies; default 6 records (comp1..comp6) |
| `deals` | Deal[] | Sales deals/opportunities; default 10 records (d1..d10) |
| `tickets` | Ticket[] | Service/support tickets; default 8 records (t1..t8) |
| `tasks` | Task[] | Action items (calls, emails, to-dos); default 8 records (task1..task8) |
| `notes` | Note[] | Notes associated with contacts/deals/companies/tickets; default 6 records (note1..note6) |
| `templates` | Template[] | Email templates with merge fields; default 4 records (tmp1..tmp4) |
| `meetings` | Meeting[] | Scheduled meetings; default 4 records (m1..m4) |
| `forms` | Form[] | Lead capture forms; default 4 records (f1..f4) |
| `dealStages` | object | Deal stage configuration keyed by stage ID; 7 stages |
| `ticketStatuses` | object | Ticket status configuration keyed by status ID; 5 statuses |
| `appState` | object | Application UI state and current user info |

### Contact

| Field | Type | Description | Default Example |
|-------|------|-------------|-----------------|
| `id` | string | Unique ID | `"c1"` |
| `firstName` | string | First name | `"Alice"` |
| `lastName` | string | Last name | `"Freeman"` |
| `email` | string | Email address | `"alice@techcorp.com"` |
| `phone` | string | Phone number | `"+1 (555) 010-1234"` |
| `jobTitle` | string | Job title | `"CTO"` |
| `companyId` | string | FK to company | `"comp1"` |
| `lifecycleStage` | string | One of: `lead`, `mql`, `sql`, `opportunity`, `customer`, `evangelist` | `"customer"` |
| `leadStatus` | string | One of: `new`, `open`, `in_progress`, `open_deal`, `unqualified`, `attempted`, `connected` | `"open_deal"` |
| `owner` | string | Assigned owner | `"Admin User"` |
| `city` | string | City | `"San Francisco"` |
| `state` | string | State/region | `"CA"` |
| `country` | string | Country | `"United States"` |
| `createDate` | string (ISO 8601) | Creation timestamp | `"2024-01-15T10:30:00Z"` |
| `lastActivityDate` | string (ISO 8601) | Last activity timestamp | `"2024-05-10T14:00:00Z"` |
| `timeline` | array | Activity timeline (currently empty) | `[]` |

### Company

| Field | Type | Description | Default Example |
|-------|------|-------------|-----------------|
| `id` | string | Unique ID | `"comp1"` |
| `name` | string | Company name | `"TechCorp"` |
| `domain` | string | Website domain | `"techcorp.com"` |
| `industry` | string | Industry (Technology, Marketing, Manufacturing, Finance, Healthcare, Education, Environmental Services, Design, Venture Capital, Other) | `"Technology"` |
| `phone` | string | Phone number | `"+1 (555) 100-0001"` |
| `city` | string | City | `"San Francisco"` |
| `state` | string | State/region | `"CA"` |
| `country` | string | Country | `"United States"` |
| `numberOfEmployees` | number | Employee count | `250` |
| `annualRevenue` | number | Annual revenue in dollars | `15000000` |
| `lifecycleStage` | string | Same enum as contact lifecycleStage | `"customer"` |
| `owner` | string | Assigned owner | `"Admin User"` |
| `description` | string | Company description | `"Enterprise SaaS platform for developer tools"` |
| `createDate` | string (ISO 8601) | Creation timestamp | `"2024-01-10T09:00:00Z"` |

### Deal

| Field | Type | Description | Default Example |
|-------|------|-------------|-----------------|
| `id` | string | Unique ID | `"d1"` |
| `name` | string | Deal name | `"TechCorp Enterprise License"` |
| `stage` | string | Pipeline stage key (see dealStages) | `"contract_sent"` |
| `amount` | number | Deal amount in dollars | `50000` |
| `closeDate` | string | Expected close date (YYYY-MM-DD) | `"2024-06-15"` |
| `dealType` | string | `"new_business"` or `"existing_business"` | `"new_business"` |
| `priority` | string | `"low"`, `"medium"`, or `"high"` | `"high"` |
| `owner` | string | Assigned owner | `"Admin User"` |
| `companyId` | string | FK to company | `"comp1"` |
| `contactIds` | string[] | FK array to contacts | `["c1", "c5"]` |
| `probability` | number | Win probability (0-100) | `90` |
| `description` | string | Deal description | `"Annual enterprise license for 250 seats"` |
| `createDate` | string (ISO 8601) | Creation timestamp | `"2024-03-01T10:00:00Z"` |
| `lastActivityDate` | string (ISO 8601) | Last activity timestamp | `"2024-05-10T14:00:00Z"` |
| `closedLostReason` | string (optional) | Reason for lost deals | `"Budget constraints"` (only on closed_lost deals) |

### Ticket

| Field | Type | Description | Default Example |
|-------|------|-------------|-----------------|
| `id` | string | Unique ID | `"t1"` |
| `subject` | string | Ticket subject | `"Cannot access admin dashboard"` |
| `description` | string | Issue description | `"User reports 403 error..."` |
| `status` | string | One of: `new`, `waiting_on_contact`, `waiting_on_us`, `in_progress`, `closed` | `"in_progress"` |
| `pipeline` | string | Pipeline name | `"support"` |
| `priority` | string | `"low"`, `"medium"`, or `"high"` | `"high"` |
| `category` | string | One of: `general_inquiry`, `bug_report`, `feature_request`, `billing`, `technical_support` | `"bug_report"` |
| `source` | string | One of: `email`, `phone`, `chat`, `form`, `manual` | `"email"` |
| `owner` | string \| null | Assigned owner | `"Admin User"` |
| `contactId` | string \| null | FK to contact | `"c1"` |
| `companyId` | string \| null | FK to company | `"comp1"` |
| `createDate` | string (ISO 8601) | Creation timestamp | `"2024-05-01T09:30:00Z"` |
| `closeDate` | string \| null | Close timestamp (null if open) | `null` |
| `lastActivityDate` | string (ISO 8601) | Last activity timestamp | `"2024-05-10T11:00:00Z"` |

### Task

| Field | Type | Description | Default Example |
|-------|------|-------------|-----------------|
| `id` | string | Unique ID | `"task1"` |
| `title` | string | Task title | `"Follow up with Alice on enterprise proposal"` |
| `type` | string | One of: `call`, `email`, `to_do` | `"call"` |
| `status` | string | One of: `not_started`, `in_progress`, `completed` | `"not_started"` |
| `priority` | string | `"low"`, `"medium"`, or `"high"` | `"high"` |
| `dueDate` | string (ISO 8601) \| null | Due date/time | `"2024-05-15T09:00:00Z"` |
| `notes` | string \| null | Task notes | `"Discuss pricing and contract terms"` |
| `owner` | string | Assigned owner | `"Admin User"` |
| `contactId` | string \| null | FK to contact | `"c1"` |
| `companyId` | string \| null | FK to company | `"comp1"` |
| `dealId` | string \| null | FK to deal | `"d1"` |
| `createDate` | string (ISO 8601) | Creation timestamp | `"2024-05-10T08:00:00Z"` |
| `completedDate` | string (ISO 8601) \| null | Completion timestamp | `null` |

### Note

| Field | Type | Description | Default Example |
|-------|------|-------------|-----------------|
| `id` | string | Unique ID | `"note1"` |
| `body` | string | Note content | `"Had a great meeting with Alice..."` |
| `associatedType` | string | One of: `contact`, `deal`, `company`, `ticket` | `"contact"` |
| `associatedId` | string | FK to the associated record | `"c1"` |
| `createdBy` | string | Author | `"Admin User"` |
| `createDate` | string (ISO 8601) | Creation timestamp | `"2024-05-10T15:00:00Z"` |

### Template (Email Template)

| Field | Type | Description | Default Example |
|-------|------|-------------|-----------------|
| `id` | string | Unique ID | `"tmp1"` |
| `name` | string | Template name | `"Introductory Email"` |
| `subject` | string | Email subject (supports merge fields like `{{first_name}}`) | `"Introduction from {{company_name}}"` |
| `body` | string | Email body (supports merge fields) | `"Hi {{first_name}},\n\nI wanted to reach out..."` |
| `folder` | string | Folder/category name | `"Sales"` or `"Onboarding"` |
| `createdBy` | string | Author | `"Admin User"` |
| `createDate` | string (ISO 8601) | Creation timestamp | `"2024-02-01T10:00:00Z"` |
| `timesUsed` | number | Usage count | `47` |

### Meeting

| Field | Type | Description | Default Example |
|-------|------|-------------|-----------------|
| `id` | string | Unique ID | `"m1"` |
| `title` | string | Meeting title | `"Demo with Alice & Emma"` |
| `date` | string (ISO 8601) | Meeting date/time | `"2024-05-10T14:00:00Z"` |
| `duration` | number | Duration in minutes (15, 30, 45, 60, 90) | `45` |
| `contactId` | string \| null | FK to contact | `"c1"` |
| `companyId` | string \| null | FK to company | `"comp1"` |
| `status` | string | One of: `scheduled`, `completed`, `cancelled`, `no_show` | `"completed"` |
| `notes` | string | Meeting notes | `"Went great -- showed enterprise features"` |
| `location` | string | Meeting location (Zoom, Google Meet, In-person, Phone, Microsoft Teams) | `"Zoom"` |
| `owner` | string | Organizer | `"Admin User"` |
| `createDate` | string (ISO 8601) | Creation timestamp | `"2024-05-08T09:00:00Z"` |

### Form

| Field | Type | Description | Default Example |
|-------|------|-------------|-----------------|
| `id` | string | Unique ID | `"f1"` |
| `name` | string | Form name | `"Contact Us"` |
| `status` | string | `"active"` or `"inactive"` | `"active"` |
| `submissions` | number | Total submission count | `156` |
| `fields` | string[] | Field names included in form | `["email", "first_name", "last_name", "company", "message"]` |
| `createDate` | string (ISO 8601) | Creation timestamp | `"2024-01-20T10:00:00Z"` |
| `lastSubmission` | string (ISO 8601) \| null | Last submission timestamp | `"2024-05-09T16:30:00Z"` |

### dealStages (configuration object)

Keyed by stage ID. Each value:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stage key |
| `label` | string | Display label |
| `probability` | number | Default win probability (0-100) |
| `color` | string | Background color hex |
| `order` | number | Display order (1-7) |

**Default stages** (in order):

| ID | Label | Probability | Order |
|----|-------|-------------|-------|
| `appointment_scheduled` | Appointment Scheduled | 20 | 1 |
| `qualified_to_buy` | Qualified to Buy | 40 | 2 |
| `presentation_scheduled` | Presentation Scheduled | 60 | 3 |
| `decision_maker_bought_in` | Decision Maker Bought-In | 80 | 4 |
| `contract_sent` | Contract Sent | 90 | 5 |
| `closed_won` | Closed Won | 100 | 6 |
| `closed_lost` | Closed Lost | 0 | 7 |

### ticketStatuses (configuration object)

Keyed by status ID. Each value:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Status key |
| `label` | string | Display label |
| `color` | string | Background color hex |
| `order` | number | Display order (1-5) |

**Default statuses** (in order): `new` (1), `waiting_on_contact` (2), `waiting_on_us` (3), `in_progress` (4), `closed` (5)

### appState

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `sidebarOpen` | boolean | Sidebar visibility | `true` |
| `currentUser` | object | `{name, email, avatar}` | `{name: "Admin User", email: "admin@example.com", avatar: null}` |

## Default Data Relationships

Contacts are linked to companies via `companyId`:
- comp1 (TechCorp): c1, c5
- comp2 (Marketing Gurus): c2, c11
- comp3 (Startups.io): c3, c9
- comp4 (Enterprise Global): c4, c8
- comp5 (GreenLeaf Solutions): c6, c10
- comp6 (Design Studio Pro): c7, c12

Deals reference companies via `companyId` and contacts via `contactIds[]`.
Tickets reference contacts via `contactId` and companies via `companyId`.
Tasks reference contacts via `contactId`, companies via `companyId`, and deals via `dealId`.
Notes reference any record type via `associatedType` + `associatedId`.
Meetings reference contacts via `contactId` and companies via `companyId`.

## Reducer Actions

| Action Type | Payload | Effect |
|-------------|---------|--------|
| `LOAD_STATE` | full state object | Replaces entire state |
| `SET_STATE` | full state object | Replaces entire state |
| `ADD_CONTACT` | Contact object | Appends to `contacts` array |
| `UPDATE_CONTACT` | Partial Contact with `id` | Merges into matching contact |
| `DELETE_CONTACT` | contact id (string) | Removes from `contacts` array |
| `ADD_COMPANY` | Company object | Appends to `companies` array |
| `UPDATE_COMPANY` | Partial Company with `id` | Merges into matching company |
| `DELETE_COMPANY` | company id (string) | Removes from `companies` array |
| `ADD_DEAL` | Deal object | Appends to `deals` array |
| `UPDATE_DEAL` | Partial Deal with `id` | Merges into matching deal |
| `UPDATE_DEAL_STAGE` | `{dealId, stage}` | Updates deal's `stage` field |
| `DELETE_DEAL` | deal id (string) | Removes from `deals` array |
| `ADD_TICKET` | Ticket object | Appends to `tickets` array |
| `UPDATE_TICKET` | Partial Ticket with `id` | Merges into matching ticket |
| `DELETE_TICKET` | ticket id (string) | Removes from `tickets` array |
| `ADD_TASK` | Task object | Appends to `tasks` array |
| `UPDATE_TASK` | Partial Task with `id` | Merges into matching task |
| `DELETE_TASK` | task id (string) | Removes from `tasks` array |
| `COMPLETE_TASK` | task id (string) | Toggles `status` between `completed` and `not_started`, sets/clears `completedDate` |
| `ADD_NOTE` | Note object | Appends to `notes` array |
| `UPDATE_NOTE` | Partial Note with `id` | Merges into matching note |
| `DELETE_NOTE` | note id (string) | Removes from `notes` array |
| `ADD_TEMPLATE` | Template object | Appends to `templates` array |
| `UPDATE_TEMPLATE` | Partial Template with `id` | Merges into matching template |
| `DELETE_TEMPLATE` | template id (string) | Removes from `templates` array |
| `ADD_MEETING` | Meeting object | Appends to `meetings` array |
| `UPDATE_MEETING` | Partial Meeting with `id` | Merges into matching meeting |
| `DELETE_MEETING` | meeting id (string) | Removes from `meetings` array |
| `ADD_FORM` | Form object | Appends to `forms` array |
| `UPDATE_FORM` | Partial Form with `id` | Merges into matching form |
| `RESET_DB` | sid or null | Reinitializes state from defaults |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8022/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "contacts": [
          {
            "id": "c1",
            "firstName": "Alice",
            "lastName": "Freeman",
            "email": "alice@techcorp.com",
            "phone": "+1 (555) 010-1234",
            "jobTitle": "CTO",
            "companyId": "comp1",
            "lifecycleStage": "customer",
            "leadStatus": "open_deal",
            "owner": "Admin User",
            "city": "San Francisco",
            "state": "CA",
            "country": "United States",
            "createDate": "2024-01-15T10:30:00Z",
            "lastActivityDate": "2024-05-10T14:00:00Z",
            "timeline": []
          }
        ],
        "companies": [
          {
            "id": "comp1",
            "name": "TechCorp",
            "domain": "techcorp.com",
            "industry": "Technology",
            "phone": "+1 (555) 100-0001",
            "city": "San Francisco",
            "state": "CA",
            "country": "United States",
            "numberOfEmployees": 250,
            "annualRevenue": 15000000,
            "lifecycleStage": "customer",
            "owner": "Admin User",
            "description": "Enterprise SaaS platform for developer tools",
            "createDate": "2024-01-10T09:00:00Z"
          }
        ],
        "deals": [
          {
            "id": "d1",
            "name": "TechCorp Enterprise License",
            "stage": "contract_sent",
            "amount": 50000,
            "closeDate": "2024-06-15",
            "dealType": "new_business",
            "priority": "high",
            "owner": "Admin User",
            "companyId": "comp1",
            "contactIds": ["c1"],
            "probability": 90,
            "description": "Annual enterprise license for 250 seats",
            "createDate": "2024-03-01T10:00:00Z",
            "lastActivityDate": "2024-05-10T14:00:00Z"
          }
        ],
        "tickets": [],
        "tasks": [],
        "notes": [],
        "templates": [],
        "meetings": [],
        "forms": [],
        "dealStages": {
          "appointment_scheduled": { "id": "appointment_scheduled", "label": "Appointment Scheduled", "probability": 20, "color": "#E5F4FF", "order": 1 },
          "qualified_to_buy": { "id": "qualified_to_buy", "label": "Qualified to Buy", "probability": 40, "color": "#FFF0E6", "order": 2 },
          "presentation_scheduled": { "id": "presentation_scheduled", "label": "Presentation Scheduled", "probability": 60, "color": "#FFF8E6", "order": 3 },
          "decision_maker_bought_in": { "id": "decision_maker_bought_in", "label": "Decision Maker Bought-In", "probability": 80, "color": "#E8F5E9", "order": 4 },
          "contract_sent": { "id": "contract_sent", "label": "Contract Sent", "probability": 90, "color": "#E6FFFA", "order": 5 },
          "closed_won": { "id": "closed_won", "label": "Closed Won", "probability": 100, "color": "#E6FFEC", "order": 6 },
          "closed_lost": { "id": "closed_lost", "label": "Closed Lost", "probability": 0, "color": "#FFE6E6", "order": 7 }
        },
        "ticketStatuses": {
          "new": { "id": "new", "label": "New", "color": "#E5F4FF", "order": 1 },
          "waiting_on_contact": { "id": "waiting_on_contact", "label": "Waiting on Contact", "color": "#FFF8E6", "order": 2 },
          "waiting_on_us": { "id": "waiting_on_us", "label": "Waiting on Us", "color": "#FFF0E6", "order": 3 },
          "in_progress": { "id": "in_progress", "label": "In Progress", "color": "#E6FFFA", "order": 4 },
          "closed": { "id": "closed", "label": "Closed", "color": "#E6FFEC", "order": 5 }
        },
        "appState": {
          "sidebarOpen": true,
          "currentUser": { "name": "Admin User", "email": "admin@example.com", "avatar": null }
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Create new contact | `contacts` array: new Contact appended |
| Edit contact fields (name, email, etc.) | `contacts` array: target contact's fields updated, `lastActivityDate` updated |
| Delete contact | `contacts` array: target contact removed |
| Bulk delete contacts | `contacts` array: multiple contacts removed |
| Create new company | `companies` array: new Company appended |
| Edit company fields | `companies` array: target company's fields updated |
| Delete company | `companies` array: target company removed |
| Create new deal | `deals` array: new Deal appended |
| Edit deal fields (name, amount, etc.) | `deals` array: target deal's fields updated, `lastActivityDate` updated |
| Drag deal to different pipeline stage | `deals` array: target deal's `stage` field changed |
| Delete deal | `deals` array: target deal removed |
| Create new ticket | `tickets` array: new Ticket appended |
| Edit ticket (change status, priority, etc.) | `tickets` array: target ticket updated; if status changed to `closed`, `closeDate` set |
| Delete ticket | `tickets` array: target ticket removed |
| Create new task | `tasks` array: new Task appended |
| Edit task fields | `tasks` array: target task's fields updated |
| Toggle task completion (checkbox) | `tasks` array: target task's `status` toggles between `completed`/`not_started`, `completedDate` set/cleared |
| Delete task | `tasks` array: target task removed |
| Create new note | `notes` array: new Note appended |
| Edit note | `notes` array: target note's `body` updated |
| Delete note | `notes` array: target note removed |
| Create email template | `templates` array: new Template appended |
| Edit template | `templates` array: target template's fields updated |
| Duplicate template | `templates` array: new Template appended (copy with "(Copy)" suffix, `timesUsed` reset to 0) |
| Delete template | `templates` array: target template removed |
| Schedule new meeting | `meetings` array: new Meeting appended |
| Edit meeting (change date, status, etc.) | `meetings` array: target meeting's fields updated |
| Delete/cancel meeting | `meetings` array: target meeting removed |
| Create new form | `forms` array: new Form appended with `submissions: 0` |
| Toggle form active/inactive | `forms` array: target form's `status` toggled between `"active"` and `"inactive"` |
| Filter contacts by lifecycle stage | No state change (UI-only filter) |
| Filter contacts by lead status | No state change (UI-only filter) |
| Search contacts/companies/deals/tickets | No state change (UI-only filter) |
| Sort table columns | No state change (UI-only sort) |
| Switch deals view (board/list) | No state change (UI-only toggle) |
| Paginate through records | No state change (UI-only navigation) |
