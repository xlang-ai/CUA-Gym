# robinhood_mock Schema

**Deploy order**: 41 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8041)
**Base URL**: `http://172.17.46.46:8041/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Active user account info. See **User** below. |
| `stocks` | array | All available stocks/ETFs in the market. Each: see **Stock** below. |
| `portfolio` | object | Holdings keyed by stock symbol → `{quantity, avgPrice}`. |
| `watchlist` | array | Array of stock symbol strings the user is following. |
| `transactions` | array | Trade history. Each: see **Transaction** below. |
| `alerts` | array | Notification alerts. Each: see **Alert** below. |
| `news` | array | Market news feed items. Each: see **News** below. |
| `lists` | object | Curated stock lists: `{topMovers: string[], mostPopular: string[], techStocks: string[]}` |

### User

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"user_1"` | User identifier |
| `name` | string | `"Alex Johnson"` | Full name |
| `email` | string | `"alex.johnson@email.com"` | Email address |
| `cashBalance` | number | `12450.00` | Available cash in account |
| `buyingPower` | number | `12450.00` | Total buying power (updated on trades) |
| `portfolioValue` | number | computed | Total market value of held stocks (auto-calculated) |
| `accountType` | string | `"Individual"` | Account type label |
| `joinDate` | string | `"2021-03-15"` | ISO date when user joined |
| `goldMember` | boolean | `false` | Whether user is a Robinhood Gold subscriber |

### Stock

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | symbol | Unique identifier (same as symbol) |
| `symbol` | string | required | Ticker symbol (e.g. `"AAPL"`) |
| `name` | string | required | Company name |
| `currentPrice` | number | `100` | Current market price (live-simulated every 3s) |
| `prevClose` | number | `100` | Previous closing price |
| `change` | number | `0` | Price change from previous close |
| `changePercent` | number | `0` | Percentage change from previous close |
| `open` | number | prevClose | Opening price |
| `high` | number | currentPrice | Day high |
| `low` | number | currentPrice | Day low |
| `volume` | number | `0` | Trading volume |
| `avgVolume` | number | `0` | Average trading volume |
| `marketCap` | number | `0` | Market capitalization |
| `peRatio` | number | `0` | Price-to-earnings ratio |
| `dividendYield` | number | `0` | Dividend yield percentage |
| `week52High` | number | `0` | 52-week high price |
| `week52Low` | number | `0` | 52-week low price |
| `about` | string | `""` | Company description |
| `sector` | string | `"Unknown"` | Industry sector |
| `employees` | number | `0` | Number of employees |
| `headquarters` | string | `""` | HQ location |
| `founded` | number | `0` | Year founded |
| `ceo` | string | `""` | CEO name |
| `tags` | array | `[]` | Array of tag strings (e.g. `["Technology", "Cloud Computing"]`) |
| `analystRating` | object | `{buy:0,hold:0,sell:0,priceTarget:0}` | Analyst consensus: `{buy, hold, sell, priceTarget}` |
| `earnings` | object | `{nextDate:"",epsEstimate:0,revenueEstimate:""}` | Earnings info: `{nextDate, epsEstimate, revenueEstimate}` |
| `history` | array | auto-generated | Array of `{date, price, volume}` for charting (100 daily points) |

### Transaction

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | generated | Unique transaction ID (e.g. `"txn_001"`) |
| `date` | string | now ISO | ISO 8601 timestamp |
| `symbol` | string | `""` | Stock ticker symbol |
| `name` | string | `""` | Company name |
| `type` | string | `"market"` | Execution type: `"market"`, `"limit"`, or `"stop"` |
| `side` | string | `"buy"` | Trade direction: `"buy"` or `"sell"` |
| `quantity` | number | `0` | Number of shares |
| `price` | number | `0` | Execution price per share |
| `totalAmount` | number | `0` | Total trade value (quantity * price) |
| `status` | string | `"filled"` | Order status: `"filled"`, `"cancelled"`, or `"pending"` |
| `limitPrice` | number\|null | `null` | Limit price (for limit orders) |
| `stopPrice` | number\|null | `null` | Stop price (for stop orders) |

### Alert

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | required | Unique alert ID (e.g. `"alert_1"`) |
| `type` | string | required | Alert type: `"order_filled"`, `"price_movement"`, `"earnings"`, `"dividend"`, `"system"` |
| `title` | string | required | Alert title |
| `message` | string | required | Alert body text |
| `timestamp` | string | required | ISO 8601 timestamp |
| `read` | boolean | `false` | Whether the alert has been read |
| `symbol` | string\|null | `null` | Related stock symbol (null for system alerts) |

### News

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | number | index+1 | News item ID |
| `headline` | string | `"News Headline"` | Article headline |
| `source` | string | `"Unknown"` | News source name (e.g. `"Reuters"`, `"Bloomberg"`) |
| `time` | string | `"Now"` | Relative time string (e.g. `"1h ago"`, `"Yesterday"`) |
| `summary` | string | `""` | Short article summary |
| `imageUrl` | string | random picsum | Thumbnail image URL |
| `relatedSymbols` | array | `[]` | Array of related stock symbols |
| `url` | string | `"#"` | Article link |

### Portfolio entry (keyed by symbol)

| Field | Type | Description |
|-------|------|-------------|
| `quantity` | number | Number of shares held |
| `avgPrice` | number | Average cost per share |

### Lists

| Field | Type | Default |
|-------|------|---------|
| `topMovers` | string[] | `["NVDA", "TSLA", "AMD", "COIN"]` |
| `mostPopular` | string[] | `["AAPL", "TSLA", "AMZN", "MSFT", "NVDA"]` |
| `techStocks` | string[] | `["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD"]` |

## Default Stock Symbols

`AAPL`, `TSLA`, `NVDA`, `MSFT`, `AMZN`, `GOOGL`, `META`, `NFLX`, `AMD`, `SPY`, `QQQ`, `DIS`, `COIN`, `PYPL`

## Default Portfolio Holdings

| Symbol | Quantity | Avg Price |
|--------|----------|-----------|
| AAPL | 15 | $165.30 |
| NVDA | 8 | $720.50 |
| MSFT | 12 | $380.25 |
| AMZN | 20 | $155.00 |
| TSLA | 5 | $195.80 |
| SPY | 10 | $480.00 |

## Default Watchlist

`["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "META", "GOOGL", "NFLX"]`

## Default Transaction IDs

`txn_001` through `txn_012` (12 pre-seeded trades spanning Feb 10 - Mar 8, 2025)

## Default Alert IDs

`alert_1` (order filled), `alert_2` (price movement), `alert_3` (earnings), `alert_4` (dividend), `alert_5` (system)

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8041/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "id": "user_1",
          "name": "Alex Johnson",
          "email": "alex.johnson@email.com",
          "cashBalance": 10000.00,
          "buyingPower": 10000.00,
          "portfolioValue": 0,
          "accountType": "Individual",
          "joinDate": "2021-03-15",
          "goldMember": false
        },
        "stocks": [
          {
            "id": "AAPL", "symbol": "AAPL", "name": "Apple Inc.",
            "currentPrice": 178.72, "prevClose": 175.50, "change": 3.22, "changePercent": 1.83,
            "open": 176.00, "high": 179.50, "low": 175.20,
            "volume": 54000000, "avgVolume": 62000000,
            "marketCap": 2800000000000, "peRatio": 29.5, "dividendYield": 0.55,
            "week52High": 199.62, "week52Low": 143.90,
            "about": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
            "sector": "Technology", "employees": 164000, "headquarters": "Cupertino, CA", "founded": 1976, "ceo": "Tim Cook",
            "tags": ["Technology", "Consumer Electronics", "Software"],
            "analystRating": {"buy": 28, "hold": 8, "sell": 2, "priceTarget": 195.00},
            "earnings": {"nextDate": "2025-04-24", "epsEstimate": 1.62, "revenueEstimate": "$94.2B"}
          },
          {
            "id": "TSLA", "symbol": "TSLA", "name": "Tesla, Inc.",
            "currentPrice": 248.50, "prevClose": 245.80, "change": 2.70, "changePercent": 1.10,
            "open": 246.00, "high": 252.30, "low": 244.50,
            "volume": 98000000, "avgVolume": 105000000,
            "marketCap": 790000000000, "peRatio": 62.8, "dividendYield": 0,
            "week52High": 299.29, "week52Low": 138.80,
            "about": "Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles.",
            "sector": "Automotive", "employees": 140000, "headquarters": "Austin, TX", "founded": 2003, "ceo": "Elon Musk",
            "tags": ["Automotive", "Electric Vehicles", "Clean Energy"],
            "analystRating": {"buy": 18, "hold": 15, "sell": 8, "priceTarget": 280.00},
            "earnings": {"nextDate": "2025-04-22", "epsEstimate": 0.73, "revenueEstimate": "$25.6B"}
          }
        ],
        "portfolio": {
          "AAPL": {"quantity": 10, "avgPrice": 165.30}
        },
        "watchlist": ["AAPL", "TSLA"],
        "transactions": [
          {
            "id": "txn_001", "date": "2025-03-08T10:30:00Z", "symbol": "AAPL", "name": "Apple Inc.",
            "type": "market", "side": "buy", "quantity": 10, "price": 165.30,
            "totalAmount": 1653.00, "status": "filled", "limitPrice": null, "stopPrice": null
          }
        ],
        "alerts": [
          {
            "id": "alert_1", "type": "order_filled", "title": "Order Filled",
            "message": "Your order to buy 10 shares of AAPL was filled at $165.30",
            "timestamp": "2025-03-08T10:30:00Z", "read": false, "symbol": "AAPL"
          }
        ],
        "news": [
          {
            "id": 1, "headline": "S&P 500 Hits New All-Time High",
            "source": "Reuters", "time": "1h ago",
            "summary": "The S&P 500 index reached a new record close.",
            "imageUrl": "https://picsum.photos/400/300?random=news1",
            "relatedSymbols": ["SPY", "AAPL"], "url": "#"
          }
        ],
        "lists": {
          "topMovers": ["TSLA"],
          "mostPopular": ["AAPL", "TSLA"],
          "techStocks": ["AAPL"]
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Buy stock (market order) | `user.cashBalance` and `user.buyingPower` decrease; `portfolio[symbol].quantity` increases (or new entry created); `portfolio[symbol].avgPrice` recalculated; `transactions` array grows by 1 (status `"filled"`); `user.portfolioValue` recalculated |
| Sell stock (market order) | `user.cashBalance` and `user.buyingPower` increase; `portfolio[symbol].quantity` decreases (entry deleted if 0); `transactions` array grows by 1; `user.portfolioValue` recalculated |
| Buy stock (limit order) | Same as market buy but `transactions[].type` = `"limit"`, `transactions[].limitPrice` set |
| Buy stock (stop order) | Same as market buy but `transactions[].type` = `"stop"`, `transactions[].stopPrice` set |
| Sell stock (limit order) | Same as market sell but `transactions[].type` = `"limit"`, `transactions[].limitPrice` set |
| Add stock to watchlist | `watchlist` array gains the symbol string |
| Remove stock from watchlist | `watchlist` array loses the symbol string |
| Toggle watchlist (from stock detail) | `watchlist` array gains or loses the symbol |
| Cancel pending order | `transactions[i].status` changes from `"pending"` to `"cancelled"` |
| Mark single alert as read | `alerts[i].read` → `true` |
| Mark all alerts as read | All entries in `alerts` have `read` → `true` |
| Price simulation tick (auto, every 3s) | `stocks[i].currentPrice`, `stocks[i].change`, `stocks[i].changePercent` updated for all stocks; `user.portfolioValue` recalculated |

## Routes

| Path | Page | Description |
|------|------|-------------|
| `/` | Dashboard | Portfolio value chart, buying power, news feed, watchlist sidebar |
| `/stock/:symbol` | StockDetail | Stock price chart, position info, about, analyst ratings, earnings, order form |
| `/portfolio` | Portfolio | Holdings table with sorting, summary cards (portfolio value, cash, buying power) |
| `/history` | History | Transaction list with date grouping, filterable by side (buy/sell) and status (filled/cancelled) |
| `/account` | Account | User profile, account type, Gold membership status, app settings |
| `/notifications` | Notifications | Alert list with mark-as-read and mark-all-as-read |
| `/crypto` | Placeholder | Coming soon page |
| `/transfers` | Placeholder | Coming soon page |
| `/go` | Go | State inspection endpoint (JSON view of initial_state, current_state, state_diff) |

## Notes

- **Live price simulation**: Stock prices are simulated with random micro-fluctuations every 3 seconds (up to +/- 0.2% per tick). The `user.portfolioValue` is recalculated on each tick.
- **History field on stocks**: The `history` array on each stock is auto-generated with ~100 daily price points when not provided in injected state. Each entry is `{date: "YYYY-MM-DD", price: number, volume: number}`.
- **State normalization on inject**: When custom state is injected, stocks are normalized (missing fields get defaults), and history is auto-generated if not provided.
- **localStorage keys**: State is stored under `tradeflow_state_v2` (or `tradeflow_state_v2_<sid>` with sessions), initial state under `tradeflow_initial_v2` (or `tradeflow_initial_v2_<sid>`).
