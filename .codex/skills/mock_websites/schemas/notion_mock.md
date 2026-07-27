# notion_mock Schema

**Deploy order**: 35 (alphabetical among all *_mock dirs, BASE_PORT=8000 -> port 8034 zero-indexed)
**Base URL**: `http://172.17.46.46:<dynamic-port>/` (port assigned by OS; check process or use `vite --port` override)
**Go Endpoint**: `GET /go?sid=<sid>` -> `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}` (or `"merge":true` to deep-merge)
**State endpoint**: `GET /state?sid=<sid>` -> `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Current user: `{id, name, email, avatar}` |
| `workspace` | object | Workspace info: `{id, name, icon, members: string[]}` |
| `pages` | object (map) | All pages keyed by page ID. Each page is a regular page or database (see below) |
| `blocks` | object (map) | All content blocks keyed by block ID |
| `trash` | array | Trashed pages: `[{id, page, deletedDate, parentId}]` |
| `comments` | object (map) | Comments keyed by comment ID: `{id, resolved, ...}` |
| `settings` | object | `{appearance: "light"|"dark", startWeekMonday: bool, fontSize: "default"|...}` |
| `notifications` | array | `[{id, type, userId, pageTitle, pageId, message, timestamp, read}]` |
| `pageOrder` | array | Ordered list of root-level page IDs |
| `focusBlockId` | string\|null | Transient: currently focused block ID |

### Page object (regular)
```
{id, title, icon, cover, parentId, blockIds: string[], favorite: bool, createdDate, lastEditedDate, properties: {}}
```

### Page object (database, type="database")
```
{id, title, icon, cover, parentId, type:"database", viewType:"table"|"board"|"gallery",
 properties: [{id, name, type, options?}],
 views: [{id, name, type, filters, sorts, groupBy, visibleProperties}],
 items: string[],   // ordered list of child page IDs (database rows)
 blockIds: string[], favorite: bool, createdDate}
```

### Block object
```
{id, type, content, properties: {}, createdDate, lastEditedDate}
```
Block types: `text`, `heading-1/2/3`, `bullet-list`, `numbered-list`, `todo`, `quote`, `callout`, `divider`, `image`, `code`, `toggle`, `table`

### Database property types
`text`, `select`, `multi-select`, `person`, `date`, `checkbox`, `status`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:<port>/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {"id": "user-1", "name": "Sarah Chen", "email": "sarah.chen@company.com", "avatar": ""},
        "workspace": {"id": "ws-1", "name": "Sarah's Workspace", "icon": "", "members": ["user-1"]},
        "pages": {
          "page-001": {
            "id": "page-001",
            "title": "My Page",
            "icon": "",
            "cover": null,
            "parentId": null,
            "blockIds": [],
            "favorite": false,
            "createdDate": "2025-01-01T00:00:00.000Z",
            "properties": {}
          }
        },
        "blocks": {},
        "trash": [],
        "comments": {},
        "settings": {"appearance": "light", "startWeekMonday": false, "fontSize": "default"},
        "notifications": [],
        "pageOrder": ["page-001"]
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User action | State field(s) that change |
|-------------|---------------------------|
| Create new page | `pages` gains new entry; `pageOrder` gains new ID (if root page) |
| Rename page | `pages[id].title`, `pages[id].lastEditedDate` |
| Toggle page favorite | `pages[id].favorite` |
| Add/edit block | `blocks[id]` updated/added; `pages[id].blockIds` order may change |
| Delete block | `blocks[id]` removed; `pages[id].blockIds` shrinks |
| Move block | `pages[id].blockIds` reordered |
| Trash page | `pages[id]` removed; `trash` gains `{id, page, deletedDate}`; `pageOrder` shrinks |
| Restore from trash | `pages[id]` re-added; `trash` entry removed |
| Permanent delete | `trash` entry removed; associated `blocks` removed |
| Add database item | `pages` gains new item page; `pages[dbId].items` grows |
| Update database item property | `pages[itemId].properties[propId]` updated |
| Add/update/delete DB view | `pages[dbId].views` array modified |
| Add/update/delete DB property | `pages[dbId].properties` array modified |
| Change settings | `settings.appearance`, `settings.startWeekMonday`, or `settings.fontSize` |
| Update workspace | `workspace.name` or `workspace.icon` |
| Reorder sidebar pages | `pageOrder` reordered |
| Mark notification read | `notifications[n].read` becomes `true` |
| Add comment | `comments[id]` gains new entry |
| Resolve/unresolve comment | `comments[id].resolved` toggled |
