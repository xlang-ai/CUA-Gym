# twitter_mock Schema

**Deploy order**: 50 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8050)
**Base URL**: `http://172.17.46.46:8050/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**State endpoint**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Current user**: `u1` (Alex Johnson, @alexj)

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `users` | `User[]` | All users. 8 seed users (u1–u8). |
| `tweets` | `Tweet[]` | All posts/tweets. 18 seed posts (p1–p18). |
| `replies` | `Reply[]` | Inline replies to tweets. 10 seed replies (r1–r10). |
| `notifications` | `Notification[]` | Notifications for current user (u1). 10 seed items (n1–n10). |
| `conversations` | `Conversation[]` | DM conversation metadata. 4 seed convs (conv1–conv4). |
| `directMessages` | `DirectMessage[]` | DM message bodies. 15 seed messages (dm1–dm15). |
| `lists` | `List[]` | Twitter lists owned by u1. 2 seed lists (list1–list2). |
| `trends` | `Trend[]` | Trending topics sidebar. 10 seed trends (t1–t10). |
| `bookmarkedPostIds` | `string[]` | Post IDs bookmarked by u1. Default: `["p3","p2","p8"]`. |
| `currentUser` | `User` | Shallow copy of the logged-in user (u1). |

### User subfields
`id, name, handle, bio, avatar, banner, location, website, joinedDate, verified (bool), followers (userId[]), following (userId[]), pinnedPostId`

### Tweet subfields
`id, userId, content, images (url[]), createdAt, likes (userId[]), reposts (userId[]), retweets (userId[]), replies (replyId[]), bookmarks (userId[]), quotedPostId, inReplyToPostId, inReplyToUserId, views (int)`

### Reply subfields
`id, tweetId, postId, userId, content, createdAt, likes (userId[])`

### Notification subfields
`id, type (like|repost|retweet|follow|reply|mention), userId, postId, tweetId, content, createdAt, read (bool)`

### Conversation subfields
`id, participants (userId[]), lastMessageId, lastMessageAt, isPinned (bool), unreadCount (int)`

### DirectMessage subfields
`id, conversationId, senderId, content, createdAt, read (bool)`

### List subfields
`id, name, description, ownerId, memberIds (userId[]), followerIds (userId[]), isPrivate (bool), createdAt, bannerUrl`

### Trend subfields
`id, category, name, postCount (string)`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8050/?sid=task001",
    "inject_state": true,
    "state_content": {"action": "set", "state": {
      "users": [
        {"id": "u1", "name": "Alex Johnson", "handle": "alexj", "verified": true,
         "followers": ["u2"], "following": ["u2"], "pinnedPostId": null,
         "avatar": "https://i.pravatar.cc/150?u=u1"},
        {"id": "u2", "name": "Sarah Chen", "handle": "sarahc", "verified": true,
         "followers": ["u1"], "following": ["u1"],
         "avatar": "https://i.pravatar.cc/150?u=u2"}
      ],
      "tweets": [
        {"id": "p1", "userId": "u1", "content": "Hello world!", "images": [],
         "likes": [], "reposts": [], "retweets": [], "replies": [], "bookmarks": [], "views": 0}
      ],
      "replies": [],
      "notifications": [],
      "conversations": [],
      "directMessages": [],
      "lists": [],
      "trends": [{"id": "t1", "category": "Technology", "name": "#WebDev", "postCount": "28.5K"}],
      "bookmarkedPostIds": [],
      "currentUser": {"id": "u1", "name": "Alex Johnson", "handle": "alexj",
                      "verified": true, "followers": ["u2"], "following": ["u2"]}
    }}
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Like a tweet | `tweets[i].likes` — u1 added/removed |
| Repost a tweet | `tweets[i].reposts` and `tweets[i].retweets` — u1 added/removed |
| Bookmark a tweet | `bookmarkedPostIds` — postId added/removed |
| Compose new tweet | `tweets` — new entry appended with `userId: "u1"` |
| Reply to tweet | `replies` — new entry; `tweets[i].replies` — reply id added |
| Follow a user | `users[currentUser].following` — target uid added; `users[target].followers` — u1 added |
| Unfollow a user | Reverse of follow |
| Send DM | `directMessages` — new entry; `conversations[i].lastMessageId` + `lastMessageAt` updated |
| Mark notification read | `notifications[i].read` → `true` |
| Edit profile | `users[u1]` fields (name, bio, location, website, etc.); `currentUser` object |
| Pin tweet | `users[u1].pinnedPostId` → tweet id |
| Create list | `lists` — new entry appended |
| Delete tweet | `tweets` — entry removed; parent `tweets[i].replies` array updated |
