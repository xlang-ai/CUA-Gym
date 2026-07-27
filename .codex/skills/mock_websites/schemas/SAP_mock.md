# SAP_mock Schema

**Deploy order**: 43 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8043)
**Base URL**: `http://172.17.46.46:8043/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`

> **Note**: This mock is in "READY FOR DEV" status — no source code yet. This schema documents the planned data model from `assets/data_model.md`.

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Logged-in user: `{id, firstName, lastName, initials, email, role, avatarColor, department, plant, companyCode, language, dateFormat, timezone}` |
| `companyInfo` | object | Company context: `{companyCode, companyName, currency, country, fiscalYearVariant, currentFiscalYear}` |
| `navigationTabs` | array | ~12 module tab items: `{id, label, key, isDefault, order}` |
| `tileGroups` | array | ~8 tile group containers: `{id, title, tabKey, order}` |
| `tiles` | array | ~40 app tiles: `{id, groupId, title, subtitle, icon, type, numericValue, numericUnit, kpiData, appRoute, order, isActive}` |
| `purchaseOrders` | array | 15 POs: `{id, poNumber, supplier, supplierName, poType, poTypeName, purchasingOrg, purchasingOrgName, purchasingGroup, purchasingGroupName, companyCode, createdDate, createdBy, totalNetValue, currency, status, deliveryStatus, plant, plantName, paymentTerms, incoterms, notes, lastChanged, lastChangedBy}` |
| `purchaseOrderItems` | array | ~40 PO line items: `{id, poId, itemNumber, materialId, materialName, materialNumber, quantity, unit, netPrice, priceUnit, netValue, currency, deliveryDate, plant, storageLocation, taxCode, accountAssignment, costCenter, glAccount}` |
| `salesOrders` | array | 12 SOs: `{id, soNumber, customer, customerName, orderType, orderTypeName, salesOrg, salesOrgName, distributionChannel, division, createdDate, createdBy, totalNetValue, currency, status, overallDeliveryStatus, overallBillingStatus, requestedDeliveryDate, customerReference, soldToParty, shipToParty, paymentTerms, incoterms, lastChanged, lastChangedBy}` |
| `salesOrderItems` | array | ~35 SO line items: `{id, soId, itemNumber, materialId, materialName, materialNumber, quantity, unit, netPrice, netValue, currency, plant, deliveryDate, deliveryStatus, billingStatus, rejectionReason}` |
| `materials` | array | 20 product/material master records: `{id, materialNumber, description, materialGroup, materialGroupName, materialType, materialTypeName, baseUnit, grossWeight, netWeight, weightUnit, productCategory, division, gtin, image, standardPrice, currency, plantData{}, stockQuantity, lastChanged, lastChangedBy}` |
| `suppliers` | array | 10 vendor records: `{id, supplierNumber, name, name2, country, city, postalCode, street, region, phone, email, taxNumber, paymentTerms, currency, accountGroup, purchasingOrg, isBlocked}` |
| `customers` | array | 10 customer records: `{id, customerNumber, name, name2, country, city, postalCode, street, region, phone, email, salesOrg, distributionChannel, division, paymentTerms, currency, creditLimit, accountGroup}` |
| `journalEntries` | array | 15 FI journal entries: `{id, documentNumber, companyCode, fiscalYear, fiscalPeriod, documentType, documentTypeName, postingDate, documentDate, entryDate, reference, headerText, totalDebit, totalCredit, currency, status, createdBy, ledgerGroup}` |
| `journalEntryItems` | array | ~40 JE line items: `{id, journalEntryId, itemNumber, glAccount, glAccountName, debitAmount, creditAmount, currency, costCenter, costCenterName, profitCenter, taxCode, assignment, text}` |
| `notifications` | array | 8 notification items: `{id, title, description, timestamp, type, priority, isRead, category, actionUrl, icon}` |
| `plants` | array | 3 plants: `{id, plantCode, name, city, country}` |
| `activeTab` | string | Currently selected navigation tab key. Default: `"my-home"` |
| `searchQuery` | string | Current shell bar search text. Default: `""` |
| `notificationCount` | number | Unread notification badge count. Default: `5` |
| `selectedVariant` | string | Selected list report variant. Default: `"Standard"` |
| `filterState` | object | Per-app filter values. Default: `{}` |

### Tile types
- `"static"` — simple app launcher tile
- `"numeric"` — tile with a numeric KPI value and unit label
- `"kpi"` — tile with numeric value, unit, and `kpiData: {trend, status}`

### Purchase Order statuses
`"Draft"` | `"Ordered"` | `"Partially Delivered"` | `"Fully Delivered"` | `"Closed"`

### Purchase Order delivery statuses
`"On Time"` | `"Overdue"` | `"Partially Received"` | `"Received"`

### Sales Order statuses
`"Open"` | `"In Process"` | `"Completed"` | `"Cancelled"`

### Journal Entry statuses
`"Posted"` | `"Parked"` | `"Reversed"`

### Notification types
`"success"` | `"warning"` | `"error"` | `"info"`

### Material types
`"HAWA"` (Trading Goods) | `"ROH"` (Raw Material) | `"FERT"` (Finished) | `"HALB"` (Semi-Finished)

### Default IDs
- User: `user-001` (Michael Quinn)
- Plants: `plant-1000` (Dallas), `plant-1100` (Chicago), `plant-2000` (Frankfurt)
- POs: `po-001` through `po-015`
- SOs: `so-001` through `so-012`
- Materials: `mat-001` through `mat-020`
- Suppliers: `sup-001` through `sup-010`
- Customers: `cust-001` through `cust-010`
- Journal Entries: `je-001` through `je-015`
- Navigation Tabs: `tab-001` through `tab-012`
- Tile Groups: `group-001` through `group-008`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8043/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "user-001",
          "firstName": "Michael",
          "lastName": "Quinn",
          "initials": "MQ",
          "email": "michael.quinn@bestrun.com",
          "role": "Procurement Manager",
          "avatarColor": "#0A6ED1",
          "department": "Procurement",
          "plant": "1000",
          "companyCode": "1000"
        },
        "companyInfo": {
          "companyCode": "1000",
          "companyName": "BestRun US",
          "currency": "USD",
          "country": "US"
        },
        "navigationTabs": [
          {"id": "tab-001", "label": "My Home", "key": "my-home", "isDefault": true, "order": 0},
          {"id": "tab-006", "label": "Procurement", "key": "procurement", "isDefault": false, "order": 5}
        ],
        "tileGroups": [
          {"id": "group-001", "title": "Purchase Order Processing", "tabKey": "procurement", "order": 0}
        ],
        "tiles": [
          {"id": "tile-001", "groupId": "group-001", "title": "Manage Purchase Orders", "subtitle": "", "icon": "shopping-cart", "type": "static", "appRoute": "/app/manage-purchase-orders", "order": 0, "isActive": true}
        ],
        "purchaseOrders": [
          {"id": "po-001", "poNumber": "4500001234", "supplier": "sup-001", "supplierName": "Global Parts Inc.", "poType": "NB", "poTypeName": "Standard PO", "totalNetValue": 15420.00, "currency": "USD", "status": "Ordered", "deliveryStatus": "Overdue", "plant": "1000", "createdDate": "2024-01-15", "createdBy": "Michael Quinn"}
        ],
        "purchaseOrderItems": [
          {"id": "poi-001", "poId": "po-001", "itemNumber": 10, "materialId": "mat-001", "materialName": "Aluminum Sheet 2mm", "quantity": 500, "unit": "PC", "netPrice": 12.50, "netValue": 6250.00, "currency": "USD", "deliveryDate": "2024-02-15"}
        ],
        "salesOrders": [],
        "salesOrderItems": [],
        "materials": [
          {"id": "mat-001", "materialNumber": "MAT-1001", "description": "Aluminum Sheet 2mm", "materialType": "HAWA", "materialTypeName": "Trading Goods", "baseUnit": "PC", "standardPrice": 12.50, "currency": "USD", "stockQuantity": 1250}
        ],
        "suppliers": [
          {"id": "sup-001", "supplierNumber": "17411730", "name": "Global Parts Inc.", "country": "US", "city": "Dallas"}
        ],
        "customers": [],
        "journalEntries": [],
        "journalEntryItems": [],
        "notifications": [
          {"id": "notif-001", "title": "PO 4500001234 approved", "type": "success", "isRead": false, "timestamp": "2024-03-10T14:30:00Z"}
        ],
        "plants": [
          {"id": "plant-1000", "plantCode": "1000", "name": "US Plant Dallas", "city": "Dallas", "country": "US"}
        ],
        "activeTab": "my-home",
        "searchQuery": "",
        "notificationCount": 1,
        "selectedVariant": "Standard",
        "filterState": {}
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Click navigation tab | `activeTab` changes |
| Search in shell bar | `searchQuery` updated |
| Click tile to open app | Route navigation (no state change) |
| Create purchase order | `purchaseOrders` array grows; `purchaseOrderItems` grows |
| Edit purchase order | `purchaseOrders[i]` fields updated; `lastChanged`, `lastChangedBy` set |
| Change PO status | `purchaseOrders[i].status` updated |
| Create sales order | `salesOrders` array grows; `salesOrderItems` grows |
| Edit sales order | `salesOrders[i]` fields updated |
| Cancel sales order | `salesOrders[i].status` → `"Cancelled"` |
| Edit material master | `materials[i]` fields updated; `lastChanged`, `lastChangedBy` set |
| Update stock quantity | `materials[i].stockQuantity` changed |
| Create journal entry | `journalEntries` grows; `journalEntryItems` grows |
| Reverse journal entry | `journalEntries[i].status` → `"Reversed"` |
| Read notification | `notifications[i].isRead` → `true`; `notificationCount` decremented |
| Apply list filter | `filterState` updated with filter key-value pairs |
| Change list variant | `selectedVariant` updated |
| Add PO line item | `purchaseOrderItems` grows; `purchaseOrders[i].totalNetValue` recalculated |
| Delete PO line item | `purchaseOrderItems` shrinks; `purchaseOrders[i].totalNetValue` recalculated |
| Add SO line item | `salesOrderItems` grows; `salesOrders[i].totalNetValue` recalculated |
