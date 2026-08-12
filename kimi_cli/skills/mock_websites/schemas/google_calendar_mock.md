# google_calendar_mock Schema

**Deploy order**: 17 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8017)
**Base URL**: `http://172.17.46.46:8017/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**State endpoint**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Current user (see User object below) |
| `calendars` | array | Calendar sources with visibility toggles (see Calendar object below) |
| `events` | array | All calendar events (see Event object below) |
| `view` | string | Current calendar view: `"day"`, `"week"`, `"month"`, or `"agenda"` (default `"week"`) |
| `currentDate` | string | ISO 8601 datetime string for the date the calendar is centered on |
| `sidebarOpen` | boolean | Whether the left sidebar (mini calendar + calendar list) is visible (default `true`) |
| `settings` | object | User preferences (see Settings object below) |

### User Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique user ID (default `"u1"`) |
| `username` | string | Display name (default `"Demo User"`) |
| `email` | string | Email address (default `"demo@example.com"`) |
| `avatar` | string | URL to avatar image |

### Calendar Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique calendar ID (e.g. `"c1"`, `"c2"`) |
| `name` | string | Calendar display name (e.g. `"Personal"`, `"Work"`) |
| `color` | string | Hex color string (e.g. `"#039BE5"`) |
| `visible` | boolean | Whether events from this calendar are shown |
| `userId` | string | Owner user ID (default `"u1"`) |
| `isDefault` | boolean | Whether this is the default calendar for new events |

### Default Calendars

| ID | Name | Color | isDefault |
|----|------|-------|-----------|
| `c1` | Personal | `#039BE5` (Peacock blue) | `true` |
| `c2` | Work | `#33B679` (Sage green) | `false` |
| `c3` | Family | `#8E24AA` (Grape purple) | `false` |
| `c4` | Holidays | `#F4511E` (Tangerine) | `false` |
| `c5` | Birthdays | `#E67C73` (Flamingo pink) | `false` |

### Event Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique event ID (e.g. `"evt_001"`, or UUID for user-created) |
| `calendarId` | string | ID of parent calendar (`"c1"`–`"c5"`). Invalid IDs are normalized to `"c1"`. |
| `title` | string | Event title. Defaults to `"(No Title)"` if empty. |
| `start` | string | ISO 8601 datetime for event start |
| `end` | string | ISO 8601 datetime for event end |
| `allDay` | boolean | Whether this is an all-day event (default `false`) |
| `location` | string | Event location (default `""`) |
| `description` | string | Event description text (default `""`) |
| `guests` | array | Array of guest email strings, e.g. `["alice@example.com"]` |
| `color` | string | Hex color for event display (defaults to parent calendar color) |
| `recurring` | string | Recurrence rule: `"none"`, `"daily"`, `"weekly"`, `"monthly"`, or `"yearly"` (default `"none"`) |
| `reminders` | array | Array of Reminder objects (see below) |
| `meetLink` | string | Google Meet URL (default `""`) |
| `status` | string | Event status: `"confirmed"` (default) |

### Reminder Object

| Field | Type | Notes |
|-------|------|-------|
| `type` | string | `"popup"` or `"email"` |
| `minutes` | number | Minutes before event to trigger reminder (e.g. `5`, `10`, `30`, `60`, `1440`) |

### Settings Object

| Field | Type | Notes |
|-------|------|-------|
| `weekStart` | number | Day of week to start on: `0` = Sunday (default) |
| `defaultDuration` | number | Default event duration in minutes (default `60`) |
| `defaultView` | string | Default calendar view: `"week"` (default) |
| `defaultReminder` | object | Default reminder: `{type: "popup", minutes: 10}` |
| `timeFormat` | string | `"12h"` (default) or `"24h"` |
| `showWeekNumbers` | boolean | Show week numbers in calendar (default `false`) |
| `showDeclinedEvents` | boolean | Show declined events (default `false`) |

### Event Colors (available choices)

| ID | Name | Hex |
|----|------|-----|
| `tomato` | Tomato | `#D50000` |
| `flamingo` | Flamingo | `#E67C73` |
| `tangerine` | Tangerine | `#F4511E` |
| `banana` | Banana | `#F6BF26` |
| `sage` | Sage | `#33B679` |
| `basil` | Basil | `#0B8043` |
| `peacock` | Peacock | `#039BE5` |
| `blueberry` | Blueberry | `#3F51B5` |
| `lavender` | Lavender | `#7986CB` |
| `grape` | Grape | `#8E24AA` |
| `graphite` | Graphite | `#616161` |

### Mock Guest Users (available for guest suggestions)

| Email | Name |
|-------|------|
| `alice@example.com` | Alice Smith |
| `bob@example.com` | Bob Jones |
| `charlie@example.com` | Charlie Brown |
| `david@example.com` | David Lee |
| `eve@example.com` | Eve Wilson |
| `frank@example.com` | Frank Garcia |
| `grace@example.com` | Grace Chen |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8017/",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {"id": "u1", "username": "Demo User", "email": "demo@example.com", "avatar": "https://picsum.photos/100/100?random=user1"},
        "calendars": [
          {"id": "c1", "name": "Personal", "color": "#039BE5", "visible": true, "userId": "u1", "isDefault": true},
          {"id": "c2", "name": "Work", "color": "#33B679", "visible": true, "userId": "u1", "isDefault": false}
        ],
        "events": [
          {
            "id": "evt_001",
            "calendarId": "c2",
            "title": "Team Standup",
            "start": "2026-03-13T09:00:00.000Z",
            "end": "2026-03-13T09:30:00.000Z",
            "allDay": false,
            "location": "Zoom",
            "description": "Daily sync with the team",
            "guests": ["alice@example.com", "bob@example.com"],
            "color": "#33B679",
            "recurring": "daily",
            "reminders": [{"type": "popup", "minutes": 5}],
            "meetLink": "",
            "status": "confirmed"
          },
          {
            "id": "evt_002",
            "calendarId": "c1",
            "title": "Lunch with Sarah",
            "start": "2026-03-13T12:00:00.000Z",
            "end": "2026-03-13T13:00:00.000Z",
            "allDay": false,
            "location": "Downtown Cafe",
            "description": "Catch up over coffee",
            "guests": [],
            "color": "#039BE5",
            "recurring": "none",
            "reminders": [{"type": "popup", "minutes": 15}],
            "meetLink": "",
            "status": "confirmed"
          },
          {
            "id": "evt_003",
            "calendarId": "c4",
            "title": "National Holiday",
            "start": "2026-03-20T00:00:00.000Z",
            "end": "2026-03-21T00:00:00.000Z",
            "allDay": true,
            "location": "",
            "description": "Public holiday",
            "guests": [],
            "color": "#F4511E",
            "recurring": "none",
            "reminders": [],
            "meetLink": "",
            "status": "confirmed"
          }
        ],
        "view": "week",
        "currentDate": "2026-03-13T00:00:00.000Z",
        "sidebarOpen": true,
        "settings": {
          "weekStart": 0,
          "defaultDuration": 60,
          "defaultView": "week",
          "defaultReminder": {"type": "popup", "minutes": 10},
          "timeFormat": "12h",
          "showWeekNumbers": false,
          "showDeclinedEvents": false
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Create a new event | New event object appended to `events` array |
| Edit an event | `events[i]` fields updated (title, start, end, location, description, guests, color, recurring, etc.) |
| Delete an event | Event removed from `events` array (by `id`) |
| Move/drag an event | `events[i].start` and `events[i].end` both updated (duration preserved) |
| Quick-create an event | New event appended to `events` with `id` prefixed `"evt_qc_"` |
| Change calendar view | `view` changed: `"day"`, `"week"`, `"month"`, or `"agenda"` |
| Navigate to a date | `currentDate` updated to new ISO datetime |
| Toggle sidebar | `sidebarOpen` toggled between `true` and `false` |
| Toggle calendar visibility | `calendars[i].visible` toggled (hides/shows events from that calendar) |
| Add a new calendar | New calendar object appended to `calendars` array |
| Delete a calendar | Calendar removed from `calendars` array (by `id`) |
| Update settings | `settings` sub-keys modified (weekStart, defaultDuration, timeFormat, etc.) |
| Add/remove guests | `events[i].guests` array modified |
| Change event color | `events[i].color` updated to new hex value |
| Change recurrence | `events[i].recurring` changed (e.g. `"none"` to `"weekly"`) |

### state_diff Structure

The `/go` endpoint returns a flat key-path diff between initial and current state:

```json
{
  "events": {
    "old": [/* initial events array */],
    "new": [/* current events array */]
  },
  "view": {
    "old": "week",
    "new": "month"
  },
  "sidebarOpen": {
    "old": true,
    "new": false
  },
  "calendars.2.visible": {
    "old": true,
    "new": false
  }
}
```

### Notes on Event Normalization

When injecting events via the state API, the following normalization is applied:
- `calendarId` is validated against `["c1", "c2", "c3", "c4", "c5"]`; invalid IDs default to `"c1"`
- Missing `id` fields are auto-generated via UUID
- `start` also accepts `startTime` as an alias
- `end` also accepts `endTime` as an alias
- Missing `title` defaults to `"(No Title)"`
- `guests` must be an array; non-array values default to `[]`
- `reminders` must be an array; non-array values default to `[]`
- `color` defaults to the parent calendar's color if omitted
- `recurring` defaults to `"none"`
- `status` defaults to `"confirmed"`

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `c` | Open create event modal |
| `d` | Switch to Day view |
| `w` | Switch to Week view |
| `m` | Switch to Month view |
| `a` | Switch to Agenda/Schedule view |
| `t` | Jump to today |
| `Escape` | Close modal / popover / search |
