# slack_mock Schema

**Deploy order**: 47 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8047)
**Base URL**: `http://172.17.46.46:8047/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Active user (same shape as users[]) |
| `workspace` | object | `{workspaceId, workspaceName, icon}` |
| `users` | array | All workspace members; each: `{userId, fullName, displayName, email, avatar, title, status, statusMessage, statusEmoji, timeZone}` |
| `channels` | array | Each: `{channelId, name, description, topic, isPrivate, isStarred, members[], createdBy, createdAt, pinnedMessages[], unreadCount}` |
| `messages` | object | Keyed by channelId or dmId → array of messages; each: `{messageId, senderId, content, timestamp, threadId\|null, reactions[], attachments[], isEdited}` |
| `threads` | object | Keyed by threadId → `{threadId, parentMessageId, channelId\|null, dmId\|null, replies[], followers[]}` |
| `dms` | array | Each: `{dmId, participants[], lastMessage, lastTime, unreadCount}` |
| `bookmarkedMessages` | array | Message IDs (strings) that currentUser has bookmarked |
| `callHistory` | array | Each: `{callId, type, participants[], dmId, startTime, duration, status}` |
| `settings` | object | `{theme, notifications, displayDensity, showAvatars, use24Hour}` |
| `invitations` | array | Each: `{invitationId, email, sentBy, sentAt, status}` |
| `notifications` | array | Each: `{notificationId, type, messageId, channelId\|null, dmId\|null, userId, timestamp, read}` |

### Default channel IDs
`general`, `random`, `engineering`, `design`, `marketing`, `project-alpha`

### Default user IDs
`user_1` (John Smith, currentUser) through `user_8` (Rachel Lee)

### Default DM IDs
`dm_1` (user_1↔user_2), `dm_2` (user_1↔user_3), `dm_3` (user_1↔user_4)

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8047/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "userId": "user_1",
          "fullName": "John Smith",
          "displayName": "John",
          "email": "john.smith@company.com",
          "avatar": "https://picsum.photos/200/200?random=1",
          "status": "online",
          "statusMessage": "",
          "statusEmoji": "",
          "timeZone": "America/New_York"
        },
        "workspace": {"workspaceId": "ws_1", "workspaceName": "Acme Corp", "icon": ""},
        "users": [
          {"userId": "user_1", "fullName": "John Smith", "displayName": "John", "email": "john.smith@company.com", "avatar": "https://picsum.photos/200/200?random=1", "status": "online"},
          {"userId": "user_2", "fullName": "Sarah Johnson", "displayName": "Sarah", "email": "sarah.johnson@company.com", "avatar": "https://picsum.photos/200/200?random=2", "status": "online"}
        ],
        "channels": [
          {"channelId": "general", "name": "general", "description": "General chat", "topic": "", "isPrivate": false, "isStarred": false, "members": ["user_1", "user_2"], "createdBy": "user_1", "createdAt": "2024-01-01T10:00:00Z", "pinnedMessages": [], "unreadCount": 0}
        ],
        "messages": {
          "general": [
            {"messageId": "msg_1", "senderId": "user_2", "content": "Hello!", "timestamp": "2024-01-01T10:00:00Z", "threadId": null, "reactions": [], "attachments": [], "isEdited": false}
          ]
        },
        "threads": {},
        "dms": [],
        "bookmarkedMessages": [],
        "callHistory": [],
        "settings": {"theme": "light", "notifications": "all", "displayDensity": "comfortable", "showAvatars": true, "use24Hour": false},
        "invitations": [],
        "notifications": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Send message in channel | `messages[channelId]` array grows by 1 |
| Send message in DM | `messages[dmId]` grows; `dms[].lastMessage` + `lastTime` updated |
| Reply in thread | `messages[channelId/dmId]` grows (threadId set); `threads[threadId].replies` grows |
| Add/remove emoji reaction | `messages[key][i].reactions` array modified |
| Star/unstar channel | `channels[i].isStarred` toggled |
| Bookmark message | `bookmarkedMessages` array updated |
| Pin message | `channels[i].pinnedMessages` updated |
| Join channel | `channels[i].members` gains `currentUser.userId` |
| Leave channel | `channels[i].members` loses `currentUser.userId` |
| Create channel | `channels` array grows; `messages[newChannelId]` initialized to `[]` |
| Edit message | `messages[key][i].content` updated; `isEdited` → `true` |
| Delete message | `messages[key]` array shrinks by 1 |
| Update profile | `currentUser` fields updated; matching entry in `users[]` updated |
| Update settings | `settings` object fields updated |
| Send invitation | `invitations` array grows by 1 |
| Start call | `callHistory` grows; call status `"calling"` |
| End call | `callHistory[i].status` → `"completed"`; `duration` set |
| Mark notification read | `notifications[i].read` → `true` |
| Clear all notifications | `notifications` → `[]` |
