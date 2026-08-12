# google_drive_mock Schema

**Deploy order**: 17 (alphabetical among all *_mock dirs)
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `items` | object | Map of all file/folder items keyed by item ID → `FileSystemItem` objects |
| `users` | object | Map of all users keyed by user ID → `User` objects |
| `currentUser` | object | Active user: `{id, name, email, avatar}` |
| `viewMode` | string | Display mode: `"grid"` or `"list"` |
| `sortConfig` | object | `{key: "name"\|"modifiedAt"\|"size"\|"type", direction: "asc"\|"desc"}` |
| `uploadQueue` | array | In-progress uploads; each: `{id, name, progress, status}` |
| `storageUsed` | number | Used storage in bytes |
| `storageTotal` | number | Total storage in bytes |
| `selectedItems` | array | IDs of currently selected items |

### FileSystemItem (values in `items` map)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique item ID (e.g., `"folder_001"`, `"file_001"`) |
| `parentId` | string\|null | Parent folder ID; `null` = root level |
| `name` | string | Display name of file/folder |
| `type` | string | `"folder"\|"image"\|"pdf"\|"doc"\|"spreadsheet"\|"presentation"\|"form"\|"video"\|"audio"\|"text"\|"code"\|"archive"\|"unknown"` |
| `mimeType` | string? | MIME type (e.g., `"application/pdf"`) |
| `size` | number | File size in bytes (0 for Google Workspace items) |
| `ownerId` | string | User ID of item owner |
| `sharedWith` | array | Each: `{userId, role: "viewer"\|"commenter"\|"editor", addedAt}` |
| `starred` | boolean | Whether item is starred |
| `trashed` | boolean | Whether item is in trash |
| `color` | string\|null | Folder color hex code (e.g., `"#4285F4"`) |
| `createdAt` | number | Creation timestamp (ms since epoch) |
| `modifiedAt` | number | Last modification timestamp (ms since epoch) |
| `accessedAt` | number | Last accessed timestamp (ms since epoch) |
| `description` | string? | Optional description |
| `thumbnailUrl` | string\|null? | Optional thumbnail image URL |
| `content` | string\|null? | Optional text content (for text files) |

### User

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique user ID (e.g., `"user_001"`) |
| `name` | string | Full name |
| `email` | string | Email address |
| `avatar` | string | Avatar image URL |

### UploadItem

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Upload session UUID |
| `name` | string | File name |
| `progress` | number | 0–100 percentage |
| `status` | string | `"uploading"\|"completed"\|"error"` |

### Default user IDs
`user_001` (Alex Johnson, currentUser), `user_002` (Sarah Chen), `user_003` (Mike Williams), `user_004` (Emily Davis), `user_005` (James Wilson)

### Default folder IDs
`folder_001` (Work Projects), `folder_002` (Personal), `folder_003` (Photos), `folder_004` (Shared Documents), `folder_005` (Q4 Reports), `folder_006` (Design Assets), `folder_007` (Taxes 2025)

### Default storage
`storageUsed`: 9,876,543,210 bytes (~9.2 GB), `storageTotal`: 16,106,127,360 bytes (~15 GB)

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "https://cua-gym-google-drive.xlang.ai/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "user_001",
          "name": "Alex Johnson",
          "email": "alex.johnson@company.com",
          "avatar": "https://ui-avatars.com/api/?name=Alex+Johnson&background=4285F4&color=fff"
        },
        "users": {
          "user_001": {"id": "user_001", "name": "Alex Johnson", "email": "alex.johnson@company.com", "avatar": "https://ui-avatars.com/api/?name=Alex+Johnson&background=4285F4&color=fff"},
          "user_002": {"id": "user_002", "name": "Sarah Chen", "email": "sarah.chen@company.com", "avatar": "https://ui-avatars.com/api/?name=Sarah+Chen&background=EA4335&color=fff"}
        },
        "items": {
          "folder_001": {
            "id": "folder_001", "parentId": null, "name": "Work Projects", "type": "folder",
            "size": 0, "ownerId": "user_001", "sharedWith": [{"userId": "user_002", "role": "editor", "addedAt": "2024-01-15T10:00:00Z"}],
            "starred": true, "trashed": false, "color": null,
            "createdAt": 1705312800000, "modifiedAt": 1710072600000, "accessedAt": 1710072600000
          },
          "file_001": {
            "id": "file_001", "parentId": "folder_001", "name": "Project Roadmap", "type": "doc",
            "mimeType": "application/vnd.google-apps.document", "size": 0,
            "ownerId": "user_001", "sharedWith": [{"userId": "user_002", "role": "editor", "addedAt": "2024-02-01T10:00:00Z"}],
            "starred": false, "trashed": false, "color": null,
            "createdAt": 1706522400000, "modifiedAt": 1710158400000, "accessedAt": 1710158400000
          }
        },
        "viewMode": "grid",
        "sortConfig": {"key": "name", "direction": "asc"},
        "uploadQueue": [],
        "storageUsed": 9876543210,
        "storageTotal": 16106127360,
        "selectedItems": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Create new folder | `items` gains new folder entry |
| Create new file | `items` gains new file entry |
| Upload file | `uploadQueue` gains entry (then completes); `items` gains new file |
| Delete file/folder (soft) | `items[id].trashed` → `true` |
| Restore from trash | `items[id].trashed` → `false` |
| Permanently delete | `items[id]` removed from map |
| Empty trash | All items with `trashed=true` removed |
| Star/unstar item | `items[id].starred` toggled |
| Rename item | `items[id].name` updated |
| Move item to folder | `items[id].parentId` updated |
| Share item | `items[id].sharedWith` array grows |
| Copy item | `items` gains new entry (copy of original with new ID) |
| Set folder color | `items[id].color` updated |
| Change view mode | `viewMode` changes (`"grid"` ↔ `"list"`) |
| Change sort | `sortConfig.key` and/or `sortConfig.direction` updated |
| Select items | `selectedItems` array updated |
| Access item | `items[id].accessedAt` updated |
