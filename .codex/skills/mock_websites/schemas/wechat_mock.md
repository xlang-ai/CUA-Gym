# wechat_mock Schema

**Deploy order**: 57 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8057)
**Base URL**: `http://172.17.46.46:8057/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{success, files: [{original_name, stored_name, size, content_type, url}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## State Management

Uses **Zustand** (`src/store.js`) with localStorage persistence (key: `wechat_mock_data[_<sid>]`). State is automatically synced to the server on every mutation via `saveToStorage()` → `POST /post` with `action: "set_current"`. Default data is generated in `defaultState.js` (shared between Vite server and React app).

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Current logged-in user profile |
| `contacts` | array | All contacts (friends) of the current user |
| `conversations` | array | Active conversation list displayed on Messages tab |
| `messages` | object | Keyed by contactId or groupId → array of message objects |
| `moments` | array | WeChat Moments (timeline/feed) posts |
| `groups` | array | Group chat definitions |
| `favorites` | array | Saved/bookmarked items from chats |

### `user` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `userId` | string | `"user_1"` | Unique user identifier |
| `nickname` | string | `"张三"` | Display name |
| `avatar` | string | `"https://picsum.photos/100/100?random=1"` | Avatar image URL |
| `wechatId` | string | `"zhangsan_2024"` | WeChat ID (immutable in UI) |
| `signature` | string | `"每天进步一点点"` | Personal signature / status text |
| `region` | string | `"北京 海淀"` | Geographic region |
| `gender` | string | `"男"` | Gender (`"男"` or `"女"`) |
| `coverImage` | string | `"https://picsum.photos/800/300?random=cover"` | Moments cover banner image URL |
| `phone` | string | `"138****1234"` | Phone number (masked) |

### `contacts[]` (array of objects)

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `userId` | string | `"user_2"` | Unique contact identifier |
| `nickname` | string | `"李四"` | Display name |
| `avatar` | string | URL | Avatar image URL |
| `wechatId` | string | `"lisi_wx"` | WeChat ID |
| `phone` | string | `"139****5678"` | Phone number (masked) |
| `signature` | string | `"简单生活"` | Personal signature |
| `region` | string | `"上海 浦东"` | Geographic region |
| `gender` | string | `"男"` | Gender |
| `tag` | string | `"朋友"` | Contact tag/category (e.g. `"朋友"`, `"同事"`, `"家人"`) |
| `isStar` | boolean | `false` | Whether contact is starred/favorited |

### Default contact IDs

| ID | Nickname | Tag |
|----|----------|-----|
| `user_2` | 李四 | 朋友 |
| `user_3` | 王五 | 同事 |
| `user_4` | 赵六 | 同事 |
| `user_5` | 小明 | 朋友 (isStar: true) |
| `user_6` | 小红 | 朋友 |
| `user_7` | 老板 | 同事 |
| `user_8` | 小美 | 家人 |

### `conversations[]` (array of objects)

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `contactId` | string | `"user_2"` or `"group_1"` | Links to contact userId or group groupId |
| `lastMessage` | string | `"好的，明天见！"` | Preview text of last message |
| `lastTime` | string (ISO) | `"2025-..."` | Timestamp of last message |
| `unreadCount` | number | `2` | Number of unread messages |
| `isGroup` | boolean | `false` | Whether this is a group conversation |
| `isPinned` | boolean | `true` | Whether pinned to top of list |
| `isMuted` | boolean | `false` | Whether notifications are muted |
| `draft` | string | `""` | Unsent draft text |

### Default conversations

| contactId | isGroup | isPinned | isMuted | unreadCount |
|-----------|---------|----------|---------|-------------|
| `user_2` | false | true | false | 2 |
| `group_1` | true | false | false | 5 |
| `user_3` | false | false | false | 0 |
| `user_4` | false | false | false | 1 |
| `user_7` | false | false | true | 0 |

### `messages` (object, keyed by contactId/groupId → array)

Each message object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messageId` | string | yes | Unique message ID (e.g. `"msg_001"`) |
| `senderId` | string | yes | User ID of sender |
| `content` | string | yes | Message content (text, image URL, file name, location text, transfer amount, or greeting for hongbao) |
| `type` | string | yes | One of: `"text"`, `"image"`, `"file"`, `"voice"`, `"location"`, `"transfer"`, `"hongbao"`, `"system"` |
| `timestamp` | string (ISO) | yes | Message send time |
| `isSelf` | boolean | yes | `true` if sent by current user |
| `recalled` | boolean | no | `true` if message was recalled (content set to `""`) |
| `amount` | number | hongbao | Red envelope amount (e.g. `66.66`) |
| `greeting` | string | hongbao | Red envelope greeting text |
| `opened` | boolean | hongbao | Whether the red envelope has been opened |
| `duration` | number | voice | Voice message duration in seconds |
| `fileName` | string | file | Original file name |
| `fileSize` | string | file | File size string (e.g. `"3.2MB"`) |
| `locationName` | string | location | Location name (optional) |
| `locationAddress` | string | location | Location address (optional) |

### Default message threads

| Key | Message Count | Types Present |
|-----|--------------|---------------|
| `user_2` | 7 | text, hongbao |
| `user_3` | 5 | text, image, voice |
| `user_4` | 4 | text, file |
| `user_7` | 4 | text |
| `group_1` | 6 | text |

### `moments[]` (array of objects)

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `postId` | string | `"moment_1"` | Unique moment post ID |
| `userId` | string | `"user_2"` | Author user ID |
| `content` | string | `"周末去爬山了..."` | Text content of the post |
| `images` | array of strings | `["https://..."]` | Array of image URLs (0-9 images) |
| `timestamp` | string (ISO) | `"2025-..."` | Post creation time |
| `likes` | array of strings | `["user_1", "user_3"]` | Array of user IDs who liked the post |
| `comments` | array of objects | `[{commentId, userId, content, timestamp, replyTo?}]` | Comments on the post |
| `location` | string | `"北京·香山公园"` | Location tag (empty string if none) |

#### `moments[].comments[]` (nested array)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `commentId` | string | yes | Unique comment ID (e.g. `"c1"`) |
| `userId` | string | yes | Commenter user ID |
| `content` | string | yes | Comment text |
| `timestamp` | string (ISO) | yes | Comment time |
| `replyTo` | string | no | User ID being replied to (for nested replies) |

### Default moments

| postId | userId | Has Images | Likes Count | Comments Count | Location |
|--------|--------|-----------|-------------|----------------|----------|
| `moment_1` | user_2 | yes (3) | 3 | 2 | 北京·香山公园 |
| `moment_2` | user_6 | yes (1) | 4 | 1 | (none) |
| `moment_3` | user_1 | no | 2 | 2 | (none) |
| `moment_4` | user_5 | no | 2 | 0 | 杭州·阿里巴巴西溪园区 |
| `moment_5` | user_3 | yes (2) | 4 | 2 | 广州·天河体育中心 |

### `groups[]` (array of objects)

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `groupId` | string | `"group_1"` | Unique group identifier |
| `name` | string | `"项目讨论组"` | Group display name |
| `avatar` | string | URL | Group avatar image URL |
| `members` | array of strings | `["user_1", "user_3", "user_4", "user_5"]` | Array of member user IDs |
| `createdAt` | string (ISO) | `"2025-01-15T09:00:00Z"` | Group creation time |
| `createdBy` | string | `"user_1"` | User ID of group creator |
| `description` | string | `"用于讨论项目进度"` | Group description |
| `announcement` | string | `"本周五下午3点开会..."` | Group announcement (empty string if none) |

### Default groups

| groupId | Name | Members | Creator |
|---------|------|---------|---------|
| `group_1` | 项目讨论组 | user_1, user_3, user_4, user_5 | user_1 |
| `group_2` | 老同学聚会 | user_1, user_2, user_5, user_6 | user_2 |

### `favorites[]` (array of objects)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `favoriteId` | string | yes | Unique favorite ID (e.g. `"fav_1"`) |
| `type` | string | yes | One of: `"text"`, `"image"`, `"link"`, `"file"` |
| `content` | string | yes | Content (text string, image URL, link URL, or filename) |
| `source` | string | yes | Name of person the item came from |
| `timestamp` | string (ISO) | yes | When the item was favorited |
| `title` | string | link only | Link title |
| `preview` | string | link only | Link preview text |
| `fileName` | string | file only | File name |
| `fileSize` | string | file only | File size string (e.g. `"2.1MB"`) |

### Default favorites

| favoriteId | Type | Source |
|------------|------|--------|
| `fav_1` | text | 李四 |
| `fav_2` | image | 小红 |
| `fav_3` | link | 王五 |
| `fav_4` | file | 赵六 |
| `fav_5` | text | 老板 |

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | redirect → `/messages` | Default redirect |
| `/messages` | MessagesPage | Conversation list (main tab) |
| `/contacts` | ContactsPage | Contacts list with letter index |
| `/discover` | DiscoverPage | Discover tab (Moments, Channels, Mini Programs, etc.) |
| `/profile` | ProfilePage | "Me" tab (user card, favorites, settings, stickers) |
| `/chat/:contactId` | ChatPage | 1-on-1 chat with a contact |
| `/user/:userId` | UserProfilePage | View user profile page |
| `/edit-profile` | EditProfilePage | Edit current user profile fields |
| `/moments` | MomentsPage | Moments (timeline/feed) page |
| `/chat-settings/:contactId` | ChatSettingsPage | Chat settings (mute, pin, background, clear history) |
| `/search-chat/:contactId` | SearchChatPage | Search within chat history |
| `/groups` | GroupsPage | Create new group chat |
| `/group/:groupId` | GroupChatPage | Group chat conversation |
| `/group-info/:groupId` | GroupInfoPage | Group info (members, announcement, settings) |
| `/channels` | ChannelsPage | Video channels page |
| `/go` | StateInspector | State inspection endpoint (JSON) |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8057/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "userId": "user_1",
          "nickname": "张三",
          "avatar": "https://picsum.photos/100/100?random=1",
          "wechatId": "zhangsan_2024",
          "signature": "每天进步一点点",
          "region": "北京 海淀",
          "gender": "男",
          "coverImage": "https://picsum.photos/800/300?random=cover",
          "phone": "138****1234"
        },
        "contacts": [
          {"userId": "user_2", "nickname": "李四", "avatar": "https://picsum.photos/100/100?random=2", "wechatId": "lisi_wx", "phone": "139****5678", "signature": "简单生活", "region": "上海 浦东", "gender": "男", "tag": "朋友", "isStar": false},
          {"userId": "user_3", "nickname": "王五", "avatar": "https://picsum.photos/100/100?random=3", "wechatId": "wangwu_88", "phone": "136****9012", "signature": "热爱运动", "region": "广州 天河", "gender": "男", "tag": "同事", "isStar": false}
        ],
        "conversations": [
          {"contactId": "user_2", "lastMessage": "你好！", "lastTime": "2025-01-20T10:00:00Z", "unreadCount": 1, "isGroup": false, "isPinned": false, "isMuted": false, "draft": ""}
        ],
        "messages": {
          "user_2": [
            {"messageId": "msg_001", "senderId": "user_2", "content": "你好！", "type": "text", "timestamp": "2025-01-20T10:00:00Z", "isSelf": false}
          ]
        },
        "moments": [
          {"postId": "moment_1", "userId": "user_2", "content": "今天天气真好", "images": [], "timestamp": "2025-01-20T09:00:00Z", "likes": [], "comments": [], "location": ""}
        ],
        "groups": [],
        "favorites": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Send text message | `messages[contactId]` array grows by 1 (type: `"text"`, isSelf: `true`); `conversations[].lastMessage` + `lastTime` updated; conversation moved to top |
| Send image/file/voice/location/transfer/hongbao | `messages[contactId]` grows (with appropriate `type`); `conversations[].lastMessage` shows type tag (e.g. `"[图片]"`, `"[文件]"`, `"[语音]"`, `"[位置]"`, `"[转账]"`, `"[微信红包]"`) |
| Receive auto-reply (individual chat) | `messages[contactId]` grows (isSelf: `false`); `conversations[].unreadCount` incremented; conversation moved to top |
| Send group message | `messages[groupId]` grows; `conversations[].lastMessage` updated; auto-reply from random group member follows |
| Recall a message | `messages[contactId][i].recalled` → `true`; `messages[contactId][i].content` → `""` |
| Mark conversation as read | `conversations[i].unreadCount` → `0` |
| Pin/unpin conversation | `conversations[i].isPinned` toggled |
| Mute/unmute conversation | `conversations[i].isMuted` toggled |
| Save draft in chat | `conversations[i].draft` updated |
| Delete conversation | `conversations` array shrinks by 1 |
| Clear chat history | `messages[contactId]` deleted; matching conversation removed |
| Open hongbao (red envelope) | `messages[contactId][i].opened` → `true` |
| Update user profile | `user` fields updated (nickname, signature, region, gender, avatar, coverImage) |
| Post a moment | `moments` array grows (new entry prepended at index 0) |
| Delete a moment | `moments` array shrinks by 1 |
| Like/unlike a moment | `moments[i].likes` array gains/loses `user.userId` |
| Comment on a moment | `moments[i].comments` array grows by 1 |
| Create a group | `groups` array grows; `messages[newGroupId]` initialized to `[]` |
| Update group name | `groups[i].name` updated |
| Set group announcement | `groups[i].announcement` updated |
| Add group member | `groups[i].members` array gains a userId |
| Remove group member | `groups[i].members` array loses a userId |
| Exit group | `groups[i].members` loses current user's ID; matching conversation removed |
| Add contact | `contacts` array grows by 1 |
| Remove contact | `contacts` array shrinks by 1 |

## Message Types Reference

| Type | Content Field | Extra Fields | Display in Conversation List |
|------|--------------|--------------|------------------------------|
| `text` | Message text | (none) | Content as-is |
| `image` | Image URL or data URI | (none) | `[图片]` |
| `file` | File name | `fileName`, `fileSize` | `[文件]` |
| `voice` | `""` (empty) | `duration` (seconds) | `[语音]` |
| `location` | Location text | `locationName?`, `locationAddress?` | `[位置]` |
| `transfer` | Amount string (e.g. `"¥88.00"`) | (none) | `[转账]` |
| `hongbao` | Greeting text | `amount`, `greeting`, `opened` | `[微信红包]` |
| `system` | System message text | (none) | (not shown) |

## State Normalization

When injecting custom state via `POST /post`, the app normalizes incoming data with sensible defaults:

- **Contacts**: `userId` falls back to `id` → `contact_<index>`; `nickname` falls back to `name` → `displayName` → `"未知用户"`
- **Conversations**: `contactId` falls back to `userId` → `id`; `unreadCount` falls back to `unread` → `0`
- **Messages**: `messageId` falls back to `id` → `msg_<index>`; `senderId` falls back to `from`; `content` falls back to `text`

This means you can inject simplified state structures and the app will fill in missing fields.
