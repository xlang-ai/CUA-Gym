# shopify_admin_mock Schema

**Deploy order**: 42 (alphabetical among all *_mock dirs)
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `store` | object | Shop profile: `{id, name, email, phone, domain, customDomain, address, currency, timezone, weightUnit, plan, owner, createdAt}` |
| `products` | array | Product catalog; each has variants, options, images (see Product below) |
| `collections` | array | Product groupings; each: `{id, title, bodyHtml, handle, collectionType, productIds[], productsCount, sortOrder, publishedAt, updatedAt, image}` |
| `orders` | array | Customer orders with line items and timeline (see Order below) |
| `customers` | array | Customer profiles (see Customer below) |
| `discounts` | array | Promotional codes and automatic discounts (see Discount below) |
| `draftOrders` | array | Manually created order quotes: `{id, name, status, lineItems[], customer, subtotalPrice, totalTax, totalPrice, note, tags[], createdAt, updatedAt}` |
| `giftCards` | array | Prepaid store credit: `{id, code, initialValue, balance, currency, status, customerId, note, expiresOn, createdAt}` |
| `analytics` | object | `{dailyMetrics[], totalSalesThisMonth, totalOrdersThisMonth, totalSessionsThisMonth}` |
| `pages` | array | Static store pages: `{id, title, handle, bodyHtml, published, createdAt, updatedAt}` |
| `blogPosts` | array | Blog articles: `{id, title, author, bodyHtml, handle, tags[], published, publishedAt, createdAt}` |
| `navigationMenus` | array | Menu structures: `{id, title, handle, items[]}` where items have `{id, title, url, position, children[]}` |
| `settings` | object | `{storeName, storeEmail, senderEmail, storePhone, currency, timezone, weightUnit}` |

### Product

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Product ID (e.g., `"prod_1"`) |
| `title` | string | Product name |
| `bodyHtml` | string | HTML description |
| `vendor` | string | Brand/vendor name |
| `productType` | string | Category (e.g., `"Shirts"`) |
| `handle` | string | URL slug |
| `status` | string | `"active"\|"draft"\|"archived"` |
| `tags` | array | String tags (e.g., `["cotton", "summer"]`) |
| `images` | array | Each: `{id, src, alt, position}` |
| `variants` | array | Each: `{id, productId, title, price, compareAtPrice, sku, inventoryQuantity, option1, option2, position}` |
| `options` | array | Each: `{id, name, position, values[]}` (e.g., Size: `["Small","Medium","Large"]`) |
| `collections` | array | Collection IDs this product belongs to |
| `createdAt` | string | ISO 8601 timestamp |
| `updatedAt` | string | ISO 8601 timestamp |

### Order

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Order ID (e.g., `"order_1"`) |
| `name` | string | Display number (e.g., `"#1001"`) |
| `orderNumber` | number | Numeric order number |
| `email` | string | Customer email |
| `financialStatus` | string | `"paid"\|"pending"\|"partially_paid"\|"refunded"\|"voided"` |
| `fulfillmentStatus` | string\|null | `null` (unfulfilled), `"fulfilled"`, or `"partial"` |
| `currency` | string | Currency code (e.g., `"USD"`) |
| `subtotalPrice` | string | Subtotal amount |
| `totalShippingPrice` | string | Shipping cost |
| `totalTax` | string | Tax amount |
| `totalDiscounts` | string | Discount amount |
| `totalPrice` | string | Final total |
| `lineItems` | array | Each: `{id, productId, variantId, title, variantTitle, quantity, price, sku, imageSrc, fulfillmentStatus}` |
| `customer` | object | `{id, firstName, lastName, email}` |
| `shippingAddress` | object | `{address1, city, province, provinceCode, country, countryCode, zip}` |
| `billingAddress` | object | Same structure as shippingAddress |
| `note` | string | Internal order note |
| `tags` | array | Order tags |
| `discountCodes` | array | Each: `{code, amount, type}` |
| `timeline` | array | Activity log; each: `{id, type, message, createdAt, user}` |
| `createdAt` | string | ISO 8601 timestamp |
| `updatedAt` | string | ISO 8601 timestamp |

### Customer

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Customer ID (e.g., `"cust_1"`) |
| `firstName` | string | First name |
| `lastName` | string | Last name |
| `email` | string | Email address |
| `phone` | string\|null | Phone number |
| `state` | string | `"enabled"\|"disabled"\|"invited"` |
| `ordersCount` | number | Total orders placed |
| `totalSpent` | string | Lifetime spend |
| `note` | string | Internal notes |
| `tags` | array | Customer tags |
| `taxExempt` | boolean | Tax exemption status |
| `verifiedEmail` | boolean | Email verified |
| `acceptsMarketing` | boolean | Marketing consent |
| `defaultAddress` | object | Primary address: `{address1, city, province, provinceCode, country, countryCode, zip}` |
| `createdAt` | string | ISO 8601 timestamp |
| `updatedAt` | string | ISO 8601 timestamp |

### Discount

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Discount ID (e.g., `"disc_1"`) |
| `title` | string | Display name |
| `code` | string\|null | Discount code (null for automatic discounts) |
| `type` | string | `"percentage"\|"fixed_amount"\|"free_shipping"\|"buy_x_get_y"` |
| `value` | string | Discount value (e.g., `"10"` for 10%) |
| `status` | string | `"active"\|"scheduled"\|"expired"` |
| `appliesTo` | string | `"all"\|"specific_collections"\|"specific_products"` |
| `appliesToIds` | array | Target collection/product IDs |
| `minimumRequirement` | string | `"none"\|"min_purchase"\|"min_quantity"` |
| `minimumValue` | string | Minimum value for requirement |
| `customerEligibility` | string | `"all"\|"specific_segments"` |
| `usageLimit` | number\|null | Total uses allowed (null = unlimited) |
| `usageCount` | number | Times used |
| `oncePerCustomer` | boolean | Restrict to once per customer |
| `startsAt` | string | ISO 8601 start date |
| `endsAt` | string\|null | ISO 8601 end date (null = no end) |
| `createdAt` | string | ISO 8601 timestamp |

### DailyMetric (in `analytics.dailyMetrics[]`)

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | `"YYYY-MM-DD"` format |
| `totalSales` | number | Revenue amount |
| `ordersCount` | number | Number of orders |
| `onlineStoreSessions` | number | Session count |
| `returningCustomerRate` | number | Decimal rate (e.g., 0.24 = 24%) |
| `conversionRate` | number | Decimal rate |
| `averageOrderValue` | number | AOV in dollars |
| `topProducts` | array | `[{productId, title, quantity, revenue}]` |
| `topReferrers` | array | `[{source, sessions}]` |
| `sessionsByLocation` | array | `[{country, sessions}]` |

### Default data counts
- 13 products (8 active, 3 draft, 2 archived), 6 collections, 18 orders, 12 customers, 6 discounts, 3 draft orders, 4 gift cards, 4 pages, 5 blog posts, 2 navigation menus, 30 days of analytics

### Default store
- Name: `"Evergreen Goods"`, Domain: `"evergreengoods.myshopify.com"`, Currency: `"USD"`, Plan: `"Basic Shopify"`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "https://cua-gym-shopify-admin.xlang.ai/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "store": {
          "id": "store_1", "name": "My Shop", "email": "admin@myshop.com",
          "domain": "myshop.myshopify.com", "currency": "USD", "plan": "Basic Shopify",
          "owner": {"firstName": "Alex", "lastName": "Chen", "email": "alex@myshop.com"}
        },
        "products": [
          {
            "id": "prod_1", "title": "Classic T-Shirt", "bodyHtml": "<p>Soft cotton tee</p>",
            "vendor": "My Brand", "productType": "Shirts", "handle": "classic-t-shirt",
            "status": "active", "tags": ["cotton", "basics"],
            "images": [{"id": "img_1", "src": "https://placehold.co/400x400/e8f5e9/2e7d32?text=T-Shirt", "alt": "T-Shirt", "position": 1}],
            "variants": [
              {"id": "var_1", "productId": "prod_1", "title": "Small", "price": "24.99", "compareAtPrice": null, "sku": "TS-SM", "inventoryQuantity": 50, "option1": "Small", "option2": null, "position": 1}
            ],
            "options": [{"id": "opt_1", "name": "Size", "position": 1, "values": ["Small", "Medium", "Large"]}],
            "collections": [], "createdAt": "2024-01-15T10:00:00Z", "updatedAt": "2024-03-10T14:30:00Z"
          }
        ],
        "collections": [],
        "orders": [
          {
            "id": "order_1", "name": "#1001", "orderNumber": 1001,
            "email": "john@example.com", "financialStatus": "paid", "fulfillmentStatus": null,
            "currency": "USD", "subtotalPrice": "24.99", "totalShippingPrice": "5.99",
            "totalTax": "2.00", "totalDiscounts": "0.00", "totalPrice": "32.98",
            "lineItems": [{"id": "li_1", "productId": "prod_1", "variantId": "var_1", "title": "Classic T-Shirt", "variantTitle": "Small", "quantity": 1, "price": "24.99", "sku": "TS-SM"}],
            "customer": {"id": "cust_1", "firstName": "John", "lastName": "Doe", "email": "john@example.com"},
            "shippingAddress": {"address1": "123 Main St", "city": "Portland", "province": "Oregon", "country": "United States", "zip": "97201"},
            "note": "", "tags": [], "discountCodes": [],
            "timeline": [{"id": "evt_1", "type": "created", "message": "Order placed", "createdAt": "2024-03-10T14:30:00Z"}],
            "createdAt": "2024-03-10T14:30:00Z", "updatedAt": "2024-03-10T14:30:00Z"
          }
        ],
        "customers": [
          {"id": "cust_1", "firstName": "John", "lastName": "Doe", "email": "john@example.com", "phone": null, "state": "enabled", "ordersCount": 1, "totalSpent": "32.98", "tags": [], "acceptsMarketing": true, "createdAt": "2024-01-01T10:00:00Z"}
        ],
        "discounts": [],
        "draftOrders": [],
        "giftCards": [],
        "analytics": {"dailyMetrics": [], "totalSalesThisMonth": 0, "totalOrdersThisMonth": 0, "totalSessionsThisMonth": 0},
        "pages": [],
        "blogPosts": [],
        "navigationMenus": [],
        "settings": {"storeName": "My Shop", "storeEmail": "admin@myshop.com", "currency": "USD", "timezone": "(GMT-08:00) Pacific Time", "weightUnit": "lb"}
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Add product | `products` array grows |
| Update product title/status/etc. | `products[i]` fields updated |
| Delete product | `products` array shrinks |
| Update product variant inventory | `products[i].variants[j].inventoryQuantity` updated |
| Update product variant price | `products[i].variants[j].price` updated |
| Change product status | `products[i].status` updated (active/draft/archived) |
| Fulfill order | `orders[i].fulfillmentStatus` → `"fulfilled"`; `timeline` grows |
| Update order tags/note | `orders[i].tags` or `orders[i].note` updated |
| Add customer | `customers` array grows |
| Update customer details | `customers[i]` fields updated |
| Create discount | `discounts` array grows |
| Delete discount | `discounts` array shrinks |
| Update store settings | `settings` fields updated |
| Add page | `pages` array grows |
| Update page content | `pages[i].bodyHtml`, `.title`, etc. updated |
| Add blog post | `blogPosts` array grows |
| Create collection | `collections` array grows |
| Add product to collection | `collections[i].productIds` grows; `products[i].collections` grows |
