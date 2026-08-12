# usa-gov_mock Schema

**Deploy order**: 53 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8053)
**Base URL**: `http://172.17.46.46:8053/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## Routes

| Path | Page Component | Description |
|------|----------------|-------------|
| `/` | Homepage | Hero banner, quick-access links, benefits CTA, topic grid (22 topics) |
| `/topics` | AllTopicsPage | Full card grid of all 22 topics |
| `/:topicSlug` | TopicPage | Topic hub with "Most Popular" links + subtopic cards |
| `/:topicSlug/:subtopicSlug` | SubtopicPage | Subtopic with content cards or article body, sidebar nav |
| `/:topicSlug/:subtopicSlug/:pageSlug` | ContentPage | Article page with body content, breadcrumbs, related pages |
| `/agency-index` | AgencyDirectory | A-Z alphabetical agency index with search and letter filter |
| `/benefit-finder` | BenefitFinder | Interactive benefit discovery tool with life-event and category filters |
| `/life-events` | LifeEventsPage | 6 life event cards linking to filtered benefit views |
| `/search` | SearchPage | Search results page (reads `?query=` param) |
| `/go` | Go | State inspection endpoint (JSON: initial_state, current_state, state_diff) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `siteName` | string | Site display name; default `"USAGov"` |
| `tagline` | string | Hero tagline; default `"Making government services easier to find"` |
| `phoneNumber` | string | Contact number; default `"1-844-USAGOV1"` |
| `language` | string | Site language code; default `"en"` |
| `topics` | array | 22 Topic objects (see Topic fields below) |
| `mainNavTopics` | array | 7 topic ID strings shown in top navigation |
| `quickLinks` | array | 4 QuickLink objects for homepage hero |
| `subtopics` | array | ~80 Subtopic objects (flat array, referenced by parentTopicId) |
| `pages` | array | ~120 Page objects (flat array, at least 30 with full body content) |
| `agencies` | array | 55+ Agency objects for A-Z directory |
| `benefits` | array | 25+ Benefit objects for Benefit Finder |
| `benefitCategories` | array | 12 category definition objects |
| `benefitLifeEvents` | array | 3 life event filter option objects |
| `lifeEvents` | array | 6 LifeEvent objects |
| `searchIndex` | array | 100+ SearchResult entries (pre-built from pages + topics) |
| `currentSearch` | string | Current search query text; default `""` |
| `selectedBenefitCategories` | array | Currently selected benefit category IDs; default `[]` |
| `selectedBenefitLifeEvent` | string\|null | Currently selected life event filter; default `null` |
| `agencyDirectoryFilter` | string | Text filter for agency search input; default `""` |
| `agencyDirectoryLetter` | string | Active letter in A-Z index; default `"A"` |
| `expandedBannerInfo` | boolean | Government banner accordion expanded state; default `false` |
| `expandedMenus` | object | Which nav menus are open (keyed by menu ID); default `{}` |
| `currentLanguage` | string | Active language toggle; default `"en"` |

---

### Topic Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique slug, e.g. `"taxes"`, `"travel"` |
| `title` | string | Display name, e.g. `"Taxes"` |
| `description` | string | Brief summary (1-2 sentences) |
| `icon` | string | Icon name/SVG identifier |
| `slug` | string | URL path segment (same as id) |
| `subtopics` | Subtopic[] | Array of subtopic objects nested under this topic |
| `popularLinks` | PopularLink[] | Top 3 most-visited links for this topic |
| `inMainNav` | boolean | Whether shown in main navigation bar |
| `order` | number | Sort order in navigation/display |

### All 22 Topic IDs

| # | ID (slug) | Title |
|---|-----------|-------|
| 1 | `the-us-and-its-government` | The U.S. and its government |
| 2 | `complaints` | Complaints |
| 3 | `disability-services` | Disability services |
| 4 | `disasters-and-emergencies` | Disasters and emergencies |
| 5 | `education` | Education |
| 6 | `government-benefits` | Government benefits |
| 7 | `health` | Health |
| 8 | `housing` | Housing help |
| 9 | `immigration-and-citizenship` | Immigration and U.S. citizenship |
| 10 | `innovation` | Innovation |
| 11 | `jobs-and-unemployment` | Jobs, labor laws, and unemployment |
| 12 | `laws-and-legal-issues` | Laws and legal issues |
| 13 | `military-and-veterans` | Military and veterans |
| 14 | `money-and-credit` | Money and credit |
| 15 | `scams-and-fraud` | Scams and fraud |
| 16 | `small-business` | Small business |
| 17 | `taxes` | Taxes |
| 18 | `travel` | Travel |
| 19 | `voting-and-elections` | Voting and elections |
| 20 | `disability-services` | Disability services |
| 21 | `life-events` | Life events |

### Main Navigation Topic IDs (inMainNav: true)

`the-us-and-its-government`, `government-benefits`, `immigration-and-citizenship`, `money-and-credit`, `taxes`, `travel`

Plus "All topics and services" link that navigates to `/topics`.

---

### PopularLink Object (nested in Topic)

| Field | Type | Notes |
|-------|------|-------|
| `label` | string | Link text, e.g. `"How to file a federal tax return"` |
| `pageId` | string | Reference to target Page id |
| `url` | string | Route path, e.g. `"/taxes/file-federal-taxes"` |

---

### Subtopic Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique slug, e.g. `"file-federal-taxes"` |
| `title` | string | Display name, e.g. `"File federal taxes"` |
| `description` | string | Brief description (1-2 sentences) |
| `parentTopicId` | string | References parent Topic id, e.g. `"taxes"` |
| `slug` | string | URL path segment (same as id) |
| `pages` | Page[] | Content pages under this subtopic |
| `order` | number | Sort order within parent topic |

### Subtopic Counts by Topic

| Topic | Expected Subtopics |
|-------|-------------------|
| taxes | 10 (file-federal-taxes, get-help-filing-taxes, state-and-local-taxes, tax-refunds, federal-tax-forms, tax-return-extensions, tax-credits-and-disaster-relief, tax-return-transcripts, resolve-tax-disputes, tax-withholding) |
| travel | 7 (us-passports, travel-documents-children, real-id, travel-to-within-us, currency-declaration, us-citizens-traveling-abroad, travel-documents-foreign-citizens) |
| voting-and-elections | 9 (voter-registration, how-when-where-to-vote, decide-who-to-vote-for, state-local-election-offices, congressional-state-local-elections, voting-election-laws, how-president-elected, inauguration, past-election-results) |
| the-us-and-its-government | 9 (buying-from-government, us-facts-and-figures, a-z-agency-index, state-local-governments, branches-of-government, find-elected-officials, federal-laws-regulations, native-american-resources, courts) |
| health | 7 (health-insurance, medical-bills-assistance, mental-health-support, substance-abuse-help, covid-19-resources, medlineplus, state-health-departments) |
| immigration-and-citizenship | 6 (immigration-case-status, green-cards-immigrant-visas, us-citizenship, nonimmigrant-tourist-visas, deportation, daca) |
| All others | 3-6 each |

---

### Page Object (Content/Article)

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique slug, e.g. `"apply-for-passport"` |
| `title` | string | Page heading (h1), e.g. `"Apply for a new adult passport"` |
| `description` | string | Intro paragraph below heading |
| `body` | string | HTML body content (paragraphs, lists, headings); at least 30 pages have full body (3-4 paragraphs) |
| `parentTopicId` | string | References parent Topic id |
| `parentSubtopicId` | string | References parent Subtopic id |
| `breadcrumbs` | Breadcrumb[] | Navigation breadcrumb trail array |
| `relatedPages` | string[] | Array of related page IDs |
| `lastUpdated` | string | ISO date, e.g. `"2024-10-15"` |

### Priority Pages with Full Body Content

These 20 pages are specified as must-have with full article content:
`apply-for-passport`, `renew-passport`, `file-federal-tax-return`, `get-help-filing-taxes`, `check-tax-refund-status`, `register-to-vote`, `how-to-vote`, `apply-for-medicare`, `apply-for-medicaid`, `check-immigration-case-status`, `apply-for-green-card`, `file-unemployment-benefits`, `find-unclaimed-money`, `report-a-scam`, `get-real-id`, `social-security-benefits`, `find-government-benefits`, `apply-for-snap`, `find-affordable-housing`, `start-small-business`

---

### Breadcrumb Object (nested in Page)

| Field | Type | Notes |
|-------|------|-------|
| `label` | string | Display text, e.g. `"Travel"` |
| `path` | string | Route path, e.g. `"/travel"` |

---

### Agency Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique slug, e.g. `"irs"` |
| `name` | string | Official name, e.g. `"Internal Revenue Service (IRS)"` |
| `acronym` | string | Abbreviation, e.g. `"IRS"` |
| `description` | string | Brief purpose statement |
| `website` | string | Official URL (display only), e.g. `"https://www.irs.gov"` |
| `phone` | string | Contact phone number, e.g. `"1-800-829-1040"` |
| `contactFormUrl` | string | Contact page URL (display only) |
| `category` | string | One of: `"department"`, `"agency"`, `"commission"`, `"corporation"` |
| `parentDepartment` | string | Parent department name if applicable, e.g. `"Department of the Treasury"` |
| `letter` | string | First letter for A-Z index, e.g. `"I"` |

### Default Agency IDs (55+ spanning A-Z)

| Letter | Example Agencies |
|--------|-----------------|
| A | `abilityone-commission`, `acf`, `agricultural-marketing-service`, `air-force`, `americorps` |
| B | `bls` (Bureau of Labor Statistics) |
| C | `census-bureau`, `cdc`, `cms`, `cia`, `cbp` |
| D | `usda`, `doc`, `dod`, `ed`, `doe`, `hhs`, `dhs`, `hud`, `doi`, `doj`, `dol`, `state`, `dot`, `treasury`, `va` |
| E | `epa`, `eeoc` |
| F | `faa`, `fbi`, `fcc`, `fdic`, `fema`, `federal-reserve`, `ftc`, `fda` |
| G | `gsa` |
| I | `ice`, `irs` |
| L | `library-of-congress` |
| N | `nasa`, `nih`, `nps`, `nsf` |
| O | `osha`, `opm` |
| P | `peace-corps` |
| S | `sec`, `sba`, `smithsonian`, `ssa` |
| T | `tsa` |
| U | `uscis`, `us-marshals`, `usps` |

---

### Benefit Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique identifier, e.g. `"snap"` |
| `name` | string | Program name, e.g. `"Supplemental Nutrition Assistance Program (SNAP)"` |
| `description` | string | What the benefit provides |
| `categories` | string[] | Benefit category IDs, e.g. `["food","children-and-families"]` |
| `lifeEvents` | string[] | Applicable life event IDs, e.g. `["financial-hardship"]` |
| `eligibility` | string | Brief eligibility summary |
| `howToApply` | string | Application instructions |
| `agencyId` | string | Administering agency ID |
| `website` | string | Program website (display only) |

### Default Benefit IDs (25+)

| ID | Name | Categories |
|----|------|------------|
| `snap` | Supplemental Nutrition Assistance Program (SNAP) | food, children-and-families |
| `medicaid` | Medicaid | health |
| `medicare` | Medicare | health, retirement-and-seniors |
| `ssdi` | Social Security Disability Insurance | disabilities |
| `ssi` | Supplemental Security Income | disabilities, retirement-and-seniors |
| `unemployment-insurance` | Unemployment Insurance | jobs-and-unemployment |
| `section-8` | Section 8 Housing Choice Voucher | housing-and-utilities |
| `pell-grant` | Pell Grant | education |
| `chip` | Children's Health Insurance Program (CHIP) | health, children-and-families |
| `tanf` | Temporary Assistance for Needy Families (TANF) | welfare-and-cash-assistance, children-and-families |
| `wic` | Women, Infants, and Children (WIC) | food, children-and-families |
| `fema-disaster` | FEMA Disaster Assistance | disasters |
| `va-health` | VA Health Care | military-and-veterans, health |
| `va-disability` | VA Disability Compensation | military-and-veterans, disabilities |
| `gi-bill` | GI Bill | military-and-veterans, education |
| `head-start` | Head Start | children-and-families, education |
| `liheap` | Low Income Home Energy Assistance (LIHEAP) | housing-and-utilities |
| `federal-student-loans` | Federal Student Loans | education |
| `cobra` | COBRA | health |
| `aca-marketplace` | ACA Marketplace | health |
| `survivor-benefits` | Survivor Benefits | death |
| `burial-benefits` | Burial Benefits | death, military-and-veterans |
| `food-assistance-seniors` | Food Assistance for Seniors | food, retirement-and-seniors |
| `railroad-retirement` | Railroad Retirement Benefits | retirement-and-seniors |
| `child-care-assistance` | Child Care Assistance | children-and-families |

---

### Benefit Categories (12 total)

| ID | Label |
|----|-------|
| `children-and-families` | Children and families |
| `death` | Death |
| `disabilities` | Disabilities |
| `disasters` | Disasters |
| `education` | Education |
| `food` | Food |
| `health` | Health |
| `housing-and-utilities` | Housing and utilities |
| `jobs-and-unemployment` | Jobs and unemployment |
| `military-and-veterans` | Military and veterans |
| `retirement-and-seniors` | Retirement and seniors |
| `welfare-and-cash-assistance` | Welfare and cash assistance |

### Benefit Life Events (3 filter options)

| ID | Label |
|----|-------|
| `disability-or-illness` | Living with disability or illness |
| `death-of-loved-one` | Death of a loved one |
| `approaching-retirement` | Approaching retirement |

---

### LifeEvent Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique slug, e.g. `"financial-hardship"` |
| `title` | string | Display name, e.g. `"Facing financial hardship"` |
| `description` | string | Brief summary |
| `icon` | string | Icon identifier |
| `relatedTopics` | string[] | Related topic IDs |
| `relatedBenefitCategories` | string[] | Benefit categories to highlight |

### All 6 Life Event IDs

| ID | Title |
|----|-------|
| `financial-hardship` | Facing financial hardship |
| `having-a-child` | Having a child and early childhood |
| `transitioning-to-adulthood` | Transitioning to adulthood |
| `approaching-retirement` | Approaching retirement |
| `recovering-from-disaster` | Recovering from a disaster |
| `death-of-loved-one` | Dealing with the death of a loved one |

---

### QuickLink Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique identifier |
| `label` | string | Button/pill text |
| `url` | string | Target route |
| `icon` | string | Optional icon identifier |
| `order` | number | Display order (1-4) |

### Default Quick Links (4)

| ID | Label | URL |
|----|-------|-----|
| `file-taxes` | File your 2025 taxes | `/taxes/file-federal-taxes` |
| `unclaimed-money` | Find unclaimed money | `/money-and-credit/unclaimed-money` |
| `passport` | Get or renew a passport | `/travel/us-passports` |
| `unemployment` | File for unemployment benefits | `/jobs-and-unemployment/unemployment-benefits` |

---

### SearchResult Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique identifier, e.g. `"sr-1"` |
| `title` | string | Result title (linked), e.g. `"Apply for a New Adult Passport"` |
| `description` | string | Snippet/excerpt (2-3 lines) |
| `url` | string | Internal route, e.g. `"/travel/us-passports/apply-for-passport"` |
| `topicId` | string | Associated topic ID |

---

## Relationships

```
Topic (22)
  +-- has many Subtopics (3-10 per topic)
  |     +-- has many Pages (1-5 per subtopic)
  +-- has 3 PopularLinks
  +-- may be referenced by LifeEvents

Agency (55+)
  +-- may administer Benefits

Benefit (25+)
  +-- belongs to 1+ BenefitCategories (from 12 categories)
  +-- belongs to 0+ BenefitLifeEvents (from 3 life events)
  +-- administered by 1 Agency

LifeEvent (6)
  +-- references related Topics
  +-- references related BenefitCategories

QuickLink (4)
  +-- links to a Page or Subtopic

SearchResult (100+)
  +-- references a Page or Topic
```

---

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8053/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "siteName": "USAGov",
        "tagline": "Making government services easier to find",
        "phoneNumber": "1-844-USAGOV1",
        "language": "en",
        "topics": [
          {
            "id": "taxes",
            "title": "Taxes",
            "description": "Get answers to common tax questions, including filing requirements and refund status.",
            "icon": "taxes",
            "slug": "taxes",
            "subtopics": [],
            "popularLinks": [
              {"label": "How to file a federal tax return", "pageId": "file-federal-tax-return", "url": "/taxes/file-federal-taxes"}
            ],
            "inMainNav": true,
            "order": 17
          },
          {
            "id": "travel",
            "title": "Travel",
            "description": "Get information about passports, traveling abroad, and more.",
            "icon": "travel",
            "slug": "travel",
            "subtopics": [],
            "popularLinks": [
              {"label": "Apply for a new passport", "pageId": "apply-for-passport", "url": "/travel/us-passports/apply-for-passport"}
            ],
            "inMainNav": true,
            "order": 18
          }
        ],
        "mainNavTopics": ["the-us-and-its-government", "government-benefits", "immigration-and-citizenship", "money-and-credit", "taxes", "travel"],
        "quickLinks": [
          {"id": "file-taxes", "label": "File your 2025 taxes", "url": "/taxes/file-federal-taxes", "icon": "taxes", "order": 1},
          {"id": "unclaimed-money", "label": "Find unclaimed money", "url": "/money-and-credit/unclaimed-money", "icon": "money", "order": 2},
          {"id": "passport", "label": "Get or renew a passport", "url": "/travel/us-passports", "icon": "travel", "order": 3},
          {"id": "unemployment", "label": "File for unemployment benefits", "url": "/jobs-and-unemployment/unemployment-benefits", "icon": "jobs", "order": 4}
        ],
        "subtopics": [
          {
            "id": "file-federal-taxes",
            "title": "File federal taxes",
            "description": "Learn whether you need to file a federal tax return and how to file.",
            "parentTopicId": "taxes",
            "slug": "file-federal-taxes",
            "pages": [],
            "order": 1
          },
          {
            "id": "us-passports",
            "title": "U.S. passports",
            "description": "Apply for or renew a U.S. passport.",
            "parentTopicId": "travel",
            "slug": "us-passports",
            "pages": [],
            "order": 1
          }
        ],
        "pages": [
          {
            "id": "apply-for-passport",
            "title": "Apply for a new adult passport",
            "description": "Find out what documents and photos you need to apply for a passport.",
            "body": "<h2>What you need</h2><p>To apply for a new passport, you will need proof of U.S. citizenship, a valid photo ID, a passport photo, and the application fee.</p>",
            "parentTopicId": "travel",
            "parentSubtopicId": "us-passports",
            "breadcrumbs": [
              {"label": "Home", "path": "/"},
              {"label": "Travel", "path": "/travel"},
              {"label": "U.S. passports", "path": "/travel/us-passports"}
            ],
            "relatedPages": ["renew-passport"],
            "lastUpdated": "2024-10-15"
          }
        ],
        "agencies": [
          {
            "id": "irs",
            "name": "Internal Revenue Service (IRS)",
            "acronym": "IRS",
            "description": "Collects taxes and enforces tax law",
            "website": "https://www.irs.gov",
            "phone": "1-800-829-1040",
            "contactFormUrl": "https://www.irs.gov/contact",
            "category": "agency",
            "parentDepartment": "Department of the Treasury",
            "letter": "I"
          }
        ],
        "benefits": [
          {
            "id": "snap",
            "name": "Supplemental Nutrition Assistance Program (SNAP)",
            "description": "Provides food-purchasing assistance for low-income individuals and families.",
            "categories": ["food", "children-and-families"],
            "lifeEvents": ["financial-hardship"],
            "eligibility": "Based on income and household size. Must meet work requirements.",
            "howToApply": "Apply through your state's SNAP office or online.",
            "agencyId": "usda",
            "website": "https://www.fns.usda.gov/snap"
          }
        ],
        "benefitCategories": [
          {"id": "children-and-families", "label": "Children and families"},
          {"id": "death", "label": "Death"},
          {"id": "disabilities", "label": "Disabilities"},
          {"id": "disasters", "label": "Disasters"},
          {"id": "education", "label": "Education"},
          {"id": "food", "label": "Food"},
          {"id": "health", "label": "Health"},
          {"id": "housing-and-utilities", "label": "Housing and utilities"},
          {"id": "jobs-and-unemployment", "label": "Jobs and unemployment"},
          {"id": "military-and-veterans", "label": "Military and veterans"},
          {"id": "retirement-and-seniors", "label": "Retirement and seniors"},
          {"id": "welfare-and-cash-assistance", "label": "Welfare and cash assistance"}
        ],
        "benefitLifeEvents": [
          {"id": "disability-or-illness", "label": "Living with disability or illness"},
          {"id": "death-of-loved-one", "label": "Death of a loved one"},
          {"id": "approaching-retirement", "label": "Approaching retirement"}
        ],
        "lifeEvents": [
          {
            "id": "financial-hardship",
            "title": "Facing financial hardship",
            "description": "Find government resources to help with financial difficulties.",
            "icon": "financial-hardship",
            "relatedTopics": ["government-benefits", "housing"],
            "relatedBenefitCategories": ["welfare-and-cash-assistance", "food", "housing-and-utilities"]
          }
        ],
        "searchIndex": [
          {
            "id": "sr-1",
            "title": "Apply for a New Adult Passport",
            "description": "Find out what documents and photos you need to apply for a passport.",
            "url": "/travel/us-passports/apply-for-passport",
            "topicId": "travel"
          }
        ],
        "currentSearch": "",
        "selectedBenefitCategories": [],
        "selectedBenefitLifeEvent": null,
        "agencyDirectoryFilter": "",
        "agencyDirectoryLetter": "A",
        "expandedBannerInfo": false,
        "expandedMenus": {},
        "currentLanguage": "en"
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Submit a search query | `currentSearch` updated to query string |
| Toggle government banner accordion | `expandedBannerInfo` toggled (`false` <-> `true`) |
| Switch language (English/Espanol) | `currentLanguage` toggled (`"en"` <-> `"es"`) |
| Select letter in A-Z agency directory | `agencyDirectoryLetter` updated (e.g. `"A"` -> `"F"`) |
| Type in agency search box | `agencyDirectoryFilter` updated with text input |
| Select benefit life event filter | `selectedBenefitLifeEvent` set to life event ID or `null` |
| Check/uncheck benefit category | `selectedBenefitCategories` array gains/loses category ID |
| Select all benefit categories | `selectedBenefitCategories` set to all 12 category IDs |
| Clear benefit category selections | `selectedBenefitCategories` set to `[]` |
| Open/close navigation mega-menu | `expandedMenus` object gains/loses menu key |

### state_diff Structure

The `/go` endpoint returns a `state_diff` object computed by comparing `initial_state` to `current_state`. The diff walks all keys and returns changed values:

```json
{
  "currentSearch": {
    "old": "",
    "new": "passport renewal"
  },
  "agencyDirectoryLetter": {
    "old": "A",
    "new": "F"
  },
  "selectedBenefitCategories": {
    "old": [],
    "new": ["health", "food"]
  },
  "expandedBannerInfo": {
    "old": false,
    "new": true
  }
}
```

Note: This mock is primarily an informational portal (no user accounts, no content creation). State changes are limited to UI interactions: search queries, filter selections, accordion toggles, and language switches. Content data (topics, subtopics, pages, agencies, benefits) is read-only and not modified by user interactions.

## Seed Data Quantities

| Entity | Count | Notes |
|--------|-------|-------|
| Topics | 22 | All with realistic titles and descriptions |
| Subtopics | ~80 | 3-10 per topic |
| Pages | ~120 | 1-5 per subtopic; 30+ with full body HTML content |
| Agencies | 55+ | Spanning letters A through U, real names and phone numbers |
| Benefits | 25+ | Covering all 12 categories and 3 life events |
| Life Events | 6 | All with related topics and benefit categories |
| Quick Links | 4 | Homepage hero section |
| Search Results | 100+ | Generated from all pages + topics |
| Benefit Categories | 12 | Fixed category definitions |
| Benefit Life Events | 3 | Fixed life event filter options |
