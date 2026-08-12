# monday_mock Schema

**Deploy order**: 30 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8030)
**Base URL**: `http://172.17.46.46:8030/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Redirect | Redirects to `/board/board-1` (preserves query params) |
| `/board/:boardId` | Board | Main board view (table or kanban) |
| `/my-work` | Placeholder | Placeholder "coming soon" page |
| `/go` | Go | State inspection endpoint (JSON output) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUserId` | `string` | ID of the logged-in user. Default: `"user-1"` |
| `users` | `Record<string, User>` | All users in the system, keyed by user ID |
| `workspaces` | `Record<string, Workspace>` | Workspaces, keyed by workspace ID |
| `activeWorkspaceId` | `string` | Currently active workspace. Default: `"ws-1"` |
| `activeBoardId` | `string` | Top-level active board reference (also in `ui`). Default: `"board-1"` |
| `boards` | `Record<string, Board>` | All boards, keyed by board ID |
| `columns` | `Record<string, Column>` | All column definitions, keyed by column ID |
| `groups` | `Record<string, Group>` | All groups (sections within boards), keyed by group ID |
| `items` | `Record<string, Item>` | All items (rows), keyed by item ID |
| `updates` | `Record<string, Update>` | Comments/updates on items, keyed by update ID |
| `notifications` | `Notification[]` | Array of notification objects |
| `activityLog` | `Activity[]` | Array of activity log entries |
| `ui` | `UIState` | UI-related transient state |

---

### User

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique user ID (e.g., `"user-1"`) |
| `name` | `string` | Display name |
| `email` | `string` | Email address |
| `initials` | `string` | Two-letter initials for avatar |
| `color` | `string` | Hex color for avatar background |
| `role` | `string` | Role: `"Admin"`, `"Member"`, or `"Viewer"` |
| `isCurrentUser` | `boolean` | Whether this is the logged-in user |

**Default users:**

| ID | Name | Email | Initials | Color | Role |
|----|------|-------|----------|-------|------|
| `user-1` | Sarah Johnson | sarah@company.com | SJ | #0073EA | Admin |
| `user-2` | Alex Chen | alex@company.com | AC | #00C875 | Member |
| `user-3` | Mike Roberts | mike@company.com | MR | #FDAB3D | Member |
| `user-4` | Emily Davis | emily@company.com | ED | #E2445C | Member |
| `user-5` | Jordan Lee | jordan@company.com | JL | #A25DDC | Member |
| `user-6` | Priya Patel | priya@company.com | PP | #FF642E | Viewer |

---

### Workspace

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique workspace ID (e.g., `"ws-1"`) |
| `name` | `string` | Workspace display name |
| `icon` | `string` | Single character icon |
| `color` | `string` | Hex color for workspace icon |
| `boardIds` | `string[]` | Ordered array of board IDs in this workspace |

**Default workspaces:**

| ID | Name | Icon | Color | Board IDs |
|----|------|------|-------|-----------|
| `ws-1` | Main Workspace | M | #0073EA | `["board-1", "board-2", "board-3"]` |
| `ws-2` | Marketing | K | #FF158A | `["board-4"]` |

---

### Board

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique board ID (e.g., `"board-1"`) |
| `name` | `string` | Board name (editable) |
| `description` | `string` | Board description (editable) |
| `workspaceId` | `string` | Parent workspace ID |
| `type` | `string` | Board type, always `"board"` |
| `isFavorite` | `boolean` | Whether board is marked as favorite |
| `groupIds` | `string[]` | Ordered array of group IDs in this board |
| `columnIds` | `string[]` | Ordered array of column IDs for this board |
| `views` | `View[]` | Array of view configurations |
| `createdAt` | `string` | ISO 8601 creation timestamp |
| `updatedAt` | `string` | ISO 8601 last update timestamp |

**Default boards:**

| ID | Name | Workspace | Favorite | Groups | Columns |
|----|------|-----------|----------|--------|---------|
| `board-1` | Team Projects | ws-1 | true | group-1, group-2, group-3 | col-person-1, col-status-1, col-priority-1, col-date-1, col-timeline-1, col-numbers-1 |
| `board-2` | Sprint Planning | ws-1 | false | group-4, group-5 | col-person-2, col-status-2, col-priority-2, col-date-2, col-text-1 |
| `board-3` | Bug Tracker | ws-1 | false | group-6, group-7 | col-person-3, col-status-3, col-priority-3, col-text-2, col-dropdown-1 |
| `board-4` | Content Calendar | ws-2 | true | group-8, group-9 | col-person-4, col-status-4, col-date-3, col-tags-1, col-text-3 |

#### View (embedded in Board)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique view ID (e.g., `"view-1"`) |
| `type` | `string` | `"table"` or `"kanban"` |
| `name` | `string` | Display name for the view tab |
| `isDefault` | `boolean` | Whether this is the default view for the board |
| `statusColumnId` | `string` (optional) | Column ID used for kanban grouping (kanban views only) |

**Default views:**

| ID | Board | Type | Name | Default | statusColumnId |
|----|-------|------|------|---------|----------------|
| `view-1` | board-1 | table | Table | true | - |
| `view-2` | board-1 | kanban | Kanban | false | col-status-1 |
| `view-3` | board-2 | table | Table | true | - |
| `view-4` | board-2 | kanban | Kanban | false | col-status-2 |
| `view-5` | board-3 | table | Table | true | - |
| `view-6` | board-4 | table | Table | true | - |

---

### Column

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique column ID (e.g., `"col-status-1"`) |
| `title` | `string` | Column header title |
| `type` | `string` | Column type (see below) |
| `width` | `number` | Column width in pixels |
| `settings` | `object` | Type-specific settings |

#### Column Types and Settings

| Type | settings shape | value stored in item.columnValues[colId].value |
|------|---------------|------------------------------------------------|
| `people` | `{}` | `string[]` - Array of user IDs |
| `status` | `{ labels: Record<number, { text: string, color: string }> }` | `number` - Index into labels map |
| `date` | `{}` | `string` - ISO date `"YYYY-MM-DD"` |
| `timeline` | `{}` | `{ start: string, end: string }` or `null` - Start/end ISO dates |
| `numbers` | `{ unit: string, direction: "left"\|"right" }` | `number` |
| `text` | `{}` | `string` |
| `dropdown` | `{ options: string[] }` | `string` - Selected option text |
| `tags` | `{ options: { id: string, name: string, color: string }[] }` | `string[]` - Array of tag IDs |

**Default columns:**

| ID | Title | Type | Board | Settings summary |
|----|-------|------|-------|-----------------|
| `col-person-1` | Owner | people | board-1 | - |
| `col-status-1` | Status | status | board-1 | Labels: 0=Done(#00C875), 1=Working on it(#FDAB3D), 2=Stuck(#E2445C), 3=Not Started(#C4C4C4) |
| `col-priority-1` | Priority | status | board-1 | Labels: 0=Critical(#333333), 1=High(#401694), 2=Medium(#5559DF), 3=Low(#579BFC), 4=""(#C4C4C4) |
| `col-date-1` | Due Date | date | board-1 | - |
| `col-timeline-1` | Timeline | timeline | board-1 | - |
| `col-numbers-1` | Budget | numbers | board-1 | unit="$", direction="left" |
| `col-person-2` | Assignee | people | board-2 | - |
| `col-status-2` | Status | status | board-2 | Labels: 0=Done(#00C875), 1=In Progress(#FDAB3D), 2=Stuck(#E2445C), 3=Ready(#579BFC), 4=Backlog(#C4C4C4) |
| `col-priority-2` | Priority | status | board-2 | Labels: 0=Critical(#333333), 1=High(#401694), 2=Medium(#5559DF), 3=Low(#579BFC), 4=""(#C4C4C4) |
| `col-date-2` | Due Date | date | board-2 | - |
| `col-text-1` | Notes | text | board-2 | - |
| `col-person-3` | Assignee | people | board-3 | - |
| `col-status-3` | Status | status | board-3 | Labels: 0=Fixed(#00C875), 1=In Progress(#FDAB3D), 2=Blocked(#E2445C), 3=Open(#579BFC), 4=Won't Fix(#C4C4C4) |
| `col-priority-3` | Severity | status | board-3 | Labels: 0=Critical(#333333), 1=High(#401694), 2=Medium(#5559DF), 3=Low(#579BFC) |
| `col-text-2` | Description | text | board-3 | - |
| `col-dropdown-1` | Component | dropdown | board-3 | options: ["Frontend", "Backend", "API", "Database", "DevOps", "Mobile"] |
| `col-person-4` | Author | people | board-4 | - |
| `col-status-4` | Status | status | board-4 | Labels: 0=Published(#00C875), 1=In Review(#FDAB3D), 2=Writing(#579BFC), 3=Idea(#C4C4C4) |
| `col-date-3` | Publish Date | date | board-4 | - |
| `col-tags-1` | Tags | tags | board-4 | options: [{id:"tag-blog",name:"Blog",color:"#0073EA"}, {id:"tag-social",name:"Social",color:"#FF158A"}, {id:"tag-email",name:"Email",color:"#00C875"}, {id:"tag-video",name:"Video",color:"#FDAB3D"}, {id:"tag-pr",name:"PR",color:"#A25DDC"}] |
| `col-text-3` | Topic | text | board-4 | - |

---

### Group

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique group ID (e.g., `"group-1"`) |
| `boardId` | `string` | Parent board ID |
| `title` | `string` | Group title (editable) |
| `color` | `string` | Hex color for the group header bar |
| `isCollapsed` | `boolean` | Whether the group is collapsed |
| `itemIds` | `string[]` | Ordered array of item IDs in this group |
| `position` | `number` | Display order within the board |

**Default groups:**

| ID | Board | Title | Color | Collapsed | Items |
|----|-------|-------|-------|-----------|-------|
| `group-1` | board-1 | This Quarter | #579BFC | false | item-1, item-2, item-3, item-4 |
| `group-2` | board-1 | Next Quarter | #00C875 | false | item-5, item-6, item-7 |
| `group-3` | board-1 | Completed | #A25DDC | true | item-8, item-9 |
| `group-4` | board-2 | Sprint 12 | #FF642E | false | item-10, item-11, item-12, item-13 |
| `group-5` | board-2 | Sprint 13 (Planned) | #579BFC | false | item-14, item-15 |
| `group-6` | board-3 | Active Bugs | #E2445C | false | item-16, item-17, item-18 |
| `group-7` | board-3 | Resolved | #00C875 | false | item-19, item-20 |
| `group-8` | board-4 | January | #FF158A | false | item-21, item-22, item-23 |
| `group-9` | board-4 | February | #0086C0 | false | item-24, item-25 |

---

### Item

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique item ID (e.g., `"item-1"`) |
| `boardId` | `string` | Parent board ID |
| `groupId` | `string` | Parent group ID |
| `name` | `string` | Item name (editable) |
| `columnValues` | `Record<string, { value: any }>` | Column values, keyed by column ID. Each value wrapped in `{ value: ... }` |
| `subitemIds` | `string[]` | Array of sub-item IDs (always `[]` in defaults) |
| `isSelected` | `boolean` | Whether item row checkbox is selected |
| `createdAt` | `string` | ISO 8601 creation timestamp |
| `updatedAt` | `string` | ISO 8601 last update timestamp |
| `creatorId` | `string` | User ID of the item creator |

**Default items (25 total):**

| ID | Board | Group | Name |
|----|-------|-------|------|
| `item-1` | board-1 | group-1 | Design landing page |
| `item-2` | board-1 | group-1 | Implement API endpoints |
| `item-3` | board-1 | group-1 | User testing phase 1 |
| `item-4` | board-1 | group-1 | Database migration |
| `item-5` | board-1 | group-2 | Mobile app redesign |
| `item-6` | board-1 | group-2 | Analytics dashboard v2 |
| `item-7` | board-1 | group-2 | Performance optimization |
| `item-8` | board-1 | group-3 | Setup CI/CD pipeline |
| `item-9` | board-1 | group-3 | Brand guidelines document |
| `item-10` | board-2 | group-4 | Fix login redirect bug |
| `item-11` | board-2 | group-4 | Add dark mode toggle |
| `item-12` | board-2 | group-4 | Optimize image loading |
| `item-13` | board-2 | group-4 | Write unit tests for auth module |
| `item-14` | board-2 | group-5 | Implement search feature |
| `item-15` | board-2 | group-5 | User profile page redesign |
| `item-16` | board-3 | group-6 | Dropdown menu not closing on outside click |
| `item-17` | board-3 | group-6 | API timeout on large data export |
| `item-18` | board-3 | group-6 | Date picker shows wrong month on first open |
| `item-19` | board-3 | group-7 | Memory leak in WebSocket handler |
| `item-20` | board-3 | group-7 | CSS grid layout breaking on mobile |
| `item-21` | board-4 | group-8 | Q1 Product Update Blog Post |
| `item-22` | board-4 | group-8 | Social media campaign: New Year |
| `item-23` | board-4 | group-8 | Customer success story video |
| `item-24` | board-4 | group-9 | Monthly newsletter |
| `item-25` | board-4 | group-9 | PR: Series B announcement |

---

### Update

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique update ID (e.g., `"update-1"`) |
| `itemId` | `string` | Parent item ID |
| `authorId` | `string` | User ID of the author |
| `body` | `string` | Update text content |
| `createdAt` | `string` | ISO 8601 creation timestamp |
| `likes` | `string[]` | Array of user IDs who liked this update |
| `isReply` | `boolean` | Whether this is a reply to another update |
| `parentUpdateId` | `string \| null` | Parent update ID for replies, `null` for top-level updates |

**Default updates:**

| ID | Item | Author | isReply | parentUpdateId |
|----|------|--------|---------|----------------|
| `update-1` | item-1 | user-2 | false | null |
| `update-2` | item-1 | user-1 | true | update-1 |
| `update-3` | item-4 | user-3 | false | null |
| `update-4` | item-4 | user-1 | true | update-3 |
| `update-5` | item-12 | user-5 | false | null |
| `update-6` | item-2 | user-3 | false | null |

---

### Notification

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique notification ID (e.g., `"notif-1"`) |
| `type` | `string` | Notification type: `"mention"`, `"status_change"`, `"assignment"`, `"update"` |
| `message` | `string` | Human-readable notification message |
| `userId` | `string` | Recipient user ID |
| `actorId` | `string` | User ID who triggered the notification |
| `itemId` | `string` | Related item ID |
| `boardId` | `string` | Related board ID |
| `isRead` | `boolean` | Whether the notification has been read |
| `createdAt` | `string` | ISO 8601 creation timestamp |

**Default notifications (4 total):**

| ID | Type | isRead | Item |
|----|------|--------|------|
| `notif-1` | mention | false | item-4 |
| `notif-2` | status_change | false | item-10 |
| `notif-3` | assignment | true | item-3 |
| `notif-4` | update | true | item-1 |

---

### Activity (activityLog entries)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique activity ID (e.g., `"activity-1"`) |
| `boardId` | `string` | Board where the activity occurred |
| `itemId` | `string` | Related item ID |
| `userId` | `string` | User who performed the action |
| `columnId` | `string` | Column that was changed |
| `action` | `string` | Action type, always `"column_change"` |
| `previousValue` | `{ value: any }` | Previous column value |
| `newValue` | `{ value: any }` | New column value |
| `createdAt` | `string` | ISO 8601 timestamp |

**Default activity log (3 entries):**

| ID | Item | Column | Previous | New |
|----|------|--------|----------|-----|
| `activity-1` | item-4 | col-status-1 | 1 (Working on it) | 2 (Stuck) |
| `activity-2` | item-10 | col-status-2 | 1 (In Progress) | 0 (Done) |
| `activity-3` | item-1 | col-status-1 | 3 (Not Started) | 1 (Working on it) |

---

### UIState

| Field | Type | Description |
|-------|------|-------------|
| `sidebarCollapsed` | `boolean` | Whether sidebar is collapsed. Default: `false` |
| `activeBoardId` | `string` | Currently displayed board ID. Default: `"board-1"` |
| `activeViewId` | `string` | Currently active view ID. Default: `"view-1"` |
| `selectedItemIds` | `string[]` | Currently selected item IDs (legacy, items track `isSelected` individually). Default: `[]` |
| `searchQuery` | `string` | Current search/filter text for items. Default: `""` |
| `filterConditions` | `FilterCondition[]` | Active filter conditions. Default: `[]` |
| `sortConditions` | `SortCondition[]` | Active sort conditions. Default: `[]` |
| `itemDetailOpenId` | `string \| null` | Item ID for the open detail panel, or `null`. Default: `null` |
| `notificationsPanelOpen` | `boolean` | Whether notifications panel is open. Default: `false` |

#### FilterCondition

| Field | Type | Description |
|-------|------|-------------|
| `columnId` | `string` | Column ID to filter on |
| `condition` | `string` | `"is"`, `"is_not"`, `"contains"`, `"is_empty"`, `"is_not_empty"` |
| `value` | `string` | Filter value (ignored for `is_empty`/`is_not_empty`) |

#### SortCondition

| Field | Type | Description |
|-------|------|-------------|
| `columnId` | `string` | Column ID to sort by |
| `direction` | `string` | `"asc"` or `"desc"` |

---

## Reducer Actions (state transitions)

| Action Type | Payload | Effect |
|-------------|---------|--------|
| `SET_STATE` | `state: object` | Replace entire state |
| `UPDATE_COLUMN_VALUE` | `{ itemId, columnId, newValue }` | Set `items[itemId].columnValues[columnId].value` and update `updatedAt` |
| `UPDATE_ITEM_NAME` | `{ itemId, name }` | Set `items[itemId].name` and update `updatedAt` |
| `CREATE_ITEM` | `{ groupId, name, boardId }` | Add new item to `items` map and append ID to `groups[groupId].itemIds` |
| `DELETE_ITEM` | `{ itemId }` | Remove from `items` map and from parent group's `itemIds` |
| `MOVE_ITEM_TO_GROUP` | `{ itemId, targetGroupId }` | Move item between groups, update `groupId` field |
| `TOGGLE_GROUP_COLLAPSE` | `{ groupId }` | Toggle `groups[groupId].isCollapsed` |
| `UPDATE_GROUP_TITLE` | `{ groupId, title }` | Set `groups[groupId].title` |
| `CREATE_GROUP` | `{ boardId, title, color }` | Add new group to `groups` map and append ID to `boards[boardId].groupIds` |
| `TOGGLE_FAVORITE` | `{ boardId }` | Toggle `boards[boardId].isFavorite` |
| `SET_ACTIVE_BOARD` | `{ boardId }` | Set `ui.activeBoardId`, auto-select default view, clear search/filter/sort |
| `SET_ACTIVE_VIEW` | `{ viewId }` | Set `ui.activeViewId` |
| `SET_SEARCH_QUERY` | `string` | Set `ui.searchQuery` |
| `TOGGLE_SIDEBAR` | (none) | Toggle `ui.sidebarCollapsed` |
| `TOGGLE_ITEM_SELECTED` | `{ itemId }` | Toggle `items[itemId].isSelected` |
| `UPDATE_BOARD_NAME` | `{ boardId, name }` | Set `boards[boardId].name` |
| `UPDATE_BOARD_DESCRIPTION` | `{ boardId, description }` | Set `boards[boardId].description` |
| `SET_ITEM_DETAIL` | `itemId \| null` | Set `ui.itemDetailOpenId` |
| `ADD_UPDATE` | `Update object` | Add new update to `updates` map |
| `SET_SORT_CONDITIONS` | `SortCondition[]` | Set `ui.sortConditions` |
| `SET_FILTER_CONDITIONS` | `FilterCondition[]` | Set `ui.filterConditions` |
| `DUPLICATE_ITEM` | `{ itemId }` | Clone item with new ID, appending " (copy)" to name |

---

## Minimal Inject Example

```json
{
  "action": "set",
  "state": {
    "items": {
      "item-1": {
        "name": "Redesign landing page",
        "columnValues": {
          "col-status-1": { "value": 0 },
          "col-priority-1": { "value": 2 }
        }
      }
    },
    "boards": {
      "board-1": {
        "name": "Engineering Projects"
      }
    }
  }
}
```

### Inject: Add a new item to an existing group

```json
{
  "action": "set",
  "merge": true,
  "state": {
    "items": {
      "item-new-1": {
        "id": "item-new-1",
        "boardId": "board-1",
        "groupId": "group-1",
        "name": "New injected task",
        "columnValues": {
          "col-person-1": { "value": ["user-2"] },
          "col-status-1": { "value": 3 },
          "col-priority-1": { "value": 2 },
          "col-date-1": { "value": "2025-03-15" }
        },
        "subitemIds": [],
        "isSelected": false,
        "createdAt": "2025-01-15T10:00:00Z",
        "updatedAt": "2025-01-15T10:00:00Z",
        "creatorId": "user-1"
      }
    },
    "groups": {
      "group-1": {
        "itemIds": ["item-1", "item-2", "item-3", "item-4", "item-new-1"]
      }
    }
  }
}
```

### Inject: Set up a new board with custom columns

```json
{
  "action": "set",
  "merge": true,
  "state": {
    "boards": {
      "board-5": {
        "id": "board-5",
        "name": "Recruiting Pipeline",
        "description": "Track job candidates",
        "workspaceId": "ws-1",
        "type": "board",
        "isFavorite": false,
        "groupIds": ["group-10"],
        "columnIds": ["col-person-1", "col-status-1", "col-date-1"],
        "views": [
          { "id": "view-7", "type": "table", "name": "Table", "isDefault": true }
        ],
        "createdAt": "2025-01-15T10:00:00Z",
        "updatedAt": "2025-01-15T10:00:00Z"
      }
    },
    "groups": {
      "group-10": {
        "id": "group-10",
        "boardId": "board-5",
        "title": "Active Candidates",
        "color": "#00C875",
        "isCollapsed": false,
        "itemIds": [],
        "position": 0
      }
    },
    "workspaces": {
      "ws-1": {
        "boardIds": ["board-1", "board-2", "board-3", "board-5"]
      }
    }
  }
}
```

---

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed | Detail |
|-------------|---------------------|--------|
| Click status cell and select a label | `items[itemId].columnValues[colId].value` | Integer index changes (e.g., 3 -> 0 for "Not Started" -> "Done") |
| Click people cell and toggle a user | `items[itemId].columnValues[colId].value` | User ID added/removed from array |
| Click date cell and pick a date | `items[itemId].columnValues[colId].value` | Date string changes (e.g., "2025-01-20" -> "2025-02-15") |
| Edit timeline start/end and save | `items[itemId].columnValues[colId].value` | `{start, end}` object updates |
| Click numbers cell and enter value | `items[itemId].columnValues[colId].value` | Number changes (e.g., 5000 -> 7500) |
| Click text cell and type new text | `items[itemId].columnValues[colId].value` | String changes |
| Click dropdown cell and select option | `items[itemId].columnValues[colId].value` | String changes (e.g., "Frontend" -> "Backend") |
| Click tags cell and toggle a tag | `items[itemId].columnValues[colId].value` | Tag ID added/removed from array |
| Double-click item name and edit | `items[itemId].name` | Name string changes |
| Right-click item, select "Delete" | `items[itemId]` removed; `groups[groupId].itemIds` updated | Item key deleted from map |
| Right-click item, select "Duplicate" | New `items[newId]` added; `groups[groupId].itemIds` grows | New item with " (copy)" suffix |
| Right-click item, "Move to Group" | `items[itemId].groupId` changes; source group loses ID, target group gains it | itemIds arrays update |
| Click "+ Add" in group footer | New `items[newId]` added; `groups[groupId].itemIds` grows | New empty item created |
| Click "New Item" in toolbar | New `items[newId]` added to first non-collapsed group | Item added to first available group |
| Click group collapse arrow | `groups[groupId].isCollapsed` | Toggles between `true`/`false` |
| Edit group title | `groups[groupId].title` | Title string changes |
| Edit board name (header input) | `boards[boardId].name` | Name string changes |
| Edit board description | `boards[boardId].description` | Description string changes |
| Click star icon on board | `boards[boardId].isFavorite` | Toggles between `true`/`false` |
| Click view tab (Table/Kanban) | `ui.activeViewId` | View ID changes |
| Navigate to different board (sidebar) | `ui.activeBoardId`, `ui.activeViewId` | Board/view switch, search/filter/sort cleared |
| Toggle sidebar collapse | `ui.sidebarCollapsed` | Toggles between `true`/`false` |
| Type in search box | `ui.searchQuery` | Search string changes |
| Add/modify/remove sort condition | `ui.sortConditions` | Array of `{columnId, direction}` changes |
| Add/modify/remove filter condition | `ui.filterConditions` | Array of `{columnId, condition, value}` changes |
| Click item name to open detail panel | `ui.itemDetailOpenId` | Changes from `null` to item ID |
| Close item detail panel | `ui.itemDetailOpenId` | Changes from item ID to `null` |
| Post an update in item detail panel | `updates[newId]` added | New update object with body text |
| Select item checkbox | `items[itemId].isSelected` | Toggles between `true`/`false` |
| Drag kanban card to different column | `items[itemId].columnValues[statusColId].value` | Status label index changes |

---

## State Persistence

- **localStorage keys**: `monday_mock_state` (or `monday_mock_state_<sid>`) for current state, `monday_mock_initial_state` (or `monday_mock_initial_state_<sid>`) for initial state
- **Server-side files**: `.mock-states/<sid>.json` for current state, `.mock-states/<sid>.initial.json` for initial state
- State is saved to localStorage on every state change via `useEffect`
- Deep merge is used when injecting state with `merge: true`, allowing partial updates
