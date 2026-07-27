# california_tax_mock Schema

**Deploy order**: 6 (alphabetical among all *_mock dirs, BASE_PORT=8000 -> port 8006)
**Base URL**: `http://172.17.46.46:8006/`
**Go Endpoint**: `GET /go?sid=<sid>` -> `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` -> `{stored_state, has_custom_state, sid}`

## Application Overview

A mock of the **California Franchise Tax Board (FTB) CalFile** system -- California's free online tax filing portal for Form 540 (California Resident Income Tax Return). It features a multi-step form wizard for entering personal information, dependents, income, deductions, credits, tax summary review, and electronic filing with confirmation.

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | WelcomePage | Landing page with CalFile branding and "Start Filing" button |
| `/filing/personal-info` | PersonalInfoForm | Step 1: Filing status, taxpayer name/SSN/DOB/address, spouse info |
| `/filing/dependents` | DependentsList | Step 2: Add/remove/edit dependents |
| `/filing/income` | IncomeForm | Step 3: W-2s, 1099-INT, 1099-DIV, other income, federal AGI |
| `/filing/deductions` | DeductionsForm | Step 4: Standard vs itemized, CA adjustments, voluntary contributions |
| `/filing/credits` | CreditsForm | Step 5: CalEITC, child care, renter's credit, other CA credits |
| `/filing/tax-summary` | TaxSummaryView | Step 6: Calculated tax summary |
| `/filing/review` | ReviewPage | Step 7: Final review of all sections before submission |
| `/filing/confirmation` | ConfirmationPage | Step 8: Submission confirmation with confirmation number |
| `/pay` | PaymentPage | Payment method for amount owed |
| `/refund` | RefundPage | Refund method (direct deposit or paper check) |
| `/forms` | FormsPage | Available tax forms reference |
| `/help` | HelpPage | Help/FAQ page |
| `/account` | AccountPage | Account settings |
| `/coming-soon/:section` | ComingSoon | Placeholder for unimplemented features |
| `/go` | Go | State inspection endpoint (JSON) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `taxReturn` | object | Return metadata: `{id, taxYear, status, createdAt, updatedAt, confirmationNumber}` |
| `personalInfo` | object | Taxpayer personal details (see nested structure below) |
| `dependents` | array | List of dependent persons claimed on the return |
| `income` | object | All income sources: W-2s, 1099-INT, 1099-DIV, other income, federal AGI |
| `deductions` | object | Standard or itemized deductions, CA adjustments, voluntary contributions |
| `credits` | object | California tax credits (CalEITC, child care, renter's, etc.) |
| `calculations` | object | Computed tax figures (auto-calculated from other sections) |
| `payment` | object | Refund/payment method and banking details |
| `formProgress` | object | Multi-step form wizard state: `{currentStep, completedSteps[], stepErrors{}}` |
| `ui` | object | UI display flags: `{currentView, showValidationErrors, isSaving, showConfirmDialog, activeTooltip}` |
| `meta` | object | Session metadata: `{lastSavedAt, sessionExpiresAt}` |

### `taxReturn` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"CA540-2024-DEMO001"` | Unique return identifier |
| `taxYear` | number | `2024` | Tax year for this return |
| `status` | string | `"in_progress"` | Return status: `"draft"`, `"in_progress"`, `"submitted"` |
| `createdAt` | string (ISO) | `"2025-02-15T10:30:00.000Z"` | Creation timestamp |
| `updatedAt` | string (ISO) | `"2025-02-15T10:30:00.000Z"` | Last update timestamp (auto-updated on changes) |
| `confirmationNumber` | string\|null | `null` | Set on submission, format: `"CA-XXXXXX-XXXXXX"` |

### `personalInfo` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `filingStatus` | string | `"single"` | One of: `"single"`, `"married_joint"`, `"married_separate"`, `"head_of_household"`, `"qualifying_widow"` |
| `firstName` | string | `"Maria"` | Taxpayer first name |
| `middleInitial` | string | `"L"` | Middle initial |
| `lastName` | string | `"Santos"` | Last name |
| `suffix` | string | `""` | Name suffix: `""`, `"SR"`, `"JR"`, `"II"`, `"III"`, `"IV"` |
| `ssn` | string | `"592847163"` | Social Security Number (9 digits, no dashes) |
| `dateOfBirth` | string | `"1988-06-14"` | Date of birth (YYYY-MM-DD) |
| `spouseFirstName` | string | `""` | Spouse first name (used when filingStatus is married) |
| `spouseMiddleInitial` | string | `""` | Spouse middle initial |
| `spouseLastName` | string | `""` | Spouse last name |
| `spouseSsn` | string | `""` | Spouse SSN (9 digits) |
| `spouseDateOfBirth` | string | `""` | Spouse date of birth |
| `address` | object | (see below) | Mailing address |
| `phone` | string | `"(408) 555-3291"` | Phone number |
| `email` | string | `"maria.santos@email.com"` | Email address |

#### `personalInfo.address` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `street` | string | `"2847 Oak Valley Drive"` | Street address |
| `apt` | string | `"Unit 12"` | Apartment/suite number |
| `city` | string | `"San Jose"` | City |
| `state` | string | `"CA"` | State (always CA for CalFile) |
| `zip` | string | `"95128"` | ZIP code |

### `dependents` (array)

Each dependent item:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | (generated) | Unique ID (`Date.now().toString()`) |
| `firstName` | string | `""` | Dependent first name |
| `lastName` | string | `""` | Dependent last name |
| `ssn` | string | `""` | Dependent SSN (9 digits) |
| `relationship` | string | `""` | Relationship: `"Son"`, `"Daughter"`, `"Stepson"`, `"Stepdaughter"`, `"Foster child"`, `"Brother"`, `"Sister"`, `"Half brother"`, `"Half sister"`, `"Stepbrother"`, `"Stepsister"`, `"Grandchild"`, `"Niece"`, `"Nephew"`, `"Parent"`, `"Other"` |
| `dateOfBirth` | string | `""` | Date of birth (YYYY-MM-DD) |
| `monthsLived` | number | `12` | Months lived in home (0-12) |

Default seed: `[]` (empty array)

### `income` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `w2s` | array | (1 item, see below) | W-2 wage statements |
| `interest1099` | array | (1 item, see below) | 1099-INT interest income |
| `dividend1099` | array | `[]` | 1099-DIV dividend income |
| `otherIncome` | array | `[]` | Other income sources |
| `federalAgi` | string | `"82500.00"` | Federal Adjusted Gross Income |

#### `income.w2s[]` (W-2 item)

| Field | Type | Default (seed) | Description |
|-------|------|----------------|-------------|
| `id` | number | `1001` | Unique ID |
| `employerName` | string | `"Bay Area Tech Solutions Inc"` | Employer name |
| `employerEin` | string | `"94-3281756"` | Employer EIN |
| `wages` | string | `"82500.00"` | Total wages |
| `federalWithheld` | string | `"14200.00"` | Federal tax withheld |
| `stateWages` | string | `"82500.00"` | State wages |
| `stateWithheld` | string | `"4950.00"` | State tax withheld |

#### `income.interest1099[]` (1099-INT item)

| Field | Type | Default (seed) | Description |
|-------|------|----------------|-------------|
| `id` | number | `2001` | Unique ID |
| `payerName` | string | `"Wells Fargo Bank"` | Payer name |
| `amount` | string | `"342.50"` | Interest amount |

#### `income.dividend1099[]` (1099-DIV item)

| Field | Type | Description |
|-------|------|-------------|
| `id` | number\|string | Unique ID |
| `payerName` | string | Payer name |
| `ordinaryDividends` | string\|number | Ordinary dividends amount |
| `qualifiedDividends` | string\|number | Qualified dividends amount |

#### `income.otherIncome[]` (Other income item)

| Field | Type | Description |
|-------|------|-------------|
| `id` | number\|string | Unique ID |
| `description` | string | Income description |
| `amount` | string\|number | Income amount |

### `deductions` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | `"standard"` | `"standard"` or `"itemized"` |
| `standardAmount` | number | `5540` | Standard deduction amount (varies by filing status) |
| `itemized` | object | (see below) | Itemized deduction amounts |
| `caAdjustmentsSubtraction` | number | `0` | California adjustments (subtraction from income) |
| `caAdjustmentsAddition` | number | `0` | California adjustments (addition to income) |
| `voluntaryContributions` | array | `[]` | Voluntary contributions to CA state funds |

**Standard deduction amounts by filing status:**
- `single`: $5,540
- `married_joint`: $11,080
- `married_separate`: $5,540
- `head_of_household`: $11,080
- `qualifying_widow`: $11,080

#### `deductions.itemized` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `medicalExpenses` | number | `0` | Medical/dental expenses |
| `stateLocalTaxes` | number | `0` | State and local taxes paid |
| `mortgageInterest` | number | `0` | Home mortgage interest |
| `charitableContributions` | number | `0` | Charitable donations |
| `otherDeductions` | number | `0` | Other itemized deductions |

#### `deductions.voluntaryContributions[]` (Contribution item)

Available fund names: `"alzheimers"`, `"ca_seniors"`, `"firefighters"`, `"wildlife"`, `"local_homeless"`, `"domestic_violence"`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Fund identifier |
| `fundName` | string | Name of the fund |
| `amount` | number | Contribution amount |

### `credits` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `calEitc` | object | `{eligible: false, amount: 0}` | California Earned Income Tax Credit (up to $3,644) |
| `childDependentCare` | object | `{eligible: false, expenses: 0, amount: 0}` | Child/Dependent Care Credit (amount = 50% of expenses) |
| `rentersCredit` | object | `{eligible: true, amount: 60}` | Renter's Credit ($60 single / $120 joint) |
| `seniorHeadOfHousehold` | object | `{eligible: false, amount: 0}` | Senior Head of Household Credit |
| `jointCustodyHeadOfHousehold` | object | `{eligible: false, amount: 0}` | Joint Custody Head of Household Credit |
| `dependentParent` | object | `{eligible: false, amount: 0}` | Dependent Parent Credit |
| `otherCredits` | array | `[]` | Additional CA tax credits |

Each credit object has: `{ eligible: boolean, amount: number }`. The `childDependentCare` credit additionally has `expenses: number`.

#### `credits.otherCredits[]` (Other credit item)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID (`Date.now().toString()`) |
| `code` | string | Credit code (e.g., `"188"`) |
| `description` | string | Credit description |
| `amount` | number | Credit amount |

### `calculations` (object, auto-computed)

These values are automatically recalculated by `taxCalculator.js` whenever state changes. California uses progressive tax brackets.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `totalIncome` | number | `0` | Sum of all income sources |
| `taxableIncome` | number | `0` | Income after deductions and adjustments |
| `taxBeforeCredits` | number | `0` | Tax calculated from CA progressive brackets |
| `totalCredits` | number | `0` | Sum of all claimed credits |
| `netTax` | number | `0` | Tax after credits applied |
| `totalPayments` | number | `0` | Total withholdings and estimated payments |
| `refundAmount` | number | `0` | Overpayment (if totalPayments > netTax) |
| `amountOwed` | number | `0` | Underpayment (if netTax > totalPayments) |
| `totalDeductions` | number | `0` | Total deductions applied |
| `effectiveTaxRate` | number | `0` | Effective tax rate (percentage) |
| `marginalTaxRate` | number | `0` | Marginal tax bracket rate (percentage) |

### `payment` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `refundMethod` | string | `"direct_deposit"` | `"direct_deposit"` or `"paper_check"` |
| `bankRoutingNumber` | string | `""` | Bank routing number (for direct deposit) |
| `bankAccountNumber` | string | `""` | Bank account number (for direct deposit) |
| `accountType` | string | `""` | `"checking"` or `"savings"` |
| `paymentMethod` | string | `""` | `"electronic"`, `"check"`, or `""` |
| `paymentDate` | string | `""` | Scheduled payment date |
| `estimatedPayments` | string | `""` | Estimated tax payments already made |
| `webPaySubmissions` | array | `[]` | Web Pay submission records |

### `formProgress` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `currentStep` | number | `1` | Current active step (1-8) |
| `completedSteps` | array | `["personal-info"]` | Step IDs that have been completed |
| `stepErrors` | object | `{}` | Validation errors by step ID, e.g., `{"personal-info": ["First name is required"]}` |

**Step IDs (correspond to filing routes):**
1. `personal-info`
2. `dependents`
3. `income`
4. `deductions`
5. `credits`
6. `tax-summary`
7. `review`
8. `confirmation`

### `ui` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `currentView` | string | `"filing"` | Current view mode |
| `showValidationErrors` | boolean | `false` | Whether to show inline validation errors |
| `isSaving` | boolean | `false` | Whether state is currently being saved |
| `showConfirmDialog` | boolean | `false` | Whether the submission confirm dialog is visible |
| `activeTooltip` | string\|null | `null` | Currently active tooltip ID |

### `meta` (object)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `lastSavedAt` | string\|null | `null` | ISO timestamp of last save |
| `sessionExpiresAt` | string\|null | `null` | ISO timestamp of session expiration |

## Dispatch Actions

| Action Type | Payload | Description |
|-------------|---------|-------------|
| `SET_STATE` | `{...full state}` | Replace entire state (used on initialization) |
| `UPDATE_SECTION` | `{section, data}` | Merge data into a top-level state section |
| `ADD_ARRAY_ITEM` | `{section, field?, item}` | Add item to array (e.g., section=`"dependents"`, item=`{...}` or section=`"income"`, field=`"w2s"`, item=`{...}`) |
| `REMOVE_ARRAY_ITEM` | `{section, field?, id\|index}` | Remove item from array by id or index |
| `UPDATE_ARRAY_ITEM` | `{section, field?, id\|index, data}` | Merge data into specific array item |
| `SUBMIT_RETURN` | (none) | Sets `taxReturn.status` to `"submitted"`, generates `confirmationNumber` |
| `RESET_STATE` / `RESET_RETURN` | (none) | Reset to seed data with new return ID |
| `SET_STEP` | step number | Set `formProgress.currentStep` |
| `COMPLETE_STEP` | step ID string | Add step to `formProgress.completedSteps` |
| `SET_STEP_ERRORS` | `{step, errors}` | Set validation errors for a specific step |
| `UPDATE_UI` | `{...ui fields}` | Merge into `ui` state object |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8006/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "taxReturn": {
          "id": "CA540-2024-TEST001",
          "taxYear": 2024,
          "status": "in_progress",
          "createdAt": "2025-02-15T10:30:00.000Z",
          "updatedAt": "2025-02-15T10:30:00.000Z",
          "confirmationNumber": null
        },
        "personalInfo": {
          "filingStatus": "married_joint",
          "firstName": "John",
          "middleInitial": "A",
          "lastName": "Doe",
          "suffix": "",
          "ssn": "123456789",
          "dateOfBirth": "1985-03-15",
          "spouseFirstName": "Jane",
          "spouseMiddleInitial": "B",
          "spouseLastName": "Doe",
          "spouseSsn": "987654321",
          "spouseDateOfBirth": "1987-07-22",
          "address": {
            "street": "456 Main Street",
            "apt": "",
            "city": "Los Angeles",
            "state": "CA",
            "zip": "90001"
          },
          "phone": "(310) 555-1234",
          "email": "john.doe@email.com"
        },
        "dependents": [
          {
            "id": "dep1",
            "firstName": "Emily",
            "lastName": "Doe",
            "ssn": "111223333",
            "relationship": "Daughter",
            "dateOfBirth": "2015-09-10",
            "monthsLived": 12
          }
        ],
        "income": {
          "w2s": [
            {
              "id": 1001,
              "employerName": "Acme Corp",
              "employerEin": "12-3456789",
              "wages": "95000.00",
              "federalWithheld": "16500.00",
              "stateWages": "95000.00",
              "stateWithheld": "5700.00"
            }
          ],
          "interest1099": [],
          "dividend1099": [],
          "otherIncome": [],
          "federalAgi": "95000.00"
        },
        "deductions": {
          "type": "standard",
          "standardAmount": 11080,
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
          "childDependentCare": { "eligible": true, "expenses": 6000, "amount": 3000 },
          "rentersCredit": { "eligible": false, "amount": 0 },
          "seniorHeadOfHousehold": { "eligible": false, "amount": 0 },
          "jointCustodyHeadOfHousehold": { "eligible": false, "amount": 0 },
          "dependentParent": { "eligible": false, "amount": 0 },
          "otherCredits": []
        },
        "payment": {
          "refundMethod": "direct_deposit",
          "bankRoutingNumber": "121000358",
          "bankAccountNumber": "1234567890",
          "accountType": "checking",
          "paymentMethod": "",
          "paymentDate": "",
          "estimatedPayments": "",
          "webPaySubmissions": []
        },
        "formProgress": {
          "currentStep": 1,
          "completedSteps": [],
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
  }
}
```

## Key Behaviors

1. **Auto-calculation**: Tax calculations (`calculations` object) are automatically recomputed on every state change via `taxCalculator.js`. CA uses progressive tax brackets.
2. **Auto-save**: State is persisted to localStorage and synced to the server via `POST /post` on every state change.
3. **Multi-step validation**: Each step can have validation errors stored in `formProgress.stepErrors`.
4. **Renter's credit auto-amount**: When `rentersCredit.eligible` is toggled on, amount is auto-set to $60 (single) or $120 (married_joint).
5. **Child care credit**: Amount is auto-calculated as 50% of expenses.
6. **Standard deduction amounts**: Automatically set based on filing status when switching between standard/itemized.
7. **Submission flow**: `SUBMIT_RETURN` action sets `taxReturn.status` to `"submitted"` and generates a `confirmationNumber`.
8. **Deep merge on inject**: Custom state provided via POST is deep-merged with seed data defaults, so partial state injection is supported.

## Default Seed IDs

- **Tax Return ID**: `CA540-2024-DEMO001`
- **W-2 ID**: `1001` (Bay Area Tech Solutions Inc)
- **1099-INT ID**: `2001` (Wells Fargo Bank)
- **Filing Status**: `single` (Maria L Santos)
