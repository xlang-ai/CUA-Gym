# workday_mock Schema

**Deploy order**: 58 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8058)
**Base URL**: `http://172.17.46.46:8058/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Merge**: `POST /post?sid=<sid>` with body `{"action":"set","merge":true,"state":{...}}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | `Employee` | Logged-in user object. Default: emp001 (Alex Morgan, Senior Software Engineer) |
| `employees` | `Employee[]` | All employees in the organization. Default: 10 employees (emp001–emp010) |
| `departments` | `Department[]` | Organization departments. Default: 5 (Engineering, Design, Marketing, Finance, Human Resources) |
| `timeEntries` | `TimeEntry[]` | Time tracking entries. Default: up to 15 entries for current user over last 3 weeks |
| `timeOffRequests` | `TimeOffRequest[]` | Time-off / leave requests. Default: 5 requests (tr1–tr5) |
| `timeOffBalance` | `TimeOffBalance` | Current user's PTO balances. Default: vacation=120, sick=40, personal=16 hours |
| `payroll` | `Paystub[]` | Payroll / paystub records. Default: 6 biweekly stubs (ps1–ps6, Oct–Dec 2024) |
| `benefits` | `Benefits` | Benefits enrollment, plans, and dependents. Default: 4 plans (Medical, Dental, Vision, 401k), 1 dependent |
| `reviews` | `Review[]` | Performance review records. Default: 3 reviews (r1–r3) |
| `goals` | `Goal[]` | Performance goals. Default: 4 goals (g1–g4) |
| `tasks` | `Task[]` | Inbox tasks (approvals, reviews, compliance, etc.). Default: 6 tasks (t1–t6; t1–t5 pending, t6 completed) |
| `announcements` | `Announcement[]` | Company announcements displayed on the dashboard. Default: 5 announcements (a1–a5) |
| `notifications` | `Notification[]` | Header notification bell items. Default: 6 notifications (n1–n6; n1–n3 unread) |
| `clockStatus` | `ClockStatus` | Clock-in/clock-out state. Default: `{ isClockedIn: false, startTime: null }` |

### Employee fields
`{ id, name, email, phone, role, department, departmentId, avatar, managerId, title, location, joinDate, employeeType, compensationGrade?, annualSalary?, workSchedule?, skills?, birthday, workAnniversary }`
- `id`: string, e.g. `"emp001"`
- `role`: `"Manager" | "Director" | "Employee"`
- `employeeType`: `"Full-Time"` (default)
- `managerId`: string (references another employee's id) or `null` for top-level
- `skills`: string[] (only on currentUser by default), e.g. `["React", "Node.js", "AWS"]`
- Default IDs: emp001 (Alex Morgan), emp002 (Sarah Connor - Director, no manager), emp003 (John Smith), emp004 (Emily Chen), emp005 (Marcus Johnson), emp006 (Lisa Park), emp007 (David Kim), emp008 (Rachel Green), emp009 (James Wilson), emp010 (Nina Patel)
- Org hierarchy: emp002 is root → emp001/emp004/emp007/emp009/emp010 report to emp002; emp003/emp005 report to emp001; emp006 reports to emp004; emp008 reports to emp007

### Department fields
`{ id, name, headcount, managerId }`
- Default IDs: dept001 (Engineering, 4), dept002 (Design, 2), dept003 (Marketing, 2), dept004 (Finance, 1), dept005 (Human Resources, 1)

### TimeEntry fields
`{ entryId, employeeId, date, hours, project, status, notes }`
- `entryId`: string, e.g. `"te1"`
- `date`: ISO date string `"YYYY-MM-DD"`
- `hours`: number (typically 6 or 8)
- `project`: `"Project Alpha" | "Project Beta" | "Internal Meetings" | "General" | "Training"`
- `status`: `"Approved" | "Pending"`

### TimeOffRequest fields
`{ requestId, employeeId, type, startDate, endDate, status, reason, totalHours, reviewedBy, reviewedDate }`
- `requestId`: string, e.g. `"tr1"`
- `type`: `"Vacation" | "Sick" | "Personal"`
- `status`: `"Approved" | "Pending" | "Denied" | "Cancelled"`
- `totalHours`: number
- `reviewedBy`: string (employee id) or `null`
- `reviewedDate`: ISO date string or `null`
- Default IDs: tr1 (Approved vacation), tr2 (Approved sick), tr3 (Denied personal), tr4 (Pending for emp003), tr5 (Pending personal)

### TimeOffBalance fields
`{ vacation, sick, personal }`
- All values in hours (number). Default: `{ vacation: 120, sick: 40, personal: 16 }`

### Paystub fields
`{ paystubId, employeeId, period, payDate, date, grossPay, federalTax, stateTax, socialSecurity, medicare, healthInsurance, retirement401k, otherDeductions, totalDeductions, netPay, deductions }`
- `paystubId`: string, e.g. `"ps1"`
- `period`: descriptive string, e.g. `"Oct 1 - Oct 15, 2024"`
- All monetary fields are numbers (USD). Default grossPay: 5576.92, default netPay: ~3398.77
- `deductions` is an alias for `totalDeductions`

### Benefits fields
`{ employeeId, enrollmentStatus, plans, dependents }`
- `enrollmentStatus`: `"Complete"` (default)

#### Benefits Plan fields
`{ id, type, name, provider, coverageLevel, employeeCost, employerCost, cost, status, effectiveDate, details }`
- `id`: string, e.g. `"b1"`
- `type`: `"Medical" | "Dental" | "Vision" | "401k"`
- `coverageLevel`: `"Employee Only" | "Employee + Spouse" | "Employee + Family"`
- `cost`: alias for `employeeCost` (monthly, number)
- `status`: `"Active"` (default)
- `details`: object with plan-specific fields (e.g. `{ deductible, outOfPocketMax, copay, coinsurance }` for Medical)
- Default plan IDs: b1 (Medical PPO Plus, $240/mo), b2 (Dental Premium, $28/mo), b3 (Vision, $12/mo), b4 (401k, $278.85/mo)

#### Dependent fields
`{ id, name, relationship, dateOfBirth }`
- `id`: string, e.g. `"dep1"`
- `relationship`: `"Spouse" | "Child" | "Domestic Partner"`
- Default: dep1 (Jane Morgan, Spouse, 1991-08-22)

### Review fields
`{ reviewId, employeeId, managerId, period, rating, ratingScore, status, selfReviewComments, managerComments, comments, completedDate }`
- `reviewId`: string, e.g. `"r1"`
- `rating`: descriptive string, e.g. `"Exceeds Expectations"` or `""` if not rated
- `ratingScore`: number 1–5 or `null`. Labels: 1=Does Not Meet, 2=Partially Meets, 3=Meets Expectations, 4=Exceeds Expectations, 5=Significantly Exceeds
- `status`: `"Completed" | "Pending Self-Review" | "Pending Manager Review"`
- Default IDs: r1 (2023 Annual, Completed, score=4), r2 (2024 Mid-Year, Pending Self-Review for emp001), r3 (2024 Mid-Year for emp003, Pending Manager Review by emp001)

### Goal fields
`{ goalId, employeeId, title, description, category, status, progress, dueDate, createdDate, milestones }`
- `goalId`: string, e.g. `"g1"`
- `category`: `"Technical" | "Leadership" | "Business" | "Personal"`
- `status`: `"Not Started" | "On Track" | "At Risk" | "Off Track" | "Completed"`
- `progress`: number 0–100 (percentage)
- `milestones`: string[]
- Default IDs: g1 (AWS migration, 75%, On Track), g2 (Mentor juniors, 50%, On Track), g3 (Reduce build time, 20%, At Risk), g4 (All-hands presentation, 100%, Completed)

### Task fields
`{ taskId, employeeId, type, subType, description, status, dueDate, createdDate, relatedId, initiator, businessProcess, priority, comments }`
- `taskId`: string, e.g. `"t1"`
- `type`: `"Approval" | "Review" | "Compliance" | "Information" | "To-Do"`
- `subType`: `"Time Off Request" | "Performance Review" | "Training" | "Expense Report" | "Benefits"` etc.
- `status`: `"Pending" | "Completed" | "Denied"`
- `priority`: `"High" | "Normal" | "Low"`
- `relatedId`: string (reference to related entity) or `null`
- `initiator`: string (name of the person/system that created the task)
- `businessProcess`: string describing the workflow, e.g. `"Request Time Off"`
- `comments`: array of `{ id, author, text, timestamp }` — inline comment thread on the task
- Default IDs: t1 (Approve time off for John, Pending), t2 (Performance review for John, Pending, High), t3 (Cyber security training, Pending, High), t4 (Approve expense for Emily, Pending), t5 (Benefits enrollment reminder, Pending, Low), t6 (Approve time off for Marcus, Completed)

### Announcement fields
`{ id, title, date, content, category, priority }`
- `id`: string, e.g. `"a1"`
- `category`: `"Benefits" | "Company" | "IT" | "HR"`
- `priority`: `"High" | "Normal"`
- Default IDs: a1 (Open Enrollment, High), a2 (Holiday Closure), a3 (All-Hands Meeting), a4 (Cyber Security Training, High), a5 (Wellness Program)

### Notification fields
`{ id, type, title, message, timestamp, read, link }`
- `id`: string, e.g. `"n1"`
- `type`: `"task" | "pay" | "timeoff" | "system"`
- `read`: boolean
- `link`: route path string, e.g. `"/inbox"`, `"/pay"`, `"/time"`
- Default: n1–n3 unread, n4–n6 read

### ClockStatus fields
`{ isClockedIn, startTime }`
- `isClockedIn`: boolean
- `startTime`: ISO datetime string or `null`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8058/",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "emp001",
          "name": "Alex Morgan",
          "email": "alex.morgan@acmecorp.com",
          "phone": "+1 (415) 555-0142",
          "role": "Manager",
          "department": "Engineering",
          "departmentId": "dept001",
          "avatar": "https://ui-avatars.com/api/?name=Alex+Morgan&background=0875E1&color=fff&size=128",
          "managerId": "emp002",
          "title": "Senior Software Engineer",
          "location": "San Francisco, CA",
          "joinDate": "2020-03-15",
          "employeeType": "Full-Time",
          "skills": ["React", "Node.js", "AWS"],
          "birthday": "1990-04-12",
          "workAnniversary": "2020-03-15"
        },
        "employees": [
          {"id": "emp001", "name": "Alex Morgan", "email": "alex.morgan@acmecorp.com", "role": "Manager", "department": "Engineering", "departmentId": "dept001", "avatar": "https://ui-avatars.com/api/?name=Alex+Morgan&background=0875E1&color=fff&size=128", "managerId": "emp002", "title": "Senior Software Engineer", "location": "San Francisco, CA", "joinDate": "2020-03-15", "employeeType": "Full-Time", "birthday": "1990-04-12", "workAnniversary": "2020-03-15"},
          {"id": "emp002", "name": "Sarah Connor", "email": "sarah.connor@acmecorp.com", "role": "Director", "department": "Engineering", "departmentId": "dept001", "avatar": "https://ui-avatars.com/api/?name=Sarah+Connor&background=7C3AED&color=fff&size=128", "managerId": null, "title": "Director of Engineering", "location": "San Francisco, CA", "joinDate": "2018-06-01", "employeeType": "Full-Time", "birthday": "1985-11-03", "workAnniversary": "2018-06-01"}
        ],
        "departments": [
          {"id": "dept001", "name": "Engineering", "headcount": 2, "managerId": "emp002"}
        ],
        "timeEntries": [
          {"entryId": "te1", "employeeId": "emp001", "date": "2026-03-10", "hours": 8, "project": "Project Alpha", "status": "Approved", "notes": ""}
        ],
        "timeOffRequests": [
          {"requestId": "tr1", "employeeId": "emp001", "type": "Vacation", "startDate": "2026-04-01", "endDate": "2026-04-05", "status": "Pending", "reason": "Spring break", "totalHours": 40, "reviewedBy": null, "reviewedDate": null}
        ],
        "timeOffBalance": {"vacation": 120, "sick": 40, "personal": 16},
        "payroll": [
          {"paystubId": "ps1", "employeeId": "emp001", "period": "Mar 1 - Mar 15, 2026", "payDate": "2026-03-15", "date": "2026-03-15", "grossPay": 5576.92, "federalTax": 892.31, "stateTax": 445.35, "socialSecurity": 345.77, "medicare": 80.87, "healthInsurance": 120.00, "retirement401k": 278.85, "otherDeductions": 15.00, "totalDeductions": 2178.15, "netPay": 3398.77, "deductions": 2178.15}
        ],
        "benefits": {
          "employeeId": "emp001",
          "enrollmentStatus": "Complete",
          "plans": [
            {"id": "b1", "type": "Medical", "name": "Medical - PPO Plus", "provider": "BlueCross BlueShield", "coverageLevel": "Employee + Spouse", "employeeCost": 240.00, "employerCost": 680.00, "cost": 240.00, "status": "Active", "effectiveDate": "2024-01-01", "details": {"deductible": 1500, "outOfPocketMax": 5000, "copay": 25, "coinsurance": 20}}
          ],
          "dependents": [
            {"id": "dep1", "name": "Jane Morgan", "relationship": "Spouse", "dateOfBirth": "1991-08-22"}
          ]
        },
        "reviews": [
          {"reviewId": "r1", "employeeId": "emp001", "managerId": "emp002", "period": "2023 Annual Review", "rating": "Exceeds Expectations", "ratingScore": 4, "status": "Completed", "selfReviewComments": "Led AWS migration.", "managerComments": "Excellent performance.", "comments": "Great year.", "completedDate": "2024-03-15"}
        ],
        "goals": [
          {"goalId": "g1", "employeeId": "emp001", "title": "Complete AWS migration", "description": "Migrate core services to AWS ECS.", "category": "Technical", "status": "On Track", "progress": 75, "dueDate": "2024-12-31", "createdDate": "2024-01-15", "milestones": ["Phase 1 complete"]}
        ],
        "tasks": [
          {"taskId": "t1", "employeeId": "emp001", "type": "Approval", "subType": "Time Off Request", "description": "Approve Time Off for John Smith", "status": "Pending", "dueDate": "2026-03-16", "createdDate": "2026-03-11", "relatedId": "tr4", "initiator": "John Smith", "businessProcess": "Request Time Off", "priority": "Normal", "comments": []}
        ],
        "announcements": [
          {"id": "a1", "title": "Open Enrollment Begins", "date": "2026-03-01", "content": "Benefits open enrollment starts next week.", "category": "Benefits", "priority": "High"}
        ],
        "notifications": [
          {"id": "n1", "type": "task", "title": "Time Off Request", "message": "John Smith has requested time off.", "timestamp": "2026-03-11T12:00:00.000Z", "read": false, "link": "/inbox"}
        ],
        "clockStatus": {"isClockedIn": false, "startTime": null}
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Clock in | `clockStatus.isClockedIn` → true, `clockStatus.startTime` set |
| Clock out | `clockStatus.isClockedIn` → false, `clockStatus.startTime` → null, new entry appended to `timeEntries` |
| Add time entry (manual) | `timeEntries` (new entry appended with status "Pending") |
| Update time entry | `timeEntries[*].hours`, `timeEntries[*].project`, `timeEntries[*].notes` |
| Request time off | `timeOffRequests` (new entry appended with status "Pending") |
| Cancel time off request | `timeOffRequests[*].status` → "Cancelled" |
| Approve/complete a task | `tasks[*].status` → "Completed" |
| Deny a task | `tasks[*].status` → "Denied" |
| Send back a task | `tasks[*].comments` (feedback comment appended) |
| Add comment to task | `tasks[*].comments` (new comment appended) |
| Update profile (name, phone, location, preferredName) | `currentUser.*`, `employees[*].*` (matching employee updated) |
| Add/remove skill | `currentUser.skills`, `employees[*].skills` |
| Add a goal | `goals` (new entry appended) |
| Update a goal (title, description, progress, status, category, dueDate) | `goals[*].*` |
| Delete a goal | `goals` (entry removed) |
| Submit self-review | `reviews[*].selfReviewComments`, `reviews[*].ratingScore`, `reviews[*].status` → "Pending Manager Review" |
| Complete manager review | `reviews[*].managerComments`, `reviews[*].rating`, `reviews[*].ratingScore`, `reviews[*].status` → "Completed", `reviews[*].completedDate` set |
| Mark notification as read | `notifications[*].read` → true |
| Mark all notifications as read | all `notifications[*].read` → true |
| Update benefit plan | `benefits.plans[*].*` (plan fields updated) |
| Add dependent | `benefits.dependents` (new entry appended) |
| Remove dependent | `benefits.dependents` (entry removed) |
| Update payment elections | `paymentElections.*` (new top-level key created/updated) |

## Routes

| Path | Page | Description |
|------|------|-------------|
| `/` | Dashboard | Home page with action items, time summary, announcements, upcoming events |
| `/inbox` | Inbox | Task list with Actions/Archive tabs, search, filter by type, bulk approve, task detail panel |
| `/time` | Time & Absence | Clock in/out, weekly timesheet, time-off request form, calendar, balance details |
| `/pay` | Pay | Paystub list, payslip detail modal, year-to-date summary, payment elections, tax documents |
| `/benefits` | Benefits | Current plans overview, plan detail modal, enrollment flow, dependent management, cost summary |
| `/performance` | Performance | Performance reviews (self-review & manager review), goals CRUD, skills management |
| `/profile` | Profile | Tabbed profile (Summary, Job, Compensation, Benefits, Pay, Time Off) with edit mode |
| `/directory` | Directory | Employee list/grid view, org chart view, search, department filter, employee detail panel |
| `/go` | Go | State inspector debug page showing `{initial_state, current_state, state_diff}` |

## Dispatch Actions Reference

| Action Type | Payload | Effect |
|-------------|---------|--------|
| `CLOCK_IN` | (none) | Sets `clockStatus.isClockedIn = true`, records `startTime` |
| `CLOCK_OUT` | (none) | Resets clockStatus, appends calculated time entry to `timeEntries` |
| `ADD_TIME_ENTRY` | `{ date, hours, project?, notes? }` | Appends new time entry |
| `UPDATE_TIME_ENTRY` | `{ entryId, ...fields }` | Updates matching time entry |
| `ADD_TIME_OFF` | `{ type, startDate, endDate, reason, totalHours?, employeeId? }` | Appends new time-off request |
| `CANCEL_TIME_OFF` | `requestId` (string) | Sets request status to "Cancelled" |
| `COMPLETE_TASK` | `taskId` (string) | Sets task status to "Completed" |
| `DENY_TASK` | `taskId` (string) | Sets task status to "Denied" |
| `SEND_BACK_TASK` | `{ taskId, feedback }` | Appends feedback comment to task |
| `ADD_TASK_COMMENT` | `{ taskId, text }` | Appends comment to task |
| `UPDATE_PROFILE` | `{ name?, phone?, location?, preferredName?, skills?, ... }` | Merges into `currentUser` and matching `employees` entry |
| `ADD_GOAL` | `{ title, description?, category?, status?, progress?, dueDate?, milestones? }` | Appends new goal |
| `UPDATE_GOAL` | `{ goalId, ...fields }` | Updates matching goal |
| `DELETE_GOAL` | `goalId` (string) | Removes goal |
| `SUBMIT_SELF_REVIEW` | `{ reviewId, selfReviewComments, ratingScore? }` | Updates review, sets status to "Pending Manager Review" |
| `ADD_REVIEW_COMMENT` | `{ reviewId, managerComments, rating?, ratingScore? }` | Completes review, sets status to "Completed" |
| `MARK_NOTIFICATION_READ` | `id` (string) | Sets `notifications[*].read = true` |
| `MARK_ALL_NOTIFICATIONS_READ` | (none) | Sets all notifications to read |
| `UPDATE_BENEFIT_PLAN` | `{ planId, updates: {...} }` | Updates matching benefit plan |
| `ADD_DEPENDENT` | `{ name, relationship, dateOfBirth, id? }` | Appends to `benefits.dependents` |
| `REMOVE_DEPENDENT` | `id` (string) | Removes from `benefits.dependents` |
| `UPDATE_PAYMENT_ELECTIONS` | `{ ...fields }` | Merges into `paymentElections` |
