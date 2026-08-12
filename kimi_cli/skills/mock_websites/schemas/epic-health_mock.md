# epic-health_mock Schema

**Deploy order**: 12 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8012)
**Base URL**: `http://172.17.46.46:8012/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**State endpoint**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## Routes

| Path | Page Component | Description |
|------|----------------|-------------|
| `/` | Home | Dashboard with upcoming appointments, unread messages, new test results, care team |
| `/visits` | Visits | All appointments (upcoming + past) |
| `/visits/:id` | VisitDetail | Appointment detail with check-in, cancel, after-visit summary |
| `/schedule` | ScheduleAppointment | 4-step scheduling wizard (reason → provider → date/time → confirm) |
| `/messages` | Messages | Inbox/Sent/Archived message threads |
| `/messages/compose` | ComposeMessage | New message to provider |
| `/messages/:threadId` | MessageThread | Thread view (delegates to Messages) |
| `/test-results` | TestResults | Lab and test results list |
| `/test-results/:id` | TestResultDetail | Individual test result with observations |
| `/medications` | Medications | Active and discontinued medications |
| `/medications/:id` | MedicationDetail | Single medication details |
| `/medications/refill` | MedicationRefill | Request refill for active medications |
| `/health-summary` | HealthSummary | Conditions, allergies, immunizations, vitals |
| `/billing` | Billing | Billing statements list |
| `/billing/:id` | BillingDetail | Statement line items |
| `/billing/pay` | PayBill | Payment form for outstanding bills |
| `/insurance` | Insurance | Insurance plan details |
| `/preventive-care` | PreventiveCare | Preventive care items and due dates |
| `/care-team` | CareTeam | Provider directory |
| `/settings` | Settings | Personal info, communication preferences, language |
| `/go` | Go | State inspection endpoint |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Patient profile (see CurrentUser fields below) |
| `providers` | array | Healthcare providers / care team (see Provider fields) |
| `appointments` | array | Past and upcoming appointments (see Appointment fields) |
| `messages` | array | All messages across all folders/threads (see Message fields) |
| `testResults` | array | Lab/test result records (see TestResult fields) |
| `medications` | array | Active and discontinued medications (see Medication fields) |
| `conditions` | array | Medical conditions / diagnoses (see Condition fields) |
| `allergies` | array | Allergy records (see Allergy fields) |
| `immunizations` | array | Vaccination records (see Immunization fields) |
| `vitals` | array | Vital signs history (see Vitals fields) |
| `billingStatements` | array | Billing statements with line items (see BillingStatement fields) |
| `insurance` | array | Insurance plan info (see Insurance fields) |
| `preventiveCare` | array | Preventive care items and due dates (see PreventiveCare fields) |
| `ui` | object | UI state: active section, selections, notifications (see UI fields) |

---

### CurrentUser Object

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `id` | string | `"patient-1"` | Unique patient ID |
| `firstName` | string | `"Sarah"` | |
| `lastName` | string | `"Chen"` | |
| `fullName` | string | `"Sarah Chen"` | |
| `dateOfBirth` | string | `"1989-07-15"` | ISO date |
| `age` | number | `35` | |
| `gender` | string | `"Female"` | |
| `email` | string | `"sarah.chen@email.com"` | Editable via Settings |
| `phone` | string | `"(555) 234-5678"` | Editable via Settings |
| `address` | object | `{street, city, state, zip}` | Full address object |
| `emergencyContact` | object | `{name, relationship, phone}` | |
| `preferredLanguage` | string | `"English"` | |
| `preferredPharmacy` | object | `{name, address, phone}` | |
| `avatarInitials` | string | `"SC"` | |
| `avatarColor` | string | `"#0075BC"` | Hex color for avatar background |

### Provider Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"provider-1"` through `"provider-5"` |
| `firstName` | string | |
| `lastName` | string | |
| `fullName` | string | Includes title, e.g. `"Elizabeth Morrison, MD"` |
| `title` | string | `"MD"`, `"DDS"`, or `""` |
| `specialty` | string | e.g. `"Family Medicine"`, `"Cardiology"`, `"Dermatology"`, `"Dentistry"` |
| `role` | string | e.g. `"Primary Care Provider"`, `"Referring Physician"`, `"Specialist"`, `"Care Team"` |
| `department` | string | |
| `phone` | string | |
| `email` | string | |
| `location` | string | Facility name |
| `address` | string | Facility address |
| `avatarInitials` | string | |
| `avatarColor` | string | Hex color |
| `imageUrl` | string\|null | Always `null` in default data |

### Default Providers

| ID | Name | Specialty | Role |
|----|------|-----------|------|
| `provider-1` | Elizabeth Morrison, MD | Family Medicine | Primary Care Provider |
| `provider-2` | James Park, MD | Cardiology | Referring Physician |
| `provider-3` | Priya Sharma, MD | Dermatology | Specialist |
| `provider-4` | Michael Torres, DDS | Dentistry | Dentist |
| `provider-5` | Nursing Staff | Family Medicine | Care Team |

### Appointment Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"appt-1"` through `"appt-6"`, new ones use `"appt-new-{timestamp}"` |
| `patientId` | string | Always `"patient-1"` |
| `providerId` | string | References a provider ID |
| `providerName` | string | e.g. `"Elizabeth Morrison, MD"` |
| `type` | string | `"Annual Physical"`, `"Follow Up"`, `"Office Visit"` |
| `status` | string | `"Scheduled"`, `"Completed"`, `"Cancelled"`, `"Checked In"` |
| `dateTime` | string | ISO 8601 datetime |
| `duration` | number | Minutes (30 or 60) |
| `location` | string | Facility name |
| `address` | string | Facility address |
| `department` | string | |
| `reason` | string | Reason for visit |
| `instructions` | string | Pre-visit instructions (for upcoming) |
| `isUpcoming` | boolean | `true` for future appointments |
| `canCheckIn` | boolean | Enables e-check-in flow |
| `canCancel` | boolean | Enables cancel action |
| `canReschedule` | boolean | Enables reschedule action |
| `afterVisitSummary` | object\|null | For completed visits: `{diagnoses: string[], medications: string[], followUp: string, providerNotes: string}` |
| `questionnairesRequired` | array | Pre-visit questionnaire IDs |
| `notes` | string | Visit notes |

### Default Appointments

| ID | Type | Status | Provider | Date |
|----|------|--------|----------|------|
| `appt-1` | Annual Physical | Scheduled | provider-1 | 2025-04-15 (canCheckIn: true) |
| `appt-2` | Follow Up | Scheduled | provider-2 | 2025-04-28 |
| `appt-3` | Office Visit | Scheduled | provider-3 | 2025-05-10 |
| `appt-4` | Office Visit | Completed | provider-1 | 2025-03-01 (has afterVisitSummary) |
| `appt-5` | Follow Up | Completed | provider-2 | 2025-01-15 (has afterVisitSummary) |
| `appt-6` | Annual Physical | Completed | provider-1 | 2024-11-20 (has afterVisitSummary) |

### Message Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"msg-1"` through `"msg-8"`, new ones use `"msg-new-{timestamp}"` or `"msg-reply-{timestamp}"` |
| `threadId` | string | Groups messages into conversation threads, e.g. `"thread-1"` |
| `parentId` | string\|null | ID of the message being replied to; `null` for first message in thread |
| `from` | object | `{id: string, name: string, type: "patient"\|"provider"\|"care-team"}` |
| `to` | object | `{id: string, name: string, type: "patient"\|"provider"}` |
| `subject` | string | |
| `body` | string | Message content, may contain newlines |
| `date` | string | ISO 8601 datetime |
| `isRead` | boolean | Read status |
| `isStarred` | boolean | Starred flag |
| `folder` | string | `"inbox"`, `"sent"`, or `"archived"` |
| `hasAttachment` | boolean | |
| `attachments` | array | Attachment objects (empty in defaults) |
| `isUrgent` | boolean | Urgent flag |

### Default Message Threads

| Thread ID | Subject | Participants | Messages |
|-----------|---------|-------------|----------|
| `thread-1` | Your Recent Lab Results | Dr. Morrison <-> Sarah Chen | msg-1 (unread, inbox), msg-2 (sent) |
| `thread-2` | Appointment Reminder — April 15 | Nursing Staff -> Sarah Chen | msg-3 (unread, inbox) |
| `thread-3` | Prescription Renewal Confirmation | Dr. Morrison -> Sarah Chen | msg-4 (read, inbox) |
| `thread-4` | Question About Medication Side Effects | Sarah Chen <-> Dr. Morrison | msg-5 (sent), msg-6 (read, inbox), msg-7 (sent) |
| `thread-5` | Follow-up question about diet | Sarah Chen -> Dr. Morrison | msg-8 (sent) |

### TestResult Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"test-1"` through `"test-5"` |
| `patientId` | string | Always `"patient-1"` |
| `orderedBy` | string | Provider name |
| `orderedById` | string | Provider ID |
| `testName` | string | e.g. `"Comprehensive Metabolic Panel"`, `"Lipid Panel"` |
| `category` | string | `"Lab"` |
| `orderedDate` | string | ISO date |
| `collectedDate` | string | ISO datetime |
| `resultDate` | string | ISO datetime |
| `status` | string | `"Final"` |
| `isReviewed` | boolean | Whether the patient has reviewed the result |
| `providerComment` | string | Doctor's interpretation |
| `observations` | array | Individual test observations (see Observation fields) |

### Observation Object (nested in TestResult)

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"obs-1-1"` |
| `name` | string | Test name, e.g. `"Glucose"`, `"LDL Cholesterol"` |
| `value` | string | Numeric value as string |
| `unit` | string | e.g. `"mg/dL"`, `"mEq/L"`, `"%"` |
| `referenceRange` | string | Normal range, e.g. `"70-100"`, `"<200"` |
| `status` | string | `"Normal"` or `"High"` |
| `flag` | string\|null | `null` for normal, `"H"` for high |

### Default Test Results

| ID | Test Name | Date | isReviewed | Notable |
|----|-----------|------|------------|---------|
| `test-1` | Comprehensive Metabolic Panel | 2025-03-01 | true | All normal |
| `test-2` | Lipid Panel | 2025-03-01 | false | LDL elevated (132, flag: "H") |
| `test-3` | Complete Blood Count (CBC) | 2025-03-01 | true | All normal |
| `test-4` | Hemoglobin A1c | 2025-01-15 | true | 6.8% (improved) |
| `test-5` | Thyroid Panel (TSH, T3, T4) | 2025-01-15 | true | All normal |

### Medication Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"med-1"` through `"med-6"` |
| `patientId` | string | Always `"patient-1"` |
| `name` | string | Brand/common name |
| `genericName` | string | Generic drug name |
| `dosage` | string | e.g. `"10 mg"`, `"500 mg"` |
| `form` | string | `"Tablet"` or `"Capsule"` |
| `frequency` | string | e.g. `"Once daily"`, `"Twice daily with meals"` |
| `route` | string | `"Oral"` |
| `instructions` | string | Full dosing instructions |
| `prescriber` | string | Provider name |
| `prescriberId` | string | Provider ID |
| `pharmacy` | string | Pharmacy name |
| `status` | string | `"Active"` or `"Discontinued"` |
| `startDate` | string | ISO date |
| `endDate` | string\|null | ISO date or `null` for active meds |
| `lastFilledDate` | string | ISO date |
| `refillsRemaining` | number | Updated by REQUEST_REFILL action |
| `totalRefills` | number | Total refills on prescription |
| `isRefillable` | boolean | Whether refill can be requested |
| `daysSupply` | number | Days per fill |
| `quantity` | number | Number of pills/capsules per fill |
| `reason` | string | Indication / condition |

### Default Medications

| ID | Name | Dosage | Status | Reason |
|----|------|--------|--------|--------|
| `med-1` | Lisinopril | 10 mg | Active | Hypertension |
| `med-2` | Atorvastatin | 20 mg | Active | Hyperlipidemia |
| `med-3` | Metformin | 500 mg | Active | Type 2 Diabetes Mellitus |
| `med-4` | Vitamin D3 | 2000 IU | Active | Vitamin D Deficiency |
| `med-5` | Amoxicillin | 500 mg | Discontinued | Respiratory Infection |
| `med-6` | Prednisone | 10 mg | Discontinued | Severe Allergic Reaction |

### Condition Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"cond-1"` through `"cond-4"` |
| `patientId` | string | Always `"patient-1"` |
| `name` | string | Condition name |
| `icdCode` | string | ICD-10 code |
| `clinicalStatus` | string | `"Active"` |
| `severity` | string | `"Mild"` |
| `onsetDate` | string | ISO date |
| `diagnosedBy` | string | Provider name |
| `notes` | string | Clinical notes |

### Default Conditions

| ID | Name | ICD Code |
|----|------|----------|
| `cond-1` | Essential Hypertension | I10 |
| `cond-2` | Type 2 Diabetes Mellitus | E11 |
| `cond-3` | Hyperlipidemia | E78.5 |
| `cond-4` | Seasonal Allergies | J30.1 |

### Allergy Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"allergy-1"` through `"allergy-3"` |
| `patientId` | string | Always `"patient-1"` |
| `allergen` | string | Substance name |
| `type` | string | `"Medication"`, `"Food"`, or `"Environmental"` |
| `reaction` | string | Reaction description |
| `severity` | string | `"Mild"`, `"Moderate"`, or `"Severe"` |
| `status` | string | `"Active"` |
| `onsetDate` | string | ISO date |
| `notes` | string | |

### Default Allergies

| ID | Allergen | Type | Severity |
|----|----------|------|----------|
| `allergy-1` | Penicillin | Medication | Moderate |
| `allergy-2` | Peanuts | Food | Severe |
| `allergy-3` | Latex | Environmental | Mild |

### Immunization Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"imm-1"` through `"imm-6"` |
| `patientId` | string | Always `"patient-1"` |
| `vaccineName` | string | |
| `vaccineCode` | string | CVX code |
| `administrationDate` | string | ISO date |
| `site` | string | Injection site, e.g. `"Left Deltoid"` |
| `administrator` | string | Facility name |
| `lotNumber` | string | Vaccine lot number |
| `status` | string | `"Completed"` |
| `nextDueDate` | string\|null | ISO date or `null` |

### Default Immunizations

| ID | Vaccine | Date | Next Due |
|----|---------|------|----------|
| `imm-1` | Influenza (Flu) | 2024-10-15 | 2025-10-01 |
| `imm-2` | COVID-19 Booster (Moderna) | 2024-09-20 | null |
| `imm-3` | Tdap | 2022-05-10 | 2032-05-10 |
| `imm-4` | Hepatitis B (Dose 3 of 3) | 2019-03-01 | null |
| `imm-5` | MMR | 1991-07-15 | null |
| `imm-6` | Varicella | 1993-02-20 | null |

### Vitals Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"vital-1"` through `"vital-3"` |
| `patientId` | string | Always `"patient-1"` |
| `date` | string | ISO date |
| `readings` | object | See Vital Readings below |
| `recordedBy` | string | e.g. `"Nursing Staff"` |
| `location` | string | Facility name |

### Vital Readings Object (nested in Vitals)

| Field | Type | Notes |
|-------|------|-------|
| `bloodPressureSystolic` | object | `{value: number, unit: "mmHg"}` |
| `bloodPressureDiastolic` | object | `{value: number, unit: "mmHg"}` |
| `heartRate` | object | `{value: number, unit: "bpm"}` |
| `temperature` | object | `{value: number, unit: "°F"}` |
| `respiratoryRate` | object | `{value: number, unit: "breaths/min"}` |
| `weight` | object | `{value: number, unit: "lbs"}` |
| `height` | object | `{value: number, unit: "in"}` |
| `bmi` | object | `{value: number, unit: "kg/m²"}` |
| `oxygenSaturation` | object | `{value: number, unit: "%"}` |

### BillingStatement Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"bill-1"` through `"bill-3"` |
| `patientId` | string | Always `"patient-1"` |
| `statementDate` | string | ISO date |
| `dueDate` | string | ISO date |
| `totalAmount` | number | Dollar amount |
| `insurancePaid` | number | Amount insurance paid |
| `patientResponsibility` | number | Amount patient owes |
| `amountPaid` | number | Amount already paid (updated by PAY_BILL) |
| `balanceDue` | number | Remaining balance (updated by PAY_BILL) |
| `status` | string | `"Due"` or `"Paid"` (auto-set to `"Paid"` when balanceDue reaches 0) |
| `lineItems` | array | Service line items (see LineItem fields) |

### LineItem Object (nested in BillingStatement)

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"item-1-1"` |
| `serviceDate` | string | ISO date |
| `description` | string | Service description |
| `cptCode` | string | CPT billing code |
| `provider` | string | Provider or facility name |
| `chargedAmount` | number | |
| `insuranceAdjustment` | number | Negative value |
| `insurancePaid` | number | Negative value |
| `patientResponsibility` | number | |

### Default Billing Statements

| ID | Date | Balance Due | Status |
|----|------|-------------|--------|
| `bill-1` | 2025-03-10 | $245.00 | Due |
| `bill-2` | 2025-02-01 | $0.00 | Paid |
| `bill-3` | 2024-12-15 | $0.00 | Paid |

### Insurance Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | `"ins-1"` |
| `patientId` | string | Always `"patient-1"` |
| `planName` | string | `"Blue Cross Blue Shield PPO"` |
| `planType` | string | `"PPO"` |
| `memberId` | string | `"XYZ123456789"` |
| `groupNumber` | string | `"GRP-98765"` |
| `subscriberName` | string | `"Sarah Chen"` |
| `relationship` | string | `"Self"` |
| `effectiveDate` | string | `"2024-01-01"` |
| `copay` | object | `{primaryCare: 25, specialist: 50, urgentCare: 75, emergency: 250}` |
| `deductible` | object | `{individual: 1500, family: 3000, metAmount: 825}` |
| `outOfPocketMax` | object | `{individual: 6000, family: 12000, metAmount: 1200}` |
| `contactPhone` | string | `"1-800-555-BCBS"` |
| `isActive` | boolean | `true` |

### PreventiveCare Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | e.g. `"prev-1"` through `"prev-6"` |
| `patientId` | string | Always `"patient-1"` |
| `name` | string | Care item name |
| `category` | string | `"Immunization"`, `"Screening"`, or `"Exam"` |
| `status` | string | `"Completed"`, `"Due"`, `"Overdue"`, or `"Not Applicable"` |
| `lastCompleted` | string\|null | ISO date |
| `nextDue` | string\|null | ISO date |
| `frequency` | string | e.g. `"Annually"`, `"Every 6 months"` |
| `notes` | string | |

### Default Preventive Care

| ID | Name | Status |
|----|------|--------|
| `prev-1` | Annual Flu Vaccination | Completed |
| `prev-2` | Mammogram | Due |
| `prev-3` | Colonoscopy | Not Applicable |
| `prev-4` | Annual Physical Exam | Due |
| `prev-5` | Eye Exam | Due |
| `prev-6` | Dental Cleaning | Overdue |

### UI Object

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `activeSection` | string | `"home"` | Current navigation section |
| `selectedAppointment` | string\|null | `null` | Selected appointment ID |
| `selectedMessage` | string\|null | `null` | Selected message ID |
| `selectedTestResult` | string\|null | `null` | Selected test result ID |
| `selectedMedication` | string\|null | `null` | Selected medication ID |
| `selectedBill` | string\|null | `null` | Selected billing statement ID |
| `sideMenuOpen` | boolean | `false` | Whether sidebar menu is open |
| `messageComposerOpen` | boolean | `false` | Whether message composer is open |
| `schedulingFlowStep` | number\|null | `null` | Current step in scheduling wizard |
| `refillSelections` | array | `[]` | Selected medication IDs for refill |
| `unreadMessageCount` | number | `2` | Count of unread inbox messages |
| `notificationBanners` | array | See below | Dismissible notification banners |

### Default Notification Banners

| ID | Type | Text | Dismissed |
|----|------|------|-----------|
| `notif-1` | `appointment` | `"Upcoming: Annual Physical on Apr 15 at 9:30 AM"` | `false` |
| `notif-2` | `result` | `"New test results available from Mar 1"` | `false` |

---

## Reducer Actions (State Mutations)

| Action Type | Payload | Effect |
|-------------|---------|--------|
| `SET_STATE` | `{...fullState}` | Replace entire state |
| `TOGGLE_SIDEBAR` | (none) | Toggle `ui.sideMenuOpen` |
| `CLOSE_SIDEBAR` | (none) | Set `ui.sideMenuOpen` to `false` |
| `SET_ACTIVE_SECTION` | `string` | Set `ui.activeSection` |
| `DISMISS_NOTIFICATION` | `notificationId` | Set `notificationBanners[i].dismissed = true` |
| `ADD_MESSAGE` | message object | Append to `messages` array; increment `ui.unreadMessageCount` if inbox + unread |
| `MARK_MESSAGE_READ` | `{threadId}` | Mark all messages in thread as `isRead: true`; recalculate `ui.unreadMessageCount` |
| `MARK_MESSAGE_UNREAD` | `{messageId}` | Mark specific message as `isRead: false`; recalculate `ui.unreadMessageCount` |
| `ARCHIVE_THREAD` | `threadId` | Move all messages in thread to `folder: "archived"`; recalculate `ui.unreadMessageCount` |
| `UPDATE_APPOINTMENT` | `{id, ...fields}` | Merge fields into matching appointment |
| `CANCEL_APPOINTMENT` | `{id}` | Set appointment `status: "Cancelled"`, `isUpcoming: false`, `canCheckIn/canCancel: false` |
| `SCHEDULE_APPOINTMENT` | appointment object | Append new appointment to `appointments` array |
| `UPDATE_MEDICATION` | `{id, ...fields}` | Merge fields into matching medication |
| `REQUEST_REFILL` | `{medicationIds: string[]}` | Update `lastFilledDate` to today, decrement `refillsRemaining` for each selected medication |
| `PAY_BILL` | `{billId, amount}` | Increase `amountPaid`, decrease `balanceDue`; set `status: "Paid"` if balance reaches 0 |
| `UPDATE_PATIENT_INFO` | `{...fields}` | Merge fields into `currentUser` (e.g. phone, email) |

---

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8012/",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "patient-1",
          "firstName": "Sarah",
          "lastName": "Chen",
          "fullName": "Sarah Chen",
          "dateOfBirth": "1989-07-15",
          "age": 35,
          "gender": "Female",
          "email": "sarah.chen@email.com",
          "phone": "(555) 234-5678",
          "address": {"street": "742 Evergreen Terrace", "city": "Springfield", "state": "IL", "zip": "62704"},
          "emergencyContact": {"name": "David Chen", "relationship": "Spouse", "phone": "(555) 234-5679"},
          "preferredLanguage": "English",
          "preferredPharmacy": {"name": "CVS Pharmacy #4521", "address": "100 Main St, Springfield, IL 62701", "phone": "(555) 100-2000"},
          "avatarInitials": "SC",
          "avatarColor": "#0075BC"
        },
        "providers": [
          {
            "id": "provider-1",
            "firstName": "Elizabeth",
            "lastName": "Morrison",
            "fullName": "Elizabeth Morrison, MD",
            "title": "MD",
            "specialty": "Family Medicine",
            "role": "Primary Care Provider",
            "department": "Family Medicine",
            "phone": "(555) 800-1234",
            "email": "e.morrison@springfieldhealth.org",
            "location": "Springfield Health Center — Main Campus",
            "address": "500 Medical Dr, Springfield, IL 62704",
            "avatarInitials": "EM",
            "avatarColor": "#4CAF50",
            "imageUrl": null
          }
        ],
        "appointments": [
          {
            "id": "appt-1",
            "patientId": "patient-1",
            "providerId": "provider-1",
            "providerName": "Elizabeth Morrison, MD",
            "type": "Annual Physical",
            "status": "Scheduled",
            "dateTime": "2025-04-15T09:30:00",
            "duration": 60,
            "location": "Springfield Health Center — Main Campus",
            "address": "500 Medical Dr, Springfield, IL 62704",
            "department": "Family Medicine",
            "reason": "Annual Physical Exam",
            "instructions": "Please fast for 12 hours before your appointment.",
            "isUpcoming": true,
            "canCheckIn": true,
            "canCancel": true,
            "canReschedule": true,
            "afterVisitSummary": null,
            "questionnairesRequired": [],
            "notes": ""
          }
        ],
        "messages": [
          {
            "id": "msg-1",
            "threadId": "thread-1",
            "parentId": null,
            "from": {"id": "provider-1", "name": "Elizabeth Morrison, MD", "type": "provider"},
            "to": {"id": "patient-1", "name": "Sarah Chen", "type": "patient"},
            "subject": "Your Recent Lab Results",
            "body": "Hi Sarah, your lab work looks great overall.",
            "date": "2025-03-08T14:23:00",
            "isRead": false,
            "isStarred": false,
            "folder": "inbox",
            "hasAttachment": false,
            "attachments": [],
            "isUrgent": false
          }
        ],
        "testResults": [],
        "medications": [
          {
            "id": "med-1",
            "patientId": "patient-1",
            "name": "Lisinopril",
            "genericName": "Lisinopril",
            "dosage": "10 mg",
            "form": "Tablet",
            "frequency": "Once daily",
            "route": "Oral",
            "instructions": "Take one tablet by mouth once daily in the morning.",
            "prescriber": "Elizabeth Morrison, MD",
            "prescriberId": "provider-1",
            "pharmacy": "CVS Pharmacy #4521",
            "status": "Active",
            "startDate": "2024-06-15",
            "endDate": null,
            "lastFilledDate": "2025-02-20",
            "refillsRemaining": 3,
            "totalRefills": 5,
            "isRefillable": true,
            "daysSupply": 30,
            "quantity": 30,
            "reason": "Hypertension"
          }
        ],
        "conditions": [],
        "allergies": [],
        "immunizations": [],
        "vitals": [],
        "billingStatements": [
          {
            "id": "bill-1",
            "patientId": "patient-1",
            "statementDate": "2025-03-10",
            "dueDate": "2025-04-10",
            "totalAmount": 245.00,
            "insurancePaid": 680.00,
            "patientResponsibility": 245.00,
            "amountPaid": 0,
            "balanceDue": 245.00,
            "status": "Due",
            "lineItems": []
          }
        ],
        "insurance": [],
        "preventiveCare": [],
        "ui": {
          "activeSection": "home",
          "selectedAppointment": null,
          "selectedMessage": null,
          "selectedTestResult": null,
          "selectedMedication": null,
          "selectedBill": null,
          "sideMenuOpen": false,
          "messageComposerOpen": false,
          "schedulingFlowStep": null,
          "refillSelections": [],
          "unreadMessageCount": 1,
          "notificationBanners": [
            {"id": "notif-1", "type": "appointment", "text": "Upcoming: Annual Physical on Apr 15 at 9:30 AM", "dismissed": false}
          ]
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Read a message thread | `messages[i].isRead: false → true` for all messages in thread; `ui.unreadMessageCount` decremented |
| Mark message as unread | `messages[i].isRead: true → false`; `ui.unreadMessageCount` incremented |
| Archive a message thread | `messages[i].folder → "archived"` for all messages in thread; `ui.unreadMessageCount` recalculated |
| Send a new message | New message object appended to `messages` with `folder: "sent"` |
| Reply to a message | New message appended to `messages` with same `threadId`, `folder: "sent"` |
| Dismiss notification banner | `ui.notificationBanners[i].dismissed: false → true` |
| Toggle sidebar | `ui.sideMenuOpen` toggled |
| Check in for appointment | `appointments[i].status: "Scheduled" → "Checked In"`, `canCheckIn: true → false` |
| Cancel appointment | `appointments[i].status → "Cancelled"`, `isUpcoming → false`, `canCheckIn/canCancel → false` |
| Schedule new appointment | New appointment object appended to `appointments` with `status: "Scheduled"` |
| Request medication refill | `medications[i].lastFilledDate` updated to today, `refillsRemaining` decremented by 1 |
| Pay a bill | `billingStatements[i].amountPaid` increased, `balanceDue` decreased; `status → "Paid"` if balance reaches 0 |
| Update personal info | `currentUser.phone` and/or `currentUser.email` updated |

### state_diff Structure

The `/go` endpoint returns a `state_diff` object computed by comparing `initial_state` to `current_state`. The diff walks all keys recursively and returns changed values in the format:

```json
{
  "field.path": {
    "old": "<previous value>",
    "new": "<current value>"
  }
}
```

For example, after marking a message as read and dismissing a notification:
```json
{
  "messages": {
    "old": [...],
    "new": [...]
  },
  "ui.unreadMessageCount": {
    "old": 2,
    "new": 1
  },
  "ui.notificationBanners": {
    "old": [...],
    "new": [...]
  }
}
```

Note: Array-level changes (messages, appointments, etc.) are reported as whole-array diffs rather than per-element diffs, since the client-side `computeStateDiff` function does not deeply compare array elements.
