# pinterest_mock Schema

**Deploy order**: 36 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8036)
**Base URL**: `http://172.17.46.46:8036/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Home | Masonry grid of all pins with search filtering and infinite scroll |
| `/profile/:userId` | Profile | User profile with created/saved tabs, boards grid, edit profile |
| `/board/:boardId` | BoardDetail | Board view with sections, pins, edit/delete board |
| `/create` | CreatePin | Create a new pin with image upload, title, description, link, board selector |
| `/go` | Go | Debug endpoint showing `{initial_state, current_state, state_diff}` as JSON |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Active logged-in user (same shape as `users[]` items) |
| `users` | array | All users in the system |
| `pins` | array | All pins (images) across all users and boards |
| `boards` | array | All boards across all users; each contains nested `sections[]` |
| `comments` | array | All comments across all pins |
| `notifications` | array | Notifications for the current user |
| `searchQuery` | string | Current active search query text (default: `""`) |
| `searchFilters` | array | Active category filter chips (default: `[]`) |
| `selectedCategory` | string\|null | Currently selected explore category (default: `null`) |
| `lastUsedBoardId` | string | ID of the last board used for quick-save (default: `"b1"`) |

### `currentUser` / `users[]` object

| Field | Type | Default (currentUser) | Description |
|-------|------|-----------------------|-------------|
| `id` | string | `"u1"` | Unique user ID |
| `username` | string | `"sarah_designs"` | Username handle |
| `name` | string | `"Sarah Chen"` | Display name |
| `avatar` | string | `"https://i.pravatar.cc/150?u=sarah"` | Avatar image URL |
| `bio` | string | `"Interior designer & plant mom \| NYC"` | Profile bio text |
| `website` | string | `"https://sarahchen.design"` | User website URL |
| `followers` | string[] | `["u2","u3","u4","u5"]` | Array of user IDs that follow this user |
| `following` | string[] | `["u2","u3"]` | Array of user IDs this user follows |
| `monthlyViews` | number | `12400` | Monthly profile views count |
| `createdAt` | number | (timestamp) | Account creation timestamp (ms) |

### `pins[]` object

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `id` | string | `"p1"` | Unique pin ID |
| `userId` | string | `"u2"` | ID of the user who created the pin |
| `title` | string | `"Minimalist Living Room"` | Pin title |
| `description` | string | `"Beautiful interior inspiration..."` | Pin description text |
| `image` | string | `"https://picsum.photos/400/..."` | Pin image URL |
| `imageWidth` | number | `400` | Image width in pixels |
| `imageHeight` | number | `300`-`800` | Image height in pixels (varies for masonry layout) |
| `url` | string | `"https://example.com/interior/1"` | Source/destination URL for the pin |
| `boardId` | string\|null | `"b1"` or `null` | Board this pin belongs to (null if unsaved) |
| `sectionId` | string\|null | `"sec1"` or `null` | Section within a board (null if not in a section) |
| `altText` | string | `"Minimalist Living Room - interior category"` | Accessibility alt text |
| `tags` | string[] | `["interior","minimalist"]` | Tag labels for categorization and search |
| `likes` | number | `42` | Total like count |
| `likedBy` | string[] | `[]` | Array of user IDs who liked this pin |
| `commentCount` | number | `3` | Number of comments on this pin |
| `saves` | number | `150` | Total save count |
| `createdAt` | number | (timestamp) | Creation timestamp (ms) |

### `boards[]` object

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `id` | string | `"b1"` | Unique board ID |
| `userId` | string | `"u1"` | ID of the board owner |
| `name` | string | `"Home Decor Ideas"` | Board name |
| `description` | string | `"Inspiration for my apartment renovation"` | Board description |
| `privacy` | string | `"public"` or `"secret"` | Privacy setting |
| `coverPinId` | string\|null | `"p1"` or `null` | ID of pin used as board cover image |
| `pins` | string[] | `["p1","p2","p3","p4","p5"]` | Array of pin IDs saved to this board |
| `sections` | object[] | (see below) | Nested array of board sections |
| `collaborators` | string[] | `[]` | Array of collaborator user IDs |
| `createdAt` | number | (timestamp) | Board creation timestamp (ms) |
| `updatedAt` | number | (timestamp) | Last update timestamp (ms) |

### `boards[].sections[]` object

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `id` | string | `"sec1"` | Unique section ID |
| `boardId` | string | `"b1"` | Parent board ID |
| `name` | string | `"Living Room"` | Section name |
| `pins` | string[] | `["p1","p3"]` | Array of pin IDs in this section |

### `comments[]` object

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `id` | string | `"c1"` | Unique comment ID |
| `pinId` | string | `"p1"` | ID of the pin this comment belongs to |
| `userId` | string | `"u2"` | ID of the comment author |
| `text` | string | `"Love this color palette!"` | Comment text content |
| `likes` | number | `3` | Total like count on the comment |
| `likedBy` | string[] | `["u1"]` | Array of user IDs who liked this comment |
| `createdAt` | number | (timestamp) | Comment creation timestamp (ms) |

### `notifications[]` object

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `id` | string | `"n1"` | Unique notification ID |
| `type` | string | `"save"` | Notification type: `"save"`, `"follow"`, `"comment"`, `"like"`, `"recommendation"`, `"board_invite"` |
| `fromUserId` | string\|null | `"u2"` or `null` | ID of the user who triggered the notification (null for system notifications) |
| `targetId` | string\|null | `"p1"` or `"b5"` or `null` | Target entity ID (pin ID starts with "p", board ID starts with "b") |
| `message` | string | `"Marco Rivera saved your pin"` | Notification message text |
| `thumbnail` | string\|null | `null` | Optional thumbnail URL |
| `read` | boolean | `false` | Whether the notification has been read |
| `createdAt` | number | (timestamp) | Notification creation timestamp (ms) |

## Default IDs

### Default user IDs
| ID | Username | Name | Role |
|----|----------|------|------|
| `u1` | `sarah_designs` | Sarah Chen | **currentUser** |
| `u2` | `chef_marco` | Marco Rivera | |
| `u3` | `wanderlust_emma` | Emma Thompson | |
| `u4` | `diy_david` | David Park | |
| `u5` | `fashion_nina` | Nina Rodriguez | |

### Default board IDs (currentUser's boards)
| ID | Name | Privacy | Pins | Sections |
|----|------|---------|------|----------|
| `b1` | Home Decor Ideas | public | `p1-p5` | `sec1` (Living Room), `sec2` (Kitchen) |
| `b2` | Recipes to Try | public | `p9-p12` | (none) |
| `b3` | Travel Bucket List | public | `p17-p20` | `sec3` (Europe), `sec4` (Asia) |
| `b4` | Gift Ideas | secret | `p33,p37` | (none) |
| `b5` | DIY Projects | public | `p33-p35` | (none), collaborator: `u4` |

### Other users' boards
| ID | Owner | Name |
|----|-------|------|
| `b6` | `u2` | My Best Recipes |
| `b7` | `u3` | Dream Destinations |

### Default pin IDs
48 pins total (`p1` through `p48`), generated from 6 categories with 8 titles each:
- `p1`-`p8`: **interior** (Minimalist Living Room, Cozy Reading Nook, Scandinavian Kitchen, Boho Bedroom, Modern Bathroom Design, Rustic Dining Table, Small Space Solutions, Plant Corner Ideas)
- `p9`-`p16`: **food** (Homemade Pasta Recipe, Summer Salad Bowl, Chocolate Lava Cake, Avocado Toast Ideas, Smoothie Bowl Art, Japanese Ramen, Mediterranean Platter, Breakfast Inspiration)
- `p17`-`p24`: **travel** (Santorini Sunset, Tokyo Street Scene, Patagonia Hiking Trail, Venice Canal View, Northern Lights Iceland, Bali Rice Terraces, NYC Skyline, Safari Adventure)
- `p25`-`p32`: **fashion** (Fall Outfit Inspo, Minimalist Wardrobe, Street Style Paris, Summer Dress Collection, Sneaker Culture, Vintage Denim Looks, Accessory Styling, Capsule Wardrobe)
- `p33`-`p40`: **diy** (Macrame Wall Hanging, Painted Furniture, Garden Planter Box, Candle Making, Concrete Planters, Resin Art Tutorial, Wood Burning Art, Tie-Dye T-Shirts)
- `p41`-`p48`: **art** (Watercolor Landscape, Abstract Painting, Digital Illustration, Pottery Workshop, Calligraphy Practice, Sketchbook Ideas, Collage Art, Photography Tips)

### Default comment IDs
| ID | Pin | Author | Text (truncated) |
|----|-----|--------|-------------------|
| `c1` | `p1` | `u2` | "Love this color palette!..." |
| `c2` | `p1` | `u3` | "Those plants really complete the room" |
| `c3` | `p1` | `u4` | "Just saved this to my home reno board!" |
| `c4` | `p9` | `u1` | "Made this last weekend..." |
| `c5` | `p9` | `u5` | "What type of flour did you use?" |
| `c6` | `p17` | `u4` | "Santorini is on my bucket list!..." |
| `c7` | `p17` | `u3` | "Go in September..." |
| `c8` | `p25` | `u5` | "This outfit is everything" |
| `c9` | `p33` | `u1` | "Tried this and it took me 3 hours..." |
| `c10` | `p41` | `u2` | "Beautiful brushwork!..." |

### Default notification IDs
| ID | Type | From | Target | Read |
|----|------|------|--------|------|
| `n1` | `save` | `u2` | `p1` | false |
| `n2` | `follow` | `u5` | (none) | false |
| `n3` | `comment` | `u3` | `p1` | false |
| `n4` | `like` | `u4` | `p9` | true |
| `n5` | `save` | `u3` | `p2` | true |
| `n6` | `recommendation` | (system) | `p45` | true |
| `n7` | `board_invite` | `u4` | `b5` | false |
| `n8` | `comment` | `u2` | `p17` | true |

### Default section IDs
| ID | Board | Name |
|----|-------|------|
| `sec1` | `b1` | Living Room |
| `sec2` | `b1` | Kitchen |
| `sec3` | `b3` | Europe |
| `sec4` | `b3` | Asia |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8036/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "u1",
          "username": "sarah_designs",
          "name": "Sarah Chen",
          "avatar": "https://i.pravatar.cc/150?u=sarah",
          "bio": "Interior designer & plant mom | NYC",
          "website": "https://sarahchen.design",
          "followers": ["u2"],
          "following": ["u2"],
          "monthlyViews": 12400,
          "createdAt": 1700000000000
        },
        "users": [
          {"id": "u1", "username": "sarah_designs", "name": "Sarah Chen", "avatar": "https://i.pravatar.cc/150?u=sarah", "bio": "Interior designer", "website": "", "followers": ["u2"], "following": ["u2"], "monthlyViews": 12400, "createdAt": 1700000000000},
          {"id": "u2", "username": "chef_marco", "name": "Marco Rivera", "avatar": "https://i.pravatar.cc/150?u=marco", "bio": "Professional chef", "website": "", "followers": ["u1"], "following": ["u1"], "monthlyViews": 8900, "createdAt": 1700000000000}
        ],
        "pins": [
          {"id": "p1", "userId": "u2", "title": "Amazing Pasta", "description": "Delicious homemade pasta recipe", "image": "https://picsum.photos/400/500?random=p1", "imageWidth": 400, "imageHeight": 500, "url": "https://example.com/food/1", "boardId": null, "sectionId": null, "altText": "Pasta dish", "tags": ["food", "pasta"], "likes": 10, "likedBy": [], "commentCount": 0, "saves": 25, "createdAt": 1700000000000}
        ],
        "boards": [
          {"id": "b1", "userId": "u1", "name": "My Recipes", "description": "Favorite recipes", "privacy": "public", "coverPinId": null, "pins": [], "sections": [], "collaborators": [], "createdAt": 1700000000000, "updatedAt": 1700000000000}
        ],
        "comments": [],
        "notifications": [],
        "searchQuery": "",
        "searchFilters": [],
        "selectedCategory": null,
        "lastUsedBoardId": "b1"
      }
    }
  }
}
```

## State Normalization

When injecting custom state, each array item is normalized with these fallback field mappings:

| Entity | Accepted Aliases |
|--------|-----------------|
| **user** | `id` or auto-generated; `username` / `handle` / `name`; `avatar` / `image` / `photo` / `profileImage` |
| **pin** | `userId` / `user` / `authorId` / `author`; `title` / `name`; `description` / `desc` / `text` / `body`; `image` / `img` / `src` / `imageUrl`; `url` / `link` / `sourceUrl`; `createdAt` / `created` |
| **board** | `userId` / `user`; `name` / `title` |
| **comment** | `userId` / `user`; `text` / `body` / `content` / `message` |
| **notification** | All fields have sensible defaults if omitted |

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Search for pins | `searchQuery` updated to query text |
| Save pin to board (quick-save) | `boards[i].pins` gains pin ID; `pins[i].boardId` set; `lastUsedBoardId` updated |
| Save pin to specific board | `boards[i].pins` gains pin ID; `pins[i].boardId` set; `lastUsedBoardId` updated |
| Remove pin from board | `boards[i].pins` shrinks; `pins[i].boardId` and `sectionId` cleared |
| Create new board | `boards` array grows by 1 |
| Update board (name/desc/privacy) | `boards[i].name`, `description`, or `privacy` updated; `updatedAt` refreshed |
| Delete board | `boards` array shrinks; pins in that board have `boardId`/`sectionId` cleared |
| Create section in board | `boards[i].sections` gains new section object |
| Create new pin | `pins` array grows by 1 (prepended); optionally `boards[i].pins` grows if boardId provided |
| Delete pin | `pins` shrinks; removed from all `boards[].pins` and `sections[].pins`; associated `comments` removed; `coverPinId` cleared if matched |
| Update pin | `pins[i]` fields updated (spread merge) |
| Like/unlike pin | `pins[i].likedBy` toggled; `pins[i].likes` incremented/decremented |
| Add comment on pin | `comments` array grows by 1; `pins[i].commentCount` incremented |
| Delete comment | `comments` array shrinks by 1; `pins[i].commentCount` decremented |
| Like/unlike comment | `comments[i].likedBy` toggled; `comments[i].likes` incremented/decremented |
| Follow/unfollow user | `currentUser.following` toggled; `users[targetIndex].followers` toggled; `currentUser` in `users[]` also updated |
| Mark notification as read | `notifications[i].read` → `true` |
| Mark all notifications read | All `notifications[].read` → `true` |
| Edit profile | `currentUser` fields updated (`name`, `username`, `bio`, `website`, `avatar`); matching `users[]` entry also updated |
| Create board + save pin inline | `boards` grows; `boards[new].pins` gets pin ID; `pins[i].boardId` set; `lastUsedBoardId` updated |

## Store Actions (Context API)

The store is provided via React Context (`StoreContext`) and exposes:

| Action | Signature | Description |
|--------|-----------|-------------|
| `addPin` | `(pinData)` | Creates a new pin; auto-generates ID, sets defaults, prepends to `pins` |
| `createBoard` | `(boardData)` → board | Creates a new board; returns the new board object |
| `updateBoard` | `(boardId, updates)` | Updates board fields by ID |
| `savePinToBoard` | `(pinId, boardId)` | Adds pin to board; updates pin's `boardId`; updates `lastUsedBoardId` |
| `removePinFromBoard` | `(pinId, boardId)` | Removes pin from board and its sections; clears pin's `boardId`/`sectionId` |
| `deleteBoard` | `(boardId)` | Deletes board; clears `boardId`/`sectionId` on all associated pins |
| `createSection` | `(boardId, name)` | Adds a new section to a board |
| `followUser` | `(targetUserId)` | Toggles follow/unfollow; updates both `currentUser.following` and target `users[].followers` |
| `setSearchQuery` | `(query)` | Sets `searchQuery` in state |
| `addComment` | `(pinId, text)` | Adds comment; increments `pin.commentCount` |
| `deleteComment` | `(commentId)` | Removes comment; decrements associated `pin.commentCount` |
| `likePin` | `(pinId)` | Toggles like on pin for current user |
| `likeComment` | `(commentId)` | Toggles like on comment for current user |
| `deletePin` | `(pinId)` | Removes pin from everywhere (boards, sections, comments, cover references) |
| `updatePin` | `(pinId, updates)` | Updates pin fields by ID |
| `markNotificationRead` | `(notificationId)` | Sets single notification as read |
| `markAllNotificationsRead` | `()` | Marks all notifications as read |
| `updateProfile` | `(updates)` | Updates `currentUser` and matching `users[]` entry |
| `getDebugState` | `()` → `{initial_state, current_state, state_diff}` | Returns full debug state for `/go` endpoint |

## localStorage Keys

| Key Pattern | Description |
|-------------|-------------|
| `pinteract_state` | Current state (no session) |
| `pinteract_state_<sid>` | Current state for session `<sid>` |
| `pinteract_initialState` | Initial/baseline state (no session) |
| `pinteract_initialState_<sid>` | Initial/baseline state for session `<sid>` |
