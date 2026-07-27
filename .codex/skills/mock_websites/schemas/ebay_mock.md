# ebay_mock Schema

**Deploy order**: 11 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8011)
**Base URL**: `http://172.17.46.46:8011/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}` (optionally add `"merge":true`)
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State inspect**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{success, files: [{original_name, stored_name, size, content_type, url}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## Tech Stack

- React 18 + Vite 5
- React Router v6 (BrowserRouter)
- React Context + useReducer for state management
- Tailwind CSS 3 with custom eBay brand colors
- lucide-react for icons
- date-fns for date formatting
- State persisted to localStorage per session

## Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Home | Homepage with hero banner, category grid, featured active listings |
| `/search` | Search | Search results with sidebar filters; query params `q` (text) and `c` (category) |
| `/item/:id` | ProductDetails | Individual listing detail: images, bid form, buy-it-now, seller info, watchlist toggle |
| `/dashboard` | Dashboard | My eBay: tabs for Buying (active bids + purchase history), Selling (active + sold), Watchlist, Messages |
| `/sell` | CreateListing | Create new listing form (auction or fixed price) |
| `/go` | Go | State inspection endpoint (JSON view of initial_state, current_state, state_diff) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Logged-in user profile |
| `users` | array | All user profiles |
| `listings` | array | All product listings (auction and fixed-price) |
| `orders` | array | Completed purchase orders |
| `messages` | array | User-to-user messages about listings |
| `notifications` | array | System notifications (e.g., outbid alerts) |
| `feedbacks` | array | Feedback left on orders |

### `currentUser` object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"user_1"` | Unique user identifier |
| `username` | string | `"admin"` | Display username |
| `email` | string | `"admin@example.com"` | User email |
| `avatar` | string | `"https://picsum.photos/100/100?random=user1"` | Avatar image URL |
| `feedbackScore` | number | `154` | Cumulative feedback score (positive +1, negative -1) |
| `feedbackRating` | number | `98.5` | Feedback percentage rating |

### `users[]` array items

Same shape as `currentUser`. Default data contains 3 users:

| id | username | feedbackScore | feedbackRating |
|----|----------|---------------|----------------|
| `user_1` | `admin` | 154 | 98.5 |
| `user_2` | `RetroGamer99` | 42 | 100 |
| `user_3` | `CameraPro` | 890 | 99.2 |

### `listings[]` array items

| Field | Type | Default/Notes | Description |
|-------|------|---------------|-------------|
| `id` | string | `"item_1"`, `"item_2"`, etc. | Unique listing identifier |
| `sellerId` | string | User ID reference | ID of the user who created the listing |
| `title` | string | | Listing title |
| `description` | string | | Detailed item description |
| `images` | string[] | URLs to item photos | Array of image URLs |
| `type` | string | `"auction"` or `"fixed"` | Listing format |
| `startingBid` | number\|null | | Starting bid for auctions; null for fixed |
| `currentBid` | number\|null | | Current highest bid for auctions; null for fixed |
| `price` | number\|null | | Fixed price for buy-it-now only listings |
| `buyItNowPrice` | number\|null | | Optional buy-it-now price (auctions may also have this) |
| `bids` | array | `[]` | Array of bid objects (see below) |
| `watchers` | string[] | `[]` | Array of user IDs watching this listing |
| `views` | number | `0` | View count |
| `endTime` | number | Unix timestamp (ms) | When the listing ends |
| `condition` | string | `"Used"` | Item condition: `"New"`, `"Open Box"`, `"Used"`, `"Refurbished"`, `"For Parts"` |
| `shipping` | number | `0` | Shipping cost in dollars |
| `category` | string | `"Electronics"` | Category: `"Electronics"`, `"Cameras"`, `"Books"`, `"Fashion"`, `"Motors"`, `"Collectibles"`, `"Sports"`, `"Home"`, `"Other"` |
| `status` | string | `"active"` | Listing status: `"active"`, `"sold"`, `"ended"` |

### `listings[].bids[]` array items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique bid identifier (e.g., `"bid_1"`, `"bid_<timestamp>"`) |
| `userId` | string | ID of the bidding user |
| `amount` | number | Displayed bid amount |
| `autoBidMax` | number | Maximum auto-bid amount (proxy bidding) |
| `timestamp` | number | Unix timestamp (ms) when bid was placed |

Bids are stored newest-first (index 0 = highest/latest bid).

### `orders[]` array items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique order identifier (e.g., `"order_<timestamp>"`) |
| `listingId` | string | Reference to the purchased listing |
| `buyerId` | string | User ID of the buyer |
| `sellerId` | string | User ID of the seller |
| `amount` | number | Purchase amount in dollars |
| `date` | number | Unix timestamp (ms) of purchase |
| `status` | string | Order status (e.g., `"paid"`) |

### `messages[]` array items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique message identifier (e.g., `"msg_1"`, `"msg_<timestamp>"`) |
| `fromId` | string | Sender user ID |
| `toId` | string | Recipient user ID |
| `listingId` | string | Related listing ID |
| `subject` | string | Message subject line |
| `content` | string | Message body text |
| `read` | boolean | Whether message has been read |
| `timestamp` | number | Unix timestamp (ms) |

### `notifications[]` array items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique notification identifier (e.g., `"notif_<timestamp>"`) |
| `userId` | string | User ID this notification is for |
| `message` | string | Notification text |
| `read` | boolean | Whether notification has been read |

### `feedbacks[]` array items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique feedback identifier (e.g., `"fb_<timestamp>"`) |
| `orderId` | string | Reference to the order |
| `fromUserId` | string | User who left the feedback |
| `toUserId` | string | User who received the feedback |
| `rating` | string | `"positive"`, `"neutral"`, or `"negative"` |
| `comment` | string | Feedback comment text |
| `created` | number | Unix timestamp (ms) |

## Default Data Summary

- **3 users**: `user_1` (admin/current), `user_2` (RetroGamer99), `user_3` (CameraPro)
- **4 listings**:
  - `item_1`: Vintage Nintendo Game Boy Color (auction, seller=user_2, 2 bids, currentBid=$55, BIN=$120, watched by user_1)
  - `item_2`: Canon EOS R5 Camera (fixed-price, seller=user_3, $3200, no bids)
  - `item_3`: Sony WH-1000XM5 Headphones (auction, seller=user_2, startingBid=$150, BIN=$280, watched by user_3)
  - `item_4`: Rare First Edition The Hobbit (auction, seller=user_1, startingBid=$500, no BIN, watched by user_2)
- **0 orders** (empty array)
- **1 message**: from user_2 to user_1 about item_4 ("Can you ship this internationally?")
- **0 notifications** (empty array)
- **0 feedbacks** (empty array)

## Reducer Actions (State Mutations)

| Action | Payload | Effect |
|--------|---------|--------|
| `PLACE_BID` | `{listingId, amount, userId}` | Implements eBay-style proxy bidding. Adds bid(s) to `listings[i].bids`, updates `listings[i].currentBid`. May add outbid notifications. |
| `BUY_NOW` | `{listingId, userId}` | Sets `listings[i].status` to `"sold"`, `listings[i].endTime` to now. Creates new order in `orders[]`. |
| `ADD_WATCHLIST` | `{listingId, userId}` | Appends userId to `listings[i].watchers[]` |
| `REMOVE_WATCHLIST` | `{listingId, userId}` | Removes userId from `listings[i].watchers[]` |
| `SEND_MESSAGE` | `{toId, listingId, subject, content}` | Appends new message to `messages[]` with `fromId` = currentUser |
| `CREATE_LISTING` | `{listing}` | Appends new listing to `listings[]` with auto-generated id, sellerId=currentUser, empty bids/watchers, views=0, status="active" |
| `END_LISTING` | `{listingId, userId}` | Sets `listings[i].status` to `"ended"`, `endTime` to now. Only works if userId matches sellerId. |
| `LEAVE_FEEDBACK` | `{orderId, fromUserId, toUserId, rating, comment}` | Appends feedback to `feedbacks[]`. Updates `users[i].feedbackScore` (+1 positive, -1 negative, 0 neutral). Also updates `currentUser.feedbackScore` if applicable. |
| `INCREMENT_VIEWS` | `{listingId}` | Increments `listings[i].views` by 1 |
| `SET_STATE` | `{...partial state}` | Merges payload into current state |
| `RESET` | none | Resets state to `INITIAL_STATE` |

## Proxy Bidding Logic

The `PLACE_BID` action implements eBay-style automatic bidding:

1. **No previous bids**: New bid placed at `startingBid`, `autoBidMax` = submitted amount
2. **Bid lower than current leader's max**: Current leader auto-outbids; new bidder gets outbid notification
3. **Bid higher than current leader's max**: New bidder wins; previous leader gets outbid notification; displayed price = previous max + $1 increment
4. **Updating own max bid**: If the current leader raises their max, only `autoBidMax` is updated

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8011/?sid=task001",
    "inject_state": true,
    "state_content": {"action": "set", "state": {
      "currentUser": {"id": "user_1", "username": "testbuyer", "email": "test@example.com", "avatar": "https://picsum.photos/100/100?random=1", "feedbackScore": 10, "feedbackRating": 100},
      "users": [
        {"id": "user_1", "username": "testbuyer", "email": "test@example.com", "avatar": "https://picsum.photos/100/100?random=1", "feedbackScore": 10, "feedbackRating": 100},
        {"id": "user_2", "username": "seller1", "email": "seller@example.com", "avatar": "https://picsum.photos/100/100?random=2", "feedbackScore": 50, "feedbackRating": 99}
      ],
      "listings": [
        {
          "id": "item_1",
          "sellerId": "user_2",
          "title": "Test Auction Item",
          "description": "A test item for auction",
          "images": ["https://picsum.photos/400/400?random=item1"],
          "type": "auction",
          "startingBid": 10.00,
          "currentBid": 10.00,
          "buyItNowPrice": 50.00,
          "bids": [],
          "watchers": [],
          "views": 0,
          "endTime": 1999999999999,
          "condition": "New",
          "shipping": 5.00,
          "category": "Electronics",
          "status": "active"
        }
      ],
      "orders": [],
      "messages": [],
      "notifications": [],
      "feedbacks": []
    }}
  }
}
```

## Listing Normalization (Custom State Injection)

When injecting custom state, listings are normalized with these defaults:

| Field | Fallback |
|-------|----------|
| `id` | `"listing_custom_<index>"` |
| `sellerId` | `"user_1"` |
| `title` | `"(No Title)"` |
| `description` | `""` |
| `images` | `[]` |
| `type` | `"auction"` |
| `startingBid` | `0` |
| `currentBid` | `startingBid` or `0` |
| `buyItNowPrice` | `price` or `null` |
| `price` | `buyItNowPrice` or `null` |
| `bids` | `[]` |
| `watchers` | `[]` |
| `views` | `0` |
| `endTime` | 7 days from now |
| `condition` | `"Used"` |
| `shipping` | `0` (also accepts `{cost: N}` object) |
| `category` | `"Other"` |
| `status` | `"active"` |

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Place bid on auction | `listings[i].currentBid` updated, `listings[i].bids[]` gains new entry(ies); possibly `notifications[]` gains outbid alert |
| Buy it now | `listings[i].status` → `"sold"`, `listings[i].endTime` set to now, `orders[]` gains new entry |
| Add to watchlist | `listings[i].watchers[]` gains userId |
| Remove from watchlist | `listings[i].watchers[]` loses userId |
| Toggle watchlist (heart button) | `listings[i].watchers[]` adds or removes currentUser.id |
| Send message to seller | `messages[]` gains new entry with `fromId`, `toId`, `listingId`, `subject`, `content` |
| Create new listing | `listings[]` gains new entry with `sellerId`=currentUser, `status:"active"`, auto-generated `id` |
| End listing early (seller) | `listings[i].status` → `"ended"`, `listings[i].endTime` set to now |
| Leave feedback on order | `feedbacks[]` gains new entry; `users[i].feedbackScore` adjusted by rating; `currentUser.feedbackScore` updated if feedback is for current user |
| View product details page | `listings[i].views` incremented (via `incrementViews`) |
| Search for items | No state change (read-only filtering on `listings[]`) |
