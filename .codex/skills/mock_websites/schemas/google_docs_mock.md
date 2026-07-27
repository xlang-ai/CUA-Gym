# google_docs_mock Schema

**Deploy order**: 18 (alphabetical among all *_mock dirs)
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{success, files: [...]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Active user → `User` object |
| `users` | array | List of all known users → `User[]` |
| `documents` | object | Map of all documents keyed by doc ID → `Document` objects |
| `comments` | array | List of all comments across documents → `Comment[]` |
| `ui` | object | UI state flags → `UIState` object |

### User

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique user ID (e.g., `"user-1"`) |
| `name` | string | Full display name |
| `email` | string | Email address |
| `avatar` | string | Avatar image URL |

### Document (values in `documents` map)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique document ID (e.g., `"doc-1"`, `"doc-1740000000000"`) |
| `title` | string | Document title |
| `content` | string | HTML content (TipTap/ProseMirror-generated) |
| `ownerId` | string | User ID of the document owner |
| `starred` | boolean | Whether the document is starred by the current user |
| `created` | string | ISO 8601 timestamp of creation (e.g., `"2025-01-15T10:00:00Z"`) |
| `updated` | string | ISO 8601 timestamp of last modification |
| `sharedWith` | array | List of share entries → `ShareEntry[]` |
| `linkSharing` | object | Link sharing settings → `LinkSharing` |

### ShareEntry (items in `Document.sharedWith`)

| Field | Type | Description |
|-------|------|-------------|
| `userId` | string | User ID of the person the doc is shared with |
| `permission` | string | `"viewer"` \| `"commenter"` \| `"editor"` |

### LinkSharing (nested in `Document.linkSharing`)

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Whether anyone with the link can access the document |
| `permission` | string | Permission for link-based access: `"viewer"` \| `"commenter"` \| `"editor"` |

### Comment (items in `comments` array)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique comment ID (e.g., `"comment-1"`, `"comment-1740000000000"`) |
| `docId` | string | ID of the document this comment belongs to |
| `userId` | string | User ID of the comment author |
| `content` | string | Comment text |
| `resolved` | boolean | Whether the comment is resolved |
| `created` | string | ISO 8601 timestamp of creation |
| `quotedText` | string | Selected text from the document the comment refers to (may be empty `""`) |
| `replies` | array | List of reply entries → `Reply[]` |

### Reply (items in `Comment.replies`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique reply ID (e.g., `"reply-1"`, `"reply-1740000000000"`) |
| `userId` | string | User ID of the reply author |
| `content` | string | Reply text |
| `created` | string | ISO 8601 timestamp of creation |

### UIState

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `currentDocId` | string\|null | `null` | ID of the currently open document (set when editing, `null` on doc list) |
| `sidebarOpen` | boolean | `false` | Whether the comments sidebar is visible |
| `sidebarTab` | string | `"comments"` | Active sidebar tab |
| `shareDialogOpen` | boolean | `false` | Whether the share dialog is open |
| `findReplaceOpen` | boolean | `false` | Whether the Find & Replace bar is open |
| `viewMode` | string | `"editing"` | Editor view mode: `"editing"` \| `"viewing"` \| `"suggesting"` |
| `zoom` | number | `100` | Editor zoom level (50-200) |
| `documentListView` | string | `"grid"` | Document list display mode: `"grid"` \| `"list"` |
| `searchQuery` | string | `""` | Current search query on the document list page |

### Default User IDs
- `user-1` (Demo User, currentUser) — `demo@example.com`
- `user-2` (Alice Chen) — `alice@example.com`
- `user-3` (Bob Smith) — `bob@example.com`

### Default Document IDs
- `doc-1` — "Project Proposal" (owned by `user-1`, starred, shared with `user-2` as editor, `user-3` as viewer)
- `doc-2` — "Meeting Notes - Feb 2025" (owned by `user-1`, link sharing enabled)
- `doc-3` — "API Documentation" (owned by `user-2`, shared with `user-1` as editor, `user-3` as commenter)
- `doc-4` — "Weekly Status Report" (owned by `user-1`, starred, no sharing)
- `doc-5` — "Onboarding Guide" (owned by `user-3`, link sharing enabled, shared with `user-1` and `user-2` as viewers)

### Default Comment IDs
- `comment-1` — on `doc-1` by `user-2`, unresolved, has 1 reply (`reply-1`)
- `comment-2` — on `doc-1` by `user-3`, unresolved, no replies
- `comment-3` — on `doc-2` by `user-2`, resolved, no replies

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "https://cua-gym-google-docs.xlang.ai/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "user-1",
          "name": "Demo User",
          "email": "demo@example.com",
          "avatar": "https://picsum.photos/100/100?random=user1"
        },
        "users": [
          {"id": "user-1", "name": "Demo User", "email": "demo@example.com", "avatar": "https://picsum.photos/100/100?random=user1"},
          {"id": "user-2", "name": "Alice Chen", "email": "alice@example.com", "avatar": "https://picsum.photos/100/100?random=user2"}
        ],
        "documents": {
          "doc-1": {
            "id": "doc-1",
            "title": "Task Document",
            "content": "<h1>Task Document</h1><p>Edit this document as instructed.</p>",
            "ownerId": "user-1",
            "starred": false,
            "created": "2025-01-15T10:00:00Z",
            "updated": "2025-02-18T14:30:00Z",
            "sharedWith": [
              {"userId": "user-2", "permission": "editor"}
            ],
            "linkSharing": {"enabled": false, "permission": "viewer"}
          }
        },
        "comments": [
          {
            "id": "comment-1",
            "docId": "doc-1",
            "userId": "user-2",
            "content": "Please review this section.",
            "resolved": false,
            "created": "2025-02-12T09:00:00Z",
            "quotedText": "Edit this document",
            "replies": []
          }
        ],
        "ui": {
          "currentDocId": null,
          "sidebarOpen": false,
          "sidebarTab": "comments",
          "shareDialogOpen": false,
          "findReplaceOpen": false,
          "viewMode": "editing",
          "zoom": 100,
          "documentListView": "grid",
          "searchQuery": ""
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Create new document | `documents` gains new entry with generated ID |
| Create document from template | `documents` gains new entry with template content |
| Delete document | `documents[docId]` removed; `comments` filtered to remove doc's comments |
| Rename document | `documents[docId].title` updated; `documents[docId].updated` refreshed |
| Star/unstar document | `documents[docId].starred` toggled |
| Edit document content | `documents[docId].content` updated (HTML); `documents[docId].updated` refreshed |
| Share document with user | `documents[docId].sharedWith` gains `{userId, permission}` entry |
| Change user permission | `documents[docId].sharedWith[n].permission` updated |
| Remove user access | `documents[docId].sharedWith` loses entry for that userId |
| Enable/disable link sharing | `documents[docId].linkSharing.enabled` toggled |
| Change link sharing permission | `documents[docId].linkSharing.permission` updated |
| Add comment | `comments` gains new `Comment` object |
| Reply to comment | `comments[n].replies` gains new `Reply` object |
| Resolve/unresolve comment | `comments[n].resolved` toggled |
| Delete comment | `comments` loses that comment entry |
| Toggle comments sidebar | `ui.sidebarOpen` toggled |
| Open/close share dialog | `ui.shareDialogOpen` toggled |
| Open/close Find & Replace | `ui.findReplaceOpen` toggled |
| Change view mode (editing/viewing/suggesting) | `ui.viewMode` updated |
| Change zoom level | `ui.zoom` updated |
| Switch document list view (grid/list) | `ui.documentListView` updated |
| Navigate into a document | `ui.currentDocId` set to doc ID |
| Navigate back to document list | `ui.currentDocId` set to `null` |
| Type in search bar (doc list) | `ui.searchQuery` updated |
| Copy document | `documents` gains new entry (copy with new ID, `"Copy of ..."` title) |
