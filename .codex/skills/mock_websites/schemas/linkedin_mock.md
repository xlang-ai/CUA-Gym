# linkedin_mock Schema

**Deploy order**: 27 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8027)
**Base URL**: `http://172.17.46.46:8027/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}` (note: inject uses `/post`, not `/go`)
**State Endpoint**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Routes**: `/` (Feed), `/mynetwork`, `/jobs`, `/messaging`, `/notifications`, `/profile/:id`, `/search`, `/go`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | The logged-in user (id: `user_admin`, name: Alex Morgan). Subfields: `id`, `name`, `headline`, `location`, `about`, `avatar`, `banner`, `connections[]` (array of userIds), `experience[]`, `education[]`, `skills[]` |
| `users` | object (map) | Other users keyed by userId (`user_2`..`user_9`). Each has same shape as `currentUser` |
| `companies` | object (map) | Companies keyed by companyId (`company_1`..`company_6`). Fields: `id`, `name`, `logo`, `industry`, `size`, `headquarters`, `description` |
| `posts` | array | Feed posts. Each: `id`, `userId`, `content`, `image`, `reactions` (object with keys `like/celebrate/love/insightful/funny/curious`, each an array of userIds), `comments[]` (`id`, `userId`, `content`, `created`, `likes[]`), `created`, `repostedBy`, `repostOf` |
| `jobs` | array | Job listings. Each: `id`, `title`, `company`, `companyId`, `location`, `type`, `level`, `logo`, `description`, `requirements[]`, `salary`, `posted`, `applicants`, `saved` (bool), `applied` (bool) |
| `chats` | array | DM conversations. Each: `id`, `participants[]` (userIds), `messages[]` (`id`, `senderId`, `content`, `created`, `read`) |
| `notifications` | array | Notifications. Each: `id`, `type` (like/comment/connection_request/connection_accept/profile_view/endorsement/job_alert/mention), `actorId`, `targetId`, `content`, `read` (bool), `created` |
| `connectionRequests` | array | Pending connection requests. Each: `id`, `fromUserId`, `toUserId`, `note`, `status` (pending), `created` |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8027/?sid=task001",
    "inject_state": true,
    "state_content": {"action": "set", "state": {
      "currentUser": {
        "id": "user_admin",
        "name": "Alex Morgan",
        "headline": "Senior Software Engineer at TechCorp",
        "location": "San Francisco Bay Area",
        "about": "Software engineer.",
        "avatar": "https://i.pravatar.cc/200?u=user_admin",
        "banner": "https://picsum.photos/1200/400?random=banner_admin",
        "connections": ["user_2", "user_3"],
        "experience": [],
        "education": [],
        "skills": []
      },
      "users": {},
      "companies": {},
      "posts": [],
      "jobs": [],
      "chats": [],
      "notifications": [],
      "connectionRequests": []
    }}
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Create a post | `posts` array gains new entry at index 0 |
| Delete a post | `posts` array loses the entry |
| React to a post (like/celebrate/etc.) | `posts[i].reactions.<type>` array adds/removes `user_admin` |
| Comment on a post | `posts[i].comments` array gains new entry |
| Save a job | `jobs[i].saved` flips to `true` |
| Apply to a job | `jobs[i].applied` flips to `true` |
| Send a message | `chats[i].messages` array gains new entry |
| Accept connection request | `connectionRequests` loses entry; `currentUser.connections` gains userId |
| Ignore connection request | `connectionRequests` loses entry |
| Send connection request | `connectionRequests` gains new entry with `status: "pending"` |
| Mark notification read | `notifications[i].read` flips to `true` |
| Update profile | `currentUser.name/headline/location/about` fields updated |
| Add/remove experience | `currentUser.experience` array modified |
| Add/remove education | `currentUser.education` array modified |
| Add/remove skill | `currentUser.skills` array modified |
