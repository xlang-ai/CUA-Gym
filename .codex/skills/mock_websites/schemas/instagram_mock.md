# instagram_mock Schema

**Deploy order**: 24 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8024)
**Base URL**: `http://172.17.46.46:8024/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `users` | object | Keyed by userId → user object: `{id, username, name, avatar, bio, website, followers[], following[], isVerified, isPrivate}` |
| `posts` | array | All posts: `{id, userId, images[], caption, location, likes[], comments[], saved[], created}` |
| `stories` | array | Stories: `{id, userId, image, created, expires, viewed}` |
| `notifications` | array | Notifications: `{id, type, fromUserId, postId, commentId, text, read, created}` |
| `conversations` | array | DM conversations: `{id, participants[], lastMessage, lastMessageTime, unreadCount}` |
| `messages` | array | All messages: `{id, conversationId, senderId, text, type, imageUrl, sharedPostId, created}` |
| `savedPostIds` | array | Post IDs saved/bookmarked by current user (strings) |

### User fields
`{ id, username, name, avatar, bio, website, followers[], following[], isVerified, isPrivate }`

### Post fields
`{ id, userId, images[], caption, location, likes[], comments[], saved[], created }`

### Comment fields (nested in `posts[].comments[]`)
`{ id, userId, text, created, likes[] }`

### Story fields
`{ id, userId, image, created, expires, viewed }`

### Notification types
`"like"` | `"comment"` | `"follow"` | `"mention"` | `"like_comment"`

### Message types
`"text"` | `"image"` | `"post_share"`

### Default user IDs
- `user_admin` (Alex Morgan — currentUser)
- `user_2` (Alice Walker / adventure_seeker)
- `user_3` (Bob Chen / tech_guru)
- `user_4` (Sarah Kim / design_daily)
- `user_5` (Chef Marco / foodie_life)
- `user_6` (Emma Green / nature_lover)
- `user_7` (Jake Thompson / fitness_coach — verified)
- `user_8` (Mia Chen / artsy_vibes)

### Default post IDs
`post_1` through `post_15` (3 from currentUser, 8 from followed users, 4 from unfollowed)

### Default conversation IDs
`conv_1` (admin↔user_2), `conv_2` (admin↔user_3), `conv_3` (admin↔user_5), `conv_4` (admin↔user_7), `conv_5` (group: admin+user_2+user_3)

### Default data counts
- 8 users, 15 posts, 8 stories, 12 notifications, 5 conversations, 25 messages

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8024/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "users": {
          "user_admin": {
            "id": "user_admin",
            "username": "alex_morgan",
            "name": "Alex Morgan",
            "avatar": "https://picsum.photos/150/150?random=1",
            "bio": "Photographer",
            "website": "",
            "followers": ["user_2"],
            "following": ["user_2"],
            "isVerified": false,
            "isPrivate": false
          },
          "user_2": {
            "id": "user_2",
            "username": "adventure_seeker",
            "name": "Alice Walker",
            "avatar": "https://picsum.photos/150/150?random=2",
            "bio": "Travel lover",
            "website": "",
            "followers": ["user_admin"],
            "following": ["user_admin"],
            "isVerified": false,
            "isPrivate": false
          }
        },
        "posts": [
          {
            "id": "post_1",
            "userId": "user_admin",
            "images": ["https://picsum.photos/800/800?random=101"],
            "caption": "Golden hour #photography",
            "location": "San Francisco, CA",
            "likes": ["user_2"],
            "comments": [
              {"id": "c_1", "userId": "user_2", "text": "Stunning!", "created": "2024-01-01T10:00:00Z", "likes": []}
            ],
            "saved": [],
            "created": "2024-01-01T08:00:00Z"
          }
        ],
        "stories": [],
        "notifications": [
          {"id": "notif_1", "type": "like", "fromUserId": "user_2", "postId": "post_1", "commentId": null, "text": "liked your photo.", "read": false, "created": "2024-01-01T10:00:00Z"}
        ],
        "conversations": [
          {"id": "conv_1", "participants": ["user_admin", "user_2"], "lastMessage": "Hello!", "lastMessageTime": "2024-01-01T10:00:00Z", "unreadCount": 1}
        ],
        "messages": [
          {"id": "msg_1", "conversationId": "conv_1", "senderId": "user_2", "text": "Hello!", "type": "text", "imageUrl": null, "sharedPostId": null, "created": "2024-01-01T10:00:00Z"}
        ],
        "savedPostIds": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Like/unlike post | `posts[i].likes` array modified (add/remove `user_admin`) |
| Like/unlike comment | `posts[i].comments[j].likes` array modified |
| Add comment to post | `posts[i].comments` array grows by 1 |
| Delete comment | `posts[i].comments` array shrinks by 1 |
| Save/unsave post | `posts[i].saved` modified; `savedPostIds` modified |
| Delete post | `posts` array shrinks; `savedPostIds` may shrink |
| Follow/unfollow user | `users[user_admin].following` modified; `users[targetId].followers` modified |
| Update profile | `users[user_admin]` fields updated (bio, name, etc.) |
| Create post | `posts` array grows by 1 (prepended) |
| View story | `stories[i].viewed` → `true` |
| Send text message | `messages` grows; `conversations[i].lastMessage` + `lastMessageTime` updated |
| Send image message | `messages` grows with `type: "image"` and `imageUrl` set |
| Share post in DM | `messages` grows with `type: "post_share"` and `sharedPostId` set |
| Mark conversation read | `conversations[i].unreadCount` → `0` |
| Mark notification read | `notifications[i].read` → `true` |
| Mark all notifications read | All `notifications[*].read` → `true` |
