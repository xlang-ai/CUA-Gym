# multi_procedure_application_mock Schema

**Deploy order**: 31 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8031)
**Base URL**: `http://172.17.46.46:8031/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## Overview

A multi-step graduate school application portal ("GradPortal") with 9 wizard steps. Uses Zustand for state management with localStorage persistence. The application simulates account setup, personal info, academic history, test scores, essays, referee management, program selection, payment, and final review/submission. Supports drag-and-drop reordering via `@dnd-kit` for addresses, institutions, courses, referees, and programs.

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `meta` | object | Application metadata: current step, save timestamps, submission status, step completion statuses |
| `meta.currentStep` | number | Active wizard step index (0-8). 0=Account, 1=Personal, 2=Academic, 3=Tests, 4=Essays, 5=Referees, 6=Programs, 7=Payment, 8=Review |
| `meta.lastSaved` | string\|null | ISO timestamp of last draft save, or `null` if never saved |
| `meta.submittedAt` | string\|null | ISO timestamp of final submission, or `null` if not submitted |
| `meta.isSubmitted` | boolean | Whether the application has been submitted (`false` by default) |
| `meta.stepStatuses` | object | Map of step index (number) → `StepStatus`. Tracks completion of each step |
| `account` | object | Step 1: Account details and eligibility |
| `account.email` | string | Applicant email address (default: `""`) |
| `account.isEligible` | boolean | Derived eligibility flag (default: `false`) |
| `account.eligibilityAnswers` | object | Free-form key-value map of eligibility responses. Keys include `"bachelors"` (boolean), `"gpa"` (boolean), `"citizenship_<status>"` (boolean for each status), `"gpa_explanation"` (string) |
| `personal` | object | Step 2: Personal information |
| `personal.firstName` | string | Applicant first name (default: `""`) |
| `personal.lastName` | string | Applicant last name (default: `""`) |
| `personal.citizenships` | array | Array of citizenship strings (default: `[]`) |
| `personal.addresses` | array | Array of `Address` objects representing address history (default: `[]`) |
| `academic` | object | Step 3: Academic background |
| `academic.institutions` | array | Array of `Institution` objects (default: `[]`) |
| `academic.gpaCourses` | array | Array of `Course` objects for GPA calculation (default: `[]`) |
| `tests` | object | Step 4: Standardized test scores |
| `tests.scores` | array | Array of `TestScore` objects (default: `[]`) |
| `essays` | object | Step 5: Application essays |
| `essays.items` | array | Array of `Essay` objects. Pre-populated with 2 items: SOP (id=`"sop"`) and Personal History (id=`"ph"`) |
| `referees` | object | Step 6: Recommendation letters |
| `referees.list` | array | Array of `Referee` objects (default: `[]`) |
| `programs` | object | Step 7: Program selection |
| `programs.selected` | array | Array of `Program` objects. Maximum 3 programs allowed (default: `[]`) |
| `payment` | object | Step 8: Application fee payment |
| `payment.method` | string\|null | `"card"`, `"waiver"`, or `null` (default: `null`) |
| `payment.status` | string | `"unpaid"` or `"paid"` (default: `"unpaid"`) |
| `payment.waiverReason` | string | Optional reason text for fee waiver (only if method is `"waiver"`) |

### StepStatus (enum)

`"not_started"` | `"in_progress"` | `"completed"`

### Address

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (random alphanumeric) |
| `from` | string | Start date in `YYYY-MM` format (or `""`) |
| `to` | string | End date in `YYYY-MM` format (or `""`) |
| `street` | string | Street address |
| `city` | string | City |
| `country` | string | Country |

### Institution

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `name` | string | Institution name |
| `country` | string | Country of institution |
| `degree` | string | Degree type (e.g. `"Bachelor of Science"`) |
| `gradingScheme` | string | Grading scheme (default: `"4.0"`) |
| `transcriptStatus` | string | `"pending"` \| `"uploaded"` \| `"verified"` |

### Course

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `name` | string | Course name |
| `credits` | number | Number of credits (default: `3`) |
| `grade` | number | Grade on 4.0 scale (default: `4.0`) |

### TestScore

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `type` | string | `"TOEFL"` \| `"IELTS"` \| `"GRE"` |
| `date` | string | Test date (ISO date string or `""`) |
| `regNumber` | string | Registration/report number |
| `scores` | object | Section scores as key-value pairs. Keys are lowercase section names (e.g. `"reading"`, `"listening"`, `"speaking"`, `"writing"`), values are numbers |

### Essay

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `"sop"` for Statement of Purpose, `"ph"` for Personal History |
| `type` | string | `"statement_of_purpose"` \| `"personal_history"` |
| `content` | string | Essay text content (supports Markdown) |
| `wordCount` | number | Auto-calculated word count of content |

### Referee

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `name` | string | Referee full name |
| `title` | string | Title or position |
| `institution` | string | Institution or organization |
| `email` | string | Email address |
| `status` | string | `"not_invited"` \| `"invited"` \| `"submitted"` |
| `rank` | number | Priority rank (0-indexed) |

### Program

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Program identifier (e.g. `"cs-ms"`, `"ds-ms"`, `"mba"`, `"psy-phd"`, `"his-ma"`) |
| `name` | string | Program name (e.g. `"Computer Science"`) |
| `department` | string | Department (e.g. `"Engineering"`) |
| `degree` | string | Degree type (e.g. `"M.S."`, `"MBA"`, `"Ph.D."`, `"M.A."`) |
| `justification` | string | Optional justification text for choosing this program |

### Available Programs (hardcoded in Step 7)

| ID | Name | Degree | Department |
|----|------|--------|------------|
| `cs-ms` | Computer Science | M.S. | Engineering |
| `ds-ms` | Data Science | M.S. | Engineering |
| `mba` | Business Administration | MBA | Business |
| `psy-phd` | Psychology | Ph.D. | Social Sciences |
| `his-ma` | History | M.A. | Humanities |

### Wizard Steps

| Index | Label | Component | Description |
|-------|-------|-----------|-------------|
| 0 | Account | Step1_Account | Email, password, eligibility questionnaire |
| 1 | Personal | Step2_Personal | Name, citizenships, address history (drag-to-reorder) |
| 2 | Academic | Step3_Academic | Institutions (drag-to-reorder), GPA calculator with courses |
| 3 | Tests | Step4_Tests | TOEFL/IELTS/GRE scores with visualization |
| 4 | Essays | Step5_Essays | Statement of Purpose + Personal History with rich text editor |
| 5 | Referees | Step6_Referees | Referee list (drag-to-reorder), invite/status tracking |
| 6 | Programs | Step7_Programs | Select up to 3 programs, drag-to-rank, justification |
| 7 | Payment | Step8_Payment | Credit card or fee waiver, order summary |
| 8 | Review | Step9_Review | Submission checklist and final submit |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8031/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "meta": {
          "currentStep": 0,
          "lastSaved": null,
          "submittedAt": null,
          "isSubmitted": false,
          "stepStatuses": { "0": "in_progress" }
        },
        "account": {
          "email": "applicant@example.com",
          "isEligible": false,
          "eligibilityAnswers": {
            "bachelors": true,
            "gpa": true,
            "citizenship_Citizen": true
          }
        },
        "personal": {
          "firstName": "Jane",
          "lastName": "Doe",
          "citizenships": ["United States"],
          "addresses": [
            {
              "id": "addr_1",
              "from": "2021-01",
              "to": "2024-06",
              "street": "123 Main St",
              "city": "Berkeley",
              "country": "United States"
            }
          ]
        },
        "academic": {
          "institutions": [
            {
              "id": "inst_1",
              "name": "UC Berkeley",
              "country": "United States",
              "degree": "Bachelor of Science",
              "gradingScheme": "4.0",
              "transcriptStatus": "verified"
            }
          ],
          "gpaCourses": [
            { "id": "course_1", "name": "Algorithms", "credits": 4, "grade": 3.8 },
            { "id": "course_2", "name": "Linear Algebra", "credits": 3, "grade": 4.0 }
          ]
        },
        "tests": {
          "scores": [
            {
              "id": "test_1",
              "type": "GRE",
              "date": "2024-03-15",
              "regNumber": "1234567",
              "scores": { "reading": 165, "writing": 4, "speaking": 0, "listening": 0 }
            }
          ]
        },
        "essays": {
          "items": [
            { "id": "sop", "type": "statement_of_purpose", "content": "I am applying because...", "wordCount": 4 },
            { "id": "ph", "type": "personal_history", "content": "", "wordCount": 0 }
          ]
        },
        "referees": {
          "list": [
            {
              "id": "ref_1",
              "name": "Dr. Smith",
              "title": "Professor",
              "institution": "UC Berkeley",
              "email": "smith@berkeley.edu",
              "status": "not_invited",
              "rank": 0
            }
          ]
        },
        "programs": {
          "selected": [
            { "id": "cs-ms", "name": "Computer Science", "department": "Engineering", "degree": "M.S.", "justification": "" }
          ]
        },
        "payment": {
          "method": null,
          "status": "unpaid"
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Enter email address | `account.email` updated |
| Answer eligibility question (bachelors) | `account.eligibilityAnswers.bachelors` set to `true`/`false` |
| Answer eligibility question (GPA) | `account.eligibilityAnswers.gpa` set to `true`/`false` |
| Check citizenship status checkbox | `account.eligibilityAnswers["citizenship_<status>"]` toggled |
| Enter GPA explanation | `account.eligibilityAnswers.gpa_explanation` updated |
| Enter first/last name | `personal.firstName` or `personal.lastName` updated |
| Add address | `personal.addresses` array grows by 1 (new empty Address) |
| Edit address fields | `personal.addresses[i]` fields updated (from, to, street, city, country) |
| Remove address | `personal.addresses` array shrinks by 1 |
| Drag-reorder addresses | `personal.addresses` array reordered |
| Add institution | `academic.institutions` array grows by 1 (new empty Institution) |
| Edit institution fields | `academic.institutions[i]` fields updated |
| Upload/verify transcript | `academic.institutions[i].transcriptStatus` → `"verified"` |
| Drag-reorder institutions | `academic.institutions` array reordered |
| Add course row | `academic.gpaCourses` array grows by 1 (default credits=3, grade=4.0) |
| Edit course fields | `academic.gpaCourses[i]` fields updated (name, credits, grade) |
| Remove course | `academic.gpaCourses` array shrinks by 1 |
| Add test (TOEFL/IELTS/GRE) | `tests.scores` array grows by 1 |
| Edit test date/regNumber | `tests.scores[i].date` or `tests.scores[i].regNumber` updated |
| Enter section score | `tests.scores[i].scores[section]` updated (e.g. reading, writing) |
| Remove test | `tests.scores` array shrinks by 1 |
| Type essay content | `essays.items[i].content` updated; `essays.items[i].wordCount` recalculated |
| Insert essay template | `essays.items[i].content` replaced with template; `wordCount` recalculated |
| Add referee | `referees.list` array grows by 1 (status=`"not_invited"`) |
| Edit referee fields | `referees.list[i]` fields updated (name, title, institution, email) |
| Send referee invite | `referees.list[i].status` → `"invited"` |
| Force submit referee (mock) | `referees.list[i].status` → `"submitted"` |
| Drag-reorder referees | `referees.list` array reordered |
| Select program | `programs.selected` array grows by 1 (max 3) |
| Deselect program | `programs.selected` array shrinks by 1 |
| Edit program justification | `programs.selected[i].justification` updated |
| Drag-reorder programs | `programs.selected` array reordered |
| Select payment method (card/waiver) | `payment.method` → `"card"` or `"waiver"` |
| Complete payment | `payment.status` → `"paid"` |
| Click Next step | `meta.currentStep` incremented; previous step marked `"completed"` in `meta.stepStatuses` |
| Click Previous step | `meta.currentStep` decremented |
| Click sidebar step | `meta.currentStep` set to clicked step index; `meta.stepStatuses` updated |
| Save draft (Ctrl+S or button) | `meta.lastSaved` → current ISO timestamp |
| Submit application | `meta.isSubmitted` → `true`; `meta.submittedAt` → current ISO timestamp |
| Reset application | All state fields reset to `INITIAL_STATE` defaults |
