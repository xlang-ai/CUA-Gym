# zoom_web_mock Schema

**Deploy order**: 63 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8063)
**Base URL**: `http://172.17.46.46:8063/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Files**: `GET /files/<sid>/<filename>` → file content

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Home | Dashboard with time display, New Meeting / Join / Schedule / Share Screen actions, upcoming meetings |
| `/chat` | TeamChat | Team Chat with channels, DMs, group DMs, messages, reactions, emoji picker |
| `/chat/:channelId` | TeamChat | Team Chat opened to a specific channel or DM |
| `/meetings` | Meetings | Meeting list (upcoming/previous/personal room), schedule, edit, delete meetings |
| `/contacts` | Contacts | Contact directory, channels list, rooms tab; add/star/delete contacts |
| `/recordings` | Recordings | Cloud recordings table with play, download, share, delete actions |
| `/settings` | Settings | General, Profile, Audio, Video, Chat, Notifications, Keyboard Shortcuts |
| `/room/:id` | Room | Live meeting room with video tiles, toolbar, participants panel, chat panel, reactions, recording |
| `/go` | StateInspector | JSON state inspection endpoint (also served by Vite middleware) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Current logged-in user profile |
| `meetings` | array | All scheduled/ended meetings |
| `contacts` | array | All contacts in the user's directory |
| `recordings` | array | Cloud recordings (video + transcript) |
| `channels` | array | Team Chat channels, DMs, and group DMs |
| `messages` | object | Keyed by channelId → array of messages |
| `settings` | object | Application settings (general, audio, video, notifications, chat) |

### `user` object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `userId` | string | `"u_admin"` | Unique user identifier |
| `username` | string | `"Alex Johnson"` | Display name |
| `email` | string | `"alex.johnson@acme.com"` | Email address |
| `avatar` | string | URL | Avatar image URL |
| `pmi` | string | `"543 888 1234"` | Personal Meeting ID |
| `status` | string | `"available"` | User status: `"available"`, `"busy"`, `"away"`, `"dnd"`, `"offline"` |
| `role` | string | `"Licensed"` | User role/license type |

### `meetings[]` array items

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `meetingId` | string | `"123 456 7890"` | Meeting ID (format: `XXX XXX XXXX`) |
| `title` | string | `"Weekly Team Sync"` | Meeting topic/title |
| `hostId` | string | `"u_admin"` | Host's user ID |
| `hostName` | string | `"Alex Johnson"` | Host's display name |
| `startTime` | string (ISO) | future date | Meeting start time |
| `duration` | number | `60` | Duration in minutes |
| `password` | string | `""` | Passcode (empty string if none) |
| `joinUrl` | string | URL | Join link |
| `participants` | string[] | `["c1","c2"]` | Array of contact IDs invited |
| `settings` | object | see below | Meeting settings |
| `settings.video` | boolean | `true` | Host video on |
| `settings.audio` | boolean | `true` | Audio on |
| `settings.waitingRoom` | boolean | `false` | Waiting room enabled |
| `settings.recording` | string | `"none"` | `"none"` or `"cloud"` |
| `recurring` | boolean | `false` | Whether meeting recurs |
| `recurrence` | object\|null | `null` | `{type, interval, endDate}` — type: `"weekly"` or `"monthly"` |
| `status` | string | `"scheduled"` | `"scheduled"` or `"ended"` |

### Default meeting IDs
- `"123 456 7890"` — Weekly Team Sync (recurring weekly, scheduled)
- `"987 654 3210"` — Project Kickoff (scheduled, has password `"proj2024"`, waiting room on)
- `"111 222 3333"` — Client Review (ended)
- `"444 555 6666"` — Design Review (scheduled)
- `"777 888 9999"` — All Hands Meeting (recurring monthly, ended, has password `"allhands"`)

### `contacts[]` array items

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `contactId` | string | `"c1"` | Unique contact identifier |
| `name` | string | `"Sarah Connor"` | Display name |
| `email` | string | `"sarah@acme.com"` | Email address |
| `avatar` | string | URL | Avatar image URL |
| `status` | string | `"available"` | One of: `"available"`, `"busy"`, `"dnd"`, `"away"`, `"offline"` |
| `department` | string | `"Engineering"` | Department name |
| `starred` | boolean | `false` | Whether contact is starred |

### Default contact IDs
- `c1` — Sarah Connor (Engineering, available, starred)
- `c2` — John Wick (Security, busy)
- `c3` — Tony Stark (Engineering, offline, starred)
- `c4` — Diana Prince (Design, available)
- `c5` — Bruce Wayne (Management, away)
- `c6` — Natasha Romanoff (Operations, dnd)
- `c7` — Peter Parker (Engineering, available, starred)
- `c8` — Wanda Maximoff (Design, offline)

### `recordings[]` array items

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `recordingId` | string | `"rec_001"` | Unique recording identifier |
| `meetingId` | string | `"111 222 3333"` | Associated meeting ID |
| `title` | string | `"Client Review"` | Recording title |
| `url` | string | `"#"` | Playback URL |
| `duration` | string | `"28:45"` | Duration string (human-readable) |
| `created` | string (ISO) | past date | Creation timestamp |
| `size` | string | `"145 MB"` | File size (human-readable) |
| `type` | string | `"video"` | `"video"` or `"transcript"` |

### Default recording IDs
- `rec_001` — Client Review video (28:45, 145 MB)
- `rec_002` — All Hands Meeting video (1:24:30, 512 MB)
- `rec_003` — All Hands Meeting transcript (1:24:30, 24 KB)

### `channels[]` array items

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `channelId` | string | `"ch_general"` | Unique channel identifier |
| `name` | string\|null | `"General"` | Channel name (null for DMs) |
| `type` | string | `"channel"` | `"channel"`, `"dm"`, or `"group_dm"` |
| `members` | string[] | `["u_admin","c1",...]` | Array of user/contact IDs |
| `description` | string | `""` | Channel description |
| `starred` | boolean | `false` | Whether channel is starred |
| `unreadCount` | number | `0` | Unread message count |
| `lastMessage` | object\|null | see below | Last message preview |
| `lastMessage.text` | string | | Message text |
| `lastMessage.senderId` | string | | Sender's user/contact ID |
| `lastMessage.timestamp` | string (ISO) | | When the message was sent |

### Default channel IDs
- `ch_general` — General (channel, starred, 3 unread)
- `ch_engineering` — Engineering (channel, starred, 0 unread)
- `ch_design` — Design (channel, 1 unread)
- `dm_sarah` — DM with Sarah Connor (dm, 2 unread)
- `dm_tony` — DM with Tony Stark (dm, 0 unread)
- `gdm_team_leads` — Team Leads (group_dm, 0 unread)

### `messages` object

Keyed by channelId → array of message objects:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `messageId` | string | `"msg_001"` | Unique message identifier |
| `channelId` | string | `"ch_general"` | Channel this message belongs to |
| `senderId` | string | `"c5"` | Sender's user/contact ID |
| `senderName` | string | `"Bruce Wayne"` | Sender's display name |
| `senderAvatar` | string | URL | Sender's avatar URL |
| `text` | string | | Message content |
| `timestamp` | string (ISO) | | When the message was sent |
| `reactions` | array | `[]` | Array of `{emoji: string, users: string[]}` |
| `replyTo` | string\|null | `null` | Parent message ID (for threading) |
| `replyCount` | number | `0` | Number of replies to this message |
| `edited` | boolean | `false` | Whether message has been edited |
| `pinned` | boolean | `false` | Whether message is pinned |

### Default message ID prefixes by channel
- `ch_general`: `msg_001` through `msg_012` (12 messages)
- `ch_engineering`: `msg_101` through `msg_106` (6 messages)
- `ch_design`: `msg_201` through `msg_204` (4 messages)
- `dm_sarah`: `msg_301` through `msg_305` (5 messages)
- `dm_tony`: `msg_401` through `msg_404` (4 messages)
- `gdm_team_leads`: `msg_501` through `msg_503` (3 messages)

### `settings` object

```
settings: {
  general: {
    theme: "light",          // "light" | "dark" | "system"
    language: "en"           // "en" | "es" | "fr" | "de" | "ja" | "zh"
  },
  audio: {
    input: "Default Microphone (Built-in)",   // microphone device
    output: "Default Speakers (Built-in)",    // speaker device
    autoJoinAudio: true,     // auto-join audio when joining meeting
    muteOnEntry: false       // mute microphone on meeting join
  },
  video: {
    input: "FaceTime Camera",  // camera device
    hd: true,                  // HD video enabled
    mirrorVideo: true,         // mirror self-view
    touchUpAppearance: false   // touch up appearance filter
  },
  notifications: {
    email: true,               // email notifications
    push: true,                // desktop push notifications
    chatNotifications: true,   // chat message notifications
    meetingReminders: true     // meeting reminder notifications
  },
  chat: {
    showPreviews: true,        // show message previews
    playSound: true,           // play sound for incoming messages
    muteNotifications: false,  // mute all chat notifications
    bounceIcon: true           // bounce app icon on notification
  }
}
```

## Data Normalizers

When injecting state via the API, the application normalizes incoming data with flexible field mappings:

| Entity | Accepted Aliases |
|--------|------------------|
| Meeting ID | `meetingId`, `id` |
| Meeting title | `title`, `topic`, `name` |
| Meeting start | `startTime`, `start_time`, `date` |
| Contact ID | `contactId`, `id` |
| Contact name | `name`, `displayName`, `username` |
| Contact avatar | `avatar`, `avatarUrl`, `image` |
| Recording ID | `recordingId`, `id` |
| Recording title | `title`, `topic`, `name` |
| Recording date | `created`, `createdAt`, `date` |
| Recording size | `size`, `fileSize` |
| Channel ID | `channelId`, `id` |
| Message ID | `messageId`, `id` |
| Message text | `text`, `content` |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8063/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "userId": "u_admin",
          "username": "Alex Johnson",
          "email": "alex.johnson@acme.com",
          "avatar": "https://ui-avatars.com/api/?name=Alex+Johnson&background=0B5CFF&color=fff&size=128",
          "pmi": "543 888 1234",
          "status": "available",
          "role": "Licensed"
        },
        "contacts": [
          {"contactId": "c1", "name": "Sarah Connor", "email": "sarah@acme.com", "avatar": "https://ui-avatars.com/api/?name=Sarah+Connor&background=random&color=fff&size=128", "status": "available", "department": "Engineering", "starred": true},
          {"contactId": "c2", "name": "John Wick", "email": "john@acme.com", "avatar": "https://ui-avatars.com/api/?name=John+Wick&background=random&color=fff&size=128", "status": "busy", "department": "Security", "starred": false}
        ],
        "meetings": [
          {
            "meetingId": "123 456 7890",
            "title": "Weekly Team Sync",
            "hostId": "u_admin",
            "hostName": "Alex Johnson",
            "startTime": "2026-03-14T10:00:00.000Z",
            "duration": 60,
            "password": "",
            "joinUrl": "https://zoom-mock.web/j/1234567890",
            "participants": ["c1", "c2"],
            "settings": {"video": true, "audio": true, "waitingRoom": false, "recording": "none"},
            "recurring": true,
            "recurrence": {"type": "weekly", "interval": 1, "endDate": null},
            "status": "scheduled"
          }
        ],
        "recordings": [
          {"recordingId": "rec_001", "meetingId": "111 222 3333", "title": "Client Review", "url": "#", "duration": "28:45", "created": "2026-03-12T15:30:00.000Z", "size": "145 MB", "type": "video"}
        ],
        "channels": [
          {"channelId": "ch_general", "name": "General", "type": "channel", "members": ["u_admin", "c1", "c2"], "description": "Company-wide announcements", "starred": true, "unreadCount": 0, "lastMessage": null}
        ],
        "messages": {
          "ch_general": [
            {"messageId": "msg_001", "channelId": "ch_general", "senderId": "c1", "senderName": "Sarah Connor", "senderAvatar": "https://ui-avatars.com/api/?name=Sarah+Connor&background=random&color=fff&size=128", "text": "Good morning everyone!", "timestamp": "2026-03-13T08:00:00.000Z", "reactions": [], "replyTo": null, "replyCount": 0, "edited": false, "pinned": false}
          ]
        },
        "settings": {
          "general": {"theme": "light", "language": "en"},
          "audio": {"input": "Default Microphone (Built-in)", "output": "Default Speakers (Built-in)", "autoJoinAudio": true, "muteOnEntry": false},
          "video": {"input": "FaceTime Camera", "hd": true, "mirrorVideo": true, "touchUpAppearance": false},
          "notifications": {"email": true, "push": true, "chatNotifications": true, "meetingReminders": true},
          "chat": {"showPreviews": true, "playSound": true, "muteNotifications": false, "bounceIcon": true}
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Schedule new meeting | `meetings` array grows by 1 with status `"scheduled"` |
| Edit meeting details | `meetings[i].title`, `startTime`, `duration`, `password`, or `settings` updated |
| Delete meeting | `meetings` array shrinks by 1 |
| Send chat message | `messages[channelId]` array grows by 1; `channels[i].lastMessage` updated |
| Edit chat message | `messages[channelId][i].text` updated; `edited` → `true` |
| Delete chat message | `messages[channelId]` array shrinks by 1 |
| Add/toggle emoji reaction | `messages[channelId][i].reactions` array modified (emoji added/toggled for user) |
| Create new channel | `channels` array grows; `messages[newChannelId]` initialized to `[]` |
| Delete channel | `channels` array shrinks; `messages[channelId]` key removed |
| Add new contact | `contacts` array grows by 1 |
| Star/unstar contact | `contacts[i].starred` toggled |
| Update contact status | `contacts[i].status` changed |
| Delete contact | `contacts` array shrinks by 1 |
| Delete recording | `recordings` array shrinks by 1 |
| Add recording | `recordings` array grows by 1 |
| Update user profile | `user.username` (or other fields) updated |
| Change settings | `settings.general`, `settings.audio`, `settings.video`, `settings.notifications`, or `settings.chat` sub-fields updated |
| Change theme | `settings.general.theme` → `"light"`, `"dark"`, or `"system"` |
| Change language | `settings.general.language` updated |
| Toggle audio setting | `settings.audio.autoJoinAudio` or `settings.audio.muteOnEntry` toggled |
| Toggle video setting | `settings.video.hd`, `mirrorVideo`, or `touchUpAppearance` toggled |
| Toggle notification | `settings.notifications.*` boolean toggled |
| Toggle chat setting | `settings.chat.*` boolean toggled |

## State Diff Format (from `/go` endpoint)

The client-side `/go` route returns:
```json
{
  "initial_state": { ... },
  "current_state": { ... },
  "state_diff": {
    "user_changed": false,
    "meetings_changed": true,
    "contacts_changed": false,
    "recordings_changed": false,
    "channels_changed": false,
    "messages_changed": true,
    "settings_changed": false
  }
}
```

The server-side `/go?sid=<sid>` endpoint returns a field-level diff object showing which top-level keys have `added` or `modified` sub-objects.
