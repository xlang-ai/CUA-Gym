# Expensify_mock Schema

**Deploy order**: 13 (BASE_PORT=8000 → port 8013)
**Base URL**: `http://172.17.46.46:8013/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → current_state JSON (or null)

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | redirect → `/inbox` | Default redirect |
| `/inbox` | Inbox | Inbox notifications, tasks, concierge welcome |
| `/expenses` | Expenses | Expense list with filters, sorting, bulk actions |
| `/expenses/:id` | Expenses | Expense list (detail opened via modal) |
| `/reports` | Reports | Report list with filters, sorting, bulk actions |
| `/reports/:id` | ReportDetail | Single report detail with expenses, comments, approval actions |
| `/settings` | redirect → `/settings/workspace/pol_001/basics` | Settings redirect |
| `/settings/workspace/:policyId/:tab` | Settings | Workspace settings (tabs: basics, connections, categories, tags, people, distance, reportfields, tax, exportformats) |
| `/go` | Go | State inspection endpoint |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | The logged-in user |
| `users` | array | All users in the organization |
| `policies` | array | Expense policies / workspaces |
| `categories` | array | Expense categories scoped to a policy |
| `tags` | array | Tags scoped to a policy |
| `expenses` | array | All expense records (types: expense, distance, time) |
| `reports` | array | Expense reports grouping expenses |
| `comments` | array | Comments and status-change history on reports |
| `inboxItems` | array | Inbox notifications, tasks, concierge messages |
| `members` | array | Policy/workspace members with roles |
| `reportFields` | array | Custom report fields per policy |
| `distanceRates` | array | Mileage/distance reimbursement rates per policy |
| `taxRates` | array | Tax rate configurations per policy |
| `ui` | object | UI state: active view, filters, sort, selections, modals |

### `currentUser` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"usr_001"` | User ID |
| `email` | string | `"sarah.chen@acmecorp.com"` | Email |
| `firstName` | string | `"Sarah"` | First name |
| `lastName` | string | `"Chen"` | Last name |
| `displayName` | string | `"Sarah Chen"` | Display name |
| `avatar` | string\|null | `null` | Avatar URL |
| `role` | string | `"admin"` | Role: `"admin"` or `"employee"` |
| `managerId` | string\|null | `null` | Manager user ID |
| `employeeId` | string | `"EMP-2847"` | Employee ID |
| `department` | string | `"Engineering"` | Department |
| `defaultPolicy` | string | `"pol_001"` | Default policy ID |
| `reimbursementMethod` | string | `"ach"` | `"ach"` or `"check"` |
| `createdAt` | string | ISO timestamp | Account creation date |

### `users[]` Array Items

Same shape as `currentUser`. Default IDs: `usr_001` through `usr_006`.

| ID | Name | Role | Department |
|----|------|------|------------|
| `usr_001` | Sarah Chen | admin | Engineering |
| `usr_002` | James Wilson | employee | Sales |
| `usr_003` | Emily Rodriguez | employee | Marketing |
| `usr_004` | Michael Park | employee | Engineering |
| `usr_005` | Lisa Thompson | employee | Finance |
| `usr_006` | David Kim | employee | Sales |

### `policies[]` Array Items

| Field | Type | Default (pol_001) | Description |
|-------|------|-------------------|-------------|
| `id` | string | `"pol_001"` | Policy ID |
| `name` | string | `"Acme Corp Expenses"` | Policy name |
| `type` | string | `"corporate"` | `"corporate"` or `"personal"` |
| `outputCurrency` | string | `"USD"` | Currency code |
| `owner` | string | `"usr_001"` | Owner user ID |
| `autoReporting` | boolean | `true` | Auto-reporting enabled |
| `autoReportingFrequency` | string | `"weekly"` | `"daily"`, `"weekly"`, `"monthly"`, `"trip"`, `"manual"` |
| `autoReportingOffset` | number | `1` | Day offset for auto-reporting |
| `requiresCategory` | boolean | `true` | Category required on expenses |
| `requiresTag` | boolean | `false` | Tag required on expenses |
| `requiresComment` | boolean | `false` | Comment required on expenses |
| `maxExpenseAge` | number | `90` | Max expense age in days (0 = unlimited) |
| `maxExpenseAmount` | number | `5000` | Max single expense amount in dollars (0 = unlimited) |
| `preventSelfApproval` | boolean | `true` | Prevent self-approval |
| `approvalMode` | string | `"basic"` | `"basic"` or `"advanced"` |
| `reimbursementChoice` | string | `"reimburseManual"` | `"reimburseManual"`, `"reimburseACH"`, `"noReimbursement"` |
| `createdAt` | string | ISO timestamp | Creation date |

Default policy IDs: `pol_001` (Acme Corp Expenses, corporate), `pol_002` (Sarah's Personal Expenses, personal).

### `categories[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"cat_001"` | Category ID |
| `policyId` | string | `"pol_001"` | Parent policy ID |
| `name` | string | `"Travel: Airfare"` | Display name |
| `enabled` | boolean | `true` | Whether category is active |
| `glCode` | string | `"6010"` | General ledger code |
| `payrollCode` | string | `""` | Payroll integration code |
| `maxExpenseAmount` | number | `3000` | Per-category max (0 = no limit) |
| `requiresComment` | boolean | `false` | Comment required for this category |
| `commentHint` | string | `""` | Placeholder hint for comment |
| `externalId` | string | `""` | External system ID |

Default category IDs: `cat_001` through `cat_015`.

| ID | Name | GL Code |
|----|------|---------|
| `cat_001` | Travel: Airfare | 6010 |
| `cat_002` | Travel: Hotel | 6020 |
| `cat_003` | Travel: Car Rental | 6030 |
| `cat_004` | Travel: Ground Transport | 6040 |
| `cat_005` | Meals & Entertainment | 6100 |
| `cat_006` | Office Supplies | 6200 |
| `cat_007` | Software & Subscriptions | 6300 |
| `cat_008` | Professional Services | 6400 |
| `cat_009` | Communication | 6500 |
| `cat_010` | Mileage | 6600 |
| `cat_011` | Equipment | 6700 |
| `cat_012` | Training & Education | 6800 |
| `cat_013` | Utilities | 6900 |
| `cat_014` | Dues & Subscriptions | 7000 |
| `cat_015` | Miscellaneous | 9999 |

### `tags[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"tag_001"` | Tag ID |
| `policyId` | string | `"pol_001"` | Parent policy ID |
| `name` | string | `"Project Alpha"` | Display name |
| `enabled` | boolean | `true` | Whether tag is active |
| `glCode` | string | `"PA-001"` | General ledger code |
| `required` | boolean | `false` | Whether tag is required |

Default tag IDs: `tag_001` through `tag_006`.

| ID | Name | GL Code |
|----|------|---------|
| `tag_001` | Project Alpha | PA-001 |
| `tag_002` | Project Beta | PB-002 |
| `tag_003` | Client: Globex | CG-003 |
| `tag_004` | Client: Initech | CI-004 |
| `tag_005` | Internal | INT-005 |
| `tag_006` | Conference | CONF-006 |

### `expenses[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"exp_001"` | Expense ID |
| `type` | string | `"expense"` | `"expense"`, `"distance"`, or `"time"` |
| `policyId` | string | `"pol_001"` | Policy ID |
| `reportId` | string\|null | `"rpt_001"` | Linked report ID (null = unreported) |
| `createdBy` | string | `"usr_002"` | Creator user ID |
| `merchant` | string | `"United Airlines"` | Merchant/vendor name |
| `amount` | number | `45600` | Amount in **cents** (e.g., 45600 = $456.00) |
| `currency` | string | `"USD"` | Currency code |
| `date` | string | `"2024-11-15"` | Expense date (YYYY-MM-DD) |
| `categoryId` | string | `"cat_001"` | Category ID |
| `category` | string | `"Travel: Airfare"` | Category display name (denormalized) |
| `tagId` | string\|null | `"tag_001"` | Tag ID (null = no tag) |
| `tag` | string | `"Project Alpha"` | Tag display name (denormalized) |
| `description` | string | `"Flight SFO to NYC"` | Description |
| `comment` | string | `""` | User comment |
| `receiptUrl` | string\|null | `null` | Receipt file URL |
| `hasReceipt` | boolean | `true` | Whether receipt is attached |
| `billable` | boolean | `true` | Billable to client |
| `reimbursable` | boolean | `true` | Eligible for reimbursement |
| `taxAmount` | number | `0` | Tax amount in cents |
| `taxRate` | string | `""` | Tax rate name |
| `distance` | number\|null | `14.6` | Distance (for type=distance) |
| `distanceUnit` | string\|null | `"mi"` | `"mi"` or `"km"` |
| `distanceRate` | number\|null | `67` | Rate in cents per unit |
| `hours` | number\|null | `8` | Hours (for type=time) |
| `hourlyRate` | number\|null | `12000` | Hourly rate in cents |
| `status` | string | `"open"` | `"unreported"`, `"open"`, `"processing"`, `"approved"`, `"reimbursed"`, `"closed"`, `"deleted"` |
| `violations` | array | `[]` | Policy violation strings |
| `createdAt` | string | ISO timestamp | Creation timestamp |
| `modifiedAt` | string | ISO timestamp | Last modification timestamp |

Default expense IDs: `exp_001` through `exp_015`.

| ID | Merchant | Amount (cents) | Type | Status | Report |
|----|----------|---------------|------|--------|--------|
| `exp_001` | United Airlines | 45600 | expense | open | rpt_001 |
| `exp_002` | Hilton Hotels | 28950 | expense | open | rpt_001 |
| `exp_003` | Yellow Cab | 4200 | expense | open | rpt_001 |
| `exp_004` | Olive Garden | 6785 | expense | open | rpt_001 |
| `exp_005` | Uber | 2850 | expense | approved | rpt_002 |
| `exp_006` | Marriott Downtown | 19500 | expense | approved | rpt_002 |
| `exp_007` | Delta Airlines | 52300 | expense | approved | rpt_002 |
| `exp_008` | Staples | 12430 | expense | reimbursed | rpt_003 |
| `exp_009` | Adobe Creative Cloud | 5499 | expense | reimbursed | rpt_003 |
| `exp_010` | 14.6 mi mileage | 978 | distance | closed | rpt_004 |
| `exp_011` | AWS Monthly | 34218 | expense | open | rpt_005 |
| `exp_012` | Starbucks | 1245 | expense | unreported | null |
| `exp_013` | Office Depot | 8999 | expense | unreported | null |
| `exp_014` | Lyft | 1975 | expense | unreported | null |
| `exp_015` | 8 hours consulting | 96000 | time | open | rpt_005 |

### `reports[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"rpt_001"` | Report ID |
| `title` | string | `"NYC Client Visit - November 2024"` | Report title |
| `reportNumber` | number | `77324820` | Numeric report number |
| `policyId` | string | `"pol_001"` | Policy ID |
| `policyName` | string | `"Acme Corp Expenses"` | Policy name (denormalized) |
| `createdBy` | string | `"usr_002"` | Creator user ID |
| `createdByName` | string | `"James Wilson"` | Creator name (denormalized) |
| `createdByEmail` | string | `"james.wilson@acmecorp.com"` | Creator email (denormalized) |
| `status` | string | `"open"` | `"open"`, `"submitted"`, `"approved"`, `"reimbursed"`, `"closed"`, `"archived"` |
| `total` | number | `85535` | Total amount in **cents** |
| `currency` | string | `"USD"` | Currency code |
| `submittedTo` | string | `"usr_001"` | Approver user ID |
| `submittedToEmail` | string | `"sarah.chen@acmecorp.com"` | Approver email |
| `submittedDate` | string\|null | `null` | Submission timestamp |
| `approvedDate` | string\|null | `null` | Approval timestamp |
| `reimbursedDate` | string\|null | `null` | Reimbursement timestamp |
| `startDate` | string | `"2024-11-15"` | Earliest expense date |
| `endDate` | string | `"2024-11-16"` | Latest expense date |
| `expenseCount` | number | `4` | Number of expenses |
| `starred` | boolean | `true` | Whether report is starred |
| `exported` | boolean | `false` | Whether report has been exported |
| `exportedDate` | string\|null | `null` | Export timestamp |
| `isRetracted` | boolean | `false` | Whether report was rejected/retracted |
| `createdAt` | string | ISO timestamp | Creation timestamp |
| `modifiedAt` | string | ISO timestamp | Last modification timestamp |

Default report IDs: `rpt_001` through `rpt_005`.

| ID | Title | Status | Total (cents) | Creator |
|----|-------|--------|---------------|---------|
| `rpt_001` | NYC Client Visit - November 2024 | open | 85535 | usr_002 |
| `rpt_002` | Marketing Conference - Chicago | approved | 74650 | usr_003 |
| `rpt_003` | Office Supplies Q4 | reimbursed | 17929 | usr_004 |
| `rpt_004` | Mileage Expenses - October | closed | 978 | usr_006 |
| `rpt_005` | Engineering Tools - December | open | 130218 | usr_004 |

### `comments[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"cmt_001"` | Comment ID |
| `reportId` | string | `"rpt_001"` | Parent report ID |
| `authorId` | string | `"usr_002"` | Author user ID (or `"system"`) |
| `authorName` | string | `"James Wilson"` | Author display name |
| `authorEmail` | string | `"james.wilson@acmecorp.com"` | Author email |
| `type` | string | `"comment"` | `"comment"`, `"system"`, or `"status_change"` |
| `text` | string | `"Please review"` | Comment text |
| `timestamp` | string | ISO timestamp | Creation timestamp |

Default comment IDs: `cmt_001` through `cmt_008`.

### `inboxItems[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"inb_001"` | Inbox item ID |
| `type` | string | `"report_submitted"` | `"report_submitted"`, `"report_approved"`, `"expense_violation"`, `"concierge"`, `"task"` |
| `title` | string | `"Expense Report Submitted"` | Display title |
| `description` | string | `"James Wilson submitted..."` | Description text |
| `relatedId` | string\|null | `"rpt_001"` | Related report/expense ID |
| `fromUserId` | string | `"usr_002"` | Sender user ID (or `"concierge"`) |
| `fromUserName` | string | `"James Wilson"` | Sender name |
| `read` | boolean | `false` | Whether item has been read |
| `hidden` | boolean | `false` | Whether item is hidden |
| `actionRequired` | boolean | `true` | Whether user action is needed |
| `actionType` | string\|null | `"approve_report"` | `"approve_report"`, `"review_violation"`, `"setup_task"`, or `null` |
| `createdAt` | string | ISO timestamp | Creation timestamp |

Default inbox item IDs: `inb_001` through `inb_006`.

### `members[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"mem_001"` | Member record ID |
| `userId` | string | `"usr_001"` | User ID |
| `policyId` | string | `"pol_001"` | Policy ID |
| `email` | string | `"sarah.chen@acmecorp.com"` | Email |
| `name` | string | `"Sarah Chen"` | Display name |
| `role` | string | `"admin"` | `"admin"`, `"member"`, or `"auditor"` |
| `managerId` | string\|null | `null` | Manager user ID |
| `managerEmail` | string\|null | `null` | Manager email |
| `employeeId` | string | `"EMP-2847"` | Employee ID |
| `submitsTo` | string\|null | `null` | User ID this member submits reports to |
| `approvesTo` | string\|null | `null` | User ID this member's approvals escalate to |
| `isApprover` | boolean | `true` | Whether member can approve reports |
| `addedAt` | string | ISO timestamp | When member was added |

Default member IDs: `mem_001` through `mem_006`.

### `reportFields[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"rf_001"` | Report field ID |
| `policyId` | string | `"pol_001"` | Policy ID |
| `name` | string | `"Department"` | Field label |
| `type` | string | `"dropdown"` | `"text"`, `"dropdown"`, or `"date"` |
| `values` | array | `["Engineering","Sales",...]` | Dropdown options (empty for text/date) |
| `required` | boolean | `true` | Whether field is required |
| `defaultValue` | string | `""` | Default value |

Default report field IDs: `rf_001` (Department, dropdown), `rf_002` (Project Code, text), `rf_003` (Trip End Date, date).

### `distanceRates[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"dr_001"` | Rate ID |
| `policyId` | string | `"pol_001"` | Policy ID |
| `unit` | string | `"mi"` | `"mi"` or `"km"` |
| `rate` | number | `67` | Rate in cents per unit |
| `currency` | string | `"USD"` | Currency code |
| `enabled` | boolean | `true` | Whether rate is active |

Default: `dr_001` (67 cents/mi).

### `taxRates[]` Array Items

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"tax_001"` | Tax rate ID |
| `policyId` | string | `"pol_001"` | Policy ID |
| `name` | string | `"No Tax"` | Display name |
| `rate` | number | `0` | Percentage rate |
| `isDefault` | boolean | `true` | Whether this is the default tax rate |
| `enabled` | boolean | `true` | Whether rate is active |

Default tax rate IDs: `tax_001` (No Tax, 0%), `tax_002` (Sales Tax, 8.25%), `tax_003` (VAT, 20%).

### `ui` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `activeView` | string | `"inbox"` | Current active view |
| `expenseViewMode` | string | `"list"` | `"list"`, `"compact"`, `"grid"`, `"receipt"` |
| `expenseFiltersVisible` | boolean | `false` | Whether expense filter panel is open |
| `reportFiltersVisible` | boolean | `false` | Whether report filter panel is open |
| `selectedExpenseIds` | array | `[]` | Array of selected expense IDs |
| `selectedReportIds` | array | `[]` | Array of selected report IDs |
| `activeSettingsTab` | string | `"basics"` | Active settings sub-tab |
| `modalOpen` | string\|null | `null` | Currently open modal name |
| `modalData` | any\|null | `null` | Data for the open modal |
| `expenseFilters` | object | see below | Expense filter state |
| `reportFilters` | object | see below | Report filter state |
| `expenseSortBy` | string | `"date"` | `"date"`, `"merchant"`, `"amount"`, `"category"`, `"policy"` |
| `expenseSortDir` | string | `"desc"` | `"asc"` or `"desc"` |
| `reportSortBy` | string | `"name"` | `"name"`, `"total"`, `"policy"`, `"from"`, `"submitted"` |
| `reportSortDir` | string | `"desc"` | `"asc"` or `"desc"` |

#### `ui.expenseFilters` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `merchant` | string | `""` | Merchant name text filter |
| `dateFrom` | string | `""` | Start date (YYYY-MM-DD) |
| `dateTo` | string | `""` | End date (YYYY-MM-DD) |
| `categories` | array | `[]` | Selected category IDs |
| `tags` | array | `[]` | Selected tag IDs |
| `policies` | array | `[]` | Selected policy IDs |
| `statuses` | array | `[]` | Selected status strings |
| `billableFilter` | string | `"all"` | `"all"`, `"billable"`, `"reimbursable"` |

#### `ui.reportFilters` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dateFrom` | string | `""` | Start date (YYYY-MM-DD) |
| `dateTo` | string | `""` | End date (YYYY-MM-DD) |
| `policies` | array | `[]` | Selected policy IDs |
| `statuses` | array | `[]` | Selected status strings |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8013/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "usr_001", "email": "sarah.chen@acmecorp.com",
          "firstName": "Sarah", "lastName": "Chen", "displayName": "Sarah Chen",
          "avatar": null, "role": "admin", "managerId": null,
          "employeeId": "EMP-2847", "department": "Engineering",
          "defaultPolicy": "pol_001", "reimbursementMethod": "ach",
          "createdAt": "2023-01-15T09:00:00Z"
        },
        "users": [
          {"id": "usr_001", "email": "sarah.chen@acmecorp.com", "firstName": "Sarah", "lastName": "Chen", "displayName": "Sarah Chen", "avatar": null, "role": "admin", "managerId": null, "employeeId": "EMP-2847", "department": "Engineering", "defaultPolicy": "pol_001", "reimbursementMethod": "ach", "createdAt": "2023-01-15T09:00:00Z"},
          {"id": "usr_002", "email": "james.wilson@acmecorp.com", "firstName": "James", "lastName": "Wilson", "displayName": "James Wilson", "avatar": null, "role": "employee", "managerId": "usr_001", "employeeId": "EMP-3912", "department": "Sales", "defaultPolicy": "pol_001", "reimbursementMethod": "ach", "createdAt": "2023-02-01T09:00:00Z"}
        ],
        "policies": [
          {"id": "pol_001", "name": "Acme Corp Expenses", "type": "corporate", "outputCurrency": "USD", "owner": "usr_001", "autoReporting": true, "autoReportingFrequency": "weekly", "autoReportingOffset": 1, "requiresCategory": true, "requiresTag": false, "requiresComment": false, "maxExpenseAge": 90, "maxExpenseAmount": 5000, "preventSelfApproval": true, "approvalMode": "basic", "reimbursementChoice": "reimburseManual", "createdAt": "2023-01-10T09:00:00Z"}
        ],
        "categories": [
          {"id": "cat_001", "policyId": "pol_001", "name": "Travel: Airfare", "enabled": true, "glCode": "6010", "payrollCode": "", "maxExpenseAmount": 3000, "requiresComment": false, "commentHint": "", "externalId": ""},
          {"id": "cat_005", "policyId": "pol_001", "name": "Meals & Entertainment", "enabled": true, "glCode": "6100", "payrollCode": "", "maxExpenseAmount": 200, "requiresComment": false, "commentHint": "", "externalId": ""}
        ],
        "tags": [
          {"id": "tag_001", "policyId": "pol_001", "name": "Project Alpha", "enabled": true, "glCode": "PA-001", "required": false}
        ],
        "expenses": [
          {"id": "exp_001", "type": "expense", "policyId": "pol_001", "reportId": "rpt_001", "createdBy": "usr_002", "merchant": "United Airlines", "amount": 45600, "currency": "USD", "date": "2024-11-15", "categoryId": "cat_001", "category": "Travel: Airfare", "tagId": "tag_001", "tag": "Project Alpha", "description": "Flight SFO to NYC", "comment": "", "receiptUrl": null, "hasReceipt": true, "billable": true, "reimbursable": true, "taxAmount": 0, "taxRate": "", "distance": null, "distanceUnit": null, "distanceRate": null, "hours": null, "hourlyRate": null, "status": "open", "violations": [], "createdAt": "2024-11-15T14:30:00Z", "modifiedAt": "2024-11-15T14:30:00Z"}
        ],
        "reports": [
          {"id": "rpt_001", "title": "NYC Client Visit", "reportNumber": 77324820, "policyId": "pol_001", "policyName": "Acme Corp Expenses", "createdBy": "usr_002", "createdByName": "James Wilson", "createdByEmail": "james.wilson@acmecorp.com", "status": "open", "total": 45600, "currency": "USD", "submittedTo": "usr_001", "submittedToEmail": "sarah.chen@acmecorp.com", "submittedDate": null, "approvedDate": null, "reimbursedDate": null, "startDate": "2024-11-15", "endDate": "2024-11-15", "expenseCount": 1, "starred": false, "exported": false, "exportedDate": null, "isRetracted": false, "createdAt": "2024-11-16T10:00:00Z", "modifiedAt": "2024-11-16T10:00:00Z"}
        ],
        "comments": [
          {"id": "cmt_001", "reportId": "rpt_001", "authorId": "usr_002", "authorName": "James Wilson", "authorEmail": "james.wilson@acmecorp.com", "type": "system", "text": "You created this report", "timestamp": "2024-11-16T10:00:00Z"}
        ],
        "inboxItems": [
          {"id": "inb_001", "type": "report_submitted", "title": "Report Submitted", "description": "James Wilson submitted 'NYC Client Visit' for approval", "relatedId": "rpt_001", "fromUserId": "usr_002", "fromUserName": "James Wilson", "read": false, "hidden": false, "actionRequired": true, "actionType": "approve_report", "createdAt": "2024-11-16T10:05:00Z"}
        ],
        "members": [
          {"id": "mem_001", "userId": "usr_001", "policyId": "pol_001", "email": "sarah.chen@acmecorp.com", "name": "Sarah Chen", "role": "admin", "managerId": null, "managerEmail": null, "employeeId": "EMP-2847", "submitsTo": null, "approvesTo": null, "isApprover": true, "addedAt": "2023-01-15T09:00:00Z"},
          {"id": "mem_002", "userId": "usr_002", "policyId": "pol_001", "email": "james.wilson@acmecorp.com", "name": "James Wilson", "role": "member", "managerId": "usr_001", "managerEmail": "sarah.chen@acmecorp.com", "employeeId": "EMP-3912", "submitsTo": "usr_001", "approvesTo": null, "isApprover": false, "addedAt": "2023-02-01T09:00:00Z"}
        ],
        "reportFields": [
          {"id": "rf_001", "policyId": "pol_001", "name": "Department", "type": "dropdown", "values": ["Engineering", "Sales", "Marketing", "Finance"], "required": true, "defaultValue": ""}
        ],
        "distanceRates": [
          {"id": "dr_001", "policyId": "pol_001", "unit": "mi", "rate": 67, "currency": "USD", "enabled": true}
        ],
        "taxRates": [
          {"id": "tax_001", "policyId": "pol_001", "name": "No Tax", "rate": 0, "isDefault": true, "enabled": true},
          {"id": "tax_002", "policyId": "pol_001", "name": "Sales Tax", "rate": 8.25, "isDefault": false, "enabled": true}
        ],
        "ui": {
          "activeView": "inbox",
          "expenseViewMode": "list",
          "expenseFiltersVisible": false,
          "reportFiltersVisible": false,
          "selectedExpenseIds": [],
          "selectedReportIds": [],
          "activeSettingsTab": "basics",
          "modalOpen": null,
          "modalData": null,
          "expenseFilters": {"merchant": "", "dateFrom": "", "dateTo": "", "categories": [], "tags": [], "policies": [], "statuses": [], "billableFilter": "all"},
          "reportFilters": {"dateFrom": "", "dateTo": "", "policies": [], "statuses": []},
          "expenseSortBy": "date",
          "expenseSortDir": "desc",
          "reportSortBy": "name",
          "reportSortDir": "desc"
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Create new expense (any type) | `expenses` array grows by 1; new expense has `status: "unreported"`, `reportId: null` |
| Edit expense (merchant, amount, category, tag, etc.) | `expenses[i]` fields updated; `modifiedAt` updated |
| Delete expense | `expenses` array shrinks by 1 |
| Create new report | `reports` array grows by 1; `comments` grows (system message); selected expenses get `reportId` set and `status: "open"` |
| Submit report | `reports[i].status` → `"submitted"`; `submittedDate` set; `comments` grows (status_change) |
| Approve report | `reports[i].status` → `"approved"`; `approvedDate` set; linked `expenses[].status` → `"approved"`; `comments` grows |
| Reject report | `reports[i].status` → `"open"`; `isRetracted` → `true`; `comments` grows |
| Delete report | `reports` array shrinks by 1 |
| Star/unstar report | `reports[i].starred` toggled |
| Add comment to report | `comments` array grows by 1 |
| Mark inbox item as read | `inboxItems[i].read` → `true` |
| Hide inbox item | `inboxItems[i].hidden` → `true` |
| Dismiss concierge welcome | `inboxItems[i].hidden` → `true` (concierge type item) |
| Select/deselect expense checkbox | `ui.selectedExpenseIds` array modified |
| Select/deselect report checkbox | `ui.selectedReportIds` array modified |
| Bulk delete expenses | `expenses` array shrinks; `ui.selectedExpenseIds` → `[]` |
| Bulk add expenses to report | `expenses[i].reportId` set; `expenses[i].status` → `"open"`; `reports[i].total` and `expenseCount` updated |
| Bulk categorize expenses | `expenses[i].categoryId` and `category` updated |
| Toggle expense filters panel | `ui.expenseFiltersVisible` toggled |
| Toggle report filters panel | `ui.reportFiltersVisible` toggled |
| Change expense filter | `ui.expenseFilters` sub-fields updated |
| Change report filter | `ui.reportFilters` sub-fields updated |
| Change expense sort | `ui.expenseSortBy` and/or `ui.expenseSortDir` updated |
| Change report sort | `ui.reportSortBy` and/or `ui.reportSortDir` updated |
| Change expense view mode | `ui.expenseViewMode` updated (`"list"`, `"compact"`, `"grid"`, `"receipt"`) |
| Update policy settings | `policies[i]` fields updated (name, currency, autoReporting, requires*, max*, approval, reimbursement) |
| Toggle category enabled | `categories[i].enabled` toggled |
| Update category GL code | `categories[i].glCode` updated |
| Add new category | `categories` array grows by 1 |
| Toggle tag enabled | `tags[i].enabled` toggled |
| Update tag GL code | `tags[i].glCode` updated |
| Add new tag | `tags` array grows by 1 |
| Change member role | `members[i].role` updated |
| Change member manager | `members[i].managerId` updated |
| Invite new member | `members` array grows by 1 |
| Update distance rate | `distanceRates[i]` fields updated |
| Add report field | `reportFields` array grows by 1 |
| Delete report field | `reportFields` array shrinks by 1 |
| Add tax rate | `taxRates` array grows by 1 |
| Set default tax rate | `taxRates[i].isDefault` toggled (only one true) |
| Toggle tax rate enabled | `taxRates[i].enabled` toggled |

## Important Notes

- **Amounts are in cents**: All monetary values (`amount`, `total`, `taxAmount`, `hourlyRate`, `distanceRate`) are stored as integers representing cents. For example, `45600` = $456.00.
- **Denormalized fields**: Expenses carry `category` (string name) alongside `categoryId`, and `tag` alongside `tagId`. Reports carry `policyName`, `createdByName`, `createdByEmail`. These should be kept in sync when updating.
- **State persistence**: State is persisted to localStorage under key `expensify_mock_state` (or `expensify_mock_state_<sid>` with session ID). Initial state is stored under `expensify_mock_initial_state` (or `expensify_mock_initial_state_<sid>`).
- **Deep merge on inject**: Custom state injected via the API is deep-merged with the default initial data, so partial state injection is supported.
- **Keyboard shortcuts**: `N` then `E` opens New Expense modal; `N` then `R` opens New Report modal; `?` shows shortcuts overlay; `Escape` closes modals.
