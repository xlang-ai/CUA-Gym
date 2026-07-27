# amazon_mock Schema

**Deploy order**: 1 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8001)
**Base URL**: `http://172.17.46.46:8001/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data)
**Serve files**: `GET /files/<sid>/<filename>`

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | `Home` | Homepage with carousel, category cards, recommendations, deals, recently viewed |
| `/search` | `ProductListing` | Product search/browse with filters, sorting, pagination. Query params: `q` (search), `category` |
| `/product/:id` | `ProductDetail` | Full product detail page with images, specs, reviews, buy box, related products |
| `/cart` | `Cart` | Shopping cart with quantity controls, save-for-later, promo codes, recommendations |
| `/checkout` | `Checkout` | Multi-step checkout: shipping → payment → review → place order |
| `/orders` | `Orders` | Order history with time filters, search, and order status tracking |
| `/wishlist` | `Wishlist` | Saved wishlist items with add-to-cart functionality |
| `/profile` | `Orders` | (Alias for Orders page) |
| `/go` | `Go` | State inspector endpoint (JSON view of initial_state, current_state, state_diff) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `products` | `Product[]` | Array of 60 products across 6 categories (p1-p60) |
| `user` | `User` | Current user profile with address and payment info |
| `cart` | `CartItem[]` | Items in shopping cart. Default: `[{productId:"p1",quantity:1},{productId:"p22",quantity:2}]` |
| `wishlist` | `string[]` | Array of product IDs in wishlist. Default: `["p5","p12","p37"]` |
| `savedForLater` | `CartItem[]` | Items saved for later from cart. Default: `[]` |
| `orders` | `Order[]` | Order history. Default: 3 seed orders (ord-seed-1, ord-seed-2, ord-seed-3) |
| `reviews` | `Review[]` | Product reviews. Default: 20 seed reviews (rev-1 through rev-20) |
| `recentSearches` | `string[]` | Recent search terms (max 10). Default: `["wireless headphones","coffee maker","running shoes","laptop stand","kindle"]` |
| `recentlyViewed` | `string[]` | Recently viewed product IDs (max 10). Default: `["p3","p7","p15","p22","p41"]` |

### Product

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique product ID. Format: `"p1"` through `"p60"` |
| `title` | `string` | Full product title |
| `price` | `number` | Current selling price |
| `originalPrice` | `number \| null` | Original/list price before discount (null if no discount) |
| `rating` | `number` | Average rating (0-5, supports decimals like 4.5) |
| `reviewCount` | `number` | Total number of ratings |
| `image` | `string` | Primary product image URL (picsum.photos) |
| `images` | `string[]` | Array of product image URLs (2-4 images) |
| `description` | `string` | Short product description paragraph |
| `bulletPoints` | `string[]` | Array of "About this item" bullet points (typically 7) |
| `specs` | `object` | Key-value pairs for product specifications (varies by product) |
| `category` | `string` | One of: `"Electronics"`, `"Books"`, `"Home & Kitchen"`, `"Fashion"`, `"Toys & Games"`, `"Beauty"` |
| `brand` | `string` | Manufacturer/brand name |
| `prime` | `boolean` | Whether product has Prime shipping |
| `inStock` | `boolean` | Whether product is in stock |
| `stockCount` | `number \| null` | Remaining stock count (null = unlimited, shown when <= 10) |
| `seller` | `string` | Seller name (e.g. "Amazon.com", brand name) |
| `badges` | `string[]` | Array of badge labels: `"Best Seller"`, `"Amazon's Choice"` |
| `createdAt` | `string` | ISO 8601 timestamp of product listing |

### Product IDs by Category

| Category | IDs | Count |
|----------|-----|-------|
| Electronics | p1-p10 | 10 |
| Books | p11-p20 | 10 |
| Home & Kitchen | p21-p30 | 10 |
| Fashion | p31-p40 | 10 |
| Toys & Games | p41-p50 | 10 |
| Beauty | p51-p60 | 10 |

### User

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Default: `"u1"` |
| `name` | `string` | Default: `"Demo User"` |
| `email` | `string` | Default: `"demo@example.com"` |
| `address` | `Address` | Default shipping address |
| `addresses` | `Address[]` | Array of saved addresses (default: 1 address) |
| `paymentMethod` | `PaymentMethod` | Default payment method |
| `paymentMethods` | `PaymentMethod[]` | Array of saved payment methods (default: 1 method) |

### Address

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Default: `"addr1"` |
| `fullName` | `string` | Default: `"Demo User"` |
| `street` | `string` | Default: `"123 Mock Lane"` |
| `city` | `string` | Default: `"Seattle"` |
| `state` | `string` | Default: `"WA"` |
| `zip` | `string` | Default: `"98109"` |
| `country` | `string` | Default: `"United States"` |
| `phone` | `string` | Default: `"555-0123"` |
| `isDefault` | `boolean` | Default: `true` |

### PaymentMethod

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Default: `"pm1"` |
| `last4` | `string` | Last 4 digits of card. Default: `"4242"` |
| `brand` | `string` | Card brand. Default: `"Visa"` |
| `expiry` | `string` | Expiration date. Default: `"12/26"` |
| `isDefault` | `boolean` | Default: `true` |

### CartItem

| Field | Type | Description |
|-------|------|-------------|
| `productId` | `string` | References a product ID (e.g. `"p1"`) |
| `quantity` | `number` | Quantity in cart (min 1, max selectable 10) |

### Order

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique order ID. Seed: `"ord-seed-1"`, `"ord-seed-2"`, `"ord-seed-3"`. New: `"ord-<timestamp>"` |
| `date` | `string` | ISO 8601 timestamp of order placement |
| `status` | `string` | One of: `"Processing"`, `"Shipped"`, `"Delivered"` |
| `total` | `number` | Order total amount |
| `items` | `CartItem[]` | Array of ordered items with productId and quantity |
| `shippingAddress` | `Address` | Shipping address for this order |
| `paymentMethod` | `PaymentMethod` | Payment method used (at least `last4` and `brand`) |
| `trackingNumber` | `string \| null` | Tracking number (null if not yet shipped) |
| `estimatedDelivery` | `string \| null` | ISO date string for estimated delivery (null if delivered or not available) |

#### Default Seed Orders

| ID | Status | Items | Total |
|----|--------|-------|-------|
| `ord-seed-1` | Delivered | p1 (qty 1), p34 (qty 1) | $199.98 |
| `ord-seed-2` | Shipped | p4 (qty 1) | $49.99 |
| `ord-seed-3` | Processing | p7 (qty 1), p23 (qty 1), p11 (qty 1) | $319.97 |

### Review

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique review ID. Seed: `"rev-1"` through `"rev-20"`. New: `"rev-<timestamp>"` |
| `productId` | `string` | Product being reviewed |
| `userId` | `string` | Reviewer user ID |
| `userName` | `string` | Display name of reviewer |
| `rating` | `number` | Rating value (1-5) |
| `title` | `string` | Review headline/title |
| `content` | `string` | Full review text body |
| `date` | `string` | ISO 8601 timestamp |
| `helpful` | `number` | Count of "helpful" votes |
| `verifiedPurchase` | `boolean` | Whether purchase is verified |

#### Seed Review Coverage

Reviews exist for products: p1 (2 reviews), p2 (2), p3 (2), p11 (2), p12 (1), p21 (1), p22 (1), p23 (2), p29 (1), p31 (1), p41 (1), p49 (1), p51 (2), p55 (1).

## Categories

```json
["Electronics", "Books", "Home & Kitchen", "Fashion", "Toys & Games", "Beauty"]
```

## Minimal Inject Example

```json
{
  "action": "set",
  "state": {
    "cart": [
      { "productId": "p3", "quantity": 2 },
      { "productId": "p11", "quantity": 1 }
    ],
    "wishlist": ["p2", "p21"],
    "savedForLater": [],
    "recentSearches": ["headphones", "books"],
    "recentlyViewed": ["p3", "p11"]
  }
}
```

## Inject Example: Custom Products

```json
{
  "action": "set",
  "state": {
    "products": [
      {
        "id": "p1",
        "title": "Custom Product",
        "price": 29.99,
        "originalPrice": 49.99,
        "rating": 4.5,
        "reviewCount": 100,
        "image": "https://picsum.photos/seed/custom1/400/400",
        "images": ["https://picsum.photos/seed/custom1/400/400"],
        "description": "A custom product for testing",
        "bulletPoints": ["Feature 1", "Feature 2"],
        "specs": {"Brand": "TestBrand", "Weight": "1 lb"},
        "category": "Electronics",
        "brand": "TestBrand",
        "prime": true,
        "inStock": true,
        "stockCount": null,
        "seller": "Amazon.com",
        "badges": ["Best Seller"],
        "createdAt": "2024-01-01T00:00:00.000Z"
      }
    ],
    "cart": [{ "productId": "p1", "quantity": 1 }]
  }
}
```

## Inject Example: Custom Orders

```json
{
  "action": "set",
  "state": {
    "orders": [
      {
        "id": "ord-custom-1",
        "date": "2024-12-01T00:00:00.000Z",
        "status": "Delivered",
        "total": 149.99,
        "items": [{ "productId": "p1", "quantity": 1 }],
        "shippingAddress": {
          "fullName": "John Doe",
          "street": "456 Test Ave",
          "city": "Portland",
          "state": "OR",
          "zip": "97201",
          "country": "United States",
          "phone": "555-9876"
        },
        "paymentMethod": { "last4": "1234", "brand": "Mastercard" },
        "trackingNumber": "1Z999BB20234567890",
        "estimatedDelivery": null
      }
    ]
  }
}
```

## Inject Example: Custom Reviews

```json
{
  "action": "set",
  "state": {
    "reviews": [
      {
        "id": "rev-custom-1",
        "productId": "p1",
        "userId": "u1",
        "userName": "Test User",
        "rating": 5,
        "title": "Excellent product!",
        "content": "This is a great product, I highly recommend it.",
        "date": "2024-12-01T00:00:00.000Z",
        "helpful": 10,
        "verifiedPurchase": true
      }
    ]
  }
}
```

## Data Normalization

When injecting state via POST, the app normalizes malformed data automatically:

- **Products**: Missing fields get defaults (e.g., `category` defaults to `"Electronics"`, `inStock` to `true`). Accepts `name` as alias for `title`, `img`/`imageUrl` as alias for `image`.
- **Cart items**: Accepts `product_id` or `id` as alias for `productId`. Quantity defaults to 1.
- **Wishlist**: Accepts strings directly or objects with `productId`/`product_id`/`id`.
- **Orders**: Accepts `address` as alias for `street`, `zipCode`/`postalCode` as alias for `zip`. Status defaults to `"Processing"`.
- **Reviews**: Accepts `headline` as alias for `title`, `body`/`text` as alias for `content`, `author` as alias for `userName`. Rating clamped 0-5.
- **Recent searches**: Accepts strings directly or objects with `term`/`query`/`text`.
- **Recently viewed**: Accepts strings directly or objects with `productId`/`product_id`/`id`.

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed | Details |
|-------------|---------------------|---------|
| Search for a product | `recentSearches` | Search term prepended to array (max 10, deduped) |
| View a product detail page | `recentlyViewed` | Product ID prepended to array (max 10, deduped) |
| Add product to cart | `cart` | New CartItem added or existing item quantity incremented |
| Remove product from cart | `cart` | CartItem removed by productId |
| Update cart item quantity | `cart` | CartItem quantity updated (removing if < 1) |
| Save cart item for later | `cart`, `savedForLater` | Item moved from cart to savedForLater |
| Move saved item to cart | `cart`, `savedForLater` | Item moved from savedForLater back to cart |
| Remove saved-for-later item | `savedForLater` | Item removed from savedForLater |
| Toggle wishlist | `wishlist` | Product ID added or removed from wishlist array |
| Add to wishlist from product page | `wishlist` | Product ID added to wishlist array |
| Remove from wishlist | `wishlist` | Product ID removed from wishlist array |
| Place order (checkout) | `orders`, `cart` | New order prepended to orders array; cart cleared to `[]` |
| Submit a product review | `reviews` | New review appended with auto-generated id (`rev-<timestamp>`) and current date |
| Add to cart from wishlist page | `cart` | New CartItem added (quantity 1) |
| Add to cart from product card | `cart` | New CartItem added (quantity 1) |
| Buy Now from product page | `cart`, then navigates to checkout | Product added to cart, then navigated to /checkout |
| Add all "Frequently Bought Together" | `cart` | Multiple products added to cart simultaneously |

## Key Default Product IDs

| ID | Title | Price | Category |
|----|-------|-------|----------|
| `p1` | Samsung Galaxy Buds Pro | $149.99 | Electronics |
| `p2` | Apple MacBook Air 13-inch M2 | $999.00 | Electronics |
| `p3` | Sony WH-1000XM5 Headphones | $348.00 | Electronics |
| `p4` | Anker PowerCore 26800mAh | $49.99 | Electronics |
| `p5` | Logitech MX Master 3S Mouse | $89.99 | Electronics |
| `p7` | Apple iPad 10th Gen | $349.00 | Electronics |
| `p11` | Atomic Habits by James Clear | $16.99 | Books |
| `p12` | Project Hail Mary by Andy Weir | $14.99 | Books |
| `p15` | Dune by Frank Herbert | $10.99 | Books |
| `p21` | Ninja AF101 Air Fryer | $89.95 | Home & Kitchen |
| `p22` | Keurig K-Classic Coffee Maker | $79.99 | Home & Kitchen |
| `p23` | Instant Pot Duo 7-in-1 | $89.99 | Home & Kitchen |
| `p31` | Nike Air Force 1 '07 | $110.00 | Fashion |
| `p34` | Champion Powerblend Hoodie | $35.00 | Fashion |
| `p37` | Herschel Classic Backpack | $49.99 | Fashion |
| `p41` | LEGO Star Wars Millennium Falcon | $169.99 | Toys & Games |
| `p43` | Nintendo Switch Joy-Con | $79.99 | Toys & Games |
| `p49` | Catan Board Game | $34.99 | Toys & Games |
| `p51` | CeraVe Moisturizing Cream | $16.99 | Beauty |
| `p55` | Revlon One-Step Volumizer | $34.99 | Beauty |

## Default Cart Contents

```json
[
  { "productId": "p1", "quantity": 1 },
  { "productId": "p22", "quantity": 2 }
]
```

Subtotal: $149.99 + ($79.99 * 2) = $309.97

## Default Wishlist

```json
["p5", "p12", "p37"]
```

Products: Logitech MX Master 3S ($89.99), Project Hail Mary ($14.99), Herschel Classic Backpack ($49.99)

## Promo Code System

The cart page supports a promo code input. The only valid code is `SAVE10` which applies a 10% discount to the subtotal. This is client-side only and does not affect persisted state.
