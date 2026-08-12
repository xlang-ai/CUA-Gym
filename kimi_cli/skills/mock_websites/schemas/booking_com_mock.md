# booking_com_mock Schema

**Deploy order**: 5 (alphabetical among all *_mock dirs, BASE_PORT=8000 -> port 8005)
**Base URL**: `http://172.17.46.46:8005/`
**Go Endpoint**: `GET /go?sid=<sid>` -> `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Home | Landing page with search bar, trending destinations, recent searches, browse by type, recently viewed |
| `/search` | Search | Property search results with sidebar filters and sort options |
| `/property/:id` | PropertyDetail | Full property page with photos, rooms, reviews, booking sidebar |
| `/checkout` | Checkout | Booking form with guest details, arrival time, special requests |
| `/confirmation/:bookingId?` | Confirmation | Booking confirmation with confirmation number and PIN |
| `/mytrips` | Trips | User's bookings with tabs for upcoming/completed/cancelled |
| `/saved` | Saved | User's saved (wishlisted) properties |
| `/go` | Go | State inspector endpoint |

## State Schema

The state is stored as `{ initial_state, current_state }` where both share the same shape. The `/go` endpoint returns `{ initial_state, current_state, state_diff }`.

### Top-Level Keys

| Key | Type | Description |
|-----|------|-------------|
| `user` | Object | Current user profile and preferences |
| `destinations` | Array\<Destination\> | All available travel destinations (10 items) |
| `properties` | Array\<Property\> | All available accommodation listings (12 items) |
| `rooms` | Array\<Room\> | All room types across all properties (28 items) |
| `reviews` | Array\<Review\> | Guest reviews for properties (28 items) |
| `reviewCategories` | Object | Per-property category review scores (keyed by property ID) |
| `bookings` | Array\<Booking\> | User's bookings (initially 3) |
| `searchParams` | Object | Current search parameters |
| `searchFilters` | Object | Active search filter settings |
| `searchResults` | Array | Search results (initially empty, populated client-side) |
| `selectedPropertyId` | String\|null | Currently viewed property ID |
| `recentSearches` | Array\<RecentSearch\> | Recent search history (max 5) |
| `recentlyViewed` | Array\<String\> | Recently viewed property IDs (max 10) |
| `notifications` | Array | Notifications (initially empty) |
| `viewedProperties` | Array\<String\> | All property IDs that have been viewed |

### user Object

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `user.id` | String | `"user_1"` | User ID |
| `user.firstName` | String | `"Sarah"` | First name |
| `user.lastName` | String | `"Johnson"` | Last name |
| `user.email` | String | `"sarah.johnson@email.com"` | Email address |
| `user.phone` | String | `"+1 (555) 123-4567"` | Phone number |
| `user.country` | String | `"United States"` | Country |
| `user.nationality` | String | `"American"` | Nationality |
| `user.avatarUrl` | String\|null | `null` | Avatar image URL |
| `user.geniusLevel` | Number | `1` | Genius loyalty level (1-3) |
| `user.geniusBookings` | Number | `2` | Number of Genius-qualifying bookings |
| `user.geniusBookingsRequired` | Number | `5` | Bookings needed for next level |
| `user.currency` | String | `"USD"` | Preferred currency |
| `user.language` | String | `"English (US)"` | Preferred language |
| `user.savedProperties` | Array\<String\> | `["prop_2", "prop_5"]` | IDs of saved/wishlisted properties |

### Destination Object

| Key | Type | Description |
|-----|------|-------------|
| `id` | String | Destination ID (e.g., `"dest_1"`) |
| `name` | String | City/region name (e.g., `"New York"`) |
| `country` | String | Country name |
| `countryCode` | String | 2-letter country code |
| `type` | String | `"city"` or `"region"` |
| `propertyCount` | Number | Number of available properties |
| `trending` | Boolean | Whether destination is trending |
| `description` | String | Short description |

**Default destination IDs**: `dest_1` (New York), `dest_2` (Paris), `dest_3` (London), `dest_4` (Tokyo), `dest_5` (Barcelona), `dest_6` (Rome), `dest_7` (Dubai), `dest_8` (Amsterdam), `dest_9` (Bali), `dest_10` (Los Angeles)

### Property Object

| Key | Type | Description |
|-----|------|-------------|
| `id` | String | Property ID (e.g., `"prop_1"`) |
| `name` | String | Property name |
| `type` | String | One of: `"hotel"`, `"apartment"`, `"resort"`, `"villa"`, `"hostel"`, `"guesthouse"` |
| `stars` | Number | Star rating (0-5; 0 for non-hotel types) |
| `destinationId` | String | FK to destination |
| `city` | String | City name |
| `country` | String | Country name |
| `address` | String | Full address |
| `distanceFromCenter` | String | Distance description (e.g., `"0.5 km from center"`) |
| `coordinates` | Object | `{ lat: Number, lng: Number }` |
| `description` | String | Full property description |
| `shortDescription` | String | One-line summary |
| `reviewScore` | Number | Overall review score (0-10) |
| `reviewScoreWord` | String | Score label (e.g., `"Fabulous"`, `"Superb"`) |
| `reviewCount` | Number | Total number of reviews |
| `pricePerNight` | Number | Current price per night in USD |
| `originalPrice` | Number\|null | Original price before discount (null if no discount) |
| `currency` | String | `"USD"` |
| `taxesAndFees` | Number | Additional taxes per night |
| `genius` | Boolean | Whether Genius discount applies |
| `geniusDiscountPercent` | Number | Genius discount percentage (0, 10, or 15) |
| `freeCancellation` | Boolean | Whether free cancellation is available |
| `freeCancellationUntil` | String\|null | Date string for cancellation deadline |
| `prepayment` | String | `"no_prepayment"` or `"prepayment_required"` |
| `breakfastIncluded` | Boolean | Whether breakfast is included |
| `thumbnailUrl` | String | Thumbnail image URL |
| `photos` | Array\<Photo\> | Photo objects `{ id, url, caption, category }` |
| `facilities` | Array\<String\> | Facility codes (e.g., `"free_wifi"`, `"pool"`, `"spa"`) |
| `popularFacilities` | Array\<String\> | Human-readable popular facility names |
| `rooms` | Array\<String\> | Room IDs belonging to this property |
| `checkInTime` | String | Check-in time (e.g., `"15:00"`) |
| `checkOutTime` | String | Check-out time (e.g., `"11:00"`) |
| `petsAllowed` | Boolean | Whether pets are allowed |
| `smokingAllowed` | Boolean | Whether smoking is allowed |
| `sustainability` | Boolean | Whether property has sustainability certification |
| `sustainabilityLevel` | Number | Sustainability level (0-3) |
| `limitedTimeDeal` | Boolean | Whether a limited-time deal is active |
| `newToBooking` | Boolean | Whether property is new on the platform |

**Default property IDs**: `prop_1` through `prop_12`

### Room Object

| Key | Type | Description |
|-----|------|-------------|
| `id` | String | Room ID (e.g., `"room_1_1"`) |
| `propertyId` | String | FK to property |
| `name` | String | Room name (e.g., `"Deluxe King Room"`) |
| `type` | String | `"single"`, `"double"`, `"suite"`, `"studio"`, `"family"`, `"dormitory"` |
| `maxGuests` | Number | Maximum occupancy |
| `bedType` | String | Bed description (e.g., `"1 king bed"`) |
| `size` | String | Room size (e.g., `"30 m2"`) |
| `pricePerNight` | Number | Room price per night |
| `originalPrice` | Number\|null | Original price before discount |
| `amenities` | Array\<String\> | Room amenities list |
| `view` | String\|null | View description |
| `breakfastIncluded` | Boolean | Whether breakfast is included for this room |
| `breakfastPrice` | Number\|null | Breakfast add-on price |
| `freeCancellation` | Boolean | Whether free cancellation applies |
| `cancellationDeadline` | String\|null | Free cancellation deadline date |
| `prepayment` | String | `"no_prepayment"` or `"prepayment_required"` |
| `availableCount` | Number | Number of rooms available at this price |
| `smokingAllowed` | Boolean | Whether smoking is allowed |
| `imageUrl` | String | Room image URL |

### Review Object

| Key | Type | Description |
|-----|------|-------------|
| `id` | String | Review ID (e.g., `"review_1_1"`) |
| `propertyId` | String | FK to property |
| `authorName` | String | Reviewer name |
| `authorCountry` | String | Reviewer country |
| `authorCountryCode` | String | 2-letter country code |
| `date` | String | Review date (YYYY-MM-DD) |
| `score` | Number | Review score (0-10) |
| `title` | String | Review title |
| `positive` | String | Positive feedback text |
| `negative` | String | Negative feedback text (may be empty) |
| `roomType` | String | Name of room stayed in |
| `nightsStayed` | Number | Duration of stay |
| `travellerType` | String | `"couple"`, `"solo"`, `"family"`, `"business"` |

### reviewCategories Object

Keyed by property ID. Each value is:

| Key | Type | Description |
|-----|------|-------------|
| `staff` | Number | Staff rating (0-10) |
| `facilities` | Number | Facilities rating (0-10) |
| `cleanliness` | Number | Cleanliness rating (0-10) |
| `comfort` | Number | Comfort rating (0-10) |
| `valueForMoney` | Number | Value for money rating (0-10) |
| `location` | Number | Location rating (0-10) |
| `freeWifi` | Number | WiFi rating (0-10) |

### Booking Object

| Key | Type | Description |
|-----|------|-------------|
| `id` | String | Booking ID (e.g., `"booking_1"`) |
| `confirmationNumber` | String | 10-digit confirmation number |
| `pinCode` | String | 4-digit PIN code |
| `userId` | String | FK to user |
| `propertyId` | String | FK to property |
| `propertyName` | String | Property name (denormalized) |
| `propertyImage` | String | Property image URL |
| `propertyCity` | String | Property city |
| `propertyAddress` | String | Property address |
| `roomId` | String | FK to room |
| `roomName` | String | Room name (denormalized) |
| `checkIn` | String | Check-in date (YYYY-MM-DD) |
| `checkOut` | String | Check-out date (YYYY-MM-DD) |
| `nights` | Number | Number of nights |
| `guests` | Object | `{ adults: Number, children: Number }` |
| `rooms` | Number | Number of rooms booked |
| `pricePerNight` | Number | Price per night |
| `totalPrice` | Number | Subtotal (price x nights) |
| `taxesAndFees` | Number | Total taxes and fees |
| `grandTotal` | Number | Grand total (subtotal + taxes) |
| `status` | String | `"confirmed"`, `"completed"`, or `"cancelled"` |
| `guestFirstName` | String | Guest first name |
| `guestLastName` | String | Guest last name |
| `guestEmail` | String | Guest email |
| `guestPhone` | String | Guest phone |
| `specialRequests` | String | Special request text |
| `arrivalTime` | String | Expected arrival time window |
| `freeCancellation` | Boolean | Whether free cancellation applies |
| `cancellationDeadline` | String\|null | Cancellation deadline date |
| `createdAt` | String | ISO timestamp of booking creation |

**Default bookings**:
- `booking_1`: Grand Plaza Hotel & Spa, New York, Jun 15-20, 2026, confirmed
- `booking_2`: Shibuya Crossing Hotel, Tokyo, May 1-5, 2025, confirmed
- `booking_3`: Hotel Le Marais Charm, Paris, Oct 10-13, 2024, completed

### searchParams Object

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `destination` | String | `""` | Search destination text |
| `destinationId` | String\|null | `null` | Selected destination ID |
| `checkIn` | String\|null | `null` | Check-in date |
| `checkOut` | String\|null | `null` | Check-out date |
| `adults` | Number | `2` | Number of adults |
| `children` | Number | `0` | Number of children |
| `childrenAges` | Array | `[]` | Ages of children |
| `rooms` | Number | `1` | Number of rooms |
| `travelingForWork` | Boolean | `false` | Business travel flag |

### searchFilters Object

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `priceMin` | Number\|null | `null` | Minimum price filter |
| `priceMax` | Number\|null | `null` | Maximum price filter |
| `starRating` | Array\<Number\> | `[]` | Star rating filter (e.g., `[4, 5]`) |
| `reviewScore` | Number\|null | `null` | Minimum review score filter |
| `propertyType` | Array\<String\> | `[]` | Property type filter |
| `facilities` | Array\<String\> | `[]` | Facility filter |
| `freeCancellation` | Boolean | `false` | Free cancellation filter |
| `breakfastIncluded` | Boolean | `false` | Breakfast included filter |
| `geniusDeals` | Boolean | `false` | Genius deals only filter |
| `sortBy` | String | `"our_top_picks"` | Sort order: `"our_top_picks"`, `"price_low"`, `"price_high"`, `"review_score"`, `"stars_high"` |

### RecentSearch Object

| Key | Type | Description |
|-----|------|-------------|
| `destination` | String | Destination name |
| `destinationId` | String | Destination ID |
| `dates` | String | Date range display string |
| `guests` | String | Guest summary string |

**Default recent searches**: New York (dest_1), Tokyo (dest_4)

## Tracked State Diff Fields

The `/go` endpoint tracks changes in these fields specifically:
- `bookings`
- `user.savedProperties`
- `searchParams`
- `searchFilters`
- `viewedProperties`
- `recentlyViewed`
- `recentSearches`

## Minimal Inject Example

```json
{
  "user": {
    "firstName": "Alex",
    "lastName": "Chen",
    "email": "alex.chen@example.com",
    "savedProperties": []
  },
  "bookings": [],
  "searchParams": {
    "destination": "Paris",
    "destinationId": "dest_2",
    "adults": 2,
    "children": 1,
    "rooms": 1
  },
  "recentSearches": [],
  "recentlyViewed": [],
  "viewedProperties": []
}
```

## Inject Example: Pre-configured Search for Tokyo Hotels

```json
{
  "searchParams": {
    "destination": "Tokyo",
    "destinationId": "dest_4",
    "checkIn": "2026-05-01",
    "checkOut": "2026-05-05",
    "adults": 2,
    "children": 0,
    "rooms": 1
  },
  "searchFilters": {
    "starRating": [4, 5],
    "freeCancellation": true,
    "sortBy": "review_score"
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Search for a destination via search bar | `searchParams` (destination, destinationId, checkIn, checkOut, adults, children, rooms) |
| Search adds to recent searches | `recentSearches` (new entry prepended, max 5, deduped by destinationId) |
| Apply search filters (price, stars, type, etc.) | `searchFilters` (note: sidebar filters are local state, only `setSearchFilters` persists to store) |
| View a property detail page | `viewedProperties` (property ID appended), `recentlyViewed` (property ID prepended, max 10), `selectedPropertyId` |
| Save/unsave a property (click heart icon) | `user.savedProperties` (property ID toggled in/out of array) |
| Complete a booking via checkout form | `bookings` (new booking object appended with status `"confirmed"`) |
| Cancel a booking from trips or confirmation page | `bookings` (matching booking's `status` changed from `"confirmed"` to `"cancelled"`) |
| Reset search filters | `searchFilters` (all values reset to defaults) |
