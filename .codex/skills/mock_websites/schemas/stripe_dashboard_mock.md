# stripe_dashboard_mock Schema

**Deploy order**: 45 (alphabetical among all *_mock dirs)
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `business` | object | `{name, email, url, support_email, country, currency, timezone}` |
| `currentUser` | object | `{id, name, email, role, avatar}` |
| `balance` | object | `{available, pending, reserved, currency}` — all amounts in cents |
| `customers` | array | Customer objects (see below) |
| `payments` | array | Payment intent objects (see below) |
| `products` | array | Product objects (see below) |
| `prices` | array | Price objects (see below) |
| `invoices` | array | Invoice objects (see below) |
| `subscriptions` | array | Subscription objects (see below) |
| `payouts` | array | Payout objects (see below) |
| `disputes` | array | Dispute objects (see below) |
| `refunds` | array | Refund objects (see below) |
| `balanceTransactions` | array | Transaction ledger entries (see below) |
| `events` | array | Audit events: `{id, type, created, data: {object: {id}}, request, livemode}` |
| `paymentMethods` | array | Payment method objects (see below) |
| `testMode` | boolean | Whether test mode is active |
| `searchQuery` | string | Current search query |
| `selectedDateRange` | string | Selected date range filter |
| `metrics` | object | Analytics/chart data (see Metrics below) |

**Note**: All monetary amounts are in **cents** (e.g., `2999` = $29.99). All timestamps are **Unix seconds**.

### Customer

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Customer ID (e.g., `"cus_P1a2b3c4d5e6f7"`) |
| `name` | string | Customer/business name |
| `email` | string | Email address |
| `phone` | string\|null | Phone number |
| `description` | string\|null | Notes/description |
| `address` | object\|null | `{line1, line2, city, state, postal_code, country}` |
| `balance` | number | Account balance in cents |
| `currency` | string | Currency code (e.g., `"usd"`) |
| `default_payment_method` | string\|null | PaymentMethod ID |
| `metadata` | object | Custom key-value pairs |
| `created` | number | Unix timestamp (seconds) |
| `livemode` | boolean | Live/test mode flag |
| `delinquent` | boolean | Payment delinquency |
| `total_spent` | number | Total spent in cents |
| `payments_count` | number | Number of payments |

### Payment

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payment intent ID (e.g., `"pi_0001Fj49a8cB"`) |
| `amount` | number | Amount in cents |
| `currency` | string | Currency code |
| `status` | string | `"succeeded"\|"pending"\|"failed"\|"processing"` |
| `description` | string\|null | Payment description |
| `customer` | string | Customer ID (foreign key) |
| `customer_email` | string | Denormalized customer email |
| `customer_name` | string | Denormalized customer name |
| `payment_method` | object | `{type: "card", card: {brand, last4, exp_month, exp_year, funding}}` |
| `amount_received` | number | Amount received in cents |
| `amount_refunded` | number | Amount refunded in cents |
| `refunded` | boolean | Whether fully refunded |
| `disputed` | boolean | Whether has active dispute |
| `captured` | boolean | Whether charge was captured |
| `receipt_email` | string\|null | Receipt email |
| `receipt_url` | string\|null | Receipt URL |
| `metadata` | object | Custom metadata (e.g., `{order_id: "..."}`) |
| `created` | number | Unix timestamp (seconds) |
| `livemode` | boolean | Live mode flag |
| `risk_score` | number | Risk score (0–100) |
| `risk_level` | string | `"normal"\|"elevated"\|"blocked"` |
| `outcome` | object | `{type, risk_level, risk_score, reason}` |
| `invoice` | string\|null | Related Invoice ID |

### Product

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Product ID (e.g., `"prod_starter01"`) |
| `name` | string | Product name |
| `description` | string | Description |
| `active` | boolean | Active status |
| `images` | array | Image URLs |
| `default_price` | string | Default Price ID |
| `metadata` | object | Custom metadata |
| `created` | number | Unix timestamp (seconds) |
| `updated` | number | Last update timestamp |
| `unit_label` | string\|null | Unit label (e.g., `"seat"`) |

### Price

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Price ID (e.g., `"price_starter_monthly"`) |
| `product` | string | Product ID (foreign key) |
| `active` | boolean | Active status |
| `currency` | string | Currency code |
| `unit_amount` | number | Price in cents (e.g., `999` = $9.99) |
| `billing_scheme` | string | `"per_unit"\|"tiered"` |
| `type` | string | `"recurring"\|"one_time"` |
| `recurring` | object\|null | `{interval: "day"\|"week"\|"month"\|"year", interval_count, usage_type: "licensed"\|"metered"}` |
| `nickname` | string | Display name (e.g., `"Monthly"`) |
| `metadata` | object | Custom metadata |
| `created` | number | Unix timestamp (seconds) |

### Invoice

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Invoice ID (e.g., `"in_0001"`) |
| `number` | string | Invoice number (e.g., `"INV-0001"`) |
| `customer` | string | Customer ID (foreign key) |
| `customer_name` | string | Denormalized customer name |
| `customer_email` | string | Denormalized customer email |
| `status` | string | `"draft"\|"open"\|"paid"\|"void"\|"uncollectible"` |
| `amount_due` | number | Amount due in cents |
| `amount_paid` | number | Amount paid in cents |
| `amount_remaining` | number | Remaining in cents |
| `currency` | string | Currency code |
| `description` | string\|null | Description |
| `due_date` | number\|null | Due date timestamp |
| `collection_method` | string | `"charge_automatically"\|"send_invoice"` |
| `billing_reason` | string | `"subscription_cycle"\|"manual"` etc. |
| `subscription` | string\|null | Subscription ID (foreign key) |
| `lines` | array | Each: `{id, description, amount, currency, quantity, price, period: {start, end}}` |
| `subtotal` | number | Subtotal in cents |
| `tax` | number | Tax in cents |
| `total` | number | Total in cents |
| `period_start` | number | Billing period start |
| `period_end` | number | Billing period end |
| `created` | number | Unix timestamp (seconds) |
| `paid_at` | number\|null | Payment timestamp |
| `metadata` | object | Custom metadata |

### Subscription

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Subscription ID (e.g., `"sub_01acme"`) |
| `customer` | string | Customer ID (foreign key) |
| `customer_name` | string | Denormalized customer name |
| `customer_email` | string | Denormalized customer email |
| `status` | string | `"active"\|"past_due"\|"canceled"\|"trialing"\|"paused"\|"unpaid"` |
| `items` | array | Each: `{id, price, product, product_name, quantity, unit_amount?, currency?, interval?}` |
| `current_period_start` | number | Period start timestamp |
| `current_period_end` | number | Period end timestamp |
| `cancel_at_period_end` | boolean | Cancel at period end flag |
| `canceled_at` | number\|null | Cancellation timestamp |
| `ended_at` | number\|null | End timestamp |
| `trial_start` | number\|null | Trial start timestamp |
| `trial_end` | number\|null | Trial end timestamp |
| `collection_method` | string | `"charge_automatically"\|"send_invoice"` |
| `default_payment_method` | string\|null | PaymentMethod ID |
| `latest_invoice` | string\|null | Latest Invoice ID |
| `pause_collection` | object\|null | `{behavior: "void"\|"keep_as_draft"}` |
| `metadata` | object | Custom metadata |
| `created` | number | Unix timestamp (seconds) |

### Payout

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payout ID (e.g., `"po_0001aB3cD"`) |
| `amount` | number | Amount in cents |
| `currency` | string | Currency code |
| `status` | string | `"pending"\|"in_transit"\|"paid"\|"failed"` |
| `arrival_date` | number | Expected arrival timestamp |
| `method` | string | `"standard"\|"instant"` |
| `type` | string | `"bank_account"` |
| `description` | string | `"STRIPE PAYOUT"` |
| `destination` | object | `{bank_name, last4, routing_number}` |
| `created` | number | Unix timestamp (seconds) |
| `metadata` | object | Custom metadata |

### Dispute

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Dispute ID (e.g., `"dp_001aB3cD"`) |
| `amount` | number | Disputed amount in cents |
| `currency` | string | Currency code |
| `charge` | string | Payment ID (foreign key) |
| `customer` | string | Customer ID (denormalized) |
| `reason` | string | `"fraudulent"\|"product_not_received"\|"duplicate"\|"unrecognized"` |
| `status` | string | `"needs_response"\|"under_review"\|"won"\|"lost"` |
| `evidence_due_by` | number\|null | Deadline timestamp |
| `created` | number | Unix timestamp (seconds) |
| `metadata` | object | Custom metadata |

### Refund

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Refund ID (e.g., `"re_001aB3cD"`) |
| `amount` | number | Refund amount in cents |
| `currency` | string | Currency code |
| `charge` | string | Payment ID being refunded (foreign key) |
| `reason` | string | `"requested_by_customer"\|"duplicate"\|"fraudulent"` |
| `status` | string | `"succeeded"\|"pending"\|"failed"` |
| `created` | number | Unix timestamp (seconds) |
| `metadata` | object | Custom metadata |

### BalanceTransaction

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Transaction ID (e.g., `"txn_ch_0001"`) |
| `amount` | number | Amount in cents (negative for debits) |
| `currency` | string | Currency code |
| `type` | string | `"charge"\|"refund"\|"payout"\|"adjustment"` |
| `fee` | number | Processing fee in cents |
| `net` | number | Net amount in cents (amount − fee) |
| `status` | string | `"available"` |
| `available_on` | number | Availability timestamp |
| `source` | string | Reference to Payment/Refund/Payout ID |
| `description` | string | Transaction description |
| `created` | number | Unix timestamp (seconds) |

### PaymentMethod

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | PaymentMethod ID (e.g., `"pm_acme_visa_01"`) |
| `type` | string | `"card"` |
| `card` | object | `{brand, last4, exp_month, exp_year, funding}` |
| `billing_details` | object | `{name}` |
| `created` | number | Unix timestamp (seconds) |
| `customer` | string | Customer ID (denormalized) |

### Metrics

| Field | Type | Description |
|-------|------|-------------|
| `today` | object | `{grossVolume, grossVolumeChart: [{time, amount}]}` |
| `summary` | object | `{grossVolume: {amount, change, previousAmount}, netVolume: {...}, disputeActivity: {rate, change, previousRate}}` |
| `chartData` | object | `{grossVolume: [{date, amount}], netVolume: [{date, amount}], disputeRate: [{date, rate}]}` |

### Entity relationships
- Payment → Customer (via `customer` field)
- Payment → Invoice (via `invoice` field, optional)
- Subscription → Customer (via `customer` field)
- Subscription.items → Product, Price (via `product`, `price` fields)
- Invoice → Customer (via `customer` field)
- Invoice → Subscription (via `subscription` field, optional)
- Refund → Payment (via `charge` field)
- Dispute → Payment (via `charge` field)
- Price → Product (via `product` field)
- PaymentMethod → Customer (via `customer` field)

### Default data counts
- 16 customers, 7 products, 10 prices, 45 payments, 10 subscriptions, 22 invoices, 12 payouts, 4 disputes, 6 refunds, 35 events

### Event types generated
`payment_intent.succeeded`, `payment_intent.created`, `charge.succeeded`, `charge.refunded`, `customer.created`, `customer.updated`, `customer.deleted`, `invoice.created`, `invoice.paid`, `invoice.payment_failed`, `invoice.updated`, `invoice.voided`, `subscription.created`, `subscription.updated`, `payout.paid`, `dispute.created`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "https://cua-gym-stripe-dashboard.xlang.ai/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "business": {
          "name": "Rocket Rides", "email": "admin@rocketrides.io", "url": "https://rocketrides.io",
          "support_email": "support@rocketrides.io", "country": "US", "currency": "usd", "timezone": "America/Los_Angeles"
        },
        "currentUser": {"id": "user_admin", "name": "Admin User", "email": "admin@rocketrides.io", "role": "administrator", "avatar": null},
        "balance": {"available": 5432100, "pending": 1234500, "reserved": 0, "currency": "usd"},
        "testMode": false,
        "searchQuery": "",
        "selectedDateRange": "7d",
        "customers": [
          {
            "id": "cus_001", "name": "Acme Corp", "email": "billing@acme.com", "phone": null,
            "description": "Enterprise customer", "address": {"line1": "123 Main St", "city": "San Francisco", "state": "CA", "postal_code": "94105", "country": "US"},
            "balance": 0, "currency": "usd", "default_payment_method": null,
            "metadata": {}, "created": 1704067200, "livemode": true, "delinquent": false,
            "total_spent": 149900, "payments_count": 3
          }
        ],
        "payments": [
          {
            "id": "pi_001", "amount": 4999, "currency": "usd", "status": "succeeded",
            "description": "Pro Plan - Monthly", "customer": "cus_001",
            "customer_email": "billing@acme.com", "customer_name": "Acme Corp",
            "payment_method": {"type": "card", "card": {"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2025, "funding": "credit"}},
            "amount_received": 4999, "amount_refunded": 0, "refunded": false, "disputed": false, "captured": true,
            "metadata": {}, "created": 1710072600, "livemode": true,
            "risk_score": 12, "risk_level": "normal",
            "outcome": {"type": "authorized", "risk_level": "normal", "risk_score": 12, "reason": null},
            "invoice": null
          }
        ],
        "products": [],
        "prices": [],
        "invoices": [],
        "subscriptions": [],
        "payouts": [],
        "disputes": [],
        "refunds": [],
        "balanceTransactions": [],
        "events": [],
        "paymentMethods": [],
        "metrics": {
          "today": {"grossVolume": 4999, "grossVolumeChart": []},
          "summary": {"grossVolume": {"amount": 4999, "change": 0, "previousAmount": 0}, "netVolume": {"amount": 4854, "change": 0, "previousAmount": 0}, "disputeActivity": {"rate": 0, "change": 0, "previousRate": 0}},
          "chartData": {"grossVolume": [], "netVolume": [], "disputeRate": []}
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Create customer | `customers` array grows; `events` gains `customer.created` |
| Update customer | `customers[i]` fields updated; `events` gains `customer.updated` |
| Delete customer | `customers` array shrinks; `events` gains `customer.deleted` |
| Create payment | `payments` grows; `balanceTransactions` grows; `events` gains `payment_intent.succeeded` |
| Refund payment | `refunds` grows; `payments[i].amount_refunded` updated; `events` gains `charge.refunded` |
| Create product | `products` array grows |
| Update product | `products[i]` fields updated |
| Add price | `prices` array grows |
| Create invoice | `invoices` grows; `events` gains `invoice.created` |
| Pay invoice | `invoices[i].status` → `"paid"`; `events` gains `invoice.paid` |
| Void invoice | `invoices[i].status` → `"void"`; `events` gains `invoice.voided` |
| Create subscription | `subscriptions` grows; `events` gains `subscription.created` |
| Cancel subscription | `subscriptions[i].status` → `"canceled"` or `cancel_at_period_end` → `true`; `events` gains `subscription.updated` |
| Update dispute | `disputes[i].status` updated |
| Toggle test mode | `testMode` toggled |
| Search | `searchQuery` updated |
