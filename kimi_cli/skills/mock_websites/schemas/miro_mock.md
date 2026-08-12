# miro_mock Schema

**Deploy order**: 29 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8029)
**Base URL**: `http://172.17.46.46:8029/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | `Dashboard` | Board gallery with sidebar (recent, starred, projects) |
| `/board/:boardId` | `BoardView` | Infinite canvas board editor |
| `/go` | `Go` | State inspection endpoint (JSON view) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Active user profile |
| `team` | object | Team with members list |
| `projects` | array | Projects that organize boards into groups |
| `boards` | array | All boards (the central entity) |
| `boardItems` | object | Keyed by boardId → array of canvas items (sticky notes, shapes, text, frames, connectors) |
| `comments` | object | Keyed by boardId → array of comment threads |
| `tags` | object | Keyed by boardId → array of tags |

---

### `currentUser` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"user_1"` | User ID |
| `name` | string | `"Alex Morgan"` | Display name |
| `email` | string | `"alex.morgan@company.com"` | Email address |
| `avatarUrl` | string\|null | `null` | Avatar image URL |
| `initials` | string | `"AM"` | Two-letter initials for avatar fallback |
| `color` | string | `"#4262ff"` | User color (hex) |
| `role` | string | `"owner"` | Team role (`"owner"`, etc.) |
| `teamId` | string | `"team_1"` | Associated team ID |

---

### `team` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"team_1"` | Team ID |
| `name` | string | `"My Team"` | Team display name |
| `memberCount` | number | `4` | Total member count |
| `members` | array | 4 members | Array of member objects |

#### `team.members[]` (object)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | User ID (e.g. `"user_1"`) |
| `name` | string | Full name |
| `initials` | string | Two-letter initials |
| `avatarUrl` | string\|null | Avatar URL |

**Default members**: `user_1` (Alex Morgan / AM), `user_2` (Jordan Lee / JL), `user_3` (Sam Chen / SC), `user_4` (Taylor Kim / TK)

---

### `projects[]` (object)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Project ID (e.g. `"project_1"`) |
| `name` | string | Project name |
| `teamId` | string | Parent team ID |
| `boardIds` | array&lt;string&gt; | IDs of boards in this project |
| `createdAt` | string (ISO 8601) | Creation timestamp |

**Default projects**:
- `project_1` — "Q1 Planning" (boards: `board_1`, `board_2`)
- `project_2` — "Product Design" (boards: `board_3`)
- `project_3` — "Engineering" (boards: `board_4`)

---

### `boards[]` (object)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Board ID (e.g. `"board_1"`) |
| `name` | string | Board title |
| `description` | string | Board description text |
| `projectId` | string\|null | Parent project ID, or `null` if unassigned |
| `teamId` | string | Parent team ID |
| `createdBy` | string | User ID of creator |
| `createdAt` | string (ISO 8601) | Creation timestamp |
| `modifiedAt` | string (ISO 8601) | Last modification timestamp (auto-updated on item changes) |
| `starred` | boolean | Whether board is starred by current user |
| `thumbnailColor` | string | Hex color for dashboard thumbnail card |
| `viewedAt` | string (ISO 8601) | Last viewed timestamp (updated on board open) |

**Default boards**:
| ID | Name | Project | Starred | Color |
|----|------|---------|---------|-------|
| `board_1` | Sprint Retrospective | project_1 | true | `#7bc86c` |
| `board_2` | Product Roadmap 2025 | project_1 | false | `#4262ff` |
| `board_3` | User Flow Diagrams | project_2 | false | `#ff9d48` |
| `board_4` | Architecture Overview | project_3 | true | `#be88c7` |
| `board_5` | Brainstorming Session | null | false | `#fff9b1` |

---

### `boardItems` (object)

Keyed by board ID. Each value is an array of canvas item objects. All items share these **common fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique item ID |
| `type` | string | One of: `"sticky_note"`, `"shape"`, `"text"`, `"frame"`, `"connector"` |
| `boardId` | string | Parent board ID |
| `x` | number | Center X position on canvas |
| `y` | number | Center Y position on canvas |
| `width` | number | Width in pixels |
| `height` | number | Height in pixels |
| `rotation` | number | Rotation in degrees |
| `parentId` | string\|null | Parent frame ID if inside a frame |
| `locked` | boolean | Whether item is locked from editing |
| `zIndex` | number | Layer order (higher = on top) |
| `createdBy` | string | User ID of creator |
| `createdAt` | string (ISO 8601) | Creation timestamp |
| `modifiedAt` | string (ISO 8601) | Last modification timestamp |

#### Item Type: `sticky_note`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | string | `""` | Sticky note text content |
| `shape` | string | `"square"` | Note shape (currently only `"square"`) |
| `tagIds` | array&lt;string&gt; | `[]` | Array of tag IDs attached to this note |
| `style.fillColor` | string | `"light_yellow"` | Color key from STICKY_COLORS map (see below) |
| `style.textAlign` | string | `"center"` | Horizontal alignment: `"left"`, `"center"`, `"right"` |
| `style.textAlignVertical` | string | `"middle"` | Vertical alignment: `"top"`, `"middle"`, `"bottom"` |
| `style.fontSize` | string | `"auto"` | Font size or `"auto"` |
| `style.bold` | boolean | — | Bold text toggle (set via context toolbar) |

**STICKY_COLORS** (valid `fillColor` keys):
`white`, `light_yellow`, `yellow`, `orange`, `lime`, `yellow_green`, `green`, `cyan`, `light_pink`, `pink`, `violet`, `red`, `light_blue`, `sky_blue`, `blue`, `black`

Hex mapping: `white`→`#ffffff`, `light_yellow`→`#fff9b1`, `yellow`→`#f5d128`, `orange`→`#ff9d48`, `lime`→`#d5f692`, `yellow_green`→`#c9df56`, `green`→`#7bc86c`, `cyan`→`#67c6c0`, `light_pink`→`#f5c8d0`, `pink`→`#e481a8`, `violet`→`#be88c7`, `red`→`#ea6162`, `light_blue`→`#b5c4e3`, `sky_blue`→`#97d5f2`, `blue`→`#6fa0e3`, `black`→`#1a1a1a`

#### Item Type: `shape`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `shapeType` | string | `"rectangle"` | Shape variant (see list below) |
| `content` | string | `""` | Text inside the shape |
| `style.fillColor` | string | `"#ffffff"` | Fill color (hex value) |
| `style.fillOpacity` | number | `1` | Fill opacity (0-1) |
| `style.borderColor` | string | `"#1a1a1a"` | Border color (hex) |
| `style.borderWidth` | number | `2` | Border width in px |
| `style.borderStyle` | string | `"normal"` | `"normal"` (solid), `"dashed"`, `"dotted"` |
| `style.borderOpacity` | number | `1` | Border opacity (0-1) |
| `style.fontFamily` | string | `"arial"` | Font family |
| `style.fontSize` | number | `14` | Font size in px |
| `style.color` | string | `"#1a1a1a"` | Text color (hex) |
| `style.textAlign` | string | `"center"` | Horizontal text alignment |
| `style.textAlignVertical` | string | `"middle"` | Vertical text alignment |

**Supported `shapeType` values**: `rectangle`, `round_rectangle`, `circle`, `triangle`, `rhombus`, `star`, `hexagon`, `pentagon`, `octagon`, `parallelogram`, `cross`, `right_arrow`, `left_arrow`, `can`

#### Item Type: `text`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | string | `""` | Text content |
| `style.fillColor` | string | `"transparent"` | Background (typically transparent) |
| `style.fontFamily` | string | `"arial"` | Font family |
| `style.fontSize` | number | `24` | Font size in px |
| `style.color` | string | `"#1a1a1a"` | Text color (hex) |
| `style.textAlign` | string | `"left"` | Text alignment: `"left"`, `"center"`, `"right"` |
| `style.bold` | boolean | `false` | Bold toggle |
| `style.italic` | boolean | `false` | Italic toggle |
| `style.underline` | boolean | `false` | Underline toggle |
| `style.strikethrough` | boolean | `false` | Strikethrough toggle |

#### Item Type: `frame`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `title` | string | `"Frame"` | Frame label (shown above frame) |
| `style.fillColor` | string | `"#f5f5f5"` | Background fill color (hex) |
| `childrenIds` | array&lt;string&gt; | `[]` | IDs of items contained within this frame |
| `showContent` | boolean | `true` | Whether to show frame contents |

#### Item Type: `connector`

| Field | Type | Description |
|-------|------|-------------|
| `start` | object | Start connection point |
| `start.itemId` | string | ID of the item the connector starts from |
| `start.position` | object | `{x, y}` normalized position (0-1) on the item |
| `start.snapTo` | string | Side snap: `"left"`, `"right"`, `"top"`, `"bottom"` |
| `end` | object | End connection point (same shape as `start`) |
| `end.itemId` | string | ID of the item the connector ends at |
| `end.position` | object | `{x, y}` normalized position |
| `end.snapTo` | string | Side snap |
| `shape` | string | Connector routing: `"straight"`, `"elbowed"`, `"curved"` |
| `style.strokeColor` | string | Line color (hex), default `"#000000"` |
| `style.strokeWidth` | number | Line width in px, default `2` |
| `style.strokeStyle` | string | `"normal"` (solid), `"dashed"`, `"dotted"` |
| `style.startStrokeCap` | string | Start cap: `"none"`, `"stealth"`, `"filled_triangle"`, `"arrow"` |
| `style.endStrokeCap` | string | End cap (same values as start) |
| `captions` | array | Labels on the connector line |
| `captions[].content` | string | Caption text |
| `captions[].position` | number | Position along line (0-1), typically `0.5` |
| `captions[].textAlignVertical` | string | Vertical alignment of caption |

---

### `comments` (object)

Keyed by board ID → array of comment objects.

#### `comments[boardId][]` (object)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Comment ID (e.g. `"comment_1"`) |
| `boardId` | string | Parent board ID |
| `x` | number | X position on canvas |
| `y` | number | Y position on canvas |
| `resolved` | boolean | Whether the comment thread is resolved |
| `threads` | array | Array of thread messages |

#### `comments[].threads[]` (object)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Thread message ID (e.g. `"tm_1"`) |
| `authorId` | string | User ID of author |
| `authorName` | string | Display name of author |
| `content` | string | Message text |
| `createdAt` | string (ISO 8601) | Timestamp |

---

### `tags` (object)

Keyed by board ID → array of tag objects.

#### `tags[boardId][]` (object)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Tag ID (e.g. `"tag_1"`) |
| `boardId` | string | Parent board ID |
| `title` | string | Tag label text |
| `color` | string | Color name: `"red"`, `"green"`, `"yellow"`, etc. |

**Default tags** (on `board_1`):
- `tag_1` — "High Priority" (red)
- `tag_2` — "Quick Win" (green)
- `tag_3` — "Blocked" (yellow)

---

## Reducer Actions (state transitions)

| Action Type | Payload | Effect |
|-------------|---------|--------|
| `SET_STATE` | `{payload: entireState}` | Replace entire state |
| `ADD_BOARD` | `{id?, name?, projectId?, thumbnailColor?}` | Adds a new board; initializes empty `boardItems`, `comments`, `tags` for it |
| `UPDATE_BOARD` | `{id, changes: {...}}` | Merges changes into board; auto-updates `modifiedAt` |
| `DELETE_BOARD` | `{id}` | Removes board, its items, comments, tags; updates project `boardIds` |
| `STAR_BOARD` | `{id}` | Toggles `starred` boolean on the board |
| `DUPLICATE_BOARD` | `{id}` | Deep-copies board with all items (remapped IDs), adds " (copy)" suffix |
| `MOVE_BOARD_TO_PROJECT` | `{boardId, projectId}` | Moves board between projects; updates board's `projectId` and project `boardIds` |
| `ADD_ITEM` | `{boardId, item}` | Adds canvas item to board; auto-sets `createdAt`/`modifiedAt`; updates board `modifiedAt` |
| `UPDATE_ITEM` | `{boardId, itemId, changes}` | Merges changes into item; updates `modifiedAt` |
| `DELETE_ITEM` | `{boardId, itemId}` | Removes item from board; updates board `modifiedAt` |
| `MOVE_ITEM` | `{boardId, itemId, x, y}` | Updates item position; updates `modifiedAt` |
| `RESIZE_ITEM` | `{boardId, itemId, width, height}` | Updates item dimensions; updates `modifiedAt` |

---

## Default Board Items Summary

### board_1 (Sprint Retrospective)
- 3 frames: `frame_1` (What went well), `frame_2` (Improvements needed), `frame_3` (Action items)
- 8 sticky notes: `sn_1`-`sn_8` (distributed across frames)
- 1 text: `text_1` ("Sprint 23 Retrospective" title)
- 1 connector: `conn_1` (frame_2 → frame_3, elbowed, caption "leads to")

### board_2 (Product Roadmap 2025)
- Empty (no items)

### board_3 (User Flow Diagrams)
- 3 shapes: `shape_flow_1` (Landing Page), `shape_flow_2` (Sign Up), `shape_flow_3` (Dashboard) — all round_rectangle

### board_4 (Architecture Overview)
- 5 shapes: `shape_1` (Frontend), `shape_2` (API Gateway), `shape_3` (Auth Service), `shape_4` (User Service), `shape_5` (PostgreSQL)
- 5 connectors: `conn_2`-`conn_6` (connecting architecture components)
- 1 text: `text_arch` ("System Architecture" title)

### board_5 (Brainstorming Session)
- 5 sticky notes: `sn_b5_1`-`sn_b5_5` (scattered with slight rotations, various colors)

---

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8029/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "user_1",
          "name": "Alex Morgan",
          "email": "alex.morgan@company.com",
          "avatarUrl": null,
          "initials": "AM",
          "color": "#4262ff",
          "role": "owner",
          "teamId": "team_1"
        },
        "team": {
          "id": "team_1",
          "name": "My Team",
          "memberCount": 2,
          "members": [
            {"id": "user_1", "name": "Alex Morgan", "initials": "AM", "avatarUrl": null},
            {"id": "user_2", "name": "Jordan Lee", "initials": "JL", "avatarUrl": null}
          ]
        },
        "projects": [
          {"id": "project_1", "name": "Q1 Planning", "teamId": "team_1", "boardIds": ["board_1"], "createdAt": "2025-01-15T10:00:00Z"}
        ],
        "boards": [
          {
            "id": "board_1",
            "name": "Sprint Retrospective",
            "description": "Team retro",
            "projectId": "project_1",
            "teamId": "team_1",
            "createdBy": "user_1",
            "createdAt": "2025-02-01T09:00:00Z",
            "modifiedAt": "2025-02-15T14:30:00Z",
            "starred": false,
            "thumbnailColor": "#7bc86c",
            "viewedAt": "2025-02-15T14:30:00Z"
          }
        ],
        "boardItems": {
          "board_1": [
            {
              "id": "sn_1",
              "type": "sticky_note",
              "boardId": "board_1",
              "content": "Great sprint velocity",
              "x": 200,
              "y": 250,
              "width": 199,
              "height": 199,
              "rotation": 0,
              "parentId": null,
              "locked": false,
              "zIndex": 10,
              "shape": "square",
              "style": {"fillColor": "green", "textAlign": "center", "textAlignVertical": "middle", "fontSize": "auto"},
              "tagIds": [],
              "createdBy": "user_1",
              "createdAt": "2025-02-01T09:15:00Z",
              "modifiedAt": "2025-02-01T09:15:00Z"
            }
          ]
        },
        "comments": {"board_1": []},
        "tags": {"board_1": []}
      }
    }
  }
}
```

---

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Create new board from dashboard | `boards` array grows by 1; `boardItems[newId]`, `comments[newId]`, `tags[newId]` initialized to `[]` |
| Rename board (dashboard or top bar) | `boards[i].name` updated; `boards[i].modifiedAt` updated |
| Star/unstar board | `boards[i].starred` toggled |
| Delete board | `boards` shrinks; `boardItems[boardId]`, `comments[boardId]`, `tags[boardId]` removed; `projects[].boardIds` updated |
| Duplicate board | `boards` grows; `boardItems[newId]` deep-copied with new IDs |
| Move board to project | `boards[i].projectId` changed; source/target `projects[].boardIds` updated |
| Open board | `boards[i].viewedAt` updated |
| Add sticky note (click with tool) | `boardItems[boardId]` grows by 1 (type=`"sticky_note"`) |
| Add text (click with tool) | `boardItems[boardId]` grows by 1 (type=`"text"`) |
| Add shape (click with tool) | `boardItems[boardId]` grows by 1 (type=`"shape"`) |
| Add frame (click with tool) | `boardItems[boardId]` grows by 1 (type=`"frame"`) |
| Edit item content (double-click) | `boardItems[boardId][i].content` or `.title` updated |
| Move item (drag) | `boardItems[boardId][i].x` and `.y` updated |
| Resize item (drag handle) | `boardItems[boardId][i].width` and `.height` updated |
| Delete item(s) | `boardItems[boardId]` shrinks |
| Change sticky note color | `boardItems[boardId][i].style.fillColor` changed |
| Toggle bold | `boardItems[boardId][i].style.bold` toggled |
| Change text alignment | `boardItems[boardId][i].style.textAlign` changed |
| Lock/unlock item | `boardItems[boardId][i].locked` toggled |
| Bring to front / Send to back | `boardItems[boardId][i].zIndex` updated |
| Copy + paste items | `boardItems[boardId]` grows (new items with offset position) |
| Duplicate items (Ctrl+D) | `boardItems[boardId]` grows (copies with +20px offset) |
| Change shape border style | `boardItems[boardId][i].style.borderStyle` changed |

## State Diff Format

The `/go` endpoint returns `state_diff` with this structure:

```json
{
  "boards": {
    "added": [...],
    "modified": [{"id": "board_1", "changes": {"name": {"old": "...", "new": "..."}}}],
    "removed": [...]
  },
  "boardItems": {
    "board_1": {
      "added": [...],
      "modified": [{"id": "sn_1", "changes": {"content": {"old": "...", "new": "..."}}}],
      "removed": [...]
    }
  },
  "comments": {
    "board_1": {"added": [...], "modified": [...], "removed": [...]}
  },
  "tags": {
    "board_1": {"added": [...], "modified": [...], "removed": [...]}
  }
}
```

Each section only appears if there are actual changes.
