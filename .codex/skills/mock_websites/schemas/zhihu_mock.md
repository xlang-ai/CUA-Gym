# zhihu_mock Schema

**Deploy order**: 61 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8061)
**Base URL**: `http://172.17.46.46:8061/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Merge**: add `"merge":true` to POST body for partial update
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

Note: This is a TypeScript app using Zustand for state management. vite.config.ts uses `port: 0` (random). Actual port assigned at runtime.

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Home | Homepage feed with recommended/followed/hot tabs |
| `/question/:id` | Question | Question detail with answers, follow, write answer |
| `/answer/:id` | Answer | Single answer detail with voting, comments, follow author |
| `/article/:id` | Article | Article detail with author info, related articles |
| `/user/:id` | User | User profile with answers/articles/ideas/collections tabs |
| `/topic/:id` | Topic | Topic page with description and related questions |
| `/search?q=<query>` | Search | Search results across questions, users, topics, articles |
| `/hot` | HotList | Hot questions ranked by viewCount (top 50) |
| `/messages` | Messages | Notification center with read/unread status |
| `/settings` | Settings | Placeholder settings page |
| `/collections` | Collections | Current user's collections list |
| `/discover` | Discover | Placeholder discover page |
| `/waiting` | WaitingForAnswer | Placeholder "waiting for answer" page |
| `/idea/:id` | IdeaPage | Placeholder idea detail page |
| `/go` | StateInspector | State inspection endpoint (JSON in browser, API for non-HTML) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | User | The logged-in user (defaults to `user0`, "Zhang Xiaofan") |
| `users` | User[] | All user profiles (10 default users: user0 through user9) |
| `questions` | Question[] | All questions (8 defaults: q1 through q8) |
| `answers` | Answer[] | All answers (18 defaults: a1 through a18) |
| `articles` | Article[] | All articles (5 defaults: art1 through art5) |
| `comments` | `{[targetId: string]: Comment[]}` | Comments keyed by answer/article ID. Each comment can have nested `replies` |
| `topics` | Topic[] | All topics (10 defaults: topic1 through topic10) |
| `collections` | Collection[] | User's collections/favorites folders (3 defaults: col1 through col3) |
| `notifications` | Notification[] | Notifications for current user (8 defaults: notif1 through notif8) |
| `ideas` | Idea[] | Short-form posts/"thoughts" (5 defaults: idea1 through idea5) |
| `userVoteups` | `{[answerId: string]: boolean}` | Map of answer IDs the current user has upvoted |
| `userFavorites` | `{[itemId: string]: boolean}` | Map of item IDs the current user has favorited |
| `userFollowings` | `{[userId: string]: boolean}` | Map of user IDs the current user follows |
| `userFollowedTopics` | `{[topicId: string]: boolean}` | Map of topic IDs the current user follows |
| `userFollowedQuestions` | `{[questionId: string]: boolean}` | Map of question IDs the current user follows |
| `userCommentVoteups` | `{[commentId: string]: boolean}` | Map of comment IDs the current user has upvoted |

## Type Definitions

### User (currentUser & users[])
```
userId: string              // e.g. "user0", "user1", ...
nickname: string            // Display name (Chinese)
avatar: string              // URL to avatar image
headline: string            // One-line bio/title
description: string         // Longer bio text
gender: "male" | "female" | "other"
location: string            // City name
industry: string            // Industry/field
employment: Employment[]    // [{company, job}]
education: Education[]      // [{school, major}]
followingCount: number
followerCount: number
voteupCount: number         // Total upvotes received
thankedCount: number
favoriteCount: number
answerCount: number
articleCount: number
questionCount: number
```

### Employment (nested in User)
```
company: string
job: string
```

### Education (nested in User)
```
school: string
major: string
```

### Question (questions[])
```
questionId: string          // e.g. "q1", "q2", ... or "q_<timestamp>" for new
title: string               // Question title
description: string         // Question body/details
topics: string[]            // Array of topicId references
authorId: string            // userId of question author
createdTime: number         // Unix timestamp (ms)
updatedTime: number         // Unix timestamp (ms)
followerCount: number       // Number of question followers
viewCount: number           // Number of views
answerCount: number         // Number of answers
```
Default questions: q1 (AI), q2 (learning methods), q3 (programmer competitiveness), q4 (books), q5 (housing prices), q6 (travel), q7 (weight loss), q8 (design aesthetics).

### Answer (answers[])
```
answerId: string            // e.g. "a1", "a2", ... or "a_<timestamp>" for new
questionId: string          // Reference to parent question
authorId: string            // userId of answer author
content: string             // Full answer text (supports \n for newlines)
createdTime: number         // Unix timestamp (ms)
updatedTime: number         // Unix timestamp (ms)
voteupCount: number         // Number of upvotes
commentCount: number        // Number of comments
favoriteCount: number       // Number of favorites/bookmarks
thankCount: number          // Number of thanks
```
Default answers: a1-a5 (for q1), a6-a8 (for q2), a9-a10 (for q3), a11-a12 (for q4), a13-a14 (for q5), a15 (for q6), a16-a17 (for q7), a18 (for q8).

### Article (articles[])
```
articleId: string           // e.g. "art1", "art2", ...
title: string
content: string             // Full article text
coverImage: string          // URL to cover image
authorId: string
columnId?: string           // Optional column reference
topics: string[]            // Array of topicId references
createdTime: number
updatedTime: number
viewCount: number
voteupCount: number
commentCount: number
favoriteCount: number
```
Default articles: art1 (product design), art2 (deep learning), art3 (procrastination psychology), art4 (frontend trends), art5 (Chengdu food guide).

### Comment (comments[targetId][])
```
commentId: string           // e.g. "c1", "c2", ... or "c_<timestamp>" for new
targetId: string            // ID of the answer/article/comment being commented on
targetType: "answer" | "article" | "idea" | "comment"
authorId: string
content: string
createdTime: number
voteupCount: number
replies: Comment[]          // Nested reply comments (same structure, recursive)
```
Default comments exist for answers: a1 (3 top-level comments with replies), a6 (3 comments), a9 (3 comments), a16 (2 comments), a18 (1 comment).

### Topic (topics[])
```
topicId: string             // e.g. "topic1", "topic2", ...
name: string                // Topic name (Chinese)
icon: string                // URL to topic icon
description: string
followerCount: number       // Typically in millions
questionCount: number
parentId?: string           // Optional parent topic reference
```
Default topics: topic1 (Internet), topic2 (AI), topic3 (Psychology), topic4 (Finance), topic5 (Career), topic6 (Reading), topic7 (Food), topic8 (Design), topic9 (Health), topic10 (Travel).

### Collection (collections[])
```
collectionId: string        // e.g. "col1", "col2", ... or "col_<timestamp>" for new
name: string
description: string
privacy: "public" | "private"
itemIds: string[]           // Array of answer/article/idea IDs saved in this collection
itemTypes: ("answer" | "article" | "idea")[]  // Parallel array of item types
createdTime: number
updatedTime: number
```
Default collections: col1 ("My Favorites", private), col2 ("Tech Articles", public), col3 ("Great Answers", public).

### Notification (notifications[])
```
notificationId: string      // e.g. "notif1", ... or "notif_custom_<index>"
type: "voteup" | "comment" | "follow" | "favorite" | "thank" | "invite" | "system"
fromUserId?: string         // Who triggered the notification (absent for "system")
targetId?: string           // Related answer/question/user ID
targetType?: "answer" | "article" | "question" | "comment"
content: string             // Notification text
isRead: boolean
createdTime: number
```
Default: 8 notifications (notif1-notif8). notif1, notif2, notif3, notif6 are unread.

### Idea (ideas[])
```
ideaId: string              // e.g. "idea1", "idea2", ...
authorId: string
content: string             // Short-form text content
images: string[]            // Array of image URLs
topics: string[]            // Array of topicId references
createdTime: number
voteupCount: number
commentCount: number
shareCount: number
```
Default ideas: idea1-idea5 from various users.

## Default State Values

### userVoteups (default)
```json
{"a1": true, "a6": true, "a9": true}
```

### userFavorites (default)
```json
{"a1": true, "a6": true}
```

### userFollowings (default)
```json
{"user1": true, "user3": true}
```

### userFollowedTopics (default)
```json
{"topic1": true, "topic2": true, "topic5": true}
```

### userFollowedQuestions (default)
```json
{"q1": true, "q2": true}
```

### userCommentVoteups (default)
```json
{}
```

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8061/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "userId": "user0",
          "nickname": "TestUser",
          "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=test",
          "headline": "Test Account",
          "description": "A test user",
          "gender": "male",
          "location": "Beijing",
          "industry": "Tech",
          "employment": [{"company": "TestCorp", "job": "Engineer"}],
          "education": [{"school": "MIT", "major": "CS"}],
          "followingCount": 10,
          "followerCount": 5,
          "voteupCount": 100,
          "thankedCount": 20,
          "favoriteCount": 30,
          "answerCount": 5,
          "articleCount": 2,
          "questionCount": 3
        },
        "questions": [
          {
            "questionId": "q1",
            "title": "What is the best programming language?",
            "description": "Looking for opinions on the best language to learn.",
            "topics": ["topic1"],
            "authorId": "user1",
            "followerCount": 500,
            "viewCount": 100000,
            "answerCount": 2
          }
        ],
        "answers": [
          {
            "answerId": "a1",
            "questionId": "q1",
            "authorId": "user1",
            "content": "Python is great for beginners.",
            "voteupCount": 50,
            "commentCount": 5,
            "favoriteCount": 10,
            "thankCount": 3
          }
        ],
        "topics": [
          {
            "topicId": "topic1",
            "name": "Programming",
            "icon": "https://picsum.photos/48/48?random=prog",
            "description": "All about programming",
            "followerCount": 1000000,
            "questionCount": 50000
          }
        ],
        "articles": [],
        "comments": {},
        "collections": [],
        "notifications": [],
        "ideas": [],
        "userVoteups": {},
        "userFavorites": {},
        "userFollowings": {},
        "userFollowedTopics": {},
        "userFollowedQuestions": {},
        "userCommentVoteups": {}
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Fields Changed |
|-------------|---------------------|
| Upvote answer | `userVoteups[answerId]` toggled, `answers[].voteupCount` incremented/decremented |
| Favorite answer (via collection) | `userFavorites[itemId] = true`, `collections[].itemIds` (id appended), `collections[].updatedTime` |
| Remove from collection | `collections[].itemIds` (id removed), possibly `userFavorites[itemId]` deleted if not in any collection |
| Follow user | `userFollowings[userId]` toggled |
| Follow topic | `userFollowedTopics[topicId]` toggled |
| Follow question | `userFollowedQuestions[questionId]` toggled |
| Write answer | `answers[]` (new entry prepended), `questions[].answerCount` incremented |
| Ask question | `questions[]` (new entry prepended), `currentUser.questionCount` incremented |
| Add comment | `comments[targetId][]` (new Comment appended), `answers[].commentCount` incremented |
| Reply to comment | `comments[targetId][].replies[]` (new Comment appended to parent), `answers[].commentCount` incremented |
| Upvote comment | `userCommentVoteups[commentId]` toggled, `comments[][].voteupCount` or `comments[][].replies[].voteupCount` incremented/decremented |
| Mark notification read | `notifications[].isRead = true` |
| Create collection | `collections[]` (new Collection appended) |
| Search | No state change (read-only filtering of questions, users, topics, articles) |

## Notes

- **Current user** is always `users[0]` (userId: "user0") by default.
- **Comments** use a nested structure: top-level comments are stored in `comments[targetId]`, and each comment has a `replies: Comment[]` array for threaded replies.
- **Collections** use parallel arrays `itemIds` and `itemTypes` to track what type each saved item is.
- **Normalizers**: When injecting state, `answers`, `questions`, and `notifications` arrays are normalized -- missing fields get default values and alternative field names (e.g., `id` -> `answerId`, `text` -> `content`) are supported.
- **Merge mode**: Use `"merge": true` in POST body to deep-merge injected state with existing state rather than replacing it.
- **Hot list**: The `/hot` page sorts questions by `viewCount` descending and shows top 50.
- **Search**: The `/search?q=<query>` page filters across questions (title/description), users (nickname/headline), topics (name/description), and articles (title/content) using case-insensitive substring matching.
