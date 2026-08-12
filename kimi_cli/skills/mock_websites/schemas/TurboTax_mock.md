# TurboTax_mock Schema

**Deploy order**: 50 (alphabetical among all *_mock dirs, BASE_PORT=8000 -> port 8050)
**Base URL**: `http://172.17.46.46:8050/`
**Go Endpoint**: `GET /go?sid=<sid>` -> `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}` (use `"merge":true` for partial update)
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) -> `{success, files: [{original_name, stored_name, size, content_type, url}]}`
**Serve files**: `GET /files/<sid>/<filename>`

Note: The actual codebase resides in `california_tax_mock/`. State is stored in localStorage under keys `california_tax_mock_state` / `california_tax_mock_initialState` (or `california_tax_mock_state_<sid>` / `california_tax_mock_initialState_<sid>` when a session ID is provided). Session ID is read from URL query param `?sid=<value>` or from `sessionStorage` key `california_tax_sid`.

## Application Overview

This mock simulates the **California Franchise Tax Board (FTB) CalFile** system -- a TurboTax-style California state income tax filing application. It is a multi-step form wizard that walks through California Form 540 preparation: personal information, dependents, income (W-2s, 1099s), deductions, credits, tax summary, review, and submission. It also includes ancillary pages for payments (Web Pay), refund status tracking, form lookup, help/contact, and an account dashboard.

### Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `WelcomePage` | Landing/welcome page to begin filing |
| `/filing/personal-info` | `PersonalInfoForm` | Step 1: Filing status, taxpayer info, spouse info, address, contact |
| `/filing/dependents` | `DependentsList` | Step 2: Add/remove/edit dependents |
| `/filing/income` | `IncomeForm` + `W2Form` | Step 3: W-2s, 1099-INT, 1099-DIV, other income, federal AGI |
| `/filing/deductions` | `DeductionsForm` | Step 4: Standard vs. itemized deductions, CA adjustments, voluntary contributions |
| `/filing/credits` | `CreditsForm` | Step 5: CalEITC, child care, renter's credit, other credits |
| `/filing/tax-summary` | `TaxSummaryView` | Step 6: Computed tax summary (read-only) |
| `/filing/review` | `ReviewPage` | Step 7: Review all sections, e-sign declaration, submit return |
| `/filing/confirmation` | `ConfirmationPage` | Step 8: Submission confirmation with confirmation number |
| `/pay` | `PaymentPage` | Web Pay -- make a payment (bank routing/account, amount, date) |
| `/refund` | `RefundPage` | "Where's My Refund?" -- check refund status |
| `/forms` | `FormsPage` | California tax forms lookup (static, no state changes) |
| `/help` | `HelpPage` | Contact info, send a message (stores in `ui.contactMessages`) |
| `/account` | `AccountPage` | MyFTB account dashboard (summary, returns, notices, payments, messages, settings) |
| `/coming-soon/:section` | `ComingSoonPage` | Placeholder for unimplemented features |
| `/go` | `Go` | State inspector: shows `initial_state`, `current_state`, `state_diff` |

All `/filing/*` routes are wrapped by `StepNavigation`, which provides Previous/Next/Save & Exit buttons and step validation.

### Filing Step Configuration

| Step Index | Step ID | Path | Label |
|-----------|---------|------|-------|
| 0 | `personal-info` | `/filing/personal-info` | Personal Information |
| 1 | `dependents` | `/filing/dependents` | Dependents |
| 2 | `income` | `/filing/income` | Income |
| 3 | `deductions` | `/filing/deductions` | Deductions |
| 4 | `credits` | `/filing/credits` | Credits |
| 5 | `tax-summary` | `/filing/tax-summary` | Tax Summary |
| 6 | `review` | `/filing/review` | Review & Sign |
| 7 | `confirmation` | `/filing/confirmation` | Confirmation |

## State Schema

The entire application state is a single object with these top-level keys:

| Key | Type | Description |
|-----|------|-------------|
| `taxReturn` | object | Tax return metadata: ID, year, status, timestamps, confirmation number |
| `personalInfo` | object | Taxpayer personal information, filing status, spouse info, address, contact |
| `dependents` | array | List of dependent objects |
| `income` | object | W-2s, 1099-INT, 1099-DIV, other income, federal AGI |
| `deductions` | object | Standard/itemized deductions, CA adjustments, voluntary contributions |
| `credits` | object | Tax credits (CalEITC, child care, renter's, etc.) |
| `calculations` | object | Computed tax calculation results (auto-generated, not directly set) |
| `payment` | object | Refund/payment method preferences, Web Pay submissions |
| `formProgress` | object | Current step, completed steps, step errors |
| `ui` | object | UI state: current view, validation errors visibility, tooltips, contact messages |
| `meta` | object | Session metadata: last saved time, session expiration |

### `taxReturn` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"CA540-2024-DEMO001"` | Tax return identifier. Format: `CA540-YYYY-XXXXXXX`. On reset, regenerated as `CA540-` + random alphanumeric. |
| `taxYear` | number | `2024` | Tax year being filed |
| `status` | string | `"in_progress"` | Return status. Values: `"draft"`, `"in_progress"`, `"submitted"` |
| `createdAt` | string | `"2025-02-15T10:30:00.000Z"` | ISO 8601 creation timestamp |
| `updatedAt` | string | `"2025-02-15T10:30:00.000Z"` | ISO 8601 last update timestamp. Updated on every `UPDATE_SECTION`, `ADD_ARRAY_ITEM`, `REMOVE_ARRAY_ITEM`, `UPDATE_ARRAY_ITEM`, `SUBMIT_RETURN` dispatch. |
| `confirmationNumber` | string\|null | `null` | Set on submission. Format: `CA-<base36_timestamp>-<random_6_chars>` (uppercase). Example: `"CA-M3F8K2-X9B4QR"` |

### `personalInfo` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `filingStatus` | string | `"single"` | Filing status. Values: `"single"`, `"married_joint"`, `"married_separate"`, `"head_of_household"`, `"qualifying_widow"` |
| `firstName` | string | `"Maria"` | Taxpayer first name |
| `middleInitial` | string | `"L"` | Taxpayer middle initial (single character, auto-uppercased) |
| `lastName` | string | `"Santos"` | Taxpayer last name |
| `suffix` | string | `""` | Name suffix. Values: `""`, `"SR"`, `"JR"`, `"II"`, `"III"`, `"IV"` |
| `ssn` | string | `"592847163"` | Social Security Number (9 digits, stored without dashes) |
| `dateOfBirth` | string | `"1988-06-14"` | Date of birth in `YYYY-MM-DD` format |
| `spouseFirstName` | string | `""` | Spouse/RDP first name (used when `filingStatus` is `married_joint` or `married_separate`) |
| `spouseMiddleInitial` | string | `""` | Spouse middle initial |
| `spouseLastName` | string | `""` | Spouse last name |
| `spouseSsn` | string | `""` | Spouse SSN (9 digits, no dashes) |
| `spouseDateOfBirth` | string | `""` | Spouse date of birth (`YYYY-MM-DD`) |
| `address` | object | *(see below)* | Home address |
| `phone` | string | `"(408) 555-3291"` | Daytime phone number (formatted as `(XXX) XXX-XXXX`) |
| `email` | string | `"maria.santos@email.com"` | Email address |

#### `personalInfo.address` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `street` | string | `"2847 Oak Valley Drive"` | Street address |
| `apt` | string | `"Unit 12"` | Apartment/suite/unit number |
| `city` | string | `"San Jose"` | City |
| `state` | string | `"CA"` | State (always `"CA"`, displayed as disabled) |
| `zip` | string | `"95128"` | ZIP code (5 digits or 5+4 format) |

### `dependents` array items

Each dependent is an object with these fields:

| Field | Type | Default (new) | Description |
|-------|------|---------------|-------------|
| `id` | string | `Date.now().toString()` | Unique identifier |
| `firstName` | string | `""` | Dependent's first name |
| `lastName` | string | `""` | Dependent's last name |
| `ssn` | string | `""` | Dependent's SSN (9 digits, no dashes) |
| `relationship` | string | `""` | Relationship to taxpayer. Values: `""`, `"Son"`, `"Daughter"`, `"Stepson"`, `"Stepdaughter"`, `"Foster child"`, `"Brother"`, `"Sister"`, `"Half brother"`, `"Half sister"`, `"Stepbrother"`, `"Stepsister"`, `"Grandchild"`, `"Niece"`, `"Nephew"`, `"Parent"`, `"Other"` |
| `dateOfBirth` | string | `""` | Date of birth (`YYYY-MM-DD`) |
| `monthsLived` | number | `12` | Months lived in home (0-12) |

Default seed data: empty array `[]`.

### `income` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `w2s` | array | *(1 pre-filled W-2)* | Array of W-2 form objects |
| `interest1099` | array | *(1 pre-filled 1099-INT)* | Array of 1099-INT interest income objects |
| `dividend1099` | array | `[]` | Array of 1099-DIV dividend income objects |
| `otherIncome` | array | `[]` | Array of other income objects |
| `federalAgi` | string | `"82500.00"` | Federal Adjusted Gross Income (from Form 1040 line 11). Stored as string. |

#### `income.w2s[]` item fields

| Field | Type | Default (new) | Description |
|-------|------|---------------|-------------|
| `id` | number | `Date.now()` | Unique identifier |
| `employerName` | string | `""` | Employer name |
| `employerEin` | string | `""` | Employer EIN (format: `XX-XXXXXXX`) |
| `wages` | string | `""` | Wages, tips, other compensation (Box 1). Stored as string. |
| `federalWithheld` | string | `""` | Federal income tax withheld (Box 2). Stored as string. |
| `stateWages` | string | `""` | State wages (Box 16). Stored as string. |
| `stateWithheld` | string | `""` | State income tax withheld (Box 17). Stored as string. |

**Seed W-2:**
```json
{
  "id": 1001,
  "employerName": "Bay Area Tech Solutions Inc",
  "employerEin": "94-3281756",
  "wages": "82500.00",
  "federalWithheld": "14200.00",
  "stateWages": "82500.00",
  "stateWithheld": "4950.00"
}
```

#### `income.interest1099[]` item fields

| Field | Type | Default (new) | Description |
|-------|------|---------------|-------------|
| `id` | number | `Date.now()` | Unique identifier |
| `payerName` | string | `""` | Payer name (bank/institution) |
| `amount` | string | `""` | Interest amount. Stored as string. |

**Seed 1099-INT:**
```json
{
  "id": 2001,
  "payerName": "Wells Fargo Bank",
  "amount": "342.50"
}
```

#### `income.dividend1099[]` item fields

| Field | Type | Default (new) | Description |
|-------|------|---------------|-------------|
| `id` | number | `Date.now() + 1` | Unique identifier |
| `payerName` | string | `""` | Payer name |
| `ordinaryDividends` | string | `""` | Ordinary dividends (Box 1a). Stored as string. |
| `qualifiedDividends` | string | `""` | Qualified dividends (Box 1b). Stored as string. |

#### `income.otherIncome[]` item fields

| Field | Type | Default (new) | Description |
|-------|------|---------------|-------------|
| `id` | number | `Date.now() + 2` | Unique identifier |
| `description` | string | `""` | Income description |
| `amount` | string | `""` | Amount. Stored as string. |

### `deductions` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | `"standard"` | Deduction method. Values: `"standard"`, `"itemized"` |
| `standardAmount` | number | `5540` | Standard deduction amount (auto-calculated based on filing status). Values: single=5540, married_joint=11080, married_separate=5540, head_of_household=11080, qualifying_widow=11080 |
| `itemized` | object | *(see below)* | Itemized deduction amounts |
| `caAdjustmentsSubtraction` | number\|string | `0` | California Schedule CA subtractions (Column B) |
| `caAdjustmentsAddition` | number\|string | `0` | California Schedule CA additions (Column C) |
| `voluntaryContributions` | array | `[]` | Array of voluntary contribution objects |

#### `deductions.itemized` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `medicalExpenses` | number\|string | `0` | Medical and dental expenses (exceeding 7.5% of federal AGI) |
| `stateLocalTaxes` | number\|string | `0` | State and local taxes (SALT) |
| `mortgageInterest` | number\|string | `0` | Home mortgage interest |
| `charitableContributions` | number\|string | `0` | Charitable contributions |
| `otherDeductions` | number\|string | `0` | Other itemized deductions |

#### `deductions.voluntaryContributions[]` item fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Fund identifier. Values: `"alzheimers"`, `"ca_seniors"`, `"firefighters"`, `"wildlife"`, `"local_homeless"`, `"domestic_violence"` |
| `fundName` | string | Full fund name |
| `amount` | string | Contribution amount (stored as string) |

### `credits` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `calEitc` | object | `{eligible: false, amount: 0}` | California Earned Income Tax Credit (refundable, up to $3,644) |
| `childDependentCare` | object | `{eligible: false, expenses: 0, amount: 0}` | Child and Dependent Care Expenses Credit (nonrefundable; `amount` = `expenses * 0.5`) |
| `rentersCredit` | object | `{eligible: true, amount: 60}` | Renter's Credit (nonrefundable; $60 single, $120 joint) |
| `seniorHeadOfHousehold` | object | `{eligible: false, amount: 0}` | Senior Head of Household Credit (nonrefundable) |
| `jointCustodyHeadOfHousehold` | object | `{eligible: false, amount: 0}` | Joint Custody Head of Household Credit (nonrefundable) |
| `dependentParent` | object | `{eligible: false, amount: 0}` | Dependent Parent Credit (nonrefundable) |
| `otherCredits` | array | `[]` | Array of other credit objects (nonrefundable) |

#### Credit object common fields

Each named credit object has:

| Field | Type | Description |
|-------|------|-------------|
| `eligible` | boolean | Whether the credit is claimed |
| `amount` | number | Credit dollar amount |
| `expenses` | number | *(childDependentCare only)* Care expenses entered |

#### `credits.otherCredits[]` item fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (`Date.now().toString()`) |
| `code` | string | Credit code (e.g., `"188"`) |
| `description` | string | Credit description |
| `amount` | number | Credit amount |

### `calculations` subfields (auto-computed)

This object is automatically recalculated by `calculateFinalTax()` on every state change. It is not directly set by state injection -- it will be recomputed from the other state fields.

| Field | Type | Description |
|-------|------|-------------|
| `totalIncome` | number | Sum of all W-2 wages + interest + dividends + other income |
| `adjustedGrossIncome` | number | Federal AGI - CA subtractions + CA additions |
| `totalDeductions` | number | Standard deduction amount or sum of itemized deductions |
| `taxableIncome` | number | AGI minus deductions (minimum 0) |
| `taxBeforeCredits` | number | California tax computed using progressive brackets |
| `exemptionCredits` | number | Personal exemption credits ($149/taxpayer, $149/spouse if joint, $461/dependent) |
| `totalNonrefundableCredits` | number | Sum of all nonrefundable credits |
| `totalRefundableCredits` | number | Sum of all refundable credits (CalEITC) |
| `netTax` | number | Tax after all credits (minimum 0) |
| `totalWithholdings` | number | Sum of state income tax withheld from all W-2s |
| `estimatedPayments` | number | Estimated tax payments from `payment.estimatedPayments` |
| `totalPayments` | number | Withholdings + estimated payments |
| `overpayment` | number | Amount overpaid (refund before voluntary contributions) |
| `amountOwed` | number | Amount still owed |
| `refundAmount` | number | Final refund amount (after voluntary contributions) |

### `payment` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `refundMethod` | string | `"direct_deposit"` | How to receive refund. Values: `"direct_deposit"`, `"paper_check"` |
| `bankRoutingNumber` | string | `""` | Bank routing number (9 digits) |
| `bankAccountNumber` | string | `""` | Bank account number |
| `accountType` | string | `""` | Account type. Values: `""`, `"checking"`, `"savings"` |
| `paymentMethod` | string | `""` | How to pay amount owed. Values: `""`, `"electronic"`, `"check"` |
| `paymentDate` | string | `""` | Payment date (`YYYY-MM-DD`) |
| `estimatedPayments` | string | `""` | Estimated tax payments already made (used in tax calculation) |
| `webPaySubmissions` | array | `[]` | Array of Web Pay submission records |

#### `payment.webPaySubmissions[]` item fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Payment confirmation ID. Format: `PAY-<base36_timestamp>` (uppercase) |
| `type` | string | Payment type. Values: `"tax_due"`, `"estimated"`, `"extension"` |
| `amount` | number | Payment amount |
| `date` | string | Payment date (`YYYY-MM-DD`) |
| `status` | string | Payment status. Value: `"pending"` |
| `accountType` | string | Bank account type (`"checking"` or `"savings"`) |
| `lastFour` | string | Last 4 digits of account number |
| `submittedAt` | string | ISO 8601 submission timestamp |

### `formProgress` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `currentStep` | number | `1` | Current step number (1-indexed) |
| `completedSteps` | array | `["personal-info"]` | Array of completed step ID strings. Values from: `"personal-info"`, `"dependents"`, `"income"`, `"deductions"`, `"credits"`, `"tax-summary"`, `"review"`, `"confirmation"` |
| `stepErrors` | object | `{}` | Map of step ID to array of error message strings. Example: `{"personal-info": ["First name is required"]}` |

### `ui` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `currentView` | string | `"filing"` | Current view mode |
| `showValidationErrors` | boolean | `false` | Whether to display validation errors |
| `isSaving` | boolean | `false` | Whether a save operation is in progress |
| `showConfirmDialog` | boolean | `false` | Whether the confirm dialog is visible |
| `activeTooltip` | string\|null | `null` | ID of the currently active tooltip |
| `contactMessages` | array | *(undefined initially)* | Array of contact messages sent via Help page. Each: `{id: string, subject: string, message: string, sentAt: string}` |

### `meta` subfields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `lastSavedAt` | string\|null | `null` | ISO 8601 timestamp of last save |
| `sessionExpiresAt` | string\|null | `null` | ISO 8601 timestamp of session expiration |

## State Management Details

- **Pattern**: React Context + `useReducer` (`TaxContext.jsx`)
- **Context provider**: `TaxProvider` wraps entire app
- **Reducer actions**: `SET_STATE`, `UPDATE_SECTION`, `ADD_ARRAY_ITEM`, `REMOVE_ARRAY_ITEM`, `UPDATE_ARRAY_ITEM`, `SET_STEP`, `COMPLETE_STEP`, `SET_STEP_ERRORS`, `UPDATE_UI`, `SUBMIT_RETURN`, `RESET_STATE` / `RESET_RETURN`
- **Auto-computation**: Every state mutation (except `SET_STEP`, `COMPLETE_STEP`, `UPDATE_UI`) triggers `calculateFinalTax()` which recomputes the `calculations` object
- **Persistence**: localStorage with keys `california_tax_mock_state` (or `california_tax_mock_state_<sid>`) and `california_tax_mock_initialState` (or `california_tax_mock_initialState_<sid>`)
- **Session ID**: Read from URL query param `?sid=<value>` or from `sessionStorage` key `california_tax_sid`
- **Custom state injection**: On first load for a session, fetches `GET /state?sid=<sid>` to check for server-injected state. Deep-merges with seed defaults.
- **Initial state snapshot**: Captured once on first load; used by `/go` for diff calculation
- **Server sync**: After every state change, the app POSTs `{action: "set_current", state}` to `/post?sid=<sid>` so the server-side `/go` endpoint returns current state

## Dispatch Patterns

The reducer accepts two dispatch patterns:

1. **Nested payload**: `dispatch({ type: 'UPDATE_SECTION', payload: { section: 'personalInfo', data: { firstName: 'John' } } })`
2. **Flat dispatch**: `dispatch({ type: 'UPDATE_SECTION', section: 'personalInfo', data: { firstName: 'John' } })`

Both are equivalent. Array operations use:
- `ADD_ARRAY_ITEM`: `{ section, field?, item }` -- `field` for nested arrays (e.g., `income.w2s`), omit for top-level arrays (e.g., `dependents`)
- `REMOVE_ARRAY_ITEM`: `{ section, field?, index | id }` -- resolve by index or by `id` field
- `UPDATE_ARRAY_ITEM`: `{ section, field?, index | id, data }` -- partial merge into matched item

## Minimal Inject Example

```json
{
  "action": "set",
  "state": {
    "taxReturn": {
      "id": "CA540-2024-DEMO001",
      "taxYear": 2024,
      "status": "in_progress",
      "createdAt": "2025-02-15T10:30:00.000Z",
      "updatedAt": "2025-02-15T10:30:00.000Z",
      "confirmationNumber": null
    },
    "personalInfo": {
      "filingStatus": "single",
      "firstName": "Maria",
      "middleInitial": "L",
      "lastName": "Santos",
      "suffix": "",
      "ssn": "592847163",
      "dateOfBirth": "1988-06-14",
      "spouseFirstName": "",
      "spouseMiddleInitial": "",
      "spouseLastName": "",
      "spouseSsn": "",
      "spouseDateOfBirth": "",
      "address": {
        "street": "2847 Oak Valley Drive",
        "apt": "Unit 12",
        "city": "San Jose",
        "state": "CA",
        "zip": "95128"
      },
      "phone": "(408) 555-3291",
      "email": "maria.santos@email.com"
    },
    "dependents": [],
    "income": {
      "w2s": [
        {
          "id": 1001,
          "employerName": "Bay Area Tech Solutions Inc",
          "employerEin": "94-3281756",
          "wages": "82500.00",
          "federalWithheld": "14200.00",
          "stateWages": "82500.00",
          "stateWithheld": "4950.00"
        }
      ],
      "interest1099": [
        {
          "id": 2001,
          "payerName": "Wells Fargo Bank",
          "amount": "342.50"
        }
      ],
      "dividend1099": [],
      "otherIncome": [],
      "federalAgi": "82500.00"
    },
    "deductions": {
      "type": "standard",
      "standardAmount": 5540,
      "itemized": {
        "medicalExpenses": 0,
        "stateLocalTaxes": 0,
        "mortgageInterest": 0,
        "charitableContributions": 0,
        "otherDeductions": 0
      },
      "caAdjustmentsSubtraction": 0,
      "caAdjustmentsAddition": 0,
      "voluntaryContributions": []
    },
    "credits": {
      "calEitc": { "eligible": false, "amount": 0 },
      "childDependentCare": { "eligible": false, "expenses": 0, "amount": 0 },
      "rentersCredit": { "eligible": true, "amount": 60 },
      "seniorHeadOfHousehold": { "eligible": false, "amount": 0 },
      "jointCustodyHeadOfHousehold": { "eligible": false, "amount": 0 },
      "dependentParent": { "eligible": false, "amount": 0 },
      "otherCredits": []
    },
    "calculations": {},
    "payment": {
      "refundMethod": "direct_deposit",
      "bankRoutingNumber": "",
      "bankAccountNumber": "",
      "accountType": "",
      "paymentMethod": "",
      "paymentDate": "",
      "estimatedPayments": "",
      "webPaySubmissions": []
    },
    "formProgress": {
      "currentStep": 1,
      "completedSteps": ["personal-info"],
      "stepErrors": {}
    },
    "ui": {
      "currentView": "filing",
      "showValidationErrors": false,
      "isSaving": false,
      "showConfirmDialog": false,
      "activeTooltip": null
    },
    "meta": {
      "lastSavedAt": null,
      "sessionExpiresAt": null
    }
  }
}
```

## Pre-filled State Example (married filing jointly with dependents)

```json
{
  "action": "set",
  "state": {
    "taxReturn": {
      "id": "CA540-2024-TASK042",
      "taxYear": 2024,
      "status": "in_progress",
      "createdAt": "2025-03-01T09:00:00.000Z",
      "updatedAt": "2025-03-01T09:15:00.000Z",
      "confirmationNumber": null
    },
    "personalInfo": {
      "filingStatus": "married_joint",
      "firstName": "James",
      "middleInitial": "R",
      "lastName": "Chen",
      "suffix": "",
      "ssn": "483921756",
      "dateOfBirth": "1985-03-22",
      "spouseFirstName": "Emily",
      "spouseMiddleInitial": "K",
      "spouseLastName": "Chen",
      "spouseSsn": "529841037",
      "spouseDateOfBirth": "1987-09-15",
      "address": {
        "street": "1520 Maple Avenue",
        "apt": "",
        "city": "Los Angeles",
        "state": "CA",
        "zip": "90025"
      },
      "phone": "(310) 555-8472",
      "email": "james.chen@example.com"
    },
    "dependents": [
      {
        "id": "dep001",
        "firstName": "Olivia",
        "lastName": "Chen",
        "ssn": "583920147",
        "relationship": "Daughter",
        "dateOfBirth": "2018-07-10",
        "monthsLived": 12
      },
      {
        "id": "dep002",
        "firstName": "Ethan",
        "lastName": "Chen",
        "ssn": "583920258",
        "relationship": "Son",
        "dateOfBirth": "2020-11-03",
        "monthsLived": 12
      }
    ],
    "income": {
      "w2s": [
        {
          "id": 1001,
          "employerName": "Pacific Engineering Corp",
          "employerEin": "95-4821367",
          "wages": "115000.00",
          "federalWithheld": "22500.00",
          "stateWages": "115000.00",
          "stateWithheld": "6900.00"
        },
        {
          "id": 1002,
          "employerName": "Westside Medical Group",
          "employerEin": "95-7623841",
          "wages": "78000.00",
          "federalWithheld": "13200.00",
          "stateWages": "78000.00",
          "stateWithheld": "4680.00"
        }
      ],
      "interest1099": [
        {
          "id": 2001,
          "payerName": "Chase Bank",
          "amount": "875.00"
        }
      ],
      "dividend1099": [
        {
          "id": 3001,
          "payerName": "Vanguard Total Stock Market Fund",
          "ordinaryDividends": "1250.00",
          "qualifiedDividends": "980.00"
        }
      ],
      "otherIncome": [],
      "federalAgi": "195125.00"
    },
    "deductions": {
      "type": "itemized",
      "standardAmount": 11080,
      "itemized": {
        "medicalExpenses": 0,
        "stateLocalTaxes": "10000.00",
        "mortgageInterest": "18500.00",
        "charitableContributions": "3200.00",
        "otherDeductions": 0
      },
      "caAdjustmentsSubtraction": 0,
      "caAdjustmentsAddition": 0,
      "voluntaryContributions": []
    },
    "credits": {
      "calEitc": { "eligible": false, "amount": 0 },
      "childDependentCare": { "eligible": true, "expenses": 6000, "amount": 3000 },
      "rentersCredit": { "eligible": false, "amount": 0 },
      "seniorHeadOfHousehold": { "eligible": false, "amount": 0 },
      "jointCustodyHeadOfHousehold": { "eligible": false, "amount": 0 },
      "dependentParent": { "eligible": false, "amount": 0 },
      "otherCredits": []
    },
    "payment": {
      "refundMethod": "direct_deposit",
      "bankRoutingNumber": "",
      "bankAccountNumber": "",
      "accountType": "",
      "paymentMethod": "",
      "paymentDate": "",
      "estimatedPayments": "",
      "webPaySubmissions": []
    },
    "formProgress": {
      "currentStep": 4,
      "completedSteps": ["personal-info", "dependents", "income"],
      "stepErrors": {}
    },
    "ui": {
      "currentView": "filing",
      "showValidationErrors": false,
      "isSaving": false,
      "showConfirmDialog": false,
      "activeTooltip": null
    },
    "meta": {
      "lastSavedAt": null,
      "sessionExpiresAt": null
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field(s) Changed |
|-------------|------------------------|
| Select filing status (e.g., "Married/RDP Filing Jointly") | `personalInfo.filingStatus` -> `"married_joint"`, `taxReturn.updatedAt` updated |
| Edit taxpayer first name | `personalInfo.firstName` set to entered value |
| Edit taxpayer SSN | `personalInfo.ssn` set to 9-digit string |
| Edit address city | `personalInfo.address.city` set to entered value |
| Edit spouse first name (married filers) | `personalInfo.spouseFirstName` set to entered value |
| Click "Add Dependent" | New item appended to `dependents[]` array |
| Fill dependent first name | `dependents[i].firstName` updated |
| Select dependent relationship | `dependents[i].relationship` updated |
| Remove a dependent | Item removed from `dependents[]` by id |
| Click "Add W-2" and fill employer name | New W-2 appended to `income.w2s[]`, `income.w2s[i].employerName` set |
| Edit W-2 wages | `income.w2s[i].wages` updated (string) |
| Click "Add 1099-INT" and fill amount | New item in `income.interest1099[]`, `.amount` set |
| Edit Federal AGI | `income.federalAgi` updated |
| Switch deduction type to "Itemized" | `deductions.type` -> `"itemized"` |
| Enter mortgage interest amount | `deductions.itemized.mortgageInterest` updated |
| Enter CA Subtractions amount | `deductions.caAdjustmentsSubtraction` updated |
| Check a voluntary contribution fund | New item added to `deductions.voluntaryContributions[]` |
| Enter voluntary contribution amount | `deductions.voluntaryContributions[i].amount` updated |
| Toggle CalEITC eligible | `credits.calEitc.eligible` toggled; `credits.calEitc.amount` updated |
| Toggle Renter's Credit eligible | `credits.rentersCredit.eligible` toggled; `credits.rentersCredit.amount` set to 60 or 120 (joint) or 0 |
| Enter child care expenses | `credits.childDependentCare.expenses` updated; `credits.childDependentCare.amount` = expenses * 0.5 |
| Add other credit | New item appended to `credits.otherCredits[]` |
| Click "Next" on a step (validation passes) | `formProgress.completedSteps` adds step ID; `formProgress.currentStep` incremented |
| Click "Next" on a step (validation fails) | `formProgress.stepErrors[stepId]` set to error array; `ui.showValidationErrors` -> `true` |
| Check e-signature declaration and click "Submit Return" | `taxReturn.status` -> `"submitted"`, `taxReturn.confirmationNumber` generated |
| Submit Web Pay payment | New entry appended to `payment.webPaySubmissions[]` |
| Send message via Help page | New entry appended to `ui.contactMessages[]` |
| Click "Start New Return" on confirmation page | All state reset to seed defaults (new `taxReturn.id` generated) |

## California Tax Calculation Details

The `calculateFinalTax()` function uses 2024 California tax brackets:

**Single / Married Filing Separately / Head of Household brackets:**
| Income Range | Rate |
|-------------|------|
| $0 - $10,412 | 1% |
| $10,413 - $24,684 | 2% |
| $24,685 - $38,959 | 4% |
| $38,960 - $54,081 | 6% |
| $54,082 - $68,350 | 8% |
| $68,351 - $349,137 | 9.3% |
| $349,138 - $418,961 | 10.3% |
| $418,962 - $698,271 | 11.3% |
| $698,272+ | 12.3% |

**Married Filing Jointly / Qualifying Widow(er) brackets** use double the single bracket amounts.

**Exemption credits**: $149 per taxpayer (+ $149 for spouse if joint) + $461 per dependent.

**Standard deductions**: Single=$5,540, Married Joint=$11,080, Married Separate=$5,540, Head of Household=$11,080, Qualifying Widow=$11,080.

## Notes

- All monetary values in income, deductions, and W-2 forms are stored as **strings** (e.g., `"82500.00"`), not numbers. They are parsed with `parseFloat()` for calculations.
- The `calculations` object is auto-recomputed on every state mutation. When injecting state, you can set `calculations: {}` and it will be recomputed automatically.
- The `taxReturn.updatedAt` timestamp is updated on most state mutations (UPDATE_SECTION, ADD/REMOVE/UPDATE_ARRAY_ITEM, SUBMIT_RETURN).
- The `taxReturn.status` transitions: `"draft"` -> `"in_progress"` (on first UPDATE_SECTION if was draft) -> `"submitted"` (on SUBMIT_RETURN).
- Voluntary contributions are subtracted from the refund amount. If contributions exceed the refund, the excess is added to the amount owed.
- The Forms page (`/forms`) and Account page (`/account`) include static mock data (prior returns, notices, messages) that is not part of the injected state.
- The `ui.contactMessages` field is only populated when users send messages via the Help page contact form. It is not present in the initial seed data.
