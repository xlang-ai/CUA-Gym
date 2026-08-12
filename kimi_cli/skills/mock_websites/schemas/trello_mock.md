# trello_mock Schema

**Deploy order**: 49 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8049)
**Base URL**: `http://172.17.46.46:8049/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | string | Active user ID (default: `"u1"`) |
| `users` | object | Map of userId → user object (`id`, `name`, `username`, `initials`, `email`, `avatarUrl`) |
| `boards` | object | Map of boardId → board object (see below) |
| `lists` | object | Map of listId → list object (see below) |
| `cards` | object | Map of cardId → card object (see below) |
| `boardOrder` | string[] | Ordered array of boardIds for home page display |

### Board object
`id`, `title`, `description`, `background` (hex color), `listIds` (string[]), `starred` (bool), `visibility` ("workspace"\|"private"), `archivedListIds` (string[]), `archivedCardIds` (string[]), `labels` (array of `{id, name, color}`), `memberIds` (string[]), `createdAt` (ISO string)

### List object
`id`, `title`, `boardId`, `cardIds` (string[]), `archived` (bool)

### Card object
`id`, `title`, `description`, `listId`, `boardId`, `labelIds` (string[]), `memberIds` (string[]), `dueDate` (ISO string | null), `startDate` (ISO string | null), `completed` (bool), `cover` (`{type:"color"|"image", value:string}` | null), `checklists` (array of `{id, title, items:[{id,text,completed,assigneeId,dueDate}]}`), `comments` (array of `{id,type:"comment"|"activity",userId,text,createdAt,editedAt}`), `attachments` (array of `{id,name,url,uploadedAt,uploadedBy}`), `archived` (bool), `watching` (bool), `position` (int), `createdAt` (ISO string)

## Default Data Summary

- 4 users: u1 (Alice), u2 (Bob), u3 (Charlie), u4 (Diana)
- 3 boards: `board-1` "Project Alpha" (lists 1-4), `board-2` "Marketing Campaign" (lists 5-7), `board-3` "Personal Tasks" (lists 8-9)
- 9 lists total; 14 cards total (card-1 through card-14)

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8049/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": "u1",
        "users": {
          "u1": {"id":"u1","name":"Alice Johnson","username":"alice","initials":"AJ","email":"alice@example.com","avatarUrl":""}
        },
        "boards": {
          "board-1": {
            "id":"board-1","title":"Project Alpha","description":"","background":"#0079BF",
            "listIds":["list-1","list-2"],"starred":false,"visibility":"workspace",
            "archivedListIds":[],"archivedCardIds":[],"labels":[],"memberIds":["u1"],"createdAt":"2025-01-15T10:00:00.000Z"
          }
        },
        "lists": {
          "list-1": {"id":"list-1","title":"To Do","boardId":"board-1","cardIds":["card-1"],"archived":false},
          "list-2": {"id":"list-2","title":"Done","boardId":"board-1","cardIds":[],"archived":false}
        },
        "cards": {
          "card-1": {
            "id":"card-1","title":"Write report","description":"","listId":"list-1","boardId":"board-1",
            "labelIds":[],"memberIds":[],"dueDate":null,"startDate":null,"completed":false,"cover":null,
            "checklists":[],"comments":[],"attachments":[],"archived":false,"watching":false,"position":0,"createdAt":"2025-01-20T10:00:00.000Z"
          }
        },
        "boardOrder": ["board-1"]
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | Changed State Fields |
|-------------|---------------------|
| Add card to list | `cards` gains new entry; `lists[listId].cardIds` appends new id |
| Move card between lists | `lists[srcListId].cardIds` removes id; `lists[destListId].cardIds` adds id; `cards[cardId].listId` changes; `cards[cardId].comments` gains activity entry |
| Add comment to card | `cards[cardId].comments` prepends new comment object |
| Toggle checklist item | `cards[cardId].checklists[n].items[m].completed` flips; `cards[cardId].comments` gains activity |
| Archive card | `cards[cardId].archived` = true; `lists[listId].cardIds` removes id; `boards[boardId].archivedCardIds` appends id |
| Star/unstar board | `boards[boardId].starred` flips |
| Add new board | `boards` gains new entry; `boardOrder` prepends new boardId |
| Add list to board | `lists` gains new entry; `boards[boardId].listIds` appends new id |
| Update card due date | `cards[cardId].dueDate` changes; `cards[cardId].comments` gains activity |
| Mark card complete | `cards[cardId].completed` = true; `cards[cardId].comments` gains activity |
| Toggle label on card | `cards[cardId].labelIds` gains/loses labelId |
| Toggle member on card | `cards[cardId].memberIds` gains/loses userId |
