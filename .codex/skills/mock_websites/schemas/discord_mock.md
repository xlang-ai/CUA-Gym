# discord_mock Schema

**Deploy order**: 11 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8010)
**Base URL**: `http://172.17.46.46:8010/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Note**: The `/go` route is a React page (client-side); the Vite middleware handles `GET /go` server-side for state JSON.

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Logged-in user: `id`, `username`, `discriminator`, `avatar`, `status` (`online`/`idle`/`dnd`/`offline`), `customStatus`, `aboutMe`, `roles[]`, `badges[]`, `bannerColor`, `isBot` |
| `servers` | object (map) | Keyed by server ID. Each: `id`, `name`, `icon`, `ownerId`, `channels[]`, `roles[]`, `members[]`, `categories[]`, `description`, `boostCount`, `boostTier` |
| `channels` | object (map) | Keyed by channel ID. Each: `id`, `serverId`, `name`, `type` (`text`/`announcement`/`voice`), `category`, `topic`, `position`, `isNsfw`, `slowMode`, `pinnedMessageIds[]`, `lastMessageId`, `unreadCount` |
| `messages` | object (map) | Keyed by message ID. Each: `id`, `channelId`, `userId`, `content`, `timestamp`, `editedTimestamp`, `reactions` (obj: emoji→userIds[]), `attachments[]`, `embeds[]`, `mentions[]`, `pinned`, `type` (`default`/`reply`/`thread_starter`), `referencedMessageId`, `threadId`, `isEdited` |
| `threads` | object (map) | Keyed by thread ID. Each: `id`, `channelId`, `messageId`, `name`, `ownerId`, `messages[]` (inline message objects), `messageCount`, `memberCount`, `archived`, `locked`, `createdAt` |
| `users` | object (map) | Keyed by user ID. Same shape as `currentUser`. Includes `user-current` through `user-6` (one is a bot). |
| `roles` | object (map) | Keyed by role ID. Each: `id`, `serverId`, `name`, `color`, `position`, `permissions[]`, `hoist`, `mentionable` |
| `dmConversations` | object (map) | Keyed by DM ID (`dm-1`, `dm-2`). Each: `id`, `recipientId`, `messages[]` (inline), `lastMessageTimestamp`, `unreadCount` |
| `activeVoiceChannel` | string\|null | ID of voice channel user is currently in, or null |
| `dms` | array | List of user IDs with active DM conversations |
| `ui` | object | `memberSidebarVisible` (bool), `threadPanelOpen` (bool), `activeThreadId` (string\|null), `searchQuery` (string), `searchResults` (array), `pinnedPanelOpen` (bool) |

### Default Data Summary
- 2 servers: `server-1` (Gaming Community, 6 users, 6 text/1 voice channels), `server-2` (Dev Hub, 4 users, 3 text/1 voice channels)
- 11 channels total across both servers
- ~25 messages across channels
- 2 threads (`thread-1` in #help, `thread-2` in #code-review)
- 6 users (`user-current`=Alex_Dev, Sarah_Mod, GameMaster42, CodeNinja, PixelArtist, BotHelper)
- 5 roles across both servers
- 2 DM conversations

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8010/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "user-current",
          "username": "Alex_Dev",
          "discriminator": "9201",
          "avatar": "https://picsum.photos/seed/alexdev/128/128",
          "status": "online",
          "customStatus": null,
          "aboutMe": "Full-stack dev & gamer.",
          "roles": ["role-admin"],
          "badges": ["server_owner"],
          "bannerColor": "#5865F2",
          "joinedAt": "2023-01-15T10:00:00Z",
          "isBot": false
        },
        "servers": {
          "server-1": {
            "id": "server-1",
            "name": "Gaming Community",
            "icon": "https://picsum.photos/seed/gaming-server/64/64",
            "ownerId": "user-current",
            "channels": ["ch-1"],
            "roles": ["role-admin"],
            "members": ["user-current"],
            "categories": [{"id": "cat-1", "name": "TEXT CHANNELS", "channelIds": ["ch-1"]}],
            "description": "A gaming community",
            "boostCount": 0,
            "boostTier": 0
          }
        },
        "channels": {
          "ch-1": {
            "id": "ch-1",
            "serverId": "server-1",
            "name": "general",
            "type": "text",
            "category": "TEXT CHANNELS",
            "topic": "General discussion",
            "position": 0,
            "isNsfw": false,
            "slowMode": 0,
            "pinnedMessageIds": [],
            "lastMessageId": null,
            "unreadCount": 0,
            "permissions": {}
          }
        },
        "messages": {},
        "threads": {},
        "users": {
          "user-current": {
            "id": "user-current",
            "username": "Alex_Dev",
            "discriminator": "9201",
            "avatar": "https://picsum.photos/seed/alexdev/128/128",
            "status": "online",
            "customStatus": null,
            "aboutMe": "Full-stack dev & gamer.",
            "roles": ["role-admin"],
            "badges": ["server_owner"],
            "bannerColor": "#5865F2",
            "joinedAt": "2023-01-15T10:00:00Z",
            "isBot": false
          }
        },
        "roles": {
          "role-admin": {
            "id": "role-admin",
            "serverId": "server-1",
            "name": "Admin",
            "color": "#e74c3c",
            "position": 3,
            "permissions": ["ADMINISTRATOR"],
            "hoist": true,
            "mentionable": true
          }
        },
        "dmConversations": {},
        "activeVoiceChannel": null,
        "dms": [],
        "ui": {
          "memberSidebarVisible": true,
          "threadPanelOpen": false,
          "activeThreadId": null,
          "searchQuery": "",
          "searchResults": [],
          "pinnedPanelOpen": false
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Fields Changed |
|-------------|---------------------|
| Send message in channel | `messages` gains new entry; `channels[id].lastMessageId` updates |
| Edit message | `messages[id].content`, `messages[id].isEdited=true`, `messages[id].editedTimestamp` |
| Delete message | `messages[id]` removed |
| Add/remove reaction | `messages[id].reactions[emoji]` array updated |
| Pin/unpin message | `messages[id].pinned`, `channels[id].pinnedMessageIds[]` |
| Create thread | `threads` gains new entry; `messages[id].threadId`, `messages[id].type='thread_starter'` |
| Send thread message | `threads[id].messages[]`, `threads[id].messageCount` |
| Send DM | `dmConversations[id].messages[]`, `dmConversations[id].lastMessageTimestamp` |
| Update user status | `currentUser.status`, `users['user-current'].status` |
| Update user profile | `currentUser.aboutMe`, `currentUser.customStatus`, `currentUser.bannerColor` |
| Toggle member sidebar | `ui.memberSidebarVisible` |
| Open/close thread panel | `ui.threadPanelOpen`, `ui.activeThreadId` |
| Toggle pinned panel | `ui.pinnedPanelOpen` |
| Search | `ui.searchQuery`, `ui.searchResults` |
| Join voice channel | `activeVoiceChannel` set to channel ID |
| Leave voice channel | `activeVoiceChannel` set to null |
