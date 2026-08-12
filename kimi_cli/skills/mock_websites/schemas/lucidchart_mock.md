# lucidchart_mock Schema

**Deploy order**: 27 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8027)
**Base URL**: `http://172.17.46.46:8027/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}` (optionally add `"merge":true`)
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State inspect**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{success, files: [{original_name, stored_name, size, content_type, url}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `Dashboard` | Document dashboard with folder sidebar, template picker, document grid/list |
| `/editor/:documentId` | `Editor` | Full diagramming editor with canvas, shape panel, toolbar, right sidebar |
| `/go` | `Go` | State inspection endpoint (JSON output of initial_state, current_state, state_diff) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Logged-in user: `{id, name, email, avatar, avatarColor}` |
| `users` | array | Other users: `[{id, name, email, avatar, avatarColor}]` |
| `folders` | array | Folder hierarchy: `[{id, name, parentId, type, createdAt, updatedAt}]` |
| `documents` | array | Diagram documents: `[{id, title, folderId, ownerId, starred, status, thumbnailUrl, createdAt, updatedAt, lastOpenedAt, sharedWith[], pageOrder[]}]` |
| `pages` | array | Pages within documents: `[{id, documentId, name, order, width, height, gridVisible, gridSize, backgroundColor}]` |
| `shapes` | array | Diagram shapes/objects: `[{id, pageId, type, category, x, y, width, height, rotation, text, fontSize, fontFamily, fontWeight, fontStyle, textAlign, textColor, fillColor, borderColor, borderWidth, borderStyle, opacity, locked, visible, zIndex, groupId}]` |
| `connectors` | array | Lines connecting shapes: `[{id, pageId, sourceShapeId, sourcePoint, targetShapeId, targetPoint, waypoints[], lineStyle, lineWidth, lineColor, sourceArrow, targetArrow, label, labelPosition, routingType, zIndex}]` |
| `comments` | array | Comments on shapes/pages: `[{id, pageId, shapeId, x, y, authorId, authorName, text, resolved, createdAt, replies[]}]` |
| `templates` | array | Available document templates: `[{id, name, category, icon, description}]` |
| `ui` | object | UI state (see below) |

### `currentUser` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"user-1"` | User identifier |
| `name` | string | `"Alex Johnson"` | Display name |
| `email` | string | `"alex.johnson@company.com"` | Email address |
| `avatar` | string | `"AJ"` | Avatar initials |
| `avatarColor` | string | `"#4A86C8"` | Avatar background color |

### `users[]` Item

Same fields as `currentUser`. Default: 3 users (user-2 Sarah Smith, user-3 Mike Chen, user-4 Emily Davis).

### `folders[]` Item

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"folder-root"` | Folder identifier |
| `name` | string | `"My Documents"` | Folder display name |
| `parentId` | string\|null | `null` | Parent folder ID (null = root level) |
| `type` | string | `"my_documents"` | Folder type: `"my_documents"`, `"shared"`, `"team"`, `"trash"` |
| `createdAt` | string (ISO) | `"2025-01-01T00:00:00Z"` | Creation timestamp |
| `updatedAt` | string (ISO) | `"2025-03-08T00:00:00Z"` | Last update timestamp |

Default root folders: `folder-root` (My Documents), `folder-shared` (Shared with Me), `folder-team` (Team Folders), `folder-trash` (Trash). Sub-folders: `folder-1` (Marketing Diagrams), `folder-2` (Engineering), `folder-3` (Q1 Planning).

### `documents[]` Item

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"doc-1"` | Document identifier |
| `title` | string | `"Sales Process Flowchart"` | Document title |
| `folderId` | string | `"folder-root"` | Parent folder ID |
| `ownerId` | string | `"user-1"` | Owner user ID |
| `starred` | boolean | `true` | Whether document is starred |
| `status` | string | `"draft"` | Status: `"draft"` or `"published"` |
| `thumbnailUrl` | string\|null | `null` | Thumbnail image URL |
| `createdAt` | string (ISO) | `"2025-01-15T10:00:00Z"` | Creation timestamp |
| `updatedAt` | string (ISO) | `"2025-03-05T16:45:00Z"` | Last update timestamp |
| `lastOpenedAt` | string (ISO) | `"2025-03-08T11:00:00Z"` | Last opened timestamp |
| `sharedWith` | array | `[{userId, permission}]` | Sharing permissions |
| `pageOrder` | array | `["page-1", "page-2"]` | Ordered page IDs |

`sharedWith[]` entries: `{userId: string, permission: "view"|"edit"}`.

Default: 9 documents (doc-1 through doc-8, doc-blank).

### `pages[]` Item

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"page-1"` | Page identifier |
| `documentId` | string | `"doc-1"` | Parent document ID |
| `name` | string | `"Page 1"` | Page display name |
| `order` | number | `0` | Page order index |
| `width` | number | `1200` | Canvas width in pixels |
| `height` | number | `900` | Canvas height in pixels |
| `gridVisible` | boolean | `true` | Whether grid is displayed |
| `gridSize` | number | `20` | Grid cell size in pixels |
| `backgroundColor` | string | `"#FFFFFF"` | Canvas background color |

Default: 10 pages (one per document, doc-1 has 2 pages).

### `shapes[]` Item

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"shape-1"` | Shape identifier |
| `pageId` | string | `"page-1"` | Parent page ID |
| `type` | string | `"process"` | Shape type (see shape types below) |
| `category` | string | `"flowchart"` | Category: `"standard"`, `"flowchart"`, `"shapes"` |
| `x` | number | `440` | X position on canvas |
| `y` | number | `160` | Y position on canvas |
| `width` | number | `200` | Shape width in pixels |
| `height` | number | `70` | Shape height in pixels |
| `rotation` | number | `0` | Rotation angle in degrees |
| `text` | string | `"Start"` | Text content inside shape |
| `fontSize` | number | `13` | Font size in pixels |
| `fontFamily` | string | `"Liberation Sans"` | Font family |
| `fontWeight` | string | `"normal"` | Font weight: `"normal"` or `"bold"` |
| `fontStyle` | string | `"normal"` | Font style: `"normal"` or `"italic"` |
| `textAlign` | string | `"center"` | Text alignment: `"left"`, `"center"`, `"right"` |
| `textColor` | string | `"#333333"` | Text color |
| `fillColor` | string | `"#FFFFFF"` | Shape fill color |
| `borderColor` | string | `"#333333"` | Border color |
| `borderWidth` | number | `2` | Border width in pixels |
| `borderStyle` | string | `"solid"` | Border style: `"solid"`, `"dashed"`, `"dotted"` |
| `opacity` | number | `1` | Opacity (0 to 1) |
| `locked` | boolean | `false` | Whether shape is locked from editing |
| `visible` | boolean | `true` | Whether shape is visible |
| `zIndex` | number | `1` | Z-order layer index |
| `groupId` | string\|null | `null` | Group identifier (for grouped shapes) |

**Shape types**: `text`, `rectangle`, `sticky_note`, `container`, `line` (standard); `process`, `decision`, `terminator`, `data`, `document_shape`, `preparation`, `connector_shape`, `merge` (flowchart); `triangle`, `circle`, `diamond`, `hexagon`, `star_5`, `cloud` (shapes).

Default: 8 shapes on page-1 forming a sales process flowchart.

### `connectors[]` Item

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"conn-1"` | Connector identifier |
| `pageId` | string | `"page-1"` | Parent page ID |
| `sourceShapeId` | string | `"shape-1"` | Source shape ID |
| `sourcePoint` | string | `"bottom"` | Source attachment point: `"top"`, `"bottom"`, `"left"`, `"right"` |
| `targetShapeId` | string | `"shape-2"` | Target shape ID |
| `targetPoint` | string | `"top"` | Target attachment point: `"top"`, `"bottom"`, `"left"`, `"right"` |
| `waypoints` | array | `[]` | Intermediate routing points |
| `lineStyle` | string | `"solid"` | Line style: `"solid"`, `"dashed"`, `"dotted"` |
| `lineWidth` | number | `2` | Line width in pixels |
| `lineColor` | string | `"#333333"` | Line color |
| `sourceArrow` | string | `"none"` | Source arrow type: `"none"`, `"arrow"` |
| `targetArrow` | string | `"arrow"` | Target arrow type: `"none"`, `"arrow"` |
| `label` | string | `"Pick"` | Text label on the connector |
| `labelPosition` | number | `0.5` | Label position along connector (0 to 1) |
| `routingType` | string | `"orthogonal"` | Routing: `"orthogonal"`, `"straight"`, `"curved"` |
| `zIndex` | number | `0` | Z-order layer index |

Default: 7 connectors on page-1 linking the flowchart shapes.

### `comments[]` Item

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"comment-1"` | Comment identifier |
| `pageId` | string | `"page-1"` | Parent page ID |
| `shapeId` | string\|null | `"shape-4"` | Associated shape ID (null for page-level comment) |
| `x` | number\|null | `null` | X position (for positioned comments) |
| `y` | number\|null | `null` | Y position (for positioned comments) |
| `authorId` | string | `"user-2"` | Comment author user ID |
| `authorName` | string | `"Sarah Smith"` | Comment author display name |
| `text` | string | `"Can this be larger?"` | Comment text content |
| `resolved` | boolean | `false` | Whether comment is resolved |
| `createdAt` | string (ISO) | `"2025-03-05T10:30:00Z"` | Creation timestamp |
| `replies` | array | `[{id, authorId, authorName, text, createdAt}]` | Reply thread |

`replies[]` entries: `{id: string, authorId: string, authorName: string, text: string, createdAt: string}`.

Default: 3 comments (2 unresolved, 1 resolved) with associated replies.

### `templates[]` Item

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"template-flowchart"` | Template identifier |
| `name` | string | `"Flowchart"` | Display name |
| `category` | string | `"flowchart"` | Category: `"general"`, `"flowchart"`, `"org"`, `"brainstorm"`, `"education"`, `"business"` |
| `icon` | string | `"flowchart"` | Icon key: `"blank"`, `"flowchart"`, `"org-chart"`, `"mind-map"`, `"education"`, `"business"` |
| `description` | string | `"Basic flowchart..."` | Template description |

Default: 6 templates (blank, flowchart, org chart, mind map, education, business analysis).

### `ui` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `activeFolderId` | string | `"folder-root"` | Currently selected folder in dashboard sidebar. Special values: `"recent"`, `"starred"`, `"search"` |
| `activeDocumentId` | string\|null | `null` | Currently open document (set when entering editor) |
| `activePageId` | string\|null | `null` | Currently active page in editor |
| `selectedShapeIds` | array | `[]` | IDs of currently selected shapes/connectors |
| `dashboardViewMode` | string | `"grid"` | Dashboard layout: `"grid"` or `"list"` |
| `dashboardSearchQuery` | string | `""` | Search query text in dashboard |
| `rightPanelTab` | string\|null | `null` | Active right panel in editor: `null`, `"settings"`, `"comments"`, `"layers"`, `"history"` |
| `zoomLevel` | number | `100` | Canvas zoom percentage. Values: `25`, `50`, `75`, `100`, `125`, `150`, `200` |
| `shapePanelSearchQuery` | string | `""` | Shape panel search text |
| `shapePanelSections` | object | `{shapesInUse:true, standard:true, flowchart:true, shapes:true}` | Collapsible shape panel section states |

## State Diff Tracking

The `/go` endpoint returns `state_diff` computed by comparing `initial_state` vs `current_state`. The diff is structured as:

- **Array fields** (`documents`, `shapes`, `connectors`, `comments`, `pages`, `folders`): diff by ID with `{added[], deleted[], modified[]}`. Each `modified` entry contains `{id, changes: {field: {old, new}}}`.
- **`ui` object**: field-level diff as `{field: {old, new}}`.

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8027/?sid=task001",
    "inject_state": true,
    "state_content": {"action": "set", "state": {
      "currentUser": {"id": "user-1", "name": "Alex Johnson", "email": "alex@company.com", "avatar": "AJ", "avatarColor": "#4A86C8"},
      "users": [{"id": "user-2", "name": "Sarah Smith", "email": "sarah@company.com", "avatar": "SS", "avatarColor": "#E74C3C"}],
      "folders": [
        {"id": "folder-root", "name": "My Documents", "parentId": null, "type": "my_documents", "createdAt": "2025-01-01T00:00:00Z", "updatedAt": "2025-03-08T00:00:00Z"},
        {"id": "folder-shared", "name": "Shared with Me", "parentId": null, "type": "shared", "createdAt": "2025-01-01T00:00:00Z", "updatedAt": "2025-03-08T00:00:00Z"},
        {"id": "folder-trash", "name": "Trash", "parentId": null, "type": "trash", "createdAt": "2025-01-01T00:00:00Z", "updatedAt": "2025-03-08T00:00:00Z"}
      ],
      "documents": [{"id": "doc-1", "title": "Test Diagram", "folderId": "folder-root", "ownerId": "user-1", "starred": false, "status": "draft", "thumbnailUrl": null, "createdAt": "2025-03-01T00:00:00Z", "updatedAt": "2025-03-01T00:00:00Z", "lastOpenedAt": "2025-03-01T00:00:00Z", "sharedWith": [], "pageOrder": ["page-1"]}],
      "pages": [{"id": "page-1", "documentId": "doc-1", "name": "Page 1", "order": 0, "width": 1200, "height": 900, "gridVisible": true, "gridSize": 20, "backgroundColor": "#FFFFFF"}],
      "shapes": [],
      "connectors": [],
      "comments": [],
      "templates": [{"id": "template-blank", "name": "Blank", "category": "general", "icon": "blank", "description": "Start with an empty canvas"}],
      "ui": {"activeFolderId": "folder-root", "activeDocumentId": null, "activePageId": null, "selectedShapeIds": [], "dashboardViewMode": "grid", "dashboardSearchQuery": "", "rightPanelTab": null, "zoomLevel": 100, "shapePanelSearchQuery": "", "shapePanelSections": {"shapesInUse": true, "standard": true, "flowchart": true, "shapes": true}}
    }}
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Create new document (from dashboard) | `documents[]` gains new entry with `status:"draft"`, `pages[]` gains matching page |
| Star/unstar document | `documents[i].starred` toggled |
| Rename document (dashboard context menu or editor title) | `documents[i].title` updated |
| Duplicate document (dashboard context menu) | `documents[]` gains new entry with title `"... (Copy)"`, `pages[]` gains cloned pages |
| Delete document (move to trash) | `documents[i].folderId` → `"folder-trash"` |
| Permanently delete document | `documents[]` loses entry |
| Restore document from trash | `documents[i].folderId` → `"folder-root"` |
| Switch dashboard view mode | `ui.dashboardViewMode` → `"grid"` or `"list"` |
| Search documents | `ui.dashboardSearchQuery` updated, `ui.activeFolderId` → `"search"` |
| Navigate folders | `ui.activeFolderId` changes |
| Create folder | `folders[]` gains new entry |
| Open document in editor | `ui.activeDocumentId` set, `ui.activePageId` set to first page |
| Add shape to canvas (click or drag-and-drop) | `shapes[]` gains new entry, `ui.selectedShapeIds` set to new shape |
| Move shape(s) on canvas | `shapes[i].x`, `shapes[i].y` updated |
| Edit shape text (double-click) | `shapes[i].text` updated |
| Change shape fill/border color | `shapes[i].fillColor`, `shapes[i].borderColor` updated |
| Change font properties | `shapes[i].fontFamily`, `shapes[i].fontSize`, `shapes[i].fontWeight`, `shapes[i].fontStyle` updated |
| Change border style/width | `shapes[i].borderStyle`, `shapes[i].borderWidth` updated |
| Lock/unlock shape | `shapes[i].locked` toggled |
| Toggle shape visibility | `shapes[i].visible` toggled |
| Delete shape(s) | `shapes[]` loses entries, related `connectors[]` entries also removed |
| Select shapes | `ui.selectedShapeIds` updated |
| Create connector (drag between shapes) | `connectors[]` gains new entry |
| Delete connector | `connectors[]` loses entry |
| Add page | `pages[]` gains new entry, `documents[i].pageOrder` updated |
| Edit page settings (name, dimensions, grid) | `pages[i].name`, `pages[i].width`, `pages[i].height`, `pages[i].gridVisible`, `pages[i].gridSize` updated |
| Switch active page | `ui.activePageId` changes |
| Zoom in/out | `ui.zoomLevel` changes (25, 50, 75, 100, 125, 150, 200) |
| Add comment | `comments[]` gains new entry |
| Resolve comment | `comments[i].resolved` → `true` |
| Share document (add user) | `documents[i].sharedWith[]` gains entry `{userId, permission}` |
| Remove share | `documents[i].sharedWith[]` loses entry |
| Make a Copy (editor File menu) | `documents[]`, `pages[]`, `shapes[]`, `connectors[]`, `comments[]` all gain cloned entries |
| Toggle right panel tab | `ui.rightPanelTab` changes (`null`, `"settings"`, `"comments"`, `"layers"`, `"history"`) |
| Undo/Redo | `shapes[]` and `connectors[]` revert/reapply, `ui.selectedShapeIds` restored |

## Default Data Summary

- **1 current user** (user-1 Alex Johnson)
- **3 other users** (user-2 Sarah Smith, user-3 Mike Chen, user-4 Emily Davis)
- **7 folders** (4 root: My Documents, Shared with Me, Team Folders, Trash; 3 sub-folders: Marketing Diagrams, Engineering, Q1 Planning)
- **9 documents** (doc-1 through doc-8, doc-blank; 3 starred, 3 published, various sharing)
- **10 pages** (one per document, doc-1 has 2 pages)
- **8 shapes** on page-1 (flowchart: 1 start terminator, 4 processes, 1 decision, 1 end terminator, 1 shipping step)
- **7 connectors** on page-1 (linking the flowchart shapes with labels "Pick", "Produce", "Order")
- **3 comments** on page-1 (2 unresolved, 1 resolved, with reply threads)
- **6 templates** (Blank, Flowchart, Org Chart, Mind Map, Education, Business Analysis)
