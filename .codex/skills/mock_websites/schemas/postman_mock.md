# postman_mock Schema

**Deploy order**: 37 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8037)
**Base URL**: `http://172.17.46.46:8037/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `workspace` | object | Active workspace metadata: `{id, name, type}` |
| `collections` | array | API collections; each contains folders and requests (see Collections below) |
| `environments` | array | Named variable sets; each: `{id, name, color, variables[], createdAt}` |
| `activeEnvironmentId` | string\|null | ID of the currently selected environment (e.g. `"env_1"`) or `null` for "No Environment" |
| `tabs` | array | Open request tabs; each: `{id, type, name, method, requestId, collectionId, isDirty, request, response}` |
| `activeTabId` | string | ID of the currently active tab |
| `currentRequest` | object | The request being edited in the active tab (see Request object below) |
| `activeRequestId` | string\|null | ID of the saved request loaded in the active tab, or `null` for unsaved |
| `response` | object\|null | Most recent response for the active tab (see Response object below) |
| `history` | array | Request execution history; each: `{id, timestamp, method, url, statusCode, responseTime}` |
| `globalVariables` | array | Global variables; each: `{id, key, value, description, enabled}` |
| `sidebarPanel` | string | Active sidebar panel: `"collections"` \| `"environments"` \| `"history"` \| `"apis"` \| `"mockservers"` \| `"monitors"` |
| `splitRatio` | number | Vertical split between request/response panels (20-80, default `50`) |

### Collection Object

```
{
  id: string,             // e.g. "col_1"
  name: string,           // e.g. "User Management API"
  description: string,
  auth: Auth,             // collection-level auth
  variables: array,       // collection variables
  folders: Folder[],      // grouped requests
  requests: Request[],    // top-level requests (outside folders)
  createdAt: string,      // ISO 8601
  updatedAt: string       // ISO 8601
}
```

### Folder Object

```
{
  id: string,             // e.g. "folder_1"
  name: string,           // e.g. "Users"
  description: string,
  auth: Auth,             // folder-level auth (usually {type:"inherit"})
  requests: Request[]     // requests in this folder
}
```

### Request Object

```
{
  id: string,             // e.g. "req_1"
  name: string,           // e.g. "Get All Users"
  description: string,
  method: string,         // "GET"|"POST"|"PUT"|"DELETE"|"PATCH"|"HEAD"|"OPTIONS"
  url: string,            // may contain {{variables}} e.g. "{{baseUrl}}/api/users"
  params: KeyValuePair[], // query parameters
  auth: Auth,             // request-level auth
  headers: KeyValuePair[],// request headers
  body: Body,             // request body
  preRequest: string,     // pre-request script (JavaScript)
  tests: string           // test script using pm.test() syntax
}
```

### KeyValuePair Object

```
{
  id: string,             // e.g. "p1", "h1"
  key: string,            // e.g. "Content-Type"
  value: string,          // e.g. "application/json"
  description: string,
  enabled: boolean
}
```

### Auth Object

```
{
  type: string,           // "none"|"inherit"|"bearer"|"basic"|"apikey"
  bearer?: { token: string },
  basic?: { username: string, password: string },
  apikey?: { key: string, value: string, addTo: "header"|"queryParams" }
}
```

### Body Object

```
{
  type: string,           // "none"|"json"|"text"|"raw"|"formdata"|"urlencoded"|"binary"|"graphql"
  content: string,        // raw/JSON/text body content
  formData: KeyValuePair[],
  urlencoded: KeyValuePair[],
  graphql: { query: string, variables: string }
}
```

### Tab Object

```
{
  id: string,             // UUID
  type: string,           // always "request"
  name: string,           // display name
  method: string,         // HTTP method
  requestId: string|null, // links to saved request ID, null if unsaved
  collectionId: string|null,
  isDirty: boolean,       // true if modified since save
  request: Request|null,  // working copy of the request
  response: Response|null // cached response for this tab
}
```

### Response Object (runtime, returned by mock execution)

```
{
  id: string,             // UUID
  statusCode: number,     // e.g. 200, 201, 404
  statusText: string,     // e.g. "OK", "Created", "Not Found"
  time: number,           // response time in ms
  size: number,           // response body size in bytes
  body: object|string|null, // parsed response body
  headers: object,        // response headers as key-value
  cookies: Cookie[],      // each: {name, value, domain, path, httpOnly, secure}
  testResults: TestResult[] // each: {name: string, passed: boolean}
}
```

### Environment Object

```
{
  id: string,             // e.g. "env_1"
  name: string,           // e.g. "Development"
  color: string,          // hex color e.g. "#00AA55"
  variables: KeyValuePair[], // environment variables
  createdAt: string       // ISO 8601
}
```

### History Item Object

```
{
  id: string,             // e.g. "hist_1" or UUID
  timestamp: number,      // Unix timestamp (ms)
  method: string,         // HTTP method
  url: string,            // resolved URL
  statusCode: number,
  responseTime: number    // ms
}
```

## Default IDs

### Collections
| ID | Name | Folders |
|----|------|---------|
| `col_1` | User Management API | `folder_1` (Users), `folder_2` (Authentication) |
| `col_2` | E-Commerce API | `folder_3` (Products), `folder_4` (Orders) |
| `col_3` | JSONPlaceholder | (no folders, top-level requests only) |

### Requests
| ID | Name | Method | Collection | Folder |
|----|------|--------|------------|--------|
| `req_1` | Get All Users | GET | col_1 | folder_1 |
| `req_2` | Get User by ID | GET | col_1 | folder_1 |
| `req_3` | Create User | POST | col_1 | folder_1 |
| `req_4` | Update User | PUT | col_1 | folder_1 |
| `req_5` | Delete User | DELETE | col_1 | folder_1 |
| `req_6` | Login | POST | col_1 | folder_2 |
| `req_7` | Get Profile | GET | col_1 | folder_2 |
| `req_8` | List Products | GET | col_2 | folder_3 |
| `req_9` | Get Product Details | GET | col_2 | folder_3 |
| `req_10` | Create Product | POST | col_2 | folder_3 |
| `req_11` | Create Order | POST | col_2 | folder_4 |
| `req_12` | Get Order Status | GET | col_2 | folder_4 |
| `req_13` | Health Check | GET | col_2 | (root) |
| `req_14` | Get Posts | GET | col_3 | (root) |
| `req_15` | Create Post | POST | col_3 | (root) |
| `req_16` | Update Post | PATCH | col_3 | (root) |

### Environments
| ID | Name | Color | Key Variables |
|----|------|-------|---------------|
| `env_1` | Development | `#00AA55` | baseUrl, authToken, apiKey, orderId |
| `env_2` | Staging | `#EAB308` | baseUrl, authToken, apiKey, orderId |
| `env_3` | Production | `#EF4444` | baseUrl, authToken (empty), apiKey (empty), orderId (disabled) |

### Default Active State
- `activeEnvironmentId`: `"env_1"`
- `activeTabId`: `"tab_1"` (Get All Users)
- `activeRequestId`: `"req_1"`
- `sidebarPanel`: `"collections"`
- `splitRatio`: `50`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8037/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "workspace": { "id": "ws_default", "name": "My Workspace", "type": "personal" },
        "collections": [
          {
            "id": "col_1",
            "name": "Test API",
            "description": "A test collection",
            "auth": { "type": "none" },
            "variables": [],
            "folders": [
              {
                "id": "folder_1",
                "name": "Users",
                "description": "",
                "auth": { "type": "inherit" },
                "requests": [
                  {
                    "id": "req_1",
                    "name": "Get Users",
                    "description": "",
                    "method": "GET",
                    "url": "{{baseUrl}}/api/users",
                    "params": [
                      { "id": "p1", "key": "page", "value": "1", "description": "", "enabled": true }
                    ],
                    "auth": { "type": "inherit" },
                    "headers": [],
                    "body": { "type": "none", "content": "", "formData": [], "urlencoded": [], "graphql": { "query": "", "variables": "" } },
                    "preRequest": "",
                    "tests": ""
                  }
                ]
              }
            ],
            "requests": []
          }
        ],
        "environments": [
          {
            "id": "env_1",
            "name": "Dev",
            "color": "#00AA55",
            "variables": [
              { "id": "v1", "key": "baseUrl", "value": "https://api.dev.example.com", "description": "Base URL", "enabled": true }
            ]
          }
        ],
        "activeEnvironmentId": "env_1",
        "tabs": [
          {
            "id": "tab_1",
            "type": "request",
            "name": "Get Users",
            "method": "GET",
            "requestId": "req_1",
            "collectionId": "col_1",
            "isDirty": false,
            "request": {
              "method": "GET",
              "url": "{{baseUrl}}/api/users",
              "params": [{ "id": "p1", "key": "page", "value": "1", "description": "", "enabled": true }],
              "auth": { "type": "inherit" },
              "headers": [],
              "body": { "type": "none", "content": "", "formData": [], "urlencoded": [], "graphql": { "query": "", "variables": "" } },
              "preRequest": "",
              "tests": ""
            },
            "response": null
          }
        ],
        "activeTabId": "tab_1",
        "currentRequest": {
          "method": "GET",
          "url": "{{baseUrl}}/api/users",
          "params": [{ "id": "p1", "key": "page", "value": "1", "description": "", "enabled": true }],
          "auth": { "type": "inherit" },
          "headers": [],
          "body": { "type": "none", "content": "", "formData": [], "urlencoded": [], "graphql": { "query": "", "variables": "" } },
          "preRequest": "",
          "tests": ""
        },
        "activeRequestId": "req_1",
        "response": null,
        "history": [],
        "globalVariables": [
          { "id": "gv1", "key": "appVersion", "value": "2.1.0", "description": "Application version", "enabled": true }
        ],
        "sidebarPanel": "collections",
        "splitRatio": 50
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Send request (click Send) | `response` populated with mock response; `history` grows by 1; active tab's `response` updated |
| Change HTTP method | `currentRequest.method` updated; active tab's `method` updated; tab marked dirty |
| Edit URL | `currentRequest.url` updated; active tab marked dirty |
| Add/edit query param | `currentRequest.params` array modified; active tab marked dirty |
| Toggle param enabled | `currentRequest.params[i].enabled` toggled |
| Add/edit header | `currentRequest.headers` array modified; active tab marked dirty |
| Toggle header enabled | `currentRequest.headers[i].enabled` toggled |
| Change body type | `currentRequest.body.type` updated |
| Edit body content | `currentRequest.body.content` updated; active tab marked dirty |
| Edit form-data | `currentRequest.body.formData` array modified |
| Edit URL-encoded | `currentRequest.body.urlencoded` array modified |
| Edit GraphQL query/vars | `currentRequest.body.graphql.query` or `.variables` updated |
| Change auth type | `currentRequest.auth.type` and related subfields updated |
| Edit auth fields | `currentRequest.auth.bearer.token`, `.basic.username`/`.password`, or `.apikey.*` updated |
| Edit pre-request script | `currentRequest.preRequest` updated |
| Edit test script | `currentRequest.tests` updated |
| Open request from sidebar | `tabs` may grow (new tab); `activeTabId`, `activeRequestId`, `currentRequest` updated |
| Open new tab | `tabs` grows by 1; `activeTabId` updated; `currentRequest` set to blank |
| Close tab | `tabs` shrinks; if active tab closed, `activeTabId` switches to adjacent tab |
| Switch tab | `activeTabId` updated; `activeRequestId`, `currentRequest`, `response` restored from tab |
| Save request to collection | `collections[i].requests` or `collections[i].folders[j].requests` grows by 1 |
| Create collection | `collections` array grows by 1 |
| Delete collection | `collections` array shrinks by 1 |
| Rename collection | `collections[i].name` updated |
| Create folder | `collections[i].folders` grows by 1 |
| Delete folder | `collections[i].folders` shrinks; all requests inside removed |
| Rename folder | `collections[i].folders[j].name` updated |
| Delete request | Request removed from its collection/folder's requests array |
| Rename request | Request's `name` updated in collection; matching tab `name` updated |
| Duplicate request | New request added to same collection/folder with `(Copy)` suffix |
| Switch environment | `activeEnvironmentId` updated |
| Create environment | `environments` array grows by 1 |
| Delete environment | `environments` shrinks; if was active, `activeEnvironmentId` set to `null` |
| Edit environment variable | `environments[i].variables[j]` fields updated |
| Add environment variable | `environments[i].variables` grows by 1 |
| Remove environment variable | `environments[i].variables` shrinks by 1 |
| Update global variables | `globalVariables` array replaced |
| Clear history | `history` set to `[]` |
| Switch sidebar panel | `sidebarPanel` updated |
| Drag resize split | `splitRatio` updated |

## Mock Network Behavior

The app does **not** make real HTTP requests. Instead, `executeRequest()` simulates responses based on URL patterns:

| URL Pattern | Method | Mock Response |
|-------------|--------|---------------|
| `/api/auth/login` | POST | JWT token + user object (status 200) |
| `/api/auth/profile` | GET | User profile object |
| `/api/users` | GET | Array of 10 mock users |
| `/api/users/:id` | GET | Single user object |
| `/api/users` | POST | Created user (status 201) |
| `/api/users/:id` | PUT/PATCH | Updated user |
| `/api/users/:id` | DELETE | No content (status 204) |
| `/api/products` | GET | Array of 5 products |
| `/api/products/:id` | GET | Single product detail |
| `/api/products` | POST | Created product (status 201) |
| `/api/orders` | POST | Created order with tracking (status 201) |
| `/api/orders/:id` | GET | Order status with items |
| `/api/health` | GET | Health check with service statuses |
| `jsonplaceholder.typicode.com/posts` | GET | Array of 5 posts |
| `jsonplaceholder.typicode.com/posts/:id` | GET | Single post |
| `jsonplaceholder.typicode.com/posts` | POST | Created post (status 201) |
| `jsonplaceholder.typicode.com/posts/:id` | PATCH/PUT | Updated post |
| URL contains `timeout` | any | Status 408 (Request Timeout) |
| URL contains `500` or `error` | any | Status 500 (Internal Server Error) |
| URL contains `404` or `notfound` | any | Status 404 (Not Found) |
| URL contains `401` or `unauthorized` | any | Status 401 (Unauthorized) |
| URL contains `403` | any | Status 403 (Forbidden) |
| (default/other) | any | Echo response with method, url, headers, body |

Test scripts using `pm.test()` are evaluated with basic assertions: status code checks, array type checks, and token existence checks.

## Notes

- Variable substitution: `{{varName}}` in URLs, headers, and body content are replaced using the active environment's variables and global variables.
- History is capped at 50 items (most recent first).
- When all tabs are closed, a blank "Untitled Request" tab is automatically created.
- The `response` field at the top level mirrors the active tab's response. Tab-switching restores each tab's cached response.
- The `currentRequest` field always reflects the working copy in the active tab. Editing it marks the tab as `isDirty: true`.
