# zillow_mock Schema

**Deploy order**: 62 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8062)
**Base URL**: `http://172.17.46.46:8062/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Home | Hero landing page (default view) or filtered search results with map |
| `/property/:id` | PropertyDetail | Full property detail page with gallery, Zestimate, tour scheduling, agent contact |
| `/saved` | SavedHomes | Saved properties and saved searches/alerts |
| `/mortgage` | Mortgage | Mortgage calculator with current rate display |
| `/agent-finder` | AgentFinder | Search and browse real estate agents |
| `/sell` | Sell | Seller tools: Zestimate lookup, selling process, listing agents |
| `/go` | Go | State inspection / debug endpoint |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Active user profile and saved items |
| `filters` | object | Current property search/filter state |
| `properties` | array | All property listings (25 default) |
| `agents` | array | Real estate agents (10 default) |
| `savedSearches` | array | Full saved search objects with filter criteria |
| `searchSuggestions` | array | Autocomplete suggestions for search (cities, neighborhoods, ZIP codes) |
| `mortgageRates` | array | Current mortgage rate data |
| `tours` | array | Scheduled property tours (empty by default) |

### `user` object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `userId` | string | `"user-1"` | Unique user identifier |
| `name` | string | `"Sarah Chen"` | Full name |
| `email` | string | `"sarah.chen@email.com"` | Email address |
| `phone` | string | `"(415) 555-0142"` | Phone number |
| `avatar` | string\|null | `null` | Avatar URL |
| `savedProperties` | string[] | `["prop-2", "prop-5", "prop-8"]` | Array of saved property IDs |
| `savedSearches` | string[] | `["search-1", "search-2"]` | Array of saved search IDs (references `savedSearches[].id`) |
| `recentlyViewed` | string[] | `["prop-1", "prop-3", "prop-7", "prop-12"]` | Array of recently viewed property IDs |

### `filters` object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `search` | string | `""` | Free-text search query (address, city, ZIP, neighborhood) |
| `listingStatus` | string | `"For Sale"` | One of: `"For Sale"`, `"For Rent"`, `"Pending"`, `"Recently Sold"`, `"All"` |
| `minPrice` | number | `0` | Minimum price filter |
| `maxPrice` | number | `10000000` | Maximum price filter |
| `minBeds` | number | `0` | Minimum bedrooms (0 = any) |
| `minBaths` | number | `0` | Minimum bathrooms (0 = any) |
| `minSqft` | number | `0` | Minimum square footage |
| `maxSqft` | number | `100000` | Maximum square footage |
| `type` | string | `"All"` | Property type: `"All"`, `"Single Family"`, `"Condo"`, `"Townhouse"`, `"Apartment"` |
| `features` | string[] | `[]` | Required features (e.g. `["Garage", "Fireplace", "Pool"]`) |
| `sortBy` | string | `"Homes for You"` | Sort order: `"Homes for You"`, `"Price (Low to High)"`, `"Price (High to Low)"`, `"Newest"`, `"Bedrooms"`, `"Square Feet"` |

### `properties[]` array (25 default properties)

Each property object:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID (`"prop-1"` through `"prop-25"`) |
| `zpid` | string | Zillow property ID |
| `address` | string | Street address |
| `city` | string | City name |
| `state` | string | State abbreviation (e.g. `"CA"`) |
| `zip` | string | ZIP code |
| `neighborhood` | string | Neighborhood name |
| `price` | number | Listing price (sale) or monthly rent |
| `zestimate` | number\|null | Zillow estimated value (null for rentals) |
| `zestimateRange` | object\|null | `{low: number, high: number}` or null |
| `rentZestimate` | number\|null | Estimated monthly rent |
| `beds` | number | Number of bedrooms |
| `baths` | number | Number of bathrooms (supports .5 for half baths) |
| `sqft` | number | Square footage |
| `lotSize` | number | Lot size in sqft (0 for condos/apartments) |
| `yearBuilt` | number | Year built |
| `type` | string | `"Single Family"`, `"Condo"`, `"Townhouse"`, `"Apartment"` |
| `propertyType` | string | Same as `type` (duplicated for compatibility) |
| `listingStatus` | string | `"For Sale"`, `"For Rent"`, `"Recently Sold"`, `"Pending"` |
| `listingType` | string | `"Agent Listed"`, `"For Sale By Owner"` |
| `daysOnZillow` | number | Days listed on Zillow |
| `description` | string | Property description text |
| `features` | string[] | Array of feature strings |
| `coordinates` | number[] | `[latitude, longitude]` for map display |
| `images` | string[] | Array of image URLs |
| `agentId` | string | ID of listing agent (references `agents[].id`) |
| `tags` | string[] | Tags: `"New Listing"`, `"Price Cut"`, `"Hot Home"`, `"Open House"`, `"For Sale By Owner"` |
| `openHouse` | string\|null | Open house schedule text or null |
| `hoaFee` | number\|null | Monthly HOA fee or null |
| `propertyTax` | number\|null | Annual property tax or null (null for rentals) |
| `walkScore` | number\|null | Walk Score (0-100) |
| `transitScore` | number\|null | Transit Score (0-100) |
| `bikeScore` | number\|null | Bike Score (0-100) |
| `priceHistory` | array | `[{date, event, price, source}]` |
| `taxHistory` | array | `[{year, propertyTax, taxAssessment}]` |
| `schools` | array | `[{name, level, grades, rating, distance, type}]` |
| `estimatedPayment` | object\|null | `{total, principalAndInterest, propertyTax, homeInsurance, hoa, mortgageInsurance}` or null |

#### Default property distribution

| Status | Type | Count | IDs |
|--------|------|-------|-----|
| For Sale | Single Family | 8 | prop-1 through prop-8 |
| For Sale | Condo | 5 | prop-9 through prop-13 |
| For Sale | Townhouse | 3 | prop-14 through prop-16 |
| For Rent | Apartment | 3 | prop-17 through prop-19 |
| For Rent | Single Family | 2 | prop-20, prop-21 |
| Recently Sold | Single Family | 2 | prop-22, prop-23 |
| Pending | Single Family | 1 | prop-24 |
| Pending | Condo | 1 | prop-25 |

### `agents[]` array (10 default agents)

Each agent object:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID (`"agent-1"` through `"agent-10"`) |
| `name` | string | Full name |
| `photo` | string\|null | Photo URL (null by default) |
| `phone` | string | Phone number |
| `email` | string | Email address |
| `brokerage` | string | Brokerage company name |
| `rating` | number | Rating (1-5 scale, e.g. 4.9) |
| `reviewCount` | number | Number of reviews |
| `recentSales` | number | Number of recent sales |
| `activeListings` | number | Number of active listings |
| `specialties` | string[] | `"Buyer's Agent"`, `"Listing Agent"`, `"Relocation"`, `"Luxury Homes"`, `"Short Sales"`, `"Investment Properties"`, `"Staging"`, `"Rentals"` |
| `serviceAreas` | string[] | Array of city/area names |
| `isFeatured` | boolean | Whether agent is featured |
| `bio` | string | Agent biography text |

#### Default agent IDs and names

| ID | Name | Brokerage | Featured |
|----|------|-----------|----------|
| `agent-1` | Jennifer Martinez | Compass Real Estate | true |
| `agent-2` | David Kim | Coldwell Banker Realty | true |
| `agent-3` | Lisa Chen | Keller Williams SF | false |
| `agent-4` | Robert Williams | Sotheby's International Realty | true |
| `agent-5` | Sarah O'Brien | Compass Real Estate | false |
| `agent-6` | Marcus Johnson | RE/MAX Gold | false |
| `agent-7` | Amy Nguyen | Compass Real Estate | false |
| `agent-8` | James Park | Keller Williams East Bay | false |
| `agent-9` | Elena Rodriguez | Sotheby's International Realty | false |
| `agent-10` | Kevin Thompson | Coldwell Banker Realty | false |

### `savedSearches[]` array

Each saved search object:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID (e.g. `"search-1"`, or `"s{timestamp}"` for new) |
| `name` | string | User-assigned search name |
| `location` | string | Location description (optional) |
| `filters` | object | Subset of the `filters` object with search criteria |
| `createdAt` | string | ISO 8601 timestamp |
| `newListings` | number | Count of new matching listings |
| `emailAlerts` | boolean | Whether email alerts are enabled |

#### Default saved searches

| ID | Name | Location Filter | Price Range | Beds | Type |
|----|------|----------------|-------------|------|------|
| `search-1` | SF Under 900K | San Francisco | $500k-$900k | 2+ | All |
| `search-2` | Oakland Family Homes | Oakland | $600k-$1.2M | 3+ | Single Family |

### `searchSuggestions[]` array (41 default entries)

Each suggestion:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `"sug-1"` through `"sug-41"` |
| `text` | string | Display text (city, neighborhood, or ZIP) |
| `type` | string | `"city"`, `"neighborhood"`, or `"zip"` |
| `subtext` | string | Description (e.g. `"City in California"`, `"Neighborhood in San Francisco, CA"`) |

### `mortgageRates[]` array (5 default rates)

Each rate:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Rate type name (e.g. `"30-Year Fixed"`, `"15-Year Fixed"`, `"5/1 ARM"`) |
| `rate` | number | Interest rate percentage |
| `apr` | number | APR percentage |
| `lastUpdated` | string | Date string (e.g. `"2024-12-01"`) |

#### Default rates

| Type | Rate | APR |
|------|------|-----|
| 30-Year Fixed | 6.89% | 6.95% |
| 20-Year Fixed | 6.67% | 6.74% |
| 15-Year Fixed | 6.12% | 6.21% |
| 5/1 ARM | 6.45% | 7.01% |
| 7/1 ARM | 6.55% | 6.98% |

### `tours[]` array (empty by default)

Each tour object (created when user schedules a tour):

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID (e.g. `"t{timestamp}"`) |
| `propertyId` | string | Reference to property ID |
| `date` | string | Tour date (YYYY-MM-DD) |
| `time` | string | Tour time (e.g. `"10:00 AM"`, `"2:00 PM"`) |
| `type` | string | `"in-person"` or `"video"` |
| `userId` | string | User who scheduled the tour |
| `name` | string | Contact name (if provided) |
| `email` | string | Contact email (if provided) |
| `phone` | string | Contact phone (if provided) |
| `status` | string | Tour status: `"pending"` |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8062/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "userId": "user-1",
          "name": "Sarah Chen",
          "email": "sarah.chen@email.com",
          "phone": "(415) 555-0142",
          "avatar": null,
          "savedProperties": [],
          "savedSearches": [],
          "recentlyViewed": []
        },
        "filters": {
          "search": "",
          "listingStatus": "For Sale",
          "minPrice": 0,
          "maxPrice": 10000000,
          "minBeds": 0,
          "minBaths": 0,
          "minSqft": 0,
          "maxSqft": 100000,
          "type": "All",
          "features": [],
          "sortBy": "Homes for You"
        },
        "properties": [
          {
            "id": "prop-1",
            "zpid": "29384756",
            "address": "2847 Pacific Avenue",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94115",
            "neighborhood": "Pacific Heights",
            "price": 2450000,
            "zestimate": 2510000,
            "zestimateRange": {"low": 2380000, "high": 2640000},
            "rentZestimate": 8500,
            "beds": 5,
            "baths": 3.5,
            "sqft": 3200,
            "lotSize": 3800,
            "yearBuilt": 1912,
            "type": "Single Family",
            "propertyType": "Single Family",
            "listingStatus": "For Sale",
            "listingType": "Agent Listed",
            "daysOnZillow": 8,
            "description": "Magnificent Pacific Heights Victorian with sweeping Bay views.",
            "features": ["Bay View", "Hardwood Floors", "Fireplace"],
            "coordinates": [37.7920, -122.4350],
            "images": ["https://picsum.photos/seed/p1a/800/600"],
            "agentId": "agent-1",
            "tags": ["Open House"],
            "openHouse": "Sat 1-4pm",
            "hoaFee": null,
            "propertyTax": 24500,
            "walkScore": 92,
            "transitScore": 85,
            "bikeScore": 72,
            "priceHistory": [
              {"date": "2024-11-01", "event": "Listed for sale", "price": 2450000, "source": "MLS"}
            ],
            "taxHistory": [
              {"year": 2023, "propertyTax": 24500, "taxAssessment": 2040000}
            ],
            "schools": [
              {"name": "Sherman Elementary", "level": "Elementary", "grades": "K-5", "rating": 8, "distance": "0.3 mi", "type": "Public"}
            ],
            "estimatedPayment": {"total": 14200, "principalAndInterest": 10800, "propertyTax": 2042, "homeInsurance": 1020, "hoa": 0, "mortgageInsurance": 0}
          }
        ],
        "agents": [
          {
            "id": "agent-1",
            "name": "Jennifer Martinez",
            "photo": null,
            "phone": "(415) 555-0198",
            "email": "jennifer.m@compass.com",
            "brokerage": "Compass Real Estate",
            "rating": 4.9,
            "reviewCount": 187,
            "recentSales": 62,
            "activeListings": 14,
            "specialties": ["Buyer's Agent", "Listing Agent"],
            "serviceAreas": ["San Francisco", "Daly City"],
            "isFeatured": true,
            "bio": "15+ years helping families find their dream home in San Francisco."
          }
        ],
        "savedSearches": [],
        "searchSuggestions": [
          {"id": "sug-1", "text": "San Francisco, CA", "type": "city", "subtext": "City in California"}
        ],
        "mortgageRates": [
          {"type": "30-Year Fixed", "rate": 6.89, "apr": 6.95, "lastUpdated": "2024-12-01"}
        ],
        "tours": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Save/unsave a property (heart icon) | `user.savedProperties` array adds/removes property ID |
| Schedule a property tour | `tours` array grows by 1 with `{id, propertyId, date, time, type, userId, status: "pending"}` |
| Save a search (from FilterBar) | `savedSearches` array grows by 1; `user.savedSearches` array gains new search ID |
| Change search/filter criteria | `filters` object fields updated (search, listingStatus, minPrice, maxPrice, minBeds, type, features, sortBy, etc.) |
| Reset all filters | `filters` reset to default values (search="", listingStatus="For Sale", type="All", etc.) |
| Navigate to property detail | No direct state change (view-only, uses `recentlyViewed` from initial data) |
| Use mortgage calculator | No state change (client-side calculation only) |
| Contact an agent (property detail) | No state change (UI confirmation only, not persisted) |
| Look up Zestimate on Sell page | No state change (client-side calculation only) |
| Filter agents on Agent Finder | No state change (client-side filtering only) |

## Notes

- **State Management**: Uses React Context (`StoreProvider`) with `useState` hooks. State is auto-saved to localStorage on every change.
- **State Normalization**: Custom state injected via `/post` is deep-merged with defaults. Array items in `properties` and `tours` are normalized with fallback defaults for all fields.
- **Map Integration**: Uses Leaflet (`react-leaflet`) with OpenStreetMap tiles. Properties display as price-labeled markers.
- **Hero vs Search View**: The Home page shows a hero landing page when `filters.search` is empty and `listingStatus` is "For Sale" with `type` "All". Once any search or filter is applied, it switches to a split-pane search results + map view.
- **Session Support**: Full `?sid=` query parameter support for isolated sessions. State files stored in `.mock-states/` directory.
- **Styling**: Tailwind CSS with a custom `brand` color palette (Zillow blue `#006AFF`).
