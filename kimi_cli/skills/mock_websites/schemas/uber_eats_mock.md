# uber_eats_mock Schema

**Deploy order**: 52 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8052)
**Base URL**: `http://172.17.46.46:8052/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{success, files: [{original_name, stored_name, size, content_type, url}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Homepage | Main feed with categories, promotions, filtered restaurant listings |
| `/store/:id` | StorePage | Restaurant detail page with menu, reviews, add-to-cart |
| `/restaurant/:id` | RedirectToStore | Redirects to `/store/:id` |
| `/search` | SearchPage | Search restaurants by name, cuisine, menu item; browse by category |
| `/checkout` | Checkout | Order summary, delivery details, payment, tip, promo code, place order |
| `/orders` | Orders | Active and past orders list with rating and reorder |
| `/orders/:orderId` | OrderTracking | Live order tracking with status progression, delivery person info, receipt |
| `/favorites` | Favorites | Saved/favorited restaurants |
| `/account` | Account | User profile, addresses, payment methods, favorites, Uber One status |
| `/go` | Go | State debug endpoint (JSON: initial_state, current_state, state_diff) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Current user profile, addresses, payment methods, favorites |
| `categories` | array | Food category chips displayed on homepage |
| `restaurants` | array | All available restaurants with metadata |
| `menuItems` | array | All menu items across all restaurants |
| `cart` | object | Current shopping cart state |
| `orders` | array | All orders (active and past) |
| `activeOrderId` | string\|null | ID of the currently tracked active order |
| `promotions` | array | Available promo codes and offers |
| `reviews` | array | Restaurant reviews from users |
| `ui` | object | UI state (selected address, delivery mode, search, filters) |

### `user` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"user_1"` | User ID |
| `name` | string | `"Alex Johnson"` | Full name |
| `email` | string | `"alex.johnson@email.com"` | Email address |
| `phone` | string | `"(415) 555-0123"` | Phone number |
| `avatarUrl` | string | `""` | Avatar image URL |
| `addresses` | array | 2 addresses | Saved delivery addresses |
| `defaultAddressId` | string | `"addr_1"` | Default address ID |
| `paymentMethods` | array | 2 methods | Saved payment methods |
| `defaultPaymentId` | string | `"pay_1"` | Default payment method ID |
| `uberOneActive` | boolean | `false` | Whether Uber One membership is active |
| `favoriteRestaurantIds` | array | `["rest_1", "rest_6"]` | IDs of favorited restaurants |

### `user.addresses[]` Object

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"addr_1"` | Address ID |
| `label` | string | `"Home"` | Address label (Home, Work, etc.) |
| `street` | string | `"123 Main St"` | Street address |
| `apt` | string | `"Apt 4B"` | Apartment/suite |
| `city` | string | `"San Francisco"` | City |
| `state` | string | `"CA"` | State |
| `zip` | string | `"94102"` | Zip code |
| `instructions` | string | `"Ring bell, 2nd floor"` | Delivery instructions |
| `isDefault` | boolean | `true` | Whether this is the default address |

### `user.paymentMethods[]` Object

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"pay_1"` | Payment method ID |
| `type` | string | `"visa"` | Type: `"visa"`, `"paypal"` |
| `label` | string | `"Visa ••••4242"` | Display label |
| `last4` | string | `"4242"` | Last 4 digits (empty for PayPal) |
| `isDefault` | boolean | `true` | Whether this is the default payment method |

### `categories[]` Object

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"cat_1"` | Category ID |
| `name` | string | `"Pizza"` | Category name |
| `icon` | string | `"🍕"` | Emoji icon |

### `restaurants[]` Object

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"rest_1"` | Restaurant ID |
| `name` | string | `"Bella Italia"` | Restaurant name |
| `imageUrl` | string | `""` | Banner/image URL |
| `cuisineType` | array | `["Italian","Pizza","Pasta"]` | Cuisine type tags |
| `rating` | number | `4.6` | Average rating (1-5) |
| `reviewCount` | number | `234` | Total review count |
| `priceRange` | string | `"$$"` | Price range: `"$"`, `"$$"`, `"$$$"`, `"$$$$"` |
| `deliveryFee` | number | `2.49` | Delivery fee in dollars |
| `deliveryTimeMin` | number | `25` | Minimum delivery time in minutes |
| `deliveryTimeMax` | number | `40` | Maximum delivery time in minutes |
| `distance` | number | `1.2` | Distance in miles |
| `isOpen` | boolean | `true` | Whether restaurant is currently open |
| `hours` | string | `"10:00 AM - 11:00 PM"` | Operating hours |
| `address` | string | `"789 Columbus Ave, San Francisco, CA"` | Restaurant address |
| `phone` | string | `"(415) 555-0456"` | Restaurant phone number |
| `isSponsored` | boolean | `false` | Whether restaurant is a sponsored listing |
| `promotions` | array | `[]` | Restaurant-specific promotions |
| `categories` | array | `["Featured Items","Appetizers","Pasta","Pizza","Desserts"]` | Menu category names |
| `tags` | array | `["Popular","Top Rated"]` | Display tags |
| `supportsPickup` | boolean | `true` | Whether pickup orders are supported |
| `pickupTimeMin` | number | `15` | Minimum pickup time in minutes |
| `pickupTimeMax` | number | `25` | Maximum pickup time in minutes |

### `menuItems[]` Object

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"item_1"` | Menu item ID |
| `restaurantId` | string | `"rest_1"` | Parent restaurant ID |
| `category` | string | `"Featured Items"` | Menu category within restaurant |
| `name` | string | `"Margherita Pizza"` | Item name |
| `description` | string | `"Fresh mozzarella, tomato sauce..."` | Item description |
| `price` | number | `14.99` | Base price in dollars |
| `imageUrl` | string | `""` | Item image URL |
| `isPopular` | boolean | `true` | Whether item is marked as popular |
| `isAvailable` | boolean | `true` | Whether item is currently available |
| `dietaryTags` | array | `["Vegetarian"]` | Dietary tags: `"Vegetarian"`, `"Vegan"`, `"Gluten-Free"` |
| `customizationGroups` | array | see below | Customization option groups |

### `menuItems[].customizationGroups[]` Object

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"cg_1"` | Group ID |
| `name` | string | `"Choose your size"` | Group display name |
| `required` | boolean | `true` | Whether a selection is required |
| `maxSelections` | number | `1` | Maximum number of selections (1 = radio, >1 = checkbox) |
| `minSelections` | number | `1` | Minimum number of selections |
| `options` | array | see below | Available options |

### `menuItems[].customizationGroups[].options[]` Object

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"co_1"` | Option ID |
| `name` | string | `"Small (10\")"` | Option display name |
| `priceModifier` | number | `0` | Additional price in dollars |
| `isDefault` | boolean | `true` | Whether option is selected by default |
| `isAvailable` | boolean | `true` | Whether option is currently available |

### `cart` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `restaurantId` | string\|null | `null` | Restaurant ID for items in cart |
| `restaurantName` | string\|null | `null` | Restaurant name for items in cart |
| `items` | array | `[]` | Cart items |
| `deliveryMode` | string | `"delivery"` | `"delivery"` or `"pickup"` |
| `scheduledTime` | string\|null | `null` | Scheduled delivery time (ISO string) |
| `promoCode` | string\|null | `null` | Applied promo code |
| `promoDiscount` | number | `0` | Promo discount amount in dollars |
| `tipAmount` | number | `0` | Custom tip amount in dollars |
| `tipPercentage` | number | `18` | Tip percentage (15, 18, 20, 25, or 0) |
| `deliveryInstructions` | string | `""` | Delivery instructions |

### `cart.items[]` Object (runtime, created by addToCart)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique cart item ID (generated) |
| `menuItemId` | string | Reference to menuItems[].id |
| `restaurantId` | string | Restaurant ID |
| `name` | string | Item name |
| `quantity` | number | Quantity ordered |
| `basePrice` | number | Base price of the item |
| `selectedOptions` | array | Selected customization options (see below) |
| `specialInstructions` | string | Special instructions for the item |
| `totalPrice` | number | Calculated total: (basePrice + modifiers) * quantity |

### `cart.items[].selectedOptions[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `groupId` | string | Customization group ID |
| `groupName` | string | Customization group name |
| `optionId` | string | Option ID |
| `optionName` | string | Option name |
| `priceModifier` | number | Price modifier in dollars |

### `orders[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Order ID (e.g., `"ord_1"`) |
| `restaurantId` | string | Restaurant ID |
| `restaurantName` | string | Restaurant name |
| `restaurantImageUrl` | string | Restaurant image URL |
| `items` | array | Ordered items (see below) |
| `status` | string | Order status: `"placed"`, `"confirmed"`, `"preparing"`, `"picked_up"`, `"delivering"`, `"out_for_delivery"`, `"delivered"`, `"cancelled"` |
| `placedAt` | string | ISO timestamp when order was placed |
| `estimatedDeliveryMin` | string\|null | ISO timestamp for earliest estimated delivery |
| `estimatedDeliveryMax` | string\|null | ISO timestamp for latest estimated delivery |
| `deliveredAt` | string\|null | ISO timestamp when order was delivered |
| `deliveryAddress` | object | Delivery address (same shape as user.addresses[]) |
| `deliveryMode` | string | `"delivery"` or `"pickup"` |
| `subtotal` | number | Subtotal in dollars |
| `serviceFee` | number | Service fee (15% of subtotal, clamped $0.99-$9.99) |
| `deliveryFee` | number | Delivery fee in dollars |
| `tax` | number | Tax (9% of subtotal) |
| `tip` | number | Tip amount in dollars |
| `promoDiscount` | number | Promo discount in dollars |
| `total` | number | Total amount in dollars |
| `paymentMethod` | string | Payment method label |
| `deliveryPerson` | object\|null | Delivery person info (see below) |
| `rating` | number\|null | Order rating (1-5) or null if unrated |
| `review` | string\|null | Review text or null |

### `orders[].items[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `menuItemId` | string | Menu item ID |
| `name` | string | Item name |
| `quantity` | number | Quantity ordered |
| `unitPrice` | number | Per-unit price (with modifiers) |
| `totalPrice` | number | Total price for this line |
| `selectedOptions` | array | Array of option name strings |
| `specialInstructions` | string | Special instructions |

### `orders[].deliveryPerson` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Delivery person ID (e.g., `"dp_1"`) |
| `name` | string | Delivery person name |
| `photoUrl` | string | Photo URL |
| `vehicleType` | string | `"car"` or `"bike"` |
| `rating` | number | Driver rating (1-5) |

### `promotions[]` Object

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"promo_1"` | Promotion ID |
| `type` | string | `"discount"` | Type: `"discount"`, `"free_delivery"`, `"percentage"` |
| `title` | string | `"$5 off $25+"` | Promotion title |
| `description` | string | `"Save $5 on orders over $25"` | Description |
| `code` | string\|null | `"SAVE5"` | Promo code (null for auto-applied) |
| `minOrder` | number | `25.00` | Minimum order amount |
| `discountAmount` | number | `5.00` | Fixed discount amount (for `"discount"` type) |
| `discountPercent` | number\|null | `null` | Percentage discount (for `"percentage"` type) |
| `expiresAt` | string | `"2025-04-01"` | Expiration date |
| `restaurantId` | string\|null | `null` | Restaurant-specific (null = global) |

### `reviews[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Review ID (e.g., `"rev_1"`) |
| `restaurantId` | string | Restaurant ID |
| `userId` | string | Reviewer user ID |
| `userName` | string | Reviewer display name |
| `rating` | number | Rating (1-5) |
| `comment` | string | Review text |
| `createdAt` | string | ISO timestamp |
| `orderId` | string\|null | Associated order ID (null for reviews by other users) |

### `ui` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `selectedAddressId` | string | `"addr_1"` | Currently selected delivery address ID |
| `deliveryMode` | string | `"delivery"` | `"delivery"` or `"pickup"` |
| `searchQuery` | string | `""` | Current search query |
| `recentSearches` | array | `["Pizza","Burgers","Sushi"]` | Recent search terms (max 5) |
| `activeFilters` | object | see below | Active filter state |

### `ui.activeFilters` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sort` | string | `"recommended"` | Sort option: `"recommended"`, `"popular"`, `"rating"`, `"delivery_time"`, `"price_low"`, `"price_high"` |
| `priceRange` | array | `[]` | Selected price ranges: `"$"`, `"$$"`, `"$$$"`, `"$$$$"` |
| `dietary` | array | `[]` | Dietary filters: `"vegetarian"`, `"vegan"`, `"gluten_free"` |
| `maxDeliveryFee` | number\|null | `null` | Maximum delivery fee filter |
| `deals` | boolean | `false` | Whether deals filter is active |

## Default IDs

### Restaurant IDs
| ID | Name | Cuisine |
|----|------|---------|
| `rest_1` | Bella Italia | Italian, Pizza, Pasta |
| `rest_2` | Tokyo Express | Japanese, Sushi, Ramen |
| `rest_3` | Burger Barn | American, Burgers, Fast Food |
| `rest_4` | Taco Fiesta | Mexican, Tacos, Burritos |
| `rest_5` | Golden Dragon | Chinese, Asian, Dim Sum |
| `rest_6` | Spice Route | Indian, Curry, Tandoori |
| `rest_7` | The Green Bowl | Healthy, Salads, Bowls |
| `rest_8` | Sweet Treats Bakery | Dessert, Bakery, Coffee |
| `rest_9` | Pho King Good | Vietnamese, Pho, Banh Mi |
| `rest_10` | Mediterranean Grill | Mediterranean, Kebabs, Falafel |

### Menu Item IDs (by restaurant)
| Restaurant | Item IDs | Notable Items |
|------------|----------|---------------|
| rest_1 (Bella Italia) | `item_1` - `item_7` | Margherita Pizza, Spaghetti Carbonara, Tiramisu |
| rest_2 (Tokyo Express) | `item_8` - `item_14` | Dragon Roll, California Roll, Tonkotsu Ramen |
| rest_3 (Burger Barn) | `item_15` - `item_21` | Classic Cheeseburger, BBQ Bacon Burger |
| rest_4 (Taco Fiesta) | `item_22` - `item_28` | Carne Asada Tacos, Super Burrito |
| rest_5 (Golden Dragon) | `item_29` - `item_34` | Kung Pao Chicken, Pork Dumplings |
| rest_6 (Spice Route) | `item_35` - `item_41` | Butter Chicken, Palak Paneer, Lamb Biryani |
| rest_7 (The Green Bowl) | `item_42` - `item_47` | Acai Power Bowl, Poke Bowl |
| rest_8 (Sweet Treats) | `item_48` - `item_53` | NY Cheesecake, Butter Croissant |
| rest_9 (Pho King Good) | `item_54` - `item_59` | Beef Pho, Classic Banh Mi |
| rest_10 (Mediterranean) | `item_60` - `item_66` | Chicken Shawarma Plate, Lamb Kebab Plate |

### Default Order IDs
| ID | Restaurant | Status | Description |
|----|-----------|--------|-------------|
| `ord_1` | rest_1 (Bella Italia) | `delivered` | Pizza + Carbonara, rated 5 stars |
| `ord_2` | rest_3 (Burger Barn) | `delivered` | 2x Cheeseburger + Fries, unrated |
| `ord_3` | rest_2 (Tokyo Express) | `delivered` | Dragon Roll, rated 4 stars |
| `ord_4` | rest_4 (Taco Fiesta) | `delivered` | Tacos + Burrito + Guac, rated 5 stars |
| `ord_5` | rest_5 (Golden Dragon) | `cancelled` | Kung Pao + Dumplings, unrated |

### Address IDs
| ID | Label | Street |
|----|-------|--------|
| `addr_1` | Home | 123 Main St, Apt 4B, San Francisco, CA 94102 |
| `addr_2` | Work | 456 Market St, Suite 800, San Francisco, CA 94105 |

### Payment Method IDs
| ID | Type | Label |
|----|------|-------|
| `pay_1` | visa | Visa ····4242 (default) |
| `pay_2` | paypal | PayPal |

### Promo Code IDs
| ID | Code | Type | Description |
|----|------|------|-------------|
| `promo_1` | `SAVE5` | discount | $5 off orders $25+ |
| `promo_2` | (auto) | free_delivery | Free delivery at Mediterranean Grill |
| `promo_3` | `FIRST20` | percentage | 20% off first order (min $15) |
| `promo_4` | `SUSHI3` | discount | $3 off at Tokyo Express (min $15) |
| `promo_5` | (auto) | free_delivery | Uber One: $0 Delivery + 5% off |

### Category IDs
`cat_1` (Pizza) through `cat_15` (Mediterranean)

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8052/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "id": "user_1",
          "name": "Alex Johnson",
          "email": "alex.johnson@email.com",
          "phone": "(415) 555-0123",
          "avatarUrl": "",
          "addresses": [
            {"id": "addr_1", "label": "Home", "street": "123 Main St", "apt": "Apt 4B", "city": "San Francisco", "state": "CA", "zip": "94102", "instructions": "", "isDefault": true}
          ],
          "defaultAddressId": "addr_1",
          "paymentMethods": [
            {"id": "pay_1", "type": "visa", "label": "Visa ••••4242", "last4": "4242", "isDefault": true}
          ],
          "defaultPaymentId": "pay_1",
          "uberOneActive": false,
          "favoriteRestaurantIds": ["rest_1"]
        },
        "categories": [
          {"id": "cat_1", "name": "Pizza", "icon": "🍕"},
          {"id": "cat_2", "name": "Burgers", "icon": "🍔"},
          {"id": "cat_3", "name": "Sushi", "icon": "🍣"}
        ],
        "restaurants": [
          {
            "id": "rest_1", "name": "Bella Italia", "imageUrl": "", "cuisineType": ["Italian", "Pizza"],
            "rating": 4.6, "reviewCount": 234, "priceRange": "$$", "deliveryFee": 2.49,
            "deliveryTimeMin": 25, "deliveryTimeMax": 40, "distance": 1.2, "isOpen": true,
            "hours": "10:00 AM - 11:00 PM", "address": "789 Columbus Ave, San Francisco, CA",
            "phone": "(415) 555-0456", "isSponsored": false, "promotions": [],
            "categories": ["Pizza", "Pasta"], "tags": ["Popular"],
            "supportsPickup": true, "pickupTimeMin": 15, "pickupTimeMax": 25
          }
        ],
        "menuItems": [
          {
            "id": "item_1", "restaurantId": "rest_1", "category": "Pizza",
            "name": "Margherita Pizza", "description": "Fresh mozzarella, tomato sauce, basil",
            "price": 14.99, "imageUrl": "", "isPopular": true, "isAvailable": true,
            "dietaryTags": ["Vegetarian"], "customizationGroups": [
              {"id": "cg_1", "name": "Choose your size", "required": true, "maxSelections": 1, "minSelections": 1, "options": [
                {"id": "co_1", "name": "Small (10\")", "priceModifier": 0, "isDefault": true, "isAvailable": true},
                {"id": "co_2", "name": "Medium (12\")", "priceModifier": 2.00, "isDefault": false, "isAvailable": true}
              ]}
            ]
          }
        ],
        "cart": {
          "restaurantId": null, "restaurantName": null, "items": [],
          "deliveryMode": "delivery", "scheduledTime": null,
          "promoCode": null, "promoDiscount": 0, "tipAmount": 0, "tipPercentage": 18,
          "deliveryInstructions": ""
        },
        "orders": [],
        "activeOrderId": null,
        "promotions": [
          {"id": "promo_1", "type": "discount", "title": "$5 off $25+", "description": "Save $5 on orders over $25", "code": "SAVE5", "minOrder": 25.00, "discountAmount": 5.00, "discountPercent": null, "expiresAt": "2025-04-01", "restaurantId": null}
        ],
        "reviews": [],
        "ui": {
          "selectedAddressId": "addr_1",
          "deliveryMode": "delivery",
          "searchQuery": "",
          "recentSearches": [],
          "activeFilters": {
            "sort": "recommended",
            "priceRange": [],
            "dietary": [],
            "maxDeliveryFee": null,
            "deals": false
          }
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Add item to cart | `cart.items` array grows; `cart.restaurantId` and `cart.restaurantName` set |
| Add item from different restaurant | `cart.items` reset to new item only; `cart.restaurantId` and `cart.restaurantName` changed |
| Remove item from cart | `cart.items` shrinks; if empty, `cart.restaurantId` and `cart.restaurantName` become `null` |
| Update cart item quantity | `cart.items[i].quantity` and `cart.items[i].totalPrice` updated |
| Increase quantity to 0 or below | Item removed from `cart.items` |
| Clear cart | `cart.items` → `[]`; `cart.restaurantId` → `null`; `cart.restaurantName` → `null` |
| Toggle delivery/pickup mode | `cart.deliveryMode` and `ui.deliveryMode` updated |
| Select delivery address | `ui.selectedAddressId` changed |
| Set tip percentage | `cart.tipPercentage` updated; `cart.tipAmount` set to 0 |
| Apply promo code | `cart.promoCode` set; `cart.promoDiscount` calculated |
| Place order | New order prepended to `orders`; `activeOrderId` set; `cart` reset to empty |
| Order status progresses | `orders[i].status` updates through: `placed` → `confirmed` → `preparing` → `out_for_delivery` → `delivered` |
| Order delivered | `orders[i].status` → `"delivered"`; `orders[i].deliveredAt` set |
| Rate order | `orders[i].rating` set (1-5); `orders[i].review` set |
| Toggle favorite restaurant | `user.favoriteRestaurantIds` array gains or loses the restaurant ID |
| Search for restaurants | `ui.searchQuery` updated; `ui.recentSearches` may grow (max 5) |
| Update sort filter | `ui.activeFilters.sort` changed |
| Toggle price range filter | `ui.activeFilters.priceRange` array updated |
| Toggle dietary filter | `ui.activeFilters.dietary` array updated |
| Toggle deals filter | `ui.activeFilters.deals` toggled |
| Clear all filters | `ui.activeFilters` reset to defaults |
| Reorder past order | Items from past order added to `cart`; navigates to checkout |

## Order Status Progression

When an order is placed and tracked, statuses auto-progress on timers:

| Status | Delay from placement | Progress bar % |
|--------|---------------------|----------------|
| `placed` | 0s | 15% |
| `confirmed` | ~3s | 30% |
| `preparing` | ~8s | 45% |
| `out_for_delivery` | ~15s | 90% |
| `delivered` | ~25s | 100% |

## Price Calculation

| Component | Formula |
|-----------|---------|
| Subtotal | Sum of all cart items' `totalPrice` |
| Service fee | `min(max(subtotal * 0.15, 0.99), 9.99)` |
| Delivery fee | From `restaurant.deliveryFee` |
| Tax | `subtotal * 0.09` |
| Tip | `subtotal * (tipPercentage / 100)` or custom `tipAmount` |
| Promo discount | Based on promo type: fixed amount or percentage |
| **Total** | `subtotal + serviceFee + deliveryFee + tax + tip - promoDiscount` |
