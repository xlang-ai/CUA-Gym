# outlook_web_mock Schema

**Deploy order**: 33 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8033)
**Base URL**: `http://172.17.46.46:8033/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State endpoint**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{success, files: [{original_name, stored_name, size, content_type, url}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Redirect | Redirects to `/mail/inbox` |
| `/mail/:folderId` | MailRoute | Mail view (inbox, drafts, sent, deleted, junk, archive, or custom folder name) |
| `/calendar` | CalendarRoute | Calendar view with month/week/day/workweek views |
| `/people` | PeopleRoute | Contacts manager |
| `/tasks` | TasksRoute | To Do task manager |
| `/go` | GoRoute | State inspection endpoint (JSON) |

### Mail Route folderId Mapping

| URL folderId | Internal ID |
|--------------|-------------|
| `inbox` | `folder-inbox` |
| `drafts` | `folder-drafts` |
| `sent` | `folder-sentitems` |
| `deleted` | `folder-deleteditems` |
| `junk` | `folder-junkemail` |
| `archive` | `folder-archive` |
| `<custom>` | `folder-<custom>` |

## State Schema (Top-Level Keys)

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Current user profile |
| `folders` | array | Mail folders (system + custom) |
| `messages` | array | All email messages across all folders |
| `calendars` | array | Calendar list (default, holidays, birthdays) |
| `events` | array | Calendar events |
| `contacts` | array | People/contacts |
| `categories` | array | Color categories for messages |
| `settings` | object | User settings (layout, theme, signatures, etc.) |
| `tasks` | array | To Do task items |
| `selectedFolderId` | string | Currently selected mail folder ID. Default: `"folder-inbox"` |
| `selectedMessageId` | string\|null | Currently selected/open email ID. Default: `null` |
| `selectedModule` | string | Active navigation module. Default: `"mail"`. Values: `"mail"`, `"calendar"`, `"people"`, `"tasks"` |
| `calendarView` | string | Calendar view mode. Default: `"month"`. Values: `"day"`, `"workweek"`, `"week"`, `"month"` |
| `calendarDate` | string | ISO 8601 date for calendar navigation. Default: current date |
| `searchQuery` | string | Active search query text. Default: `""` |
| `composeState` | object\|null | Compose modal state. `null` = closed. Default: `null` |
| `settingsOpen` | boolean | Whether settings panel is open. Default: `false` |
| `settingsSection` | string | Active settings section. Default: `"accounts"` |
| `folderPaneCollapsed` | boolean | Whether folder pane is collapsed. Default: `false` |

---

## User Object

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `id` | string | `"user-1"` | |
| `displayName` | string | `"Katy Reid"` | |
| `email` | string | `"katyreid@outlook.com"` | |
| `initials` | string | `"KR"` | |
| `avatarColor` | string | `"#0078D4"` | |
| `jobTitle` | string | `"Product Manager"` | |
| `company` | string | `"Contoso Ltd"` | |
| `timezone` | string | `"America/New_York"` | |
| `signature` | string | `"<p>Best regards,<br>Katy Reid</p>"` | HTML signature |

---

## Folder Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"folder-inbox"`, `"folder-drafts"`, `"folder-expenses"` |
| `displayName` | string | Display name: `"Inbox"`, `"Drafts"`, etc. |
| `parentFolderId` | string\|null | Parent folder ID for nesting (e.g. `"folder-inbox"` for subfolders) |
| `wellKnownName` | string\|null | System name: `"inbox"`, `"drafts"`, `"sentitems"`, `"deleteditems"`, `"junkemail"`, `"archive"`, or `null` |
| `totalItemCount` | number | Total messages in folder (recomputed automatically) |
| `unreadItemCount` | number | Unread messages in folder (recomputed automatically) |
| `isSystem` | boolean | `true` for built-in folders, `false` for user-created |
| `icon` | string | Icon key: `"inbox"`, `"drafts"`, `"send"`, `"trash"`, `"warning"`, `"archive"`, `"folder"` |
| `childFolders` | array | IDs of child folders |
| `isFavorite` | boolean | Whether folder appears in Favorites section |

### Default Folders

| ID | Display Name | wellKnownName | isSystem | isFavorite |
|----|-------------|---------------|----------|------------|
| `folder-inbox` | Inbox | `inbox` | true | true |
| `folder-drafts` | Drafts | `drafts` | true | false |
| `folder-sentitems` | Sent Items | `sentitems` | true | false |
| `folder-deleteditems` | Deleted Items | `deleteditems` | true | false |
| `folder-junkemail` | Junk Email | `junkemail` | true | false |
| `folder-archive` | Archive | `archive` | true | false |
| `folder-expenses` | Expenses | `null` | false | true |
| `folder-invoices` | Invoices | `null` | false | true |
| `folder-projects` | Projects | `null` | false | false |

---

## Message Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique ID: `"msg-001"` through `"msg-030"` |
| `conversationId` | string | Groups messages in same thread: `"conv-001"`, etc. |
| `parentFolderId` | string | Folder ID this message belongs to |
| `subject` | string | Email subject line |
| `bodyPreview` | string | Plain-text preview (max ~255 chars) |
| `body` | object | `{contentType: "html", content: "<p>...</p>"}` |
| `from` | object | `{name: string, email: string}` |
| `sender` | object | `{name: string, email: string}` (usually same as from) |
| `toRecipients` | array | `[{name: string, email: string}]` |
| `ccRecipients` | array | `[{name: string, email: string}]` |
| `bccRecipients` | array | `[{name: string, email: string}]` |
| `receivedDateTime` | string | ISO 8601 datetime |
| `sentDateTime` | string | ISO 8601 datetime |
| `isRead` | boolean | Read status |
| `isDraft` | boolean | Whether message is a draft |
| `importance` | string | `"normal"`, `"high"`, or `"low"` |
| `flag` | object | `{flagStatus: "notFlagged" \| "flagged"}` |
| `categories` | array | Category names: `["Blue category", "Red category"]` etc. |
| `hasAttachments` | boolean | Whether message has attachments |
| `attachments` | array | `[{id, name, contentType, size, isInline}]` |
| `inferenceClassification` | string | `"focused"` or `"other"` (Focused Inbox classification) |
| `isPinned` | boolean | Whether message is pinned to top |

### Default Messages Summary (30 total)

| ID Range | Folder | Count | Description |
|----------|--------|-------|-------------|
| `msg-001` to `msg-012` | folder-inbox (focused) | 12 | Inbox focused tab messages |
| `msg-013` to `msg-017` | folder-inbox (other) | 5 | Inbox other tab messages |
| `msg-018` to `msg-019` | folder-drafts | 2 | Draft messages |
| `msg-020` to `msg-024` | folder-sentitems | 5 | Sent messages |
| `msg-025` to `msg-026` | folder-deleteditems | 2 | Deleted messages |
| `msg-027` to `msg-028` | folder-junkemail | 2 | Junk/spam messages |
| `msg-029` | folder-expenses | 1 | Expense report email |
| `msg-030` | folder-invoices | 1 | Invoice email |

### Attachment Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"att-001"` |
| `name` | string | Filename: `"E-Ticket_CA4521.pdf"` |
| `contentType` | string | MIME type: `"application/pdf"`, `"application/zip"` |
| `size` | number | Size in bytes |
| `isInline` | boolean | Whether attachment is inline |

---

## Calendar Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | `"cal-default"`, `"cal-holidays"`, `"cal-birthdays"` |
| `name` | string | Display name |
| `color` | string | Hex color |
| `isDefault` | boolean | Whether this is the default calendar |
| `isVisible` | boolean | Whether events from this calendar are shown |
| `canEdit` | boolean | Whether events can be created/edited on this calendar |

### Default Calendars

| ID | Name | Color | canEdit |
|----|------|-------|---------|
| `cal-default` | Calendar | `#0078D4` | true |
| `cal-holidays` | United States holidays | `#107C10` | false |
| `cal-birthdays` | Birthdays | `#FF8C00` | false |

---

## Event Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"evt-standup-0"`, `"evt-1on1"`, `"evt-sprint"` |
| `subject` | string | Event title |
| `calendarId` | string | Calendar ID this event belongs to |
| `color` | string | Hex color for display |
| `body` | object | `{contentType: "text", content: string}` |
| `start` | object | `{dateTime: ISO8601, timeZone: "America/New_York"}` |
| `end` | object | `{dateTime: ISO8601, timeZone: "America/New_York"}` |
| `location` | object | `{displayName: string}` |
| `isAllDay` | boolean | Whether event spans entire day |
| `isCancelled` | boolean | Whether event is cancelled |
| `organizer` | object | `{name: string, email: string}` |
| `attendees` | array | `[{name: string, email: string, status: "accepted"\|"tentative"\|"declined"\|"none"}]` |
| `importance` | string | `"normal"` or `"high"` |
| `showAs` | string | `"free"`, `"tentative"`, `"busy"`, `"oof"` |
| `sensitivity` | string | `"normal"` |
| `categories` | array | Category names |
| `isOnlineMeeting` | boolean | Whether there's an online meeting link |
| `onlineMeetingUrl` | string\|null | Teams meeting URL |
| `recurrence` | object\|null | `{pattern: "daily"\|"weekly"}` or `null` |
| `reminderMinutesBefore` | number | Minutes before event for reminder (0, 5, 15, 30, 60, 1440) |
| `hasAttachments` | boolean | |
| `responseStatus` | string | `"accepted"`, `"tentative"`, `"organizer"`, `"none"` |

### Default Events (dynamically generated relative to current date)

| ID | Subject | Calendar | Type |
|----|---------|----------|------|
| `evt-standup-0` to `evt-standup-4` | Team Standup | cal-default | Recurring daily Mon-Fri 9:00-9:30 AM |
| `evt-1on1` | 1:1 with Marcus | cal-default | Weekly Tuesday 2:00-2:30 PM |
| `evt-sprint` | Sprint Planning | cal-default | Weekly Monday 10:00-11:00 AM |
| `evt-demo` | Product Demo | cal-default | Wednesday 3:00-4:00 PM |
| `evt-design` | Design Review | cal-default | Thursday 1:00-2:00 PM |
| `evt-client` | Client Call -- Woodgrove Bank | cal-default | Friday 11:00-11:30 AM |
| `evt-offsite` | Company Offsite | cal-default | Next Friday, all day |
| `evt-birthday` | Marcus Chen's Birthday | cal-birthdays | Next Tuesday, all day |
| `evt-qbr` | Quarterly Review | cal-default | Last Monday 2:00-3:00 PM |
| `evt-lunch` | Team Lunch | cal-default | Last Wednesday 12:00-1:00 PM |
| `evt-spring` | Spring Break | cal-holidays | 10 days from now, all day |

---

## Contact Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"contact-001"` through `"contact-018"` |
| `displayName` | string | Full name |
| `givenName` | string | First name |
| `surname` | string | Last name |
| `emailAddresses` | array | `[{address: string, name: string}]` |
| `businessPhones` | array | `[string]` |
| `mobilePhone` | string\|null | Mobile phone number |
| `homePhones` | array | `[string]` |
| `jobTitle` | string\|null | Job title |
| `companyName` | string\|null | Company |
| `department` | string\|null | Department |
| `officeLocation` | string\|null | Office location |
| `businessAddress` | object\|null | Business address |
| `homeAddress` | object\|null | Home address |
| `birthday` | string\|null | Date string e.g. `"1990-06-15"` |
| `personalNotes` | string | Notes about the contact |
| `initials` | string | Two-letter initials for avatar |
| `avatarColor` | string | Hex color for avatar background |
| `isFavorite` | boolean | Whether contact is in favorites |
| `categories` | array | Category names |

### Default Contacts (18 total)

| ID | Name | Company | Favorite |
|----|------|---------|----------|
| `contact-001` | Elvia Atkins | Contoso Ltd | true |
| `contact-002` | Marcus Chen | Contoso Ltd | true |
| `contact-003` | Lydia Bauer | Contoso Ltd | false |
| `contact-004` | Kevin Thompson | Contoso Ltd | true |
| `contact-005` | Alex Wilber | Contoso Ltd | true |
| `contact-006` | Megan Bowen | Contoso Ltd | false |
| `contact-007` | Pradeep Gupta | Contoso Ltd | false |
| `contact-008` | Nestor Wilke | Contoso Ltd | false |
| `contact-009` | Johanna Lorenz | Contoso Ltd | false |
| `contact-010` | Isaiah Langer | Contoso Ltd | false |
| `contact-011` | Lee Gu | Contoso Ltd | false |
| `contact-012` | Miriam Graham | Contoso Ltd | true |
| `contact-013` | Daisy Phillips | (personal) | false |
| `contact-014` | Amanda Brady | Brady Real Estate | false |
| `contact-015` | Shannon Trine | Fabrikam Inc | false |
| `contact-016` | Kristin Patterson | Woodgrove Bank | false |
| `contact-017` | Contoso Airlines | Contoso Airlines | false |
| `contact-018` | Margie's Travel | Margie's Travel | false |

---

## Category Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"cat-blue"` |
| `displayName` | string | e.g. `"Blue category"` |
| `color` | string | Hex color |
| `presetIndex` | number | Preset index (0-5) |

### Default Categories

| ID | Display Name | Color |
|----|-------------|-------|
| `cat-blue` | Blue category | `#0078D4` |
| `cat-green` | Green category | `#107C10` |
| `cat-orange` | Orange category | `#FF8C00` |
| `cat-purple` | Purple category | `#8764B8` |
| `cat-red` | Red category | `#D13438` |
| `cat-yellow` | Yellow category | `#FFB900` |

---

## Settings Object

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `readingPanePosition` | string | `"right"` | `"right"`, `"bottom"`, or `"off"` |
| `density` | string | `"medium"` | `"full"`, `"medium"`, or `"compact"` |
| `conversationView` | boolean | `true` | Group emails by conversation |
| `focusedInbox` | boolean | `true` | Enable Focused/Other inbox tabs |
| `autoReply` | object | see below | Automatic reply settings |
| `signature` | object | see below | Email signature settings |
| `theme` | string | `"light"` | `"light"`, `"dark"`, or `"system"` |
| `previewText` | boolean | `true` | Show email preview text in list |
| `weekStart` | string | `"Sunday"` | First day of the week |
| `workingHours` | object | see below | Working hours configuration |

### AutoReply Sub-Object

| Field | Type | Default |
|-------|------|---------|
| `enabled` | boolean | `false` |
| `internalMessage` | string | `""` |
| `externalMessage` | string | `""` |

### Signature Sub-Object

| Field | Type | Default |
|-------|------|---------|
| `name` | string | `"Default Signature"` |
| `html` | string | `"<p>Best regards,<br>Katy Reid</p>"` |
| `useForNew` | boolean | `true` |
| `useForReply` | boolean | `false` |

### WorkingHours Sub-Object

| Field | Type | Default |
|-------|------|---------|
| `start` | string | `"08:00"` |
| `end` | string | `"17:00"` |
| `days` | array | `[1, 2, 3, 4, 5]` (Mon-Fri) |

---

## Task Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"task-001"` through `"task-007"` |
| `title` | string | Task title |
| `dueDate` | string | ISO 8601 datetime |
| `completed` | boolean | Whether task is done |
| `importance` | string | `"high"`, `"normal"`, or `"low"` |
| `categories` | array | Category names |

### Default Tasks (7 total)

| ID | Title | Importance | Completed |
|----|-------|-----------|-----------|
| `task-001` | Review Project Falcon PR #142 | high | false |
| `task-002` | Approve Q2 marketing budget | high | false |
| `task-003` | Prepare QBR presentation slides | normal | false |
| `task-004` | Follow up with legal on ToS changes | normal | false |
| `task-005` | Send team outing photo selections | low | false |
| `task-006` | Book conference room for sprint demo | normal | true |
| `task-007` | Submit March expense report | normal | true |

---

## ComposeState Object (when not null)

| Field | Type | Notes |
|-------|------|-------|
| `mode` | string | `"new"`, `"reply"`, `"replyAll"`, or `"forward"` |
| `to` | string | Pre-filled "To" field (comma-separated emails) |
| `subject` | string | Pre-filled subject |
| `body` | string | Pre-filled body content |
| `replyTo` | object | Original message object (for reply/replyAll) |
| `forwardFrom` | object | Original message object (for forward) |

---

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8033/",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "id": "user-1",
          "displayName": "Katy Reid",
          "email": "katyreid@outlook.com",
          "initials": "KR",
          "avatarColor": "#0078D4"
        },
        "folders": [
          {"id": "folder-inbox", "displayName": "Inbox", "parentFolderId": null, "wellKnownName": "inbox", "totalItemCount": 1, "unreadItemCount": 1, "isSystem": true, "icon": "inbox", "childFolders": [], "isFavorite": true}
        ],
        "messages": [
          {
            "id": "msg-001",
            "conversationId": "conv-001",
            "parentFolderId": "folder-inbox",
            "subject": "Test Email Subject",
            "bodyPreview": "This is a test email body preview...",
            "body": {"contentType": "html", "content": "<p>This is a test email.</p>"},
            "from": {"name": "Alice Smith", "email": "alice@example.com"},
            "sender": {"name": "Alice Smith", "email": "alice@example.com"},
            "toRecipients": [{"name": "Katy Reid", "email": "katyreid@outlook.com"}],
            "ccRecipients": [],
            "bccRecipients": [],
            "receivedDateTime": "2026-03-13T10:00:00Z",
            "sentDateTime": "2026-03-13T10:00:00Z",
            "isRead": false,
            "isDraft": false,
            "importance": "normal",
            "flag": {"flagStatus": "notFlagged"},
            "categories": [],
            "hasAttachments": false,
            "attachments": [],
            "inferenceClassification": "focused",
            "isPinned": false
          }
        ],
        "calendars": [
          {"id": "cal-default", "name": "Calendar", "color": "#0078D4", "isDefault": true, "isVisible": true, "canEdit": true}
        ],
        "events": [],
        "contacts": [],
        "categories": [
          {"id": "cat-blue", "displayName": "Blue category", "color": "#0078D4", "presetIndex": 0}
        ],
        "settings": {
          "readingPanePosition": "right",
          "density": "medium",
          "conversationView": true,
          "focusedInbox": true,
          "autoReply": {"enabled": false, "internalMessage": "", "externalMessage": ""},
          "signature": {"name": "Default Signature", "html": "<p>Best regards,<br>Katy Reid</p>", "useForNew": true, "useForReply": false},
          "theme": "light",
          "previewText": true,
          "weekStart": "Sunday",
          "workingHours": {"start": "08:00", "end": "17:00", "days": [1, 2, 3, 4, 5]}
        },
        "tasks": [],
        "selectedFolderId": "folder-inbox",
        "selectedMessageId": null,
        "selectedModule": "mail",
        "calendarView": "month",
        "calendarDate": "2026-03-13T00:00:00.000Z",
        "searchQuery": "",
        "composeState": null,
        "settingsOpen": false,
        "settingsSection": "accounts",
        "folderPaneCollapsed": false
      }
    }
  }
}
```

---

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Select a folder | `selectedFolderId` changes; `selectedMessageId` set to `null`; `searchQuery` cleared |
| Select/read an email | `selectedMessageId` changes; `messages[i].isRead: false -> true` |
| Toggle read/unread | `messages[i].isRead` toggled |
| Flag/unflag email | `messages[i].flag.flagStatus`: `"notFlagged"` <-> `"flagged"` |
| Pin/unpin email | `messages[i].isPinned` toggled |
| Delete email | If in Deleted Items: message removed from `messages`. Otherwise: `messages[i].parentFolderId` -> `"folder-deleteditems"` |
| Archive email | `messages[i].parentFolderId` -> `"folder-archive"` |
| Move email to folder | `messages[i].parentFolderId` changes to target folder ID |
| Categorize email | `messages[i].categories` array modified (add/remove category name) |
| Send email (compose) | New message object added to `messages` with `parentFolderId: "folder-sentitems"`; `composeState` set to `null` |
| Open compose modal | `composeState` set to `{mode: "new"\|"reply"\|"replyAll"\|"forward", ...}` |
| Close compose modal | `composeState` set to `null` |
| Search for emails | `searchQuery` updated |
| Create folder | New folder object added to `folders` |
| Toggle folder favorite | `folders[i].isFavorite` toggled |
| Toggle folder pane | `folderPaneCollapsed` toggled |
| Switch module (Mail/Calendar/People/Tasks) | `selectedModule` changes |
| Change calendar view | `calendarView` changes (`"day"`, `"workweek"`, `"week"`, `"month"`) |
| Navigate calendar date | `calendarDate` changes |
| Create calendar event | New event object added to `events` |
| Edit calendar event | `events[i]` fields updated |
| Delete calendar event | Event removed from `events` |
| Toggle calendar visibility | `calendars[i].isVisible` toggled |
| Add contact | New contact object added to `contacts` |
| Edit contact | `contacts[i]` fields updated |
| Delete contact | Contact removed from `contacts` |
| Create task | New task object added to `tasks` |
| Toggle task complete | `tasks[i].completed` toggled |
| Delete task | Task removed from `tasks` |
| Update settings | `settings` sub-fields updated (e.g. `settings.theme`, `settings.density`) |
| Open settings panel | `settingsOpen: true` |
| Close settings panel | `settingsOpen: false` |

### state_diff Structure

The `/go` endpoint returns `state_diff` which contains keys that differ between `initial_state` and `current_state`. Each changed key maps to `{original: <initial_value>, current: <current_value>}`.

```json
{
  "state_diff": {
    "messages": {
      "original": [...],
      "current": [...]
    },
    "selectedMessageId": {
      "original": null,
      "current": "msg-001"
    },
    "selectedFolderId": {
      "original": "folder-inbox",
      "current": "folder-sentitems"
    }
  }
}
```

---

## State Management Details

- **Pattern**: React Context (`StoreContext.jsx`)
- **Persistence**: localStorage with keys `outlook_mock_data` (current) and `outlook_mock_initial_state` (initial), suffixed with `_<sid>` when session ID is present
- **Folder counts**: `totalItemCount` and `unreadItemCount` are automatically recomputed from `messages` whenever messages or folders change
- **Deep merge**: Custom state injected via `/post` is deep-merged with the default `createInitialData()` output, so partial state overrides work correctly
