# salesforce_mock Schema

**Deploy order**: 45 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8044)
**Base URL**: `http://172.17.46.46:8044/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Merge**: `POST /post?sid=<sid>` with body `{"action":"set","merge":true,"state":{...}}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Logged-in user (userId, firstName, lastName, email, phone, title, department, role, avatar, timezone, locale, theme) |
| `users` | User[] | All team members (same shape as `user`); default 5 users (user-1..user-5) |
| `leads` | Lead[] | Sales leads; default 8 records (lead-1..lead-8) |
| `accounts` | Account[] | Company accounts; default 5 records (account-1..account-5) |
| `contacts` | Contact[] | Contact persons linked to accounts; default 6 records (contact-1..contact-6) |
| `opportunities` | Opportunity[] | Sales opportunities; default 6 records (opp-1..opp-6) |
| `cases` | Case[] | Support cases; default 5 records (case-1..case-5) |
| `activities` | Activity[] | Tasks and events; default 8 records (activity-1..activity-8) |
| `chatterPosts` | ChatterPost[] | Feed posts with comments and likes; default 5 posts |
| `files` | FileItem[] | Uploaded files; default 5 records (file-1..file-5) |
| `following` | string[] | userIds current user follows; default `["user-2","user-3"]` |
| `recentlyViewed` | RecentItem[] | Recently viewed records `{type,id,name,path,timestamp}`; default `[]` |
| `dismissedNotifications` | string[] | IDs of dismissed notifications; default `[]` |

### Key Subfield Details

**Lead**: `leadId`, `status` (New/Working/Qualified/Unqualified), `rating` (Hot/Warm/Cold), `source`, `ownerId`, `company`, `industry`, `employees`, `revenue`

**Account**: `accountId`, `name`, `type` (Customer/Prospect/Partner), `industry`, `revenue`, `employees`, `ownerId`, billing/shipping address fields

**Contact**: `contactId`, `accountId`, `firstName`, `lastName`, `title`, `department`, `email`, `phone`, `ownerId`

**Opportunity**: `opportunityId`, `name`, `accountId`, `contactId`, `amount`, `closeDate`, `stage` (Prospecting/Qualification/Needs Analysis/Value Proposition/Proposal/Negotiation/Closed Won/Closed Lost), `probability`, `ownerId`

**Case**: `caseId`, `caseNumber`, `subject`, `status` (New/Working/Escalated/Closed), `priority` (Low/Medium/High/Critical), `origin`, `type`, `accountId`, `contactId`, `ownerId`, `closedDate`

**Activity**: `activityId`, `type` (task/event), `subject`, `status`, `priority`, `dueDate` (task) or `startDateTime`/`endDateTime` (event), `relatedToType`, `relatedToId`, `assignedToId`

**ChatterPost**: `postId`, `userId`, `content`, `likeCount`, `commentCount`, `likes` (userId[]), `comments` (array of `{commentId,userId,content,likeCount,likes}`)

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8044/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "userId": "user-1",
          "firstName": "John",
          "lastName": "Smith",
          "email": "john.smith@company.com",
          "phone": "(555) 123-4567",
          "title": "Sales Manager",
          "department": "Sales",
          "role": "Manager",
          "avatar": "https://i.pravatar.cc/150?u=user-1",
          "timezone": "America/New_York",
          "locale": "en-US",
          "theme": "lightning"
        },
        "leads": [
          {
            "leadId": "lead-1",
            "firstName": "Sarah",
            "lastName": "Johnson",
            "company": "TechVentures Inc.",
            "title": "VP of Engineering",
            "email": "sarah.j@techventures.com",
            "phone": "(555) 111-2222",
            "mobile": "",
            "status": "New",
            "source": "Website",
            "rating": "Hot",
            "street": "", "city": "", "state": "", "zip": "", "country": "USA",
            "industry": "Technology",
            "employees": 250,
            "revenue": 15000000,
            "website": "",
            "description": "",
            "ownerId": "user-1",
            "createdDate": "2026-03-01T00:00:00.000Z",
            "modifiedDate": "2026-03-01T00:00:00.000Z"
          }
        ],
        "accounts": [],
        "contacts": [],
        "opportunities": [],
        "cases": [],
        "activities": [],
        "chatterPosts": [],
        "files": [],
        "users": [],
        "following": [],
        "recentlyViewed": [],
        "dismissedNotifications": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Create new lead | `leads` array: `added` count increases by 1 |
| Edit lead status (e.g., New → Working) | `leads` array: `modified` count increases, target lead's `status` updated |
| Convert lead to account/contact | `leads` modified (status=Qualified), `accounts`/`contacts` arrays gain new record |
| Create new opportunity | `opportunities` array: `added` count increases |
| Update opportunity stage | `opportunities` array: `modified`, target `stage` and `probability` updated |
| Close opportunity (Won/Lost) | `opportunities` modified: `stage` = "Closed Won" or "Closed Lost" |
| Create new case | `cases` array: `added` count increases |
| Update case status | `cases` modified: target `status` updated |
| Close case | `cases` modified: `status` = "Closed", `closedDate` set |
| Create account | `accounts` array: `added` count increases |
| Create contact | `contacts` array: `added` count increases |
| Create task/event | `activities` array: `added` count increases |
| Complete task | `activities` modified: target `status` = "Completed" |
| Post to Chatter | `chatterPosts` array: `added` count increases |
| Like a post | `chatterPosts` modified: target post `likeCount`/`likes` updated |
| Comment on post | `chatterPosts` modified: `commentCount` incremented, `comments` array updated |
| Follow a user | `following` array: target userId added |
| View a record | `recentlyViewed` array: new `RecentItem` prepended |
| Dismiss notification | `dismissedNotifications` array: notification ID added |
