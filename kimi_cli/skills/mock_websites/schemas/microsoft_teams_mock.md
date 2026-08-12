# microsoft_teams_mock Schema

**Deploy order**: 28 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8028)
**Base URL**: `http://172.17.46.46:8028/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Redirect | Redirects to `/chat` |
| `/activity` | ActivityPage | Notification feed with filtering |
| `/chat` | ChatPage | 1:1, group, and meeting chats |
| `/chat/:chatId` | ChatPage | Specific chat selected |
| `/teams` | TeamsPage | Teams and channels view |
| `/teams/:teamId` | TeamsPage | Specific team selected |
| `/teams/:teamId/channels/:channelId` | TeamsPage | Specific channel selected |
| `/calendar` | CalendarPage | Work-week/day calendar with meetings |
| `/calls` | CallsPage | Call history and speed dial |
| `/files` | FilesPage | File browser (recent, by team, downloads) |
| `/go` | Go | State inspection endpoint |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | The logged-in user (same shape as `users[]` entries) |
| `users` | array | All organization members (10 users by default) |
| `teams` | array | Teams the current user belongs to |
| `channels` | array | All channels across all teams |
| `chats` | array | 1:1, group, and meeting chats |
| `messages` | object | Keyed by containerId (channelId or chatId) → array of messages |
| `meetings` | array | Calendar meetings/events |
| `calls` | array | Call history records |
| `files` | array | Shared files across channels and chats |
| `notifications` | array | Activity feed notifications |
| `settings` | object | User preferences (theme, notifications, privacy, display) |
| `ui` | object | UI state (active view, selected team/channel/chat, thread, search) |

---

## Detailed Object Schemas

### `currentUser` / `users[]` — User Object

```jsonc
{
  "userId": "user_1",                          // string, unique ID
  "displayName": "Adele Vance",                // string, full display name
  "firstName": "Adele",                        // string
  "lastName": "Vance",                         // string
  "email": "adele.vance@contoso.com",          // string
  "avatar": "https://i.pravatar.cc/150?u=user_1", // string, avatar URL
  "jobTitle": "Senior Marketing Manager",      // string
  "department": "Marketing",                   // string
  "location": "Seattle, WA",                   // string
  "phone": "+1 (206) 555-0110",               // string
  "presence": "available",                     // "available"|"busy"|"dnd"|"brb"|"away"|"inAMeeting"|"offline"
  "statusMessage": "",                         // string, custom status text
  "statusEmoji": "",                           // string, custom status emoji
  "outOfOffice": false,                        // boolean
  "timezone": "America/Los_Angeles"            // string, IANA timezone
}
```

### `teams[]` — Team Object

```jsonc
{
  "teamId": "team_1",                         // string, unique ID
  "displayName": "Contoso Engineering",        // string
  "description": "Engineering team collaboration space", // string
  "avatar": "",                                // string, team avatar URL (empty = use initials)
  "avatarColor": "#4A90D9",                    // string, hex color for avatar background
  "avatarInitials": "CE",                      // string, 1-2 char initials
  "visibility": "private",                     // "private"|"public"
  "isArchived": false,                         // boolean
  "isFavorite": true,                          // boolean
  "createdDateTime": "2024-06-15T10:00:00Z",  // string, ISO datetime
  "members": ["user_1", "user_2", ...],        // array of userId strings
  "owners": ["user_2"],                        // array of userId strings (subset of members)
  "channels": ["ch_1", "ch_2", ...],           // array of channelId strings
  "settings": {                                // team-level settings
    "allowMemberCreateChannels": true,         // boolean
    "allowMemberDeleteMessages": true,         // boolean
    "allowGiphy": true,                        // boolean
    "allowStickers": true,                     // boolean
    "allowMemes": true                         // boolean
  }
}
```

### `channels[]` — Channel Object

```jsonc
{
  "channelId": "ch_1",                        // string, unique ID
  "teamId": "team_1",                         // string, parent team ID
  "displayName": "General",                   // string
  "description": "General engineering discussions", // string
  "membershipType": "standard",               // "standard"|"private"
  "isFavoriteByDefault": true,                // boolean
  "isPinned": false,                          // boolean
  "isMuted": false,                           // boolean
  "unreadCount": 3,                           // number
  "lastMessagePreview": "Alex: The deployment went smoothly", // string
  "lastMessageTimestamp": "2025-03-13T14:30:00.000Z", // string, ISO datetime
  "createdDateTime": "2024-06-15T10:00:00Z",  // string, ISO datetime
  "members": [],                              // array of userId strings (for private channels)
  "tabs": [                                   // array of tab objects
    {
      "tabId": "tab_posts_1",                 // string
      "displayName": "Posts",                 // string
      "type": "posts",                        // "posts"|"files"
      "isDefault": true                       // boolean (optional)
    }
  ],
  "pinnedMessages": []                        // array of messageId strings
}
```

### `chats[]` — Chat Object

```jsonc
{
  "chatId": "chat_1",                         // string, unique ID
  "chatType": "oneOnOne",                     // "oneOnOne"|"group"|"meeting"
  "topic": "",                                // string, group/meeting chat topic
  "participants": ["user_1", "user_2"],       // array of userId strings
  "isPinned": true,                           // boolean
  "isMuted": false,                           // boolean
  "isHidden": false,                          // boolean
  "unreadCount": 2,                           // number
  "lastMessagePreview": "Sounds good, I'll push the fix now.", // string
  "lastMessageSenderId": "user_2",            // string, userId
  "lastMessageTimestamp": "2025-03-13T14:45:00.000Z", // string, ISO datetime
  "createdDateTime": "2024-12-01T09:00:00Z",  // string, ISO datetime
  "pinnedMessages": [],                       // array of messageId strings
  "tabs": [                                   // array of tab objects
    {
      "tabId": "tab_chat_1",                  // string
      "displayName": "Chat",                  // string
      "type": "chat",                         // "chat"|"files"
      "isDefault": true                       // boolean (optional)
    }
  ]
}
```

### `messages[containerId][]` — Message Object

```jsonc
{
  "messageId": "msg_1",                       // string, unique ID
  "containerId": "ch_1",                      // string, channelId or chatId
  "containerType": "channel",                 // "channel"|"chat"
  "senderId": "user_2",                       // string, userId (or "system" for system events)
  "content": "Good morning team! Quick update on the API refactor...", // string
  "contentType": "text",                      // string, always "text"
  "messageType": "message",                   // "message"|"systemEvent"
  "createdDateTime": "2025-03-12T09:00:00.000Z", // string, ISO datetime
  "lastEditedDateTime": null,                 // string|null, ISO datetime when edited
  "deletedDateTime": null,                    // string|null, ISO datetime when deleted
  "importance": "normal",                     // "normal"|"high"
  "subject": "API Refactor Update",           // string, message subject/title (optional)
  "replyToId": null,                          // string|null, messageId of parent (for threaded replies)
  "reactions": [                              // array of reaction objects
    {
      "emoji": "\ud83d\udc4d",               // string, emoji character
      "users": ["user_1", "user_9"]           // array of userId strings
    }
  ],
  "mentions": [                               // array of mention objects
    {
      "userId": "user_2",                     // string
      "displayName": "Alex Wilber",           // string
      "mentionText": "@Alex Wilber"           // string
    }
  ],
  "attachments": [                            // array of attachment objects
    {
      "attachmentId": "att_1",                // string
      "name": "Sprint_Backlog.xlsx",          // string
      "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // string
      "contentUrl": "#",                      // string
      "thumbnailUrl": "",                     // string
      "size": 184320                          // number, bytes
    }
  ],
  "isBookmarked": false                       // boolean
}
```

### `meetings[]` — Meeting Object

```jsonc
{
  "meetingId": "meeting_1",                   // string, unique ID
  "subject": "Daily Standup",                 // string
  "startDateTime": "2025-03-13T09:00:00.000Z", // string, ISO datetime
  "endDateTime": "2025-03-13T09:30:00.000Z",  // string, ISO datetime
  "isAllDay": false,                          // boolean (optional, present on some)
  "location": "Microsoft Teams Meeting",       // string (optional)
  "organizer": "user_2",                      // string, userId
  "participants": [                           // array of participant objects
    {
      "userId": "user_2",                     // string
      "role": "organizer",                    // "organizer"|"attendee"
      "rsvp": "accepted"                      // "accepted"|"tentative"|"pending"|"declined"
    }
  ],
  "isRecurring": true,                        // boolean (optional)
  "recurrencePattern": "daily",               // string|null, e.g. "daily"
  "chatId": null,                             // string|null, linked chat
  "channelId": null,                          // string|null, linked channel (optional)
  "teamId": null,                             // string|null, linked team (optional)
  "bodyPreview": "Daily sync to discuss progress and blockers.", // string
  "joinUrl": "#",                             // string
  "status": "scheduled"                       // string (optional)
}
```

### `calls[]` — Call Object

```jsonc
{
  "callId": "call_1",                         // string, unique ID
  "callType": "oneOnOne",                     // string
  "direction": "incoming",                    // "incoming"|"outgoing"
  "participants": ["user_1", "user_2"],       // array of userId strings
  "startDateTime": "2025-03-12T16:00:00.000Z", // string, ISO datetime
  "endDateTime": "2025-03-12T16:12:00.000Z",  // string|null, ISO datetime
  "duration": 720,                            // number|null, seconds
  "status": "completed",                      // "completed"|"missed"
  "isVideoCall": true                         // boolean
}
```

### `files[]` — File Object

```jsonc
{
  "fileId": "file_1",                         // string, unique ID
  "name": "Q3_Roadmap.pdf",                   // string
  "contentType": "application/pdf",            // string, MIME type
  "size": 245760,                             // number, bytes
  "containerId": "ch_1",                      // string, channelId or chatId
  "containerType": "channel",                 // "channel"|"chat"
  "sharedBy": "user_2",                       // string, userId
  "sharedDateTime": "2025-03-10T10:00:00.000Z", // string, ISO datetime
  "lastModifiedDateTime": "2025-03-10T10:00:00.000Z", // string, ISO datetime
  "lastModifiedBy": "user_2",                 // string, userId
  "thumbnailUrl": "",                         // string
  "downloadUrl": "#"                          // string
}
```

### `notifications[]` — Notification Object

```jsonc
{
  "notificationId": "notif_1",                // string, unique ID
  "type": "mention",                          // "mention"|"reply"|"reaction"|"meeting"|"system"|"assignment"
  "actorId": "user_2",                        // string, userId who triggered the notification
  "targetMessageId": "msg_8",                 // string|null, related message ID
  "containerId": "ch_1",                      // string|null, channel/chat ID
  "containerType": "channel",                 // "channel"|"chat"|null
  "containerName": "General",                 // string, human-readable container name
  "teamName": "Contoso Engineering",          // string|null, team name if channel
  "previewText": "Alex Wilber mentioned you: @Adele the data pipeline job failed...", // string
  "timestamp": "2025-03-13T08:30:00.000Z",   // string, ISO datetime
  "isRead": false,                            // boolean
  "isActionable": false                       // boolean (e.g. meeting join buttons)
}
```

### `settings` — Settings Object

```jsonc
{
  "theme": "light",                           // string
  "language": "en-US",                        // string
  "notifications": {
    "showMessagePreviews": true,              // boolean
    "playSound": true,                        // boolean
    "showBadgeCount": true,                   // boolean
    "muteAll": false,                         // boolean
    "quietHoursEnabled": false,               // boolean
    "quietHoursStart": "22:00",               // string, HH:MM
    "quietHoursEnd": "07:00"                  // string, HH:MM
  },
  "privacy": {
    "readReceipts": true,                     // boolean
    "showPresence": true                      // boolean
  },
  "display": {
    "density": "comfortable",                 // string
    "showChannelPreview": true                // boolean
  }
}
```

### `ui` — UI State Object

```jsonc
{
  "activeView": "chat",                       // "chat"|"teams"|"activity"|"calendar"|"calls"|"files"
  "activeTeamId": null,                       // string|null
  "activeChannelId": null,                    // string|null
  "activeChatId": null,                       // string|null
  "activeThreadMessageId": null,              // string|null
  "isThreadPanelOpen": false,                 // boolean
  "isDetailsPanelOpen": false,                // boolean
  "searchQuery": "",                          // string
  "searchResults": null                       // object|null
}
```

---

## Default IDs

### Users (10 total, `currentUser` = `user_1`)
| ID | Name | Job Title | Department |
|----|------|-----------|------------|
| `user_1` | Adele Vance (currentUser) | Senior Marketing Manager | Marketing |
| `user_2` | Alex Wilber | Software Engineer | Engineering |
| `user_3` | Megan Bowen | HR Manager | Human Resources |
| `user_4` | Nestor Wilke | IT Admin | IT |
| `user_5` | Joni Sherman | Legal Counsel | Legal |
| `user_6` | Lee Gu | UX Designer | Design |
| `user_7` | Lynne Robbins | VP of Sales | Sales |
| `user_8` | Diego Siciliani | Finance Analyst | Finance |
| `user_9` | Pradeep Gupta | Data Scientist | Engineering |
| `user_10` | Henrietta Mueller | Project Manager | PMO |

### Teams (4 total)
| ID | Name | Visibility | Channels |
|----|------|------------|----------|
| `team_1` | Contoso Engineering | private | `ch_1` (General), `ch_2` (Backend), `ch_3` (Frontend), `ch_4` (DevOps), `ch_5` (Code Reviews) |
| `team_2` | Marketing | private | `ch_6` (General), `ch_7` (Campaigns), `ch_8` (Social Media), `ch_9` (Brand Guidelines, private) |
| `team_3` | Product Design | private | `ch_10` (General), `ch_11` (UI/UX Research), `ch_12` (Design Reviews) |
| `team_4` | All Company | public | `ch_13` (General), `ch_14` (Announcements) |

### Channels (14 total): `ch_1` through `ch_14`

### Chats (8 total)
| ID | Type | Participants / Topic |
|----|------|---------------------|
| `chat_1` | oneOnOne | user_1 ↔ user_2 (Alex Wilber) |
| `chat_2` | oneOnOne | user_1 ↔ user_3 (Megan Bowen) |
| `chat_3` | oneOnOne | user_1 ↔ user_7 (Lynne Robbins) |
| `chat_4` | oneOnOne | user_1 ↔ user_6 (Lee Gu) |
| `chat_5` | group | user_1, user_2, user_6, user_10 — "Project Kickoff" |
| `chat_6` | group | user_1, user_3, user_5, user_8 — "Lunch Plans" |
| `chat_7` | group | user_6, user_1, user_2 — "Design Sprint" |
| `chat_meeting_1` | meeting | user_1, user_2, user_10, user_9, user_6 — "Sprint Planning" |

### Meetings (8 total): `meeting_1` through `meeting_8`

### Calls (5 total): `call_1` through `call_5`

### Files (12 total): `file_1` through `file_12`

### Notifications (15 total): `notif_1` through `notif_15`

---

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8028/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "userId": "user_1",
          "displayName": "Adele Vance",
          "firstName": "Adele",
          "lastName": "Vance",
          "email": "adele.vance@contoso.com",
          "avatar": "https://i.pravatar.cc/150?u=user_1",
          "jobTitle": "Senior Marketing Manager",
          "department": "Marketing",
          "location": "Seattle, WA",
          "phone": "+1 (206) 555-0110",
          "presence": "available",
          "statusMessage": "",
          "statusEmoji": "",
          "outOfOffice": false,
          "timezone": "America/Los_Angeles"
        },
        "users": [
          {"userId": "user_1", "displayName": "Adele Vance", "firstName": "Adele", "lastName": "Vance", "email": "adele.vance@contoso.com", "avatar": "https://i.pravatar.cc/150?u=user_1", "jobTitle": "Senior Marketing Manager", "department": "Marketing", "location": "Seattle, WA", "phone": "+1 (206) 555-0110", "presence": "available", "statusMessage": "", "statusEmoji": "", "outOfOffice": false, "timezone": "America/Los_Angeles"},
          {"userId": "user_2", "displayName": "Alex Wilber", "firstName": "Alex", "lastName": "Wilber", "email": "alex.wilber@contoso.com", "avatar": "https://i.pravatar.cc/150?u=user_2", "jobTitle": "Software Engineer", "department": "Engineering", "location": "Seattle, WA", "phone": "+1 (206) 555-0120", "presence": "available", "statusMessage": "", "statusEmoji": "", "outOfOffice": false, "timezone": "America/Los_Angeles"}
        ],
        "teams": [
          {
            "teamId": "team_1",
            "displayName": "Contoso Engineering",
            "description": "Engineering team collaboration space",
            "avatar": "",
            "avatarColor": "#4A90D9",
            "avatarInitials": "CE",
            "visibility": "private",
            "isArchived": false,
            "isFavorite": true,
            "createdDateTime": "2024-06-15T10:00:00Z",
            "members": ["user_1", "user_2"],
            "owners": ["user_2"],
            "channels": ["ch_1"],
            "settings": {"allowMemberCreateChannels": true, "allowMemberDeleteMessages": true, "allowGiphy": true, "allowStickers": true, "allowMemes": true}
          }
        ],
        "channels": [
          {"channelId": "ch_1", "teamId": "team_1", "displayName": "General", "description": "General discussions", "membershipType": "standard", "isFavoriteByDefault": true, "isPinned": false, "isMuted": false, "unreadCount": 0, "lastMessagePreview": "", "lastMessageTimestamp": "2025-03-13T10:00:00Z", "createdDateTime": "2024-06-15T10:00:00Z", "members": [], "tabs": [{"tabId": "tab_posts_1", "displayName": "Posts", "type": "posts", "isDefault": true}, {"tabId": "tab_files_1", "displayName": "Files", "type": "files"}], "pinnedMessages": []}
        ],
        "chats": [
          {"chatId": "chat_1", "chatType": "oneOnOne", "topic": "", "participants": ["user_1", "user_2"], "isPinned": false, "isMuted": false, "isHidden": false, "unreadCount": 0, "lastMessagePreview": "Hello!", "lastMessageSenderId": "user_2", "lastMessageTimestamp": "2025-03-13T10:00:00Z", "createdDateTime": "2025-01-01T09:00:00Z", "pinnedMessages": [], "tabs": [{"tabId": "tab_chat_1", "displayName": "Chat", "type": "chat", "isDefault": true}, {"tabId": "tab_files_c1", "displayName": "Files", "type": "files"}]}
        ],
        "messages": {
          "ch_1": [
            {"messageId": "msg_1", "containerId": "ch_1", "containerType": "channel", "senderId": "user_2", "content": "Welcome to the team!", "contentType": "text", "messageType": "message", "createdDateTime": "2025-03-13T10:00:00Z", "lastEditedDateTime": null, "deletedDateTime": null, "importance": "normal", "subject": "", "replyToId": null, "reactions": [], "mentions": [], "attachments": [], "isBookmarked": false}
          ],
          "chat_1": [
            {"messageId": "cm_1", "containerId": "chat_1", "containerType": "chat", "senderId": "user_2", "content": "Hello!", "contentType": "text", "messageType": "message", "createdDateTime": "2025-03-13T10:00:00Z", "lastEditedDateTime": null, "deletedDateTime": null, "importance": "normal", "subject": "", "replyToId": null, "reactions": [], "mentions": [], "attachments": [], "isBookmarked": false}
          ]
        },
        "meetings": [],
        "calls": [],
        "files": [],
        "notifications": [],
        "settings": {
          "theme": "light",
          "language": "en-US",
          "notifications": {"showMessagePreviews": true, "playSound": true, "showBadgeCount": true, "muteAll": false, "quietHoursEnabled": false, "quietHoursStart": "22:00", "quietHoursEnd": "07:00"},
          "privacy": {"readReceipts": true, "showPresence": true},
          "display": {"density": "comfortable", "showChannelPreview": true}
        },
        "ui": {"activeView": "chat", "activeTeamId": null, "activeChannelId": null, "activeChatId": null, "activeThreadMessageId": null, "isThreadPanelOpen": false, "isDetailsPanelOpen": false, "searchQuery": "", "searchResults": null}
      }
    }
  }
}
```

---

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Send message in channel | `messages[channelId]` grows by 1; `channels[i].lastMessagePreview` + `lastMessageTimestamp` updated |
| Send message in chat | `messages[chatId]` grows by 1; `chats[i].lastMessagePreview`, `lastMessageSenderId`, `lastMessageTimestamp` updated; `isHidden` → `false` |
| Reply in thread | `messages[channelId]` grows by 1 (new message has `replyToId` set to parent messageId) |
| Edit message | `messages[containerId][i].content` updated; `lastEditedDateTime` set to ISO timestamp |
| Delete message | `messages[containerId][i].deletedDateTime` set; `content` → `"This message has been deleted."` |
| Add emoji reaction | `messages[containerId][i].reactions` — existing emoji's `users` grows, or new reaction object added |
| Remove emoji reaction | `messages[containerId][i].reactions[j].users` loses userId; if empty, reaction removed |
| Create channel | `channels` grows by 1; `teams[i].channels` gains new channelId; `messages[newChannelId]` = `[]` |
| Create team | `teams` grows by 1 (with auto-created General channel); `channels` grows by 1; `messages[generalChId]` = `[]` |
| Create chat | `chats` gains new entry at index 0; `messages[newChatId]` = `[]` |
| Pin message | `chats[i].pinnedMessages` or `channels[i].pinnedMessages` gains messageId |
| Unpin message | `chats[i].pinnedMessages` or `channels[i].pinnedMessages` loses messageId |
| Mark as read | `chats[i].unreadCount` → `0` or `channels[i].unreadCount` → `0` |
| Change presence status | `currentUser.presence` updated (e.g. `"available"` → `"busy"`) |
| Set status message | `currentUser.statusMessage` and `currentUser.statusEmoji` updated |
| Update settings | `settings` sub-fields updated (deep merge) |
| Mark all notifications read | All `notifications[i].isRead` → `true` |
| Create meeting | `meetings` grows by 1 with new meeting object |

## Actions Available via Context

The `AppContext` exposes these action methods:

| Action | Signature | Description |
|--------|-----------|-------------|
| `sendMessage` | `(containerId, content, mentions?, attachments?)` | Send a new message to a channel or chat |
| `sendReply` | `(containerId, replyToId, content)` | Send a threaded reply |
| `editMessage` | `(containerId, messageId, newContent)` | Edit an existing message |
| `deleteMessage` | `(containerId, messageId)` | Soft-delete a message |
| `addReaction` | `(containerId, messageId, emoji)` | Add emoji reaction |
| `removeReaction` | `(containerId, messageId, emoji)` | Remove emoji reaction |
| `createChannel` | `(teamId, displayName, description?, membershipType?)` | Create channel in a team |
| `createTeam` | `(displayName, description, visibility, members)` | Create a new team with auto General channel |
| `createChat` | `(participants, topic?)` | Create 1:1 or group chat |
| `pinMessage` | `(containerId, messageId)` | Pin a message |
| `unpinMessage` | `(containerId, messageId)` | Unpin a message |
| `markAsRead` | `(containerId)` | Reset unread count to 0 |
| `updatePresence` | `(presence)` | Change current user presence |
| `updateStatus` | `(statusMessage, statusEmoji)` | Set custom status |
| `updateSettings` | `(settingsUpdate)` | Deep-merge settings update |
| `markAllNotificationsRead` | `()` | Mark all notifications as read |
| `createMeeting` | `(subject, startDateTime, endDateTime, participantIds, bodyPreview?)` | Create a calendar meeting |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+1` | Navigate to Activity |
| `Ctrl+2` | Navigate to Chat |
| `Ctrl+3` | Navigate to Teams |
| `Ctrl+4` | Navigate to Calendar |
| `Ctrl+5` | Navigate to Calls |
| `Ctrl+N` | Navigate to Chat (new chat) |
| `Ctrl+E` | Focus search bar |
| `Enter` | Send message (in composer) |
| `Shift+Enter` | New line in message composer |

## Storage Keys

- **State**: `teamsState` (no sid) or `teamsState_<sid>` (with sid)
- **Initial state**: `teamsInitialState` (no sid) or `teamsInitialState_<sid>` (with sid)
