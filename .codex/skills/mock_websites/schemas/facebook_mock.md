# facebook_mock Schema

**Deploy order**: 14 (alphabetical among all *_mock dirs, BASE_PORT=8000 -> port 8014)
**Base URL**: `http://172.17.46.46:8014/`
**Go Endpoint**: `GET /go?sid=<sid>` -> `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Upload**: `POST /upload?sid=<sid>` (multipart/form-data) -> `{files: [...]}`
**Files**: `GET /files/<sid>/<filename>`

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Home | News feed with sidebar, stories, create-post, and right contacts bar |
| `/profile` | Profile | Current user's profile (posts, about, friends, photos tabs) |
| `/profile/:userId` | UserProfile | Other user's profile page |
| `/friends` | Friends | Friend requests and all friends list |
| `/groups` | Groups | Group listings and group posts feed |
| `/pages/:id` | PageProfile | Facebook Page profile with posts, about, reviews |
| `/marketplace` | Marketplace | Marketplace listings grid with search/filter |
| `/watch` | Watch | Video feed (video and photo posts) |
| `/events` | Events | Events listing with RSVP functionality |
| `/saved` | Saved | Saved items (posts, listings, events) |
| `/go` | Go | State inspector (JSON view of initial_state, current_state, state_diff) |

## State Management

- **Pattern**: React Context (`AppContext.jsx`)
- **Storage keys**: `fb_mock_state` / `fb_mock_initialState` (with `_<sid>` suffix when session-based)
- **Persistence**: localStorage, auto-saves on every state change

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | `User` | The logged-in user object (always `user_1` by default) |
| `users` | `Record<string, User>` | Map of all users keyed by user ID (`user_1` through `user_10`) |
| `friendRequests` | `FriendRequest[]` | Pending friend requests for the current user |
| `groups` | `Group[]` | All Facebook groups |
| `pages` | `Page[]` | All Facebook pages |
| `posts` | `Post[]` | All posts (feed, group, and page posts) |
| `notifications` | `Notification[]` | All notifications for the current user |
| `marketplace` | `MarketplaceListing[]` | All marketplace listings |
| `events` | `Event[]` | All events |
| `stories` | `Story[]` | All stories |
| `savedItems` | `SavedItem[]` | Items saved by the current user |
| `messages` | `Record<string, Message[]>` | Messenger conversations keyed by `conv_<userId>` |

---

### User

| Field | Type | Default (user_1) | Description |
|-------|------|-------------------|-------------|
| `id` | `string` | `"user_1"` | Unique identifier (`user_1` through `user_10`) |
| `name` | `string` | `"Admin User"` | Display name |
| `avatar` | `string` | `"https://picsum.photos/100/100?random=user_1"` | Avatar image URL |
| `cover` | `string` | `"https://picsum.photos/1200/400?random=cover_1"` | Cover photo URL |
| `bio` | `string` | `"Software Engineer \| Coffee Lover \| Traveler"` | Profile bio text |
| `friends` | `string[]` | `["user_2", "user_3", "user_4"]` | Array of friend user IDs |
| `location` | `string` | `"San Francisco, CA"` | Location text |
| `workplace` | `string` | `"Tech Corp"` | Workplace name |
| `education` | `string` | `"Stanford University"` | Education institution |
| `joinedDate` | `string` | `"2020-03-15"` | ISO date string of join date |
| `relationship` | `string` | `"Single"` | Relationship status (Single, In a Relationship, Married) |
| `online` | `boolean` | `true` | Online status indicator |

**Default Users**:

| ID | Name | Location | Online |
|----|------|----------|--------|
| `user_1` | Admin User | San Francisco, CA | true |
| `user_2` | Jane Doe | Los Angeles, CA | true |
| `user_3` | John Smith | New York, NY | false |
| `user_4` | Sarah Wilson | Austin, TX | true |
| `user_5` | Mike Brown | Chicago, IL | false |
| `user_6` | Emily Davis | Seattle, WA | true |
| `user_7` | Carlos Rivera | Miami, FL | true |
| `user_8` | Aisha Johnson | Atlanta, GA | false |
| `user_9` | David Kim | San Jose, CA | true |
| `user_10` | Lily Chen | San Francisco, CA | false |

---

### FriendRequest

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `string` | `"user_5"`, `"user_6"` | User ID of the requester |
| `timestamp` | `number` | `Date.now() - 3600000` | Unix timestamp of request |
| `mutualFriends` | `number` | `2` | Count of mutual friends |

**Default friend requests**: From `user_5` (2 mutual) and `user_6` (1 mutual).

---

### Group

| Field | Type | Default (group_1) | Description |
|-------|------|-------------------|-------------|
| `id` | `string` | `"group_1"` | Unique identifier (`group_1` through `group_4`) |
| `name` | `string` | `"React Developers"` | Group name |
| `cover` | `string` | `"https://picsum.photos/1200/400?random=group_1"` | Cover image URL |
| `members` | `string[]` | `["user_1", "user_2", "user_4"]` | Array of member user IDs |
| `description` | `string` | `"A community for React developers..."` | Group description |
| `posts` | `string[]` | `["post_g1"]` | Array of post IDs belonging to this group |
| `privacy` | `string` | `"public"` | `"public"` or `"private"` |
| `category` | `string` | `"Technology"` | Group category |
| `createdBy` | `string` | `"user_1"` | User ID of group creator |

**Default Groups**:

| ID | Name | Privacy | Category | Creator |
|----|------|---------|----------|---------|
| `group_1` | React Developers | public | Technology | user_1 |
| `group_2` | Digital Art Community | public | Art | user_2 |
| `group_3` | Photography Enthusiasts | public | Photography | user_3 |
| `group_4` | Foodie Adventures | private | Food | user_5 |

---

### Page

| Field | Type | Default (page_1) | Description |
|-------|------|-------------------|-------------|
| `id` | `string` | `"page_1"` | Unique identifier (`page_1` through `page_3`) |
| `name` | `string` | `"Tech News Daily"` | Page name |
| `avatar` | `string` | `"https://picsum.photos/100/100?random=page_1"` | Page avatar URL |
| `cover` | `string` | `"https://picsum.photos/1200/400?random=page_cover_1"` | Cover image URL |
| `description` | `string` | `"Your daily dose of technology news..."` | Page description |
| `followers` | `string[]` | `["user_1", "user_3", "user_7", "user_9"]` | Array of follower user IDs |
| `reviews` | `Review[]` | *(see below)* | Array of review objects |
| `posts` | `string[]` | `["post_p1"]` | Array of post IDs |
| `category` | `string` | `"Technology"` | Page category |
| `website` | `string\|null` | `"https://technewsdaily.com"` | Website URL |
| `phone` | `string\|null` | `"+1 (415) 555-0192"` | Phone number |
| `address` | `string\|null` | `"123 Tech Street, San Francisco, CA 94105"` | Physical address |
| `isLiked` | `boolean` | `true` | Whether current user has liked this page |

#### Review (nested in Page)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Review ID (e.g., `"r1"`) |
| `userId` | `string` | Reviewer user ID |
| `rating` | `number` | Rating 1-5 |
| `content` | `string` | Review text |
| `timestamp` | `number` | Unix timestamp |

**Default Pages**:

| ID | Name | Category | isLiked |
|----|------|----------|---------|
| `page_1` | Tech News Daily | Technology | true |
| `page_2` | Foodie Paradise | Food & Beverage | false |
| `page_3` | Travel Adventures Blog | Travel | true |

---

### Post

| Field | Type | Default (post_1) | Description |
|-------|------|-------------------|-------------|
| `id` | `string` | `"post_1"` | Unique identifier |
| `userId` | `string` | `"user_2"` | Author user ID (for user posts) |
| `pageId` | `string\|undefined` | *undefined* | Page ID (for page posts, e.g., `"page_1"`) |
| `groupId` | `string\|undefined` | *undefined* | Group ID (for group posts, e.g., `"group_1"`) |
| `content` | `string` | `"Just finished my latest..."` | Post text content |
| `image` | `string\|null\|undefined` | `"https://picsum.photos/800/400?random=post_1"` | Image URL (for photo posts) |
| `video` | `string\|undefined` | *undefined* | Video URL (for video posts) |
| `link` | `PostLink\|undefined` | *undefined* | Link preview object (for link posts) |
| `likes` | `string[]` | `["user_1", "user_3"]` | Array of user IDs who liked (legacy, kept in sync with reactions) |
| `reactions` | `Reaction[]` | `[{userId:"user_1",type:"love"}, ...]` | Array of reaction objects |
| `comments` | `Comment[]` | *(see below)* | Array of comment objects |
| `timestamp` | `number` | `Date.now() - 7200000` | Unix timestamp |
| `type` | `string` | `"photo"` | Post type: `"status"`, `"photo"`, `"video"`, `"link"`, `"life_event"` |
| `privacy` | `string` | `"friends"` | `"public"`, `"friends"`, or `"private"` |
| `shares` | `number` | `4` | Share count |
| `edited` | `boolean` | `false` | Whether post has been edited |
| `feeling` | `string\|undefined` | *undefined* | Feeling/activity label (e.g., `"grateful"`) |

#### PostLink (nested in Post)

| Field | Type | Description |
|-------|------|-------------|
| `url` | `string` | Link URL |
| `title` | `string` | Link title |
| `description` | `string` | Link description |
| `image` | `string` | Link preview image URL |

#### Reaction (nested in Post)

| Field | Type | Description |
|-------|------|-------------|
| `userId` | `string` | User ID of the reactor |
| `type` | `string` | Reaction type: `"like"`, `"love"`, `"care"`, `"haha"`, `"wow"`, `"sad"`, `"angry"` |

#### Comment (nested in Post)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Comment ID (e.g., `"c1"`, `"c_<timestamp>"`) |
| `userId` | `string` | Author user ID |
| `content` | `string` | Comment text |
| `timestamp` | `number` | Unix timestamp |
| `replies` | `Comment[]` | Array of reply comment objects (same shape, nested) |
| `likes` | `string[]` | Array of user IDs who liked the comment |

**Default Posts** (18 total):

| ID | Author | Type | Context |
|----|--------|------|---------|
| `post_1` | user_2 | photo | Digital art piece |
| `post_2` | user_3 | photo | Beach sunset |
| `post_3` | user_1 | life_event | New job announcement |
| `post_4` | user_4 | link | React article |
| `post_5` | user_2 | video | Painting timelapse |
| `post_6` | user_7 | status | GitHub 1000 stars |
| `post_7` | user_8 | photo | Campaign launch |
| `post_8` | user_5 | photo | Avocado toast recipe |
| `post_9` | user_4 | photo | Tokyo travel |
| `post_10` | user_1 | status | Feeling grateful |
| `post_11` | user_9 | link | LLM trends article |
| `post_12` | user_10 | photo | Series A announcement |
| `post_13` | user_1 | photo | Weekend hike |
| `post_14` | user_1 | photo | Coffee shop |
| `post_g1` | user_2 | status | Group: React Developers (group_1) |
| `post_g2` | user_3 | photo | Group: Photography Enthusiasts (group_3) |
| `post_g3` | user_5 | photo | Group: Foodie Adventures (group_4) |
| `post_p1` | (page_1) | photo | Page: Tech News Daily |
| `post_p2` | (page_2) | photo | Page: Foodie Paradise |
| `post_p3` | (page_3) | photo | Page: Travel Adventures Blog |

---

### Notification

| Field | Type | Default (n1) | Description |
|-------|------|--------------|-------------|
| `id` | `string` | `"n1"` | Unique identifier (`n1` through `n8`) |
| `type` | `string` | `"like"` | Type: `"like"`, `"comment"`, `"friend_request"`, `"group"`, `"event"`, `"page"`, `"mention"` |
| `userId` | `string` | `"user_2"` | User ID who triggered the notification |
| `content` | `string` | `"liked your post"` | Notification description text |
| `read` | `boolean` | `false` | Whether notification has been read |
| `timestamp` | `number` | `Date.now() - 1800000` | Unix timestamp |
| `postId` | `string\|undefined` | `"post_3"` | Related post ID (optional) |
| `groupId` | `string\|undefined` | *undefined* | Related group ID (optional) |
| `pageId` | `string\|undefined` | *undefined* | Related page ID (optional) |

**Default Notifications** (8 total):

| ID | Type | From | Read | Description |
|----|------|------|------|-------------|
| `n1` | like | user_2 | false | liked your post |
| `n2` | comment | user_3 | true | commented on your photo |
| `n3` | friend_request | user_9 | false | sent you a friend request |
| `n4` | like | user_4 | false | loved your post about your new job |
| `n5` | group | user_2 | true | posted in React Developers group |
| `n6` | event | user_7 | false | invited you to React Developers Meetup |
| `n7` | page | user_9 | true | Tech News Daily shared a new post |
| `n8` | mention | user_9 | false | mentioned you in a comment |

---

### MarketplaceListing

| Field | Type | Default (listing_1) | Description |
|-------|------|---------------------|-------------|
| `id` | `string` | `"listing_1"` | Unique identifier (`listing_1` through `listing_10`) |
| `sellerId` | `string` | `"user_9"` | Seller user ID |
| `title` | `string` | `"iPhone 14 Pro Max - 256GB Space Black"` | Listing title |
| `description` | `string` | `"Excellent condition iPhone..."` | Full description |
| `price` | `number` | `750` | Price in USD (0 = free) |
| `currency` | `string` | `"USD"` | Currency code |
| `category` | `string` | `"electronics"` | Category: `"electronics"`, `"home_goods"`, `"sports"`, `"apparel"`, `"entertainment"`, `"free"` |
| `condition` | `string` | `"Used - Like New"` | Condition: `"New"`, `"Used - Like New"`, `"Used - Good"`, `"Used - Fair"` |
| `images` | `string[]` | `["https://picsum.photos/600/600?random=listing_1"]` | Array of image URLs |
| `location` | `string` | `"San Jose, CA"` | Seller location |
| `listed` | `number` | `Date.now() - 86400000` | Unix timestamp when listed |
| `saved` | `boolean` | `false` | Whether current user saved this listing |

**Default Listings** (10 total):

| ID | Title | Price | Category | Seller |
|----|-------|-------|----------|--------|
| `listing_1` | iPhone 14 Pro Max - 256GB | $750 | electronics | user_9 |
| `listing_2` | Vintage Solid Oak Writing Desk | $220 | home_goods | user_3 |
| `listing_3` | Trek Mountain Bike | $380 | sports | user_7 |
| `listing_4` | Nike Air Force 1 Low | $85 | apparel | user_6 |
| `listing_5` | MacBook Pro 16" M2 Pro | $1800 | electronics | user_10 |
| `listing_6` | REI Co-op Half Dome 2 Tent | $95 | sports | user_8 |
| `listing_7` | Coach Signature Tote Bag | $175 | apparel | user_4 |
| `listing_8` | IKEA EKTORP 3-Seater Sofa | $280 | home_goods | user_5 |
| `listing_9` | Box of Art Books - FREE | $0 | free | user_2 |
| `listing_10` | Fender Player Stratocaster | $450 | entertainment | user_7 |

---

### Event

| Field | Type | Default (event_1) | Description |
|-------|------|-------------------|-------------|
| `id` | `string` | `"event_1"` | Unique identifier (`event_1` through `event_4`) |
| `name` | `string` | `"React Developers Meetup"` | Event name |
| `description` | `string` | `"Monthly meetup for React developers..."` | Full description |
| `cover` | `string` | `"https://picsum.photos/1200/400?random=event_1"` | Cover image URL |
| `hostId` | `string` | `"user_1"` | Host user ID |
| `date` | `string` | Dynamic ISO string (5 days from now) | Start date-time ISO string |
| `endDate` | `string` | Dynamic ISO string | End date-time ISO string |
| `location` | `string` | `"Covo SF, 981 Mission St, San Francisco, CA"` | Event location |
| `interested` | `string[]` | `["user_2", "user_7", "user_9"]` | User IDs who marked interested |
| `going` | `string[]` | `["user_1", "user_4"]` | User IDs who marked going |
| `category` | `string` | `"networking"` | Category: `"networking"`, `"social"`, `"education"` |

**Default Events**:

| ID | Name | Host | Category | Days from now |
|----|------|------|----------|---------------|
| `event_1` | React Developers Meetup | user_1 | networking | +5 |
| `event_2` | Summer Beach Party 2026 | user_4 | social | +14 |
| `event_3` | Photography Workshop | user_3 | education | +7 |
| `event_4` | SoMa Food Festival 2026 | user_5 | social | +3 |

---

### Story

| Field | Type | Default (story_1) | Description |
|-------|------|-------------------|-------------|
| `id` | `string` | `"story_1"` | Unique identifier (`story_1` through `story_5`) |
| `userId` | `string` | `"user_2"` | Author user ID |
| `image` | `string\|undefined` | `"https://picsum.photos/420/740?random=story_1"` | Story image URL (for image stories) |
| `bgColor` | `string\|undefined` | *undefined* | Background color hex (for text stories, e.g., `"#1877F2"`) |
| `text` | `string\|undefined` | *undefined* | Text content (for text stories) |
| `timestamp` | `number` | `Date.now() - 3600000` | Unix timestamp |
| `viewed` | `boolean` | `false` | Whether current user has viewed this story |

**Default Stories**:

| ID | User | Viewed |
|----|------|--------|
| `story_1` | user_2 | false |
| `story_2` | user_3 | false |
| `story_3` | user_4 | true |
| `story_4` | user_7 | true |
| `story_5` | user_8 | true |

---

### SavedItem

| Field | Type | Default (saved_1) | Description |
|-------|------|-------------------|-------------|
| `id` | `string` | `"saved_1"` | Unique identifier |
| `type` | `string` | `"post"` | Type: `"post"`, `"listing"`, `"event"`, `"link"` |
| `referenceId` | `string` | `"post_2"` | ID of the saved entity |
| `savedAt` | `number` | `Date.now() - 86400000` | Unix timestamp when saved |
| `collection` | `string\|null` | `null` | Collection name (e.g., `"Furniture"`) or null |

**Default Saved Items**:

| ID | Type | Reference | Collection |
|----|------|-----------|------------|
| `saved_1` | post | post_2 | null |
| `saved_2` | listing | listing_2 | Furniture |
| `saved_3` | event | event_1 | null |

---

### Message

Stored in `messages` map keyed by conversation key (`conv_<userId>`).

| Field | Type | Default (msg_1) | Description |
|-------|------|-----------------|-------------|
| `id` | `string` | `"msg_1"` | Unique identifier |
| `senderId` | `string` | `"user_2"` | Sender user ID |
| `content` | `string` | `"Hey! Did you see my latest art post?"` | Message text |
| `timestamp` | `number` | `Date.now() - 7200000` | Unix timestamp |
| `read` | `boolean` | `true` | Whether message has been read |

**Default Conversations**:

| Conversation Key | Partner | Messages |
|------------------|---------|----------|
| `conv_user_2` | Jane Doe | 5 messages (msg_1 through msg_5), msg_5 unread |
| `conv_user_3` | John Smith | 3 messages (msg_6 through msg_8) |
| `conv_user_4` | Sarah Wilson | 2 messages (msg_9, msg_10), msg_10 unread |

---

## Context Actions (State Mutators)

| Action | Function | Description |
|--------|----------|-------------|
| Add post | `addPost(post)` | Prepends a new post to `posts` array |
| Toggle reaction | `toggleLike(postId, userId, reactionType)` | Adds, changes, or removes a reaction on a post; syncs `likes` and `reactions` |
| Delete post | `deletePost(postId)` | Removes a post from `posts` array |
| Edit post | `editPost(postId, newContent)` | Updates post content and sets `edited: true` |
| Add comment | `addComment(postId, comment, parentId?)` | Adds comment to post; if parentId given, adds as reply |
| Toggle comment like | `toggleCommentLike(postId, commentId, userId, isReply?, parentCommentId?)` | Toggles like on a comment or reply |
| Delete comment | `deleteComment(postId, commentId, isReply?, parentCommentId?)` | Removes a comment or reply |
| Add story | `addStory(story)` | Prepends a new story to `stories` array |
| Mark story viewed | `markStoryViewed(storyId)` | Sets `viewed: true` on a story |
| Mark notification read | `markNotificationRead(notifId)` | Sets `read: true` on a notification |
| Mark all notifications read | `markAllNotificationsRead()` | Sets `read: true` on all notifications |
| Send message | `sendMessage(convKey, content, senderId)` | Appends a new message to the conversation |
| Handle friend request | `handleFriendRequest(requesterId, action)` | Confirms or deletes a friend request; updates friends lists |

---

## Minimal Inject Example

```json
{
  "currentUser": {
    "id": "user_1",
    "name": "Test User",
    "avatar": "https://picsum.photos/100/100?random=user_1",
    "cover": "https://picsum.photos/1200/400?random=cover_1",
    "bio": "Testing profile",
    "friends": ["user_2"],
    "location": "San Francisco, CA",
    "workplace": "Test Corp",
    "education": "Test University",
    "joinedDate": "2024-01-01",
    "relationship": "Single",
    "online": true
  },
  "users": {
    "user_1": {
      "id": "user_1",
      "name": "Test User",
      "avatar": "https://picsum.photos/100/100?random=user_1",
      "cover": "https://picsum.photos/1200/400?random=cover_1",
      "bio": "Testing profile",
      "friends": ["user_2"],
      "location": "San Francisco, CA",
      "workplace": "Test Corp",
      "education": "Test University",
      "joinedDate": "2024-01-01",
      "relationship": "Single",
      "online": true
    },
    "user_2": {
      "id": "user_2",
      "name": "Jane Doe",
      "avatar": "https://picsum.photos/100/100?random=user_2",
      "cover": "https://picsum.photos/1200/400?random=cover_2",
      "bio": "Digital Artist",
      "friends": ["user_1"],
      "location": "Los Angeles, CA",
      "workplace": "Freelance",
      "education": "RISD",
      "joinedDate": "2019-07-22",
      "relationship": "Single",
      "online": true
    }
  },
  "posts": [
    {
      "id": "post_1",
      "userId": "user_2",
      "content": "Hello world! This is a test post.",
      "likes": [],
      "reactions": [],
      "comments": [],
      "timestamp": 1710000000000,
      "type": "status",
      "privacy": "public",
      "shares": 0,
      "edited": false
    }
  ],
  "friendRequests": [],
  "groups": [],
  "pages": [],
  "notifications": [],
  "marketplace": [],
  "events": [],
  "stories": [],
  "savedItems": [],
  "messages": {}
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed | Details |
|-------------|---------------------|---------|
| Create a new post | `posts` | New post object prepended to array with auto-generated `id: "post_<timestamp>"` |
| Like/react to a post | `posts[].reactions`, `posts[].likes` | Reaction added/changed/removed; likes array synced |
| Comment on a post | `posts[].comments` | New comment appended with `id: "c_<timestamp>"` |
| Reply to a comment | `posts[].comments[].replies` | New reply appended to parent comment's replies array |
| Like a comment | `posts[].comments[].likes` | User ID toggled in comment's likes array |
| Like a reply | `posts[].comments[].replies[].likes` | User ID toggled in reply's likes array |
| Delete a comment | `posts[].comments` | Comment removed from array |
| Delete a reply | `posts[].comments[].replies` | Reply removed from parent comment's replies array |
| Edit a post | `posts[].content`, `posts[].edited` | Content updated, `edited` set to `true` |
| Delete a post | `posts` | Post removed from array |
| Accept friend request | `friendRequests`, `currentUser.friends`, `users[].friends` | Request removed; both users' friend lists updated |
| Decline friend request | `friendRequests` | Request removed from array |
| Send a chat message | `messages[conv_<userId>]` | New message appended with `id: "msg_<timestamp>"` |
| Mark notification read | `notifications[].read` | Single notification `read` set to `true` |
| Mark all notifications read | `notifications[].read` | All notifications `read` set to `true` |
| View a story | `stories[].viewed` | Story's `viewed` set to `true` |
| Create a story (text) | `stories` | New story prepended with `bgColor`, `text`, `viewed: false` |
| Create a story (image) | `stories` | New story prepended with `image`, `viewed: false` |

### Notes on State Observation

- The `/go` endpoint (with `?sid=<sid>`) returns server-side state. Without `?sid`, it renders the React Go component which shows client-side localStorage state.
- `currentUser` is duplicated in `users["user_1"]` -- both should stay in sync when friends list changes via friend request handling.
- Post `likes` array and `reactions` array are kept in sync by the `toggleLike` action -- `likes` contains just user IDs, `reactions` contains `{userId, type}` objects.
- Event RSVP changes are tracked in **local component state only** (via `rsvpMap` in Events.jsx) and do NOT persist to the global state/localStorage. They are not observable via `/go`.
- Marketplace listing creation modal exists but the submit handler is a no-op -- new listings are NOT added to state.
