# instacart_mock Schema

**Deploy order**: 23 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8023)
**Base URL**: `http://172.17.46.46:8023/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Home | Homepage with stores, categories, on-sale items, popular items |
| `/store/:storeId` | StoreFront | Store product listing with department filtering, sort, and search |
| `/store/:storeId/department/:deptId` | StoreFront | Store filtered to a specific department |
| `/cart` | Cart | Full cart page with item quantities and order summary |
| `/checkout` | Checkout | Delivery address, time slot, tip, payment, and place order |
| `/orders` | Orders | Order history with ratings |
| `/search` | Search | Product search results page |
| `/lists` | Lists | Shopping lists CRUD with checkable items |
| `/deals` | Deals | Deals and coupons with clip functionality |
| `/recipes` | Recipes | Recipe browser with add-to-cart for ingredients |
| `/account` | Account | User profile, Instacart+ status, addresses |
| `/go` | Go | State inspection endpoint (JSON) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Active user profile |
| `addresses` | array | User delivery addresses |
| `stores` | array | Available stores |
| `departments` | array | Store departments (categories) |
| `products` | array | Product catalog (80 items across 10 departments) |
| `cart` | array | Current shopping cart items |
| `orders` | array | Order history |
| `shoppingLists` | array | User-created shopping lists |
| `recipes` | array | Available recipes with ingredients |
| `deals` | array | Deals and coupons |
| `deliverySlots` | array | Available delivery time slots (5 days) |
| `selectedStoreId` | string | Currently selected store ID |
| `selectedDepartmentId` | string\|null | Currently selected department filter |
| `searchQuery` | string | Current search query text |
| `cartOpen` | boolean | Whether the cart flyout panel is open |
| `activeModal` | string\|null | Currently open modal type (e.g., `"product"`) |
| `activeModalData` | object\|null | Data passed to the active modal |
| `deliveryAddressId` | string | Selected delivery address ID |
| `selectedDeliverySlot` | object\|null | Selected delivery slot `{id, date, window}` |
| `shopperTip` | number | Shopper tip amount in dollars |
| `sortBy` | string | Product sort order |
| `filters` | object | Active product filters |

### `user` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"user_1"` | User ID |
| `firstName` | string | `"Sarah"` | First name |
| `lastName` | string | `"Johnson"` | Last name |
| `email` | string | `"sarah.johnson@email.com"` | Email address |
| `phone` | string | `"(415) 555-0142"` | Phone number |
| `avatar` | string\|null | `null` | Avatar URL |
| `defaultAddressId` | string | `"addr_1"` | Default delivery address ID |
| `instacartPlus` | boolean | `true` | Whether user has Instacart+ membership |
| `instacartPlusExpiry` | string | `"2026-01-15"` | Membership expiry date |
| `preferredStoreId` | string | `"store_1"` | Preferred store ID |
| `createdAt` | string | `"2023-06-15T10:00:00Z"` | Account creation timestamp |

### `addresses[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Address ID (e.g., `"addr_1"`) |
| `userId` | string | Owner user ID |
| `label` | string | Display label (e.g., `"Home"`, `"Work"`) |
| `street` | string | Street address |
| `apt` | string | Apartment/suite number |
| `city` | string | City |
| `state` | string | State abbreviation |
| `zip` | string | ZIP code |
| `isDefault` | boolean | Whether this is the default address |
| `deliveryInstructions` | string | Special delivery instructions |

### `stores[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Store ID (e.g., `"store_1"`) |
| `name` | string | Store name (e.g., `"Safeway"`) |
| `slug` | string | URL slug |
| `color` | string | Brand hex color |
| `emoji` | string | Store icon emoji |
| `description` | string | Store description |
| `deliveryFee` | number | Standard delivery fee |
| `deliveryFeeWithPlus` | number | Delivery fee for Instacart+ members (always 0) |
| `serviceFeePercent` | number | Service fee percentage (always 5) |
| `minOrder` | number | Minimum order amount |
| `deliveryTimeMin` | number | Minimum delivery time in minutes |
| `deliveryTimeMax` | number | Maximum delivery time in minutes |
| `rating` | number | Store rating |
| `isInStorePricing` | boolean | Whether store uses in-store pricing |
| `categories` | array | Store category tags |

### `departments[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Department ID (e.g., `"dept_produce"`) |
| `storeId` | string | Parent store ID |
| `name` | string | Department name |
| `slug` | string | URL slug |
| `icon` | string | Department emoji icon |
| `displayOrder` | number | Sort order |
| `subcategories` | array | Sub-categories: `{id, name, slug}` |

### `products[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Product ID (e.g., `"prod_1"`) |
| `storeId` | string | Store ID |
| `departmentId` | string | Department ID |
| `subcategoryId` | string | Subcategory ID |
| `name` | string | Product name |
| `brand` | string | Brand name |
| `description` | string | Product description |
| `emoji` | string | Product display emoji |
| `price` | number | Current price |
| `originalPrice` | number\|null | Original price (if on sale) |
| `priceUnit` | string | Price unit (e.g., `"each"`, `"lb"`, `"oz"`) |
| `unitSize` | string | Package size description |
| `unitPrice` | number | Price per unit |
| `unitPriceLabel` | string | Unit price label (e.g., `"/lb"`) |
| `isOrganic` | boolean | Whether product is organic |
| `isOnSale` | boolean | Whether product is currently on sale |
| `saleEndDate` | string\|null | Sale end date |
| `inStock` | boolean | Whether product is in stock |
| `rating` | number | Product rating (4.0-5.0) |
| `reviewCount` | number | Number of reviews |
| `nutrition` | object\|null | Nutrition facts: `{servingSize, calories, totalFat, sodium, totalCarbs, fiber, sugars, protein}` |
| `ingredients` | string\|null | Ingredients text |
| `allergens` | array | Allergen strings (e.g., `["wheat", "milk"]`) |
| `tags` | array | Product tags (e.g., `["organic", "fruit", "fresh"]`) |

### `cart[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Cart item ID (e.g., `"cart_1"`) |
| `productId` | string | Product ID reference |
| `storeId` | string | Store ID |
| `quantity` | number | Item quantity |
| `replacementPreference` | string | `"best_match"` or `"refund"` |
| `specificReplacementId` | string\|null | Specific replacement product ID |
| `note` | string | Item-level note for shopper |
| `addedAt` | string | ISO timestamp when added |

### `orders[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Order ID (e.g., `"order_1"`) |
| `userId` | string | User ID |
| `storeId` | string | Store ID |
| `storeName` | string | Store display name |
| `status` | string | `"placed"`, `"shopping"`, `"delivering"`, or `"delivered"` |
| `items` | array | Order items: `{productId, productName, quantity, price, wasReplaced, replacementProductName}` |
| `subtotal` | number | Items subtotal |
| `serviceFee` | number | Service fee |
| `deliveryFee` | number | Delivery fee |
| `tip` | number | Shopper tip |
| `tax` | number | Tax amount |
| `total` | number | Order total |
| `itemCount` | number | Total number of items |
| `deliveryAddress` | string | Formatted delivery address |
| `deliveryDate` | string | Delivery date (YYYY-MM-DD) |
| `deliveryWindow` | string | Delivery time window (e.g., `"2:00 PM - 3:00 PM"`) |
| `placedAt` | string | ISO timestamp when order was placed |
| `deliveredAt` | string\|null | ISO timestamp when delivered |
| `shopperName` | string\|null | Shopper name |
| `shopperRating` | number\|null | Rating given to shopper (1-5) |

### `shoppingLists[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | List ID (e.g., `"list_1"`) |
| `userId` | string | Owner user ID |
| `name` | string | List name |
| `items` | array | List items (see below) |
| `createdAt` | string | ISO timestamp |
| `updatedAt` | string | ISO timestamp |

#### `shoppingLists[].items[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | List item ID (e.g., `"li_1"`) |
| `productId` | string\|null | Linked product ID (null for freeform items) |
| `name` | string | Item display name |
| `checked` | boolean | Whether item is checked off |
| `quantity` | number | Item quantity |
| `addedAt` | string | ISO timestamp |

### `recipes[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Recipe ID (e.g., `"recipe_1"`) |
| `title` | string | Recipe title |
| `description` | string | Recipe description |
| `prepTime` | string | Prep time (e.g., `"15 min"`) |
| `cookTime` | string | Cook time |
| `totalTime` | string | Total time |
| `servings` | number | Number of servings |
| `difficulty` | string | `"Easy"` or `"Medium"` |
| `tags` | array | Recipe tags (e.g., `["dinner", "italian", "pasta"]`) |
| `ingredients` | array | Ingredients: `{name, quantity, productId}` (productId may be null) |
| `instructions` | array | Step-by-step instruction strings |
| `emoji` | string | Recipe emoji icon |

### `deals[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Deal ID (e.g., `"deal_1"`) |
| `storeId` | string\|null | Store ID (null for site-wide deals) |
| `type` | string | `"percent_off"`, `"dollar_off"`, `"bogo"`, or `"free_delivery"` |
| `title` | string | Deal title |
| `description` | string | Deal description |
| `discountValue` | number | Discount amount (percent or dollars) |
| `badge` | string | Display badge text (e.g., `"20% OFF"`, `"BOGO"`) |
| `minPurchase` | number | Minimum purchase amount (0 if none) |
| `applicableDepartmentId` | string\|null | Department restriction (null for all) |
| `startDate` | string | Start date (YYYY-MM-DD) |
| `endDate` | string | End date (YYYY-MM-DD) |
| `isClipped` | boolean | Whether user has clipped this deal |

### `deliverySlots[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Slot day ID (e.g., `"slot_0"`) |
| `date` | string | Date (YYYY-MM-DD) |
| `dayLabel` | string | Display label (`"Today"`, `"Tomorrow"`, or day name) |
| `windows` | array | Time windows (see below) |

#### `deliverySlots[].windows[]` Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Window ID (e.g., `"win_0_1"`) |
| `start` | string | Start time (e.g., `"9:00 AM"`) |
| `end` | string | End time (e.g., `"11:00 AM"`) |
| `available` | boolean | Whether this window is available |
| `priority` | boolean | Whether this is a priority window |
| `fee` | number | Extra fee for priority window |

### `selectedDeliverySlot` Object (when set)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Slot day ID |
| `date` | string | Date (YYYY-MM-DD) |
| `window` | object | Selected window object from `deliverySlots[].windows[]` |

### `filters` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `onSale` | boolean | `false` | Filter to on-sale products only |
| `organic` | boolean | `false` | Filter to organic products only |
| `buyItAgain` | boolean | `false` | Filter to previously purchased products |

### `sortBy` Values

| Value | Description |
|-------|-------------|
| `"best_match"` | Default sorting (default) |
| `"price_low"` | Price: Low to High |
| `"price_high"` | Price: High to Low |
| `"name"` | Name: A to Z |

## Default IDs

### Store IDs
| ID | Name |
|----|------|
| `store_1` | Safeway |
| `store_2` | Costco |
| `store_3` | Whole Foods Market |
| `store_4` | Sprouts Farmers Market |
| `store_5` | CVS Pharmacy |
| `store_6` | Target |
| `store_7` | Petco |
| `store_8` | Total Wine & More |

### Department IDs
| ID | Name | Icon |
|----|------|------|
| `dept_produce` | Produce | `🥬` |
| `dept_dairy` | Dairy & Eggs | `🥛` |
| `dept_meat` | Meat & Seafood | `🥩` |
| `dept_bakery` | Bakery | `🍞` |
| `dept_deli` | Deli | `🧀` |
| `dept_frozen` | Frozen | `❄️` |
| `dept_pantry` | Pantry | `🥫` |
| `dept_snacks` | Snacks & Candy | `🍿` |
| `dept_beverages` | Beverages | `🥤` |
| `dept_breakfast` | Breakfast | `🥣` |
| `dept_household` | Household | `🧹` |
| `dept_health` | Health & Beauty | `💊` |
| `dept_baby` | Baby & Kids | `🍼` |
| `dept_pet` | Pet Care | `🐾` |

### Product IDs (sequential)
| Range | Department | Count | Notable Products |
|-------|-----------|-------|------------------|
| `prod_1` - `prod_12` | Produce | 12 | `prod_1`=Organic Bananas, `prod_3`=Avocados, `prod_4`=Baby Spinach |
| `prod_13` - `prod_22` | Dairy & Eggs | 10 | `prod_13`=2% Milk, `prod_14`=Large Eggs, `prod_15`=Greek Yogurt |
| `prod_23` - `prod_30` | Meat & Seafood | 8 | `prod_25`=Chicken Breast, `prod_27`=Atlantic Salmon |
| `prod_31` - `prod_36` | Bakery | 6 | `prod_31`=Sourdough Bread, `prod_33`=Everything Bagels |
| `prod_37` - `prod_44` | Frozen | 8 | `prod_37`=DiGiorno Frozen Pizza, `prod_38`=Vanilla Ice Cream |
| `prod_45` - `prod_54` | Pantry | 10 | `prod_45`=Spaghetti Pasta, `prod_46`=Marinara Sauce |
| `prod_55` - `prod_62` | Snacks | 8 | `prod_55`=Lay's Classic Chips, `prod_58`=Oreo Cookies |
| `prod_63` - `prod_70` | Beverages | 8 | `prod_63`=Spring Water, `prod_64`=Coca-Cola 12-Pack |
| `prod_71` - `prod_76` | Household | 6 | `prod_71`=Paper Towels, `prod_73`=Laundry Detergent |
| `prod_77` - `prod_80` | Health & Beauty | 4 | `prod_77`=Ibuprofen, `prod_80`=Toothpaste |

**Note**: Product IDs are sequentially generated (`prod_1` through `prod_80`, 80 total). The default cart and order data contain hardcoded `productName` fields alongside `productId` references. The `productName` in order/cart defaults was written manually and may reference product names by intended association rather than strict ID lookup (e.g., default cart item `prod_37` is labeled "Sourdough Bread" in the cart initializer, but the generated product `prod_37` is actually DiGiorno Frozen Pizza). The UI resolves product display via `products.find(p => p.id === item.productId)`, so the rendered name always matches the product catalog.

### Default Address IDs
| ID | Label |
|----|-------|
| `addr_1` | Home (742 Evergreen Terrace, SF 94110) - default |
| `addr_2` | Work (200 Market Street, SF 94105) |

### Default Order IDs
| ID | Store | Status | Rating |
|----|-------|--------|--------|
| `order_1` | Safeway | delivered | unrated |
| `order_2` | Whole Foods Market | delivered | 5 |
| `order_3` | Costco | delivered | 4 |
| `order_4` | Safeway | delivered | 5 |
| `order_5` | Target | delivered | unrated |

### Default Shopping List IDs
| ID | Name | Items |
|----|------|-------|
| `list_1` | Weekly Essentials | 8 items (2 checked) |
| `list_2` | Party Supplies | 12 items (0 checked) |
| `list_3` | Healthy Eating | 6 items (2 checked) |

### Default Recipe IDs
| ID | Title |
|----|-------|
| `recipe_1` | Classic Spaghetti Bolognese |
| `recipe_2` | Chicken Stir-Fry |
| `recipe_3` | Greek Salad |
| `recipe_4` | Breakfast Scramble |
| `recipe_5` | Grilled Salmon with Vegetables |
| `recipe_6` | Chocolate Chip Pancakes |

### Default Deal IDs
| ID | Type | Store |
|----|------|-------|
| `deal_1` | percent_off (20%) | Safeway - Organic Produce |
| `deal_2` | bogo | Safeway - Ice Cream |
| `deal_3` | dollar_off ($3) | Whole Foods - $35+ orders |
| `deal_4` | dollar_off ($5) | Site-wide - First order |
| `deal_5` | free_delivery | Site-wide - Weekend |
| `deal_6` | percent_off (15%) | Safeway - Breakfast |
| `deal_7` | bogo | Target - Chips & Snacks |
| `deal_8` | percent_off (10%) | Costco - Household |

### Default Cart (5 items from Safeway)
| Cart ID | Product | Quantity |
|---------|---------|----------|
| `cart_1` | `prod_1` (Organic Bananas) | 3 |
| `cart_2` | `prod_13` (2% Milk) | 1 |
| `cart_3` | `prod_25` (Chicken Breast) | 2 |
| `cart_4` | `prod_37` (Sourdough Bread) | 1 |
| `cart_5` | `prod_15` (Greek Yogurt) | 2 |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8023/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "id": "user_1",
          "firstName": "Sarah",
          "lastName": "Johnson",
          "email": "sarah.johnson@email.com",
          "phone": "(415) 555-0142",
          "avatar": null,
          "defaultAddressId": "addr_1",
          "instacartPlus": true,
          "instacartPlusExpiry": "2026-01-15",
          "preferredStoreId": "store_1",
          "createdAt": "2023-06-15T10:00:00Z"
        },
        "addresses": [
          {"id": "addr_1", "userId": "user_1", "label": "Home", "street": "742 Evergreen Terrace", "apt": "Apt 3B", "city": "San Francisco", "state": "CA", "zip": "94110", "isDefault": true, "deliveryInstructions": "Leave at the front door"}
        ],
        "stores": [
          {"id": "store_1", "name": "Safeway", "slug": "safeway", "color": "#E8372C", "emoji": "\ud83d\uded2", "description": "Fresh groceries", "deliveryFee": 3.99, "deliveryFeeWithPlus": 0, "serviceFeePercent": 5, "minOrder": 10, "deliveryTimeMin": 45, "deliveryTimeMax": 60, "rating": 4.7, "isInStorePricing": true, "categories": ["Groceries"]}
        ],
        "departments": [
          {"id": "dept_produce", "storeId": "store_1", "name": "Produce", "slug": "produce", "icon": "\ud83e\udd2c", "displayOrder": 1, "subcategories": [{"id": "subcat_fruits", "name": "Fresh Fruits", "slug": "fresh-fruits"}]}
        ],
        "products": [
          {"id": "prod_1", "storeId": "store_1", "departmentId": "dept_produce", "subcategoryId": "subcat_fruits", "name": "Organic Bananas", "brand": "Organic", "description": "Ripe organic bananas", "emoji": "\ud83c\udf4c", "price": 0.79, "originalPrice": null, "priceUnit": "each", "unitSize": "1 ct", "unitPrice": 0.79, "unitPriceLabel": "/each", "isOrganic": true, "isOnSale": false, "saleEndDate": null, "inStock": true, "rating": 4.5, "reviewCount": 150, "nutrition": {"servingSize": "1 medium", "calories": 110, "totalFat": "0g", "sodium": "0mg", "totalCarbs": "28g", "fiber": "3g", "sugars": "15g", "protein": "1g"}, "ingredients": "Organic bananas", "allergens": [], "tags": ["organic", "fruit", "fresh"]}
        ],
        "cart": [],
        "orders": [],
        "shoppingLists": [],
        "recipes": [],
        "deals": [],
        "deliverySlots": [],
        "selectedStoreId": "store_1",
        "selectedDepartmentId": null,
        "searchQuery": "",
        "cartOpen": false,
        "activeModal": null,
        "activeModalData": null,
        "deliveryAddressId": "addr_1",
        "selectedDeliverySlot": null,
        "shopperTip": 5.00,
        "sortBy": "best_match",
        "filters": {"onSale": false, "organic": false, "buyItAgain": false}
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Select a store | `selectedStoreId` changes to the store ID |
| Browse department | `selectedDepartmentId` changes |
| Search for products | `searchQuery` updated |
| Change sort order | `sortBy` updated |
| Toggle on-sale filter | `filters.onSale` toggled |
| Toggle organic filter | `filters.organic` toggled |
| Add product to cart | `cart` array grows by 1 (new item) or existing item `quantity` incremented |
| Remove product from cart | `cart` array shrinks by 1 |
| Update cart item quantity | `cart[i].quantity` updated |
| Change replacement preference | `cart[i].replacementPreference` updated to `"best_match"` or `"refund"` |
| Clear cart | `cart` becomes `[]` |
| Open cart flyout | `cartOpen` becomes `true` |
| Close cart flyout | `cartOpen` becomes `false` |
| Open product modal | `activeModal` becomes `"product"`; `activeModalData` set to product object |
| Close product modal | `activeModal` becomes `null`; `activeModalData` becomes `null` |
| Select delivery address | `deliveryAddressId` changes |
| Select delivery time slot | `selectedDeliverySlot` set to `{id, date, window}` |
| Set shopper tip | `shopperTip` changes (0, 2, 5, 10, or 15) |
| Place order | `orders` array grows by 1; `cart` becomes `[]`; `selectedDeliverySlot` becomes `null`; `shopperTip` resets to 5.00; `cartOpen` becomes `false` |
| Rate order shopper | `orders[i].shopperRating` set to 1-5 |
| Create shopping list | `shoppingLists` array grows by 1 |
| Delete shopping list | `shoppingLists` array shrinks by 1 |
| Add item to shopping list | `shoppingLists[i].items` array grows by 1; `updatedAt` updated |
| Remove item from shopping list | `shoppingLists[i].items` array shrinks by 1; `updatedAt` updated |
| Toggle shopping list item | `shoppingLists[i].items[j].checked` toggled; `updatedAt` updated |
| Clip/unclip deal | `deals[i].isClipped` toggled |
| Add address | `addresses` array grows by 1 |
| Delete address | `addresses` array shrinks by 1 |
| Update user profile | `user` fields (firstName, lastName, email, phone) updated |
| Add recipe ingredients to cart | `cart` grows (one entry per ingredient with a productId not already in cart) |
