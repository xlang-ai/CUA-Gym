# visa_portal_mock Schema

**Deploy order**: 55 (BASE_PORT=8000 → port 8055)
**Base URL**: `http://172.17.46.46:8055/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}` (use `"merge":true` for partial update)
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data)
**Serve files**: `GET /files/<sid>/<filename>`

Note: vite.config.js uses `port: 0` (random). Actual port depends on deployment config. The inject endpoint is `/post`, not `/go`.

## Application Overview

A multi-step government-style visa application portal with 8 form sections, session management, drag-and-drop reordering, and a formal GOV.UK-inspired UI. The application simulates a complete visa application workflow from personal details through to submission and appointment booking.

### Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Landing page with "Start new application" and "Continue application" |
| `/application/applicant` | ApplicantDetails | Step 1: Personal info, nationality, contact, address |
| `/application/passport` | PassportIdentity | Step 2: Passport details, MRZ parsing, other passports, uploads |
| `/application/travel` | TravelHistory | Step 3: International trips list with drag-and-drop reorder |
| `/application/employment` | Employment | Step 4: Employment status, history, financials, funding sources |
| `/application/family` | Family | Step 5: Family members list |
| `/application/security` | Security | Step 6: Security/background yes-no questions with details |
| `/application/documents` | Documents | Step 7: Required document uploads checklist |
| `/application/review` | ReviewAppointment | Step 8: Review summary, declaration, signature, appointment slot |
| `/go` | Go | State inspection/debug endpoint (JSON view) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `visaApplication` | object | Application metadata (ID, status, timestamps) |
| `applicant` | object | Personal details, nationality, contact, address |
| `passportInfo` | object | Passport details, other passports, MRZ, uploads |
| `travelHistory` | object | International travel records and gap explanation |
| `employmentAndFinancials` | object | Employment status, history, income, savings, funding |
| `family` | object | Family members and dependant links |
| `securityQuestions` | array | Background/security yes-no questions (4 in default) |
| `documents` | object | Required documents checklist and uploaded files |
| `appointment` | object | Appointment scheduling, signature, declaration |
| `meta` | object | Session/autosave metadata |

---

### `visaApplication` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `applicationId` | string | `"VISA-<random9>"` | Unique application reference (e.g. `"VISA-K3XP9Q1ZR"`) |
| `createdAt` | string (ISO) | current timestamp | When the application was created |
| `updatedAt` | string (ISO) | current timestamp | When the application was last updated |
| `status` | string | `"DRAFT"` | Application status. Enum: `"DRAFT"`, `"SUBMITTED"` |
| `currentSection` | number | `0` | Current step index (0-based) |

---

### `applicant` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `surname` | string | `""` | Family name |
| `givenNames` | string | `""` | Given/first names |
| `otherNames` | string | `""` | Any other names (aliases, maiden names) |
| `sex` | string | `""` | Enum: `"Male"`, `"Female"`, `"Other"` |
| `dob` | string | `""` | Date of birth (YYYY-MM-DD) |
| `pob` | string | `""` | Place of birth |
| `countryOfBirth` | string | `""` | Country of birth code. Options: `"USA"`, `"GBR"`, `"CAN"`, `"FRA"`, `"DEU"`, `"JPN"` |
| `nationalities` | array of string | `[]` | Current nationalities. Options: `"American"`, `"British"`, `"Canadian"`, `"French"`, `"German"` |
| `previousNationalities` | array of object | `[]` | Former nationalities held |
| `address` | object | (see below) | Address details |
| `phones` | array of object | `[{id:"ph1", type:"Mobile", number:""}]` | Phone numbers list (drag-and-drop reorderable) |
| `email` | string | `""` | Email address |

#### `applicant.previousNationalities[]` item shape

| Field | Type | Description |
|-------|------|-------------|
| `id` | number/string | Unique identifier (timestamp-based when created in UI) |
| `country` | string | Country name |
| `from` | string | Start date (YYYY-MM-DD) |
| `to` | string | End date (YYYY-MM-DD) |

#### `applicant.address` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `present` | string | `""` | Current residential address |
| `mailing` | string | `""` | Mailing address (if different) |
| `residenceSince` | string | `""` | Date started living at present address (YYYY-MM-DD) |
| `sameAsPresent` | boolean | `true` | Whether mailing address is same as present |

#### `applicant.phones[]` item shape

| Field | Type | Description |
|-------|------|-------------|
| `id` | string/number | Unique identifier (e.g. `"ph1"` or timestamp) |
| `type` | string | Phone type. Enum: `"Mobile"`, `"Home"`, `"Work"` |
| `number` | string | Phone number |

---

### `passportInfo` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `passportNumber` | string | `""` | Passport number (validated: 6-9 alphanumeric uppercase) |
| `issuingCountry` | string | `""` | Country that issued the passport |
| `dateOfIssue` | string | `""` | Passport issue date (YYYY-MM-DD) |
| `expiryDate` | string | `""` | Passport expiry date (YYYY-MM-DD). Warning shown if < 6 months |
| `passportType` | string | `"Regular"` | Enum: `"Regular"`, `"Diplomatic"`, `"Official"` |
| `hasOtherPassport` | boolean | `false` | Whether applicant has held other passports |
| `otherPassports` | array of object | `[]` | Previous/other passports |
| `mrzRaw` | string | `""` | Raw MRZ text for auto-fill parsing |
| `uploads` | array of object | `[]` | Passport page scan uploads (drag-and-drop reorderable) |

#### `passportInfo.otherPassports[]` item shape

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique identifier (timestamp-based) |
| `number` | string | Previous passport number |
| `country` | string | Issuing country |
| `expiry` | string | Expiry year (YYYY) |

#### `passportInfo.uploads[]` item shape

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique identifier (timestamp-based) |
| `name` | string | File name (e.g. `"passport_page_1.jpg"`) |
| `size` | string | File size string (e.g. `"1.2 MB"`) |
| `preview` | string | Preview image URL |

---

### `travelHistory` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `trips` | array of object | `[]` | International trips (drag-and-drop reorderable, sortable by date) |
| `gapsExplanation` | string | `""` | Explanation for gaps > 6 months (max 500 chars) |

#### `travelHistory.trips[]` item shape

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique identifier (timestamp-based) |
| `country` | string | Destination country |
| `city` | string | Destination city |
| `from` | string | Departure date (YYYY-MM-DD) |
| `to` | string | Return date (YYYY-MM-DD) |
| `purpose` | string | Purpose of travel (e.g. `"Tourism"`, `"Business"`) |
| `isResidence` | boolean | Whether this was the country of residence during the period |

**Normalizer aliases when injecting**: `destination` → `country`, `reason` → `purpose`, `startDate` → `dateFrom` → `from`, `endDate` → `dateTo` → `to`, `visa` → `visaType`

---

### `employmentAndFinancials` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `currentStatus` | string | `"Employed"` | Enum: `"Employed"`, `"Self-employed"`, `"Student"`, `"Unemployed"`, `"Retired"` |
| `employments` | array of object | `[]` | Employment history (drag-and-drop reorderable) |
| `sponsorDetails` | object/null | `null` | Sponsor information (if funded by sponsor) |
| `income` | object | `{amount: 0, currency: "USD"}` | Monthly income |
| `savings` | number | `0` | Available savings in USD (range slider: 0-50000, step 500) |
| `fundingSources` | array of string | `[]` | Who is paying for the trip. Options: `"Myself"`, `"Sponsor"`, `"Employer"`, `"Scholarship"` |

#### `employmentAndFinancials.income` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `amount` | number | `0` | Monthly income amount (range slider: 0-10000, step 100) |
| `currency` | string | `"USD"` | Currency code |

#### `employmentAndFinancials.employments[]` item shape

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique identifier (timestamp-based) |
| `employer` | string | Employer/company name |
| `title` | string | Job title |
| `from` | string | Start date (YYYY-MM-DD) |
| `to` | string | End date (YYYY-MM-DD) |
| `duties` | string | Main duties/responsibilities |

**Normalizer aliases when injecting**: `company`/`companyName` → `employer`, `position`/`role` → `title`, `startDate` → `dateFrom` → `from`, `endDate` → `dateTo` → `to`, `location` → `address`

---

### `family` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `members` | array of object | `[]` | Family members list |
| `dependantsLinks` | array | `[]` | Links to dependant applications |

#### `family.members[]` item shape

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique identifier (timestamp-based) |
| `name` | string | Full name |
| `relation` | string | Relationship. Enum: `"Spouse"`, `"Child"`, `"Parent"`, `"Sibling"` |
| `dob` | string | Date of birth (YYYY-MM-DD) |
| `nationality` | string | Nationality |

**Normalizer aliases when injecting**: `fullName` → `name`, `relation` → `relationship`, `dateOfBirth`/`birthday` → `dob`, `country` → `nationality`

---

### `securityQuestions[]` item shape

The default state contains 4 security questions:

| id | category | question |
|----|----------|----------|
| `crim1` | `Criminal` | Have you ever been convicted of a crime? |
| `imm1` | `Immigration` | Have you ever been refused a visa? |
| `med1` | `Medical` | Do you have any communicable diseases? |
| `sec1` | `Security` | Have you ever been involved in espionage? |

#### Per-item fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | (see above) | Unique question identifier |
| `category` | string | (see above) | Category. Enum: `"Criminal"`, `"Immigration"`, `"Medical"`, `"Security"`, `"General"` |
| `question` | string | (see above) | The question text |
| `answer` | string/null | `null` | Answer value. Enum: `"Yes"`, `"No"`, or `null` (unanswered) |
| `details` | string | `""` | Required details if answer is `"Yes"` (max 500 chars) |

**Normalizer aliases when injecting**: `text` → `question`, `explanation` → `details`. Boolean `answer` values are preserved as-is.

**Note**: The Security page requires all questions to be answered (progress = 100%) before the "Save and Continue" button is enabled.

---

### `documents` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `required` | array of object | (see below) | Required document checklist |
| `uploads` | array of object | `[]` | Uploaded document files |

#### Default `documents.required[]`

| id | name | required |
|----|------|----------|
| `doc_pass` | Passport Bio Page | `true` |
| `doc_photo` | Passport Photo | `true` |
| `doc_bank` | Bank Statements | `true` |
| `doc_inv` | Invitation Letter | `false` |

#### `documents.required[]` item shape

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique document type identifier |
| `name` | string | Document type name |
| `required` | boolean | Whether this document is mandatory |

#### `documents.uploads[]` item shape

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique identifier (timestamp-based) |
| `docId` | string | References `documents.required[].id` to link upload to requirement |
| `name` | string | File name (e.g. `"document_doc_pass.pdf"`) |
| `size` | string | File size string (e.g. `"1.4 MB"`) |
| `preview` | string | Preview image URL |

**Note**: The Documents page requires all `required: true` documents to have at least one upload before the "Save and Continue" button is enabled.

**Normalizer aliases when injecting uploads**: `fileName` → `name`, `docId` → `documentId`, `fileUrl` → `url`, `created` → `uploadedAt`

---

### `appointment` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `preferredCenter` | string | `""` | Preferred visa application center |
| `selectedSlot` | string/null | `null` | Selected appointment date (YYYY-MM-DD) |
| `scheduledAt` | string/null | `null` | Confirmed appointment time (ISO) |
| `signature` | any/null | `null` | Digital signature data |
| `declarationAgreed` | boolean | `false` | Whether declaration checkbox was checked |

**Note**: The Review page generates 5 available appointment slots (next 5 days from today). Submitting the application changes `visaApplication.status` from `"DRAFT"` to `"SUBMITTED"`.

---

### `meta` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `autosaveTimestamp` | string/null | `null` | ISO timestamp of last autosave (updated on every dispatch) |
| `sessionExpiryTime` | number | `Date.now() + 1800000` | Session expiry time in ms since epoch (30 min from creation) |

**Note**: The session timer is displayed in the header. Users can click "Extend Session" to reset it to 30 minutes.

---

## State Management

- **Pattern**: React Context + `useReducer` (in `src/context/VisaContext.jsx`)
- **Storage key**: `visa_application_state` (or `visa_application_state_<sid>` with session)
- **Initial state key**: `visa_application_initialState` (or `visa_application_initialState_<sid>`)
- **Autosave**: On every state change via `useEffect`

### Reducer Actions

| Action Type | Payload | Description |
|-------------|---------|-------------|
| `SET_STATE` | `{...fullState}` | Replace entire state |
| `UPDATE_SECTION` | `{section, data}` | Merge `data` into `state[section]` |
| `UPDATE_NESTED` | `{section, path, value}` | Update nested field (simplified, 1-level) |
| `ADD_ARRAY_ITEM` | `{section, field, item}` | Append item to `state[section][field]` array |
| `REMOVE_ARRAY_ITEM` | `{section, field, index}` | Remove item at index from array |
| `UPDATE_ARRAY_ITEM` | `{section, field, index, data}` | Merge `data` into array item at index |
| `REORDER_ARRAY` | `{section, field, fromIndex, toIndex}` | Drag-and-drop reorder array item |
| `RESET_SESSION` | (none) | Reset session expiry to 30 minutes from now |

---

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8055/?sid=task01",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "visaApplication": {
          "applicationId": "VISA-ABC123DEF",
          "createdAt": "2025-03-01T10:00:00Z",
          "updatedAt": "2025-03-01T10:00:00Z",
          "status": "DRAFT",
          "currentSection": 0
        },
        "applicant": {
          "surname": "Smith",
          "givenNames": "John Michael",
          "otherNames": "",
          "sex": "Male",
          "dob": "1990-05-15",
          "pob": "London",
          "countryOfBirth": "GBR",
          "nationalities": ["British"],
          "previousNationalities": [],
          "address": {
            "present": "42 Oxford Street, London, W1D 1BN, UK",
            "mailing": "",
            "residenceSince": "2018-06-01",
            "sameAsPresent": true
          },
          "phones": [
            {"id": "ph1", "type": "Mobile", "number": "+44 7700 900123"}
          ],
          "email": "john.smith@example.com"
        },
        "passportInfo": {
          "passportNumber": "AB1234567",
          "issuingCountry": "United Kingdom",
          "dateOfIssue": "2020-03-10",
          "expiryDate": "2030-03-10",
          "passportType": "Regular",
          "hasOtherPassport": false,
          "otherPassports": [],
          "mrzRaw": "",
          "uploads": []
        },
        "travelHistory": {
          "trips": [
            {"id": 1, "country": "France", "city": "Paris", "from": "2023-06-01", "to": "2023-06-10", "purpose": "Tourism", "isResidence": false},
            {"id": 2, "country": "United States", "city": "New York", "from": "2024-01-15", "to": "2024-01-25", "purpose": "Business", "isResidence": false}
          ],
          "gapsExplanation": ""
        },
        "employmentAndFinancials": {
          "currentStatus": "Employed",
          "employments": [
            {"id": 1, "employer": "Acme Corp", "title": "Software Engineer", "from": "2020-01-01", "to": "", "duties": "Full-stack development"}
          ],
          "sponsorDetails": null,
          "income": {"amount": 5000, "currency": "USD"},
          "savings": 25000,
          "fundingSources": ["Myself"]
        },
        "family": {
          "members": [
            {"id": 1, "name": "Jane Smith", "relation": "Spouse", "dob": "1992-08-20", "nationality": "British"}
          ],
          "dependantsLinks": []
        },
        "securityQuestions": [
          {"id": "crim1", "category": "Criminal", "question": "Have you ever been convicted of a crime?", "answer": "No", "details": ""},
          {"id": "imm1", "category": "Immigration", "question": "Have you ever been refused a visa?", "answer": "No", "details": ""},
          {"id": "med1", "category": "Medical", "question": "Do you have any communicable diseases?", "answer": "No", "details": ""},
          {"id": "sec1", "category": "Security", "question": "Have you ever been involved in espionage?", "answer": "No", "details": ""}
        ],
        "documents": {
          "required": [
            {"id": "doc_pass", "name": "Passport Bio Page", "required": true},
            {"id": "doc_photo", "name": "Passport Photo", "required": true},
            {"id": "doc_bank", "name": "Bank Statements", "required": true},
            {"id": "doc_inv", "name": "Invitation Letter", "required": false}
          ],
          "uploads": []
        },
        "appointment": {
          "preferredCenter": "",
          "selectedSlot": null,
          "scheduledAt": null,
          "signature": null,
          "declarationAgreed": false
        },
        "meta": {
          "autosaveTimestamp": null,
          "sessionExpiryTime": 1743500400000
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field(s) Changed |
|-------------|------------------------|
| Fill surname field | `applicant.surname` |
| Fill given names field | `applicant.givenNames` |
| Select sex radio button | `applicant.sex` (to `"Male"`, `"Female"`, or `"Other"`) |
| Fill date of birth | `applicant.dob` |
| Select country of birth | `applicant.countryOfBirth` |
| Add a nationality | `applicant.nationalities` array gains new string entry |
| Remove a nationality | `applicant.nationalities` array loses entry |
| Add a previous nationality | `applicant.previousNationalities` array gains `{id, country, from, to}` |
| Add a phone number | `applicant.phones` array gains `{id, type, number}` |
| Reorder phone numbers | `applicant.phones` array reordered |
| Update phone type/number | `applicant.phones[i].type` or `.number` |
| Change address | `applicant.address.present` or `.mailing` |
| Toggle mailing same as present | `applicant.address.sameAsPresent` |
| Fill passport number | `passportInfo.passportNumber` |
| Set passport type | `passportInfo.passportType` |
| Use MRZ auto-fill | `passportInfo.passportNumber`, `.issuingCountry`, `.dateOfIssue`, `.expiryDate` |
| Toggle has other passport | `passportInfo.hasOtherPassport` |
| Add a previous passport | `passportInfo.otherPassports` array gains `{id, number, country, expiry}` |
| Upload passport scan | `passportInfo.uploads` array gains `{id, name, size, preview}` |
| Add a trip | `travelHistory.trips` array gains `{id, country, city, from, to, purpose, isResidence}` |
| Reorder trips | `travelHistory.trips` array reordered |
| Sort trips by date | `travelHistory.trips` array sorted (newest first) |
| Import mock trips | `travelHistory.trips` replaced with 2 mock entries |
| Fill gaps explanation | `travelHistory.gapsExplanation` |
| Change employment status | `employmentAndFinancials.currentStatus` |
| Add employment record | `employmentAndFinancials.employments` array gains `{id, employer, title, from, to, duties}` |
| Reorder employment records | `employmentAndFinancials.employments` array reordered |
| Adjust income slider | `employmentAndFinancials.income.amount` (0-10000, step 100) |
| Adjust savings slider | `employmentAndFinancials.savings` (0-50000, step 500) |
| Toggle funding source | `employmentAndFinancials.fundingSources` array adds/removes string |
| Add family member | `family.members` array gains `{id, name, relation, dob, nationality}` |
| Remove family member | `family.members` array loses entry at index |
| Update family member fields | `family.members[i].name`, `.relation`, `.dob`, `.nationality` |
| Answer security question Yes/No | `securityQuestions[i].answer` (to `"Yes"` or `"No"`) |
| Provide security details | `securityQuestions[i].details` |
| Mark all security as No | All `securityQuestions[].answer` set to `"No"`, all `.details` cleared |
| Upload a document | `documents.uploads` array gains `{id, docId, name, size, preview}` |
| Remove uploaded document | `documents.uploads` array loses entry |
| Select appointment slot | `appointment.selectedSlot` set to date string (YYYY-MM-DD) |
| Submit application | `visaApplication.status` changes from `"DRAFT"` to `"SUBMITTED"` |
| Extend session | `meta.sessionExpiryTime` reset to `Date.now() + 1800000` |

## Normalizer Aliases (for state injection)

The initialState module contains normalizer functions that accept alternative field names when injecting custom state. This allows flexibility in state payloads:

| Section | Standard Field | Accepted Aliases |
|---------|---------------|-----------------|
| `applicant.phones[]` | `number` | `phoneNumber` |
| `travelHistory.trips[]` | `country` | `destination` |
| `travelHistory.trips[]` | `purpose` | `reason` |
| `travelHistory.trips[]` | `dateFrom` | `startDate`, `from` |
| `travelHistory.trips[]` | `dateTo` | `endDate`, `to` |
| `travelHistory.trips[]` | `visaType` | `visa` |
| `employmentAndFinancials.employments[]` | `employer` | `company`, `companyName` |
| `employmentAndFinancials.employments[]` | `title` | `position`, `role` |
| `employmentAndFinancials.employments[]` | `dateFrom` | `startDate`, `from` |
| `employmentAndFinancials.employments[]` | `dateTo` | `endDate`, `to` |
| `employmentAndFinancials.employments[]` | `address` | `location` |
| `family.members[]` | `name` | `fullName` |
| `family.members[]` | `relationship` | `relation` |
| `family.members[]` | `dob` | `dateOfBirth`, `birthday` |
| `family.members[]` | `nationality` | `country` |
| `securityQuestions[]` | `question` | `text` |
| `securityQuestions[]` | `details` | `explanation` |
| `documents.required[]` | `name` | `title`, `label` |
| `documents.uploads[]` | `name` | `fileName`, `label` |
| `documents.uploads[]` | `documentId` | `docId` |
| `documents.uploads[]` | `url` | `fileUrl` |
| `documents.uploads[]` | `uploadedAt` | `created` |
| `passportInfo.uploads[]` | (same as documents.uploads normalizer) | (same aliases) |
