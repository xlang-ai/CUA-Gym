# reddit_mock Schema

**Deploy order**: 43 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8043)
**Base URL**: `http://172.17.46.46:8043/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Merge**: add `"merge":true` to POST body for partial update

Note: vite.config.js uses `port: 0` (random). Actual port assigned at runtime.

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Logged-in user with profile and lists |
| `users` | array | All user profiles |
| `subreddits` | array | All subreddit definitions |
| `posts` | array | All posts across subreddits |
| `comments` | array | All comments (flat, linked by postId/parentId) |
| `votes` | array | All vote records |
| `notifications` | array | Inbox notifications |
| `awards` | array | Available award definitions |

### currentUser fields
```
id, username, avatar, postKarma, commentKarma, cakeDay, about,
joinedSubreddits: string[],   // subreddit IDs
savedPosts: string[],         // post IDs
savedComments: string[],      // comment IDs
hiddenPosts: string[]         // post IDs
```

### users[] fields
```
id, username, avatar, postKarma, commentKarma, cakeDay, about
```

### subreddits[] fields
```
id, name, description, icon, bannerColor, members, online, created,
rules: string[], moderators: string[], flairs: [{id, text, color, bgColor}]
```
Default subreddits: s1=technology, s2=funny, s3=programming, s4-s6 others.

### posts[] fields
```
id, subredditId, userId, title, content, type (text|link|image),
url, flairId, upvotes, downvotes, created,
isStickied, isLocked, isSpoiler, isNSFW,
commentIds: string[], awards: string[], pollOptions
```

### comments[] fields
```
id, postId, parentId (null=top-level), userId, content,
upvotes, downvotes, created, isEdited, isDistinguished, awards: string[]
```

### votes[] fields
```
id, userId, targetId, targetType (post|comment), value (1|-1)
```

### notifications[] fields
```
id, type (reply|mention|...), fromUserId, postId, commentId,
content, read: bool, created
```

### awards[] fields
```
id, name, icon, cost
```

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8043/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "u1",
          "username": "redditor_42",
          "postKarma": 3450,
          "commentKarma": 8920,
          "joinedSubreddits": ["s1", "s2"],
          "savedPosts": [],
          "savedComments": [],
          "hiddenPosts": []
        },
        "subreddits": [
          {"id": "s1", "name": "technology", "members": 14500000, "online": 12000}
        ],
        "posts": [
          {
            "id": "p1",
            "subredditId": "s1",
            "userId": "u2",
            "title": "New AI breakthrough announced",
            "content": "Details here.",
            "type": "text",
            "upvotes": 1500,
            "downvotes": 50,
            "commentIds": []
          }
        ],
        "comments": [],
        "votes": [],
        "notifications": [],
        "awards": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Fields Changed |
|-------------|---------------------|
| Upvote/downvote post | `posts[].upvotes` / `posts[].downvotes`, `votes[]` (entry added/modified) |
| Upvote/downvote comment | `comments[].upvotes` / `comments[].downvotes`, `votes[]` |
| Add comment | `comments[]` (new entry), `posts[].commentIds` (id appended) |
| Create post | `posts[]` (new entry prepended) |
| Join subreddit | `currentUser.joinedSubreddits` (id added) |
| Leave subreddit | `currentUser.joinedSubreddits` (id removed) |
| Save post | `currentUser.savedPosts` (id added) |
| Unsave post | `currentUser.savedPosts` (id removed) |
| Hide post | `currentUser.hiddenPosts` (id added) |
| Edit comment | `comments[].content`, `comments[].isEdited = true` |
| Delete comment | `comments[].content = "[deleted]"`, `comments[].userId = null` |
| Give award | `posts[].awards` or `comments[].awards` (awardId appended) |
| Mark notification read | `notifications[].read = true` |
