# google_sheets_mock Schema

**Deploy order**: 18 (alphabetical among all *_mock dirs)
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | Unique workbook identifier (e.g., `"workbook_1"`) |
| `title` | string | Workbook display name |
| `sheets` | array | Array of `Sheet` objects (see below) |
| `activeSheetId` | string | ID of currently active sheet |
| `selectedCell` | string\|null | Currently selected cell (e.g., `"A1"`, `"B5"`) |
| `selectionRange` | array\|null | Array of cell IDs in multi-cell selection |
| `clipboard` | object\|null | Clipboard data: `{type, data, range, sourceSheetId}` |
| `isDragging` | boolean | Whether drag-select is in progress |
| `undoStack` | array | Stack of undo history entries (max 100) |
| `redoStack` | array | Stack of redo history entries |
| `namedRanges` | array | Each: `{name, sheetId, range}` |
| `conditionalFormats` | array | Conditional formatting rules |
| `charts` | array | Embedded chart definitions |
| `showGridlines` | boolean | Toggle grid visibility |
| `showFormulas` | boolean | Toggle formula display vs. computed values |
| `zoom` | number | Zoom level percentage (e.g., 100) |

### Sheet

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique sheet ID (e.g., `"sheet_1"`) |
| `name` | string | Sheet tab name (e.g., `"Sales Data"`) |
| `data` | object | Map of cell ID → `CellData`; keys are Excel-style (e.g., `"A1"`, `"B5"`) |
| `rowCount` | number | Total rows (e.g., 100) |
| `colCount` | number | Total columns (e.g., 26 = A–Z) |
| `frozenRows` | number? | Number of frozen header rows |
| `frozenCols` | number? | Number of frozen header columns |
| `tabColor` | string\|null? | Sheet tab hex color (e.g., `"#1A73E8"`) |
| `isHidden` | boolean? | Whether sheet is hidden |
| `columnWidths` | object? | Custom widths: `{colIndex: width}` |
| `rowHeights` | object? | Custom heights: `{rowIndex: height}` |
| `filterRange` | string\|null? | Range with active filter (e.g., `"A1:F10"`) |
| `filterCriteria` | object? | Column-specific filter states: `{colKey: FilterCriteria}` |
| `sortColumn` | string\|null? | Column letter currently sorted by |
| `sortDirection` | string\|null? | `"asc"\|"desc"\|null` |

### CellData (values in `sheet.data` map)

| Field | Type | Description |
|-------|------|-------------|
| `value` | string | Raw input value (e.g., `"45200"`, `"=C2*1.15"`) |
| `formula` | string | Formula or raw value string |
| `computed` | string\|number? | Evaluated result of formula |
| `style` | object? | Cell formatting: `{bold, italic, underline, strikethrough, align, verticalAlign, color, bg, fontSize, fontFamily, textWrap, textRotation, borders}` |
| `format` | string? | Number format: `"text"\|"number"\|"currency"\|"percent"\|"date"\|"scientific"\|"time"` |
| `note` | string\|null? | Cell comment/note |
| `hyperlink` | string\|null? | URL for hyperlink |
| `validation` | object\|null? | Data validation: `{type, criteria, showWarning, helpText}` |
| `mergedWith` | string\|null? | ID of merge anchor cell |
| `isMergeAnchor` | boolean? | Whether this cell is a merge anchor |
| `mergeSpan` | object\|null? | `{rows, cols}` span of merged area |

### CellStyle

| Field | Type | Description |
|-------|------|-------------|
| `bold` | boolean? | Font weight bold |
| `italic` | boolean? | Font style italic |
| `underline` | boolean? | Text underline |
| `strikethrough` | boolean? | Text strikethrough |
| `align` | string? | `"left"\|"center"\|"right"` |
| `verticalAlign` | string? | `"top"\|"middle"\|"bottom"` |
| `color` | string? | Text color hex (e.g., `"#0F9D58"`) |
| `bg` | string? | Background color hex (e.g., `"#F3F3F3"`) |
| `fontSize` | number? | Font size in pt |
| `fontFamily` | string? | Font name |
| `textWrap` | string? | `"overflow"\|"wrap"\|"clip"` |
| `textRotation` | number? | Rotation angle in degrees |
| `borders` | object? | `{top, right, bottom, left}` each: `{style, width, color}` or null |

### FilterCriteria

| Field | Type | Description |
|-------|------|-------------|
| `visibleValues` | array | Values currently visible |
| `hiddenValues` | array | Values hidden by filter |
| `condition` | string\|null | Condition expression (e.g., `">100"`) |
| `conditionValue` | string\|null | Value for condition |

### Chart

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Chart ID |
| `type` | string | `"bar"\|"line"\|"pie"\|"scatter"\|"area"` |
| `title` | string | Chart title |
| `dataRange` | string | Data range (e.g., `"A1:C10"`) |
| `sheetId` | string | Sheet containing this chart |
| `position` | object | `{row, col}` position in sheet |
| `size` | object | `{width, height}` dimensions |

### ConditionalFormatRule

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Rule ID |
| `range` | string | Target range (e.g., `"A1:F10"`) |
| `sheetId` | string | Sheet this rule applies to |
| `condition` | object | `{type, value}` where type is `"greaterThan"\|"lessThan"\|"equalTo"\|"textContains"\|"isEmpty"\|"isNotEmpty"\|"customFormula"` |
| `format` | object | CellStyle to apply when condition is met |

### UndoEntry

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | Description (e.g., `"Edit cell A1"`) |
| `sheetId` | string | Modified sheet ID |
| `cellChanges` | object | `{cellId: {before: CellData\|null, after: CellData\|null}}` |
| `timestamp` | number | Unix timestamp |

### Default sheets
- `sheet_1`: "Sales Data" — 9 product rows + summary formulas (SUM, AVERAGE, MAX, MIN, COUNT), frozen row 1
- `sheet_2`: "Summary" — Category breakdown with revenue percentages, tab color `"#1A73E8"`
- `sheet_3`: "Notes" — Documentation (Data Source, Review Date, Status Criteria, Next Steps)

### Default workbook
- ID: `"workbook_1"`, Title: `"Q4 2024 Sales Report"`

### Cell reference format
- Column-Row notation: `A1`, `B5`, `AA100`
- Ranges: `A1:C5` (start:end)
- Columns A–Z (indices 0–25), rows 1-indexed

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "https://cua-gym-google-sheets.xlang.ai/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "id": "workbook_1",
        "title": "Budget Tracker",
        "activeSheetId": "sheet_1",
        "selectedCell": "A1",
        "selectionRange": null,
        "clipboard": null,
        "isDragging": false,
        "undoStack": [],
        "redoStack": [],
        "namedRanges": [],
        "conditionalFormats": [],
        "charts": [],
        "showGridlines": true,
        "showFormulas": false,
        "zoom": 100,
        "sheets": [
          {
            "id": "sheet_1",
            "name": "Monthly Budget",
            "rowCount": 100,
            "colCount": 26,
            "frozenRows": 1,
            "frozenCols": 0,
            "tabColor": null,
            "isHidden": false,
            "columnWidths": {"0": 140, "1": 120, "2": 100},
            "data": {
              "A1": {"value": "Category", "formula": "Category", "style": {"bold": true, "bg": "#E8EAED", "align": "center"}},
              "B1": {"value": "Budget", "formula": "Budget", "style": {"bold": true, "bg": "#E8EAED", "align": "center"}},
              "C1": {"value": "Actual", "formula": "Actual", "style": {"bold": true, "bg": "#E8EAED", "align": "center"}},
              "A2": {"value": "Rent", "formula": "Rent"},
              "B2": {"value": "2000", "formula": "2000", "format": "currency"},
              "C2": {"value": "2000", "formula": "2000", "format": "currency"},
              "A3": {"value": "Utilities", "formula": "Utilities"},
              "B3": {"value": "300", "formula": "300", "format": "currency"},
              "C3": {"value": "275", "formula": "275", "format": "currency"}
            }
          }
        ]
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Edit cell value | `sheets[i].data[cellId].value`, `.formula`, `.computed` updated |
| Format cell (bold, color, etc.) | `sheets[i].data[cellId].style` updated |
| Set number format | `sheets[i].data[cellId].format` updated |
| Select cell | `selectedCell` updated; `selectionRange` may update |
| Select range | `selectionRange` updated |
| Add new sheet | `sheets` array grows; `activeSheetId` updated |
| Switch sheet | `activeSheetId` updated |
| Rename sheet | `sheets[i].name` updated |
| Delete sheet | `sheets` array shrinks |
| Duplicate sheet | `sheets` array grows (copy with new ID) |
| Set sheet tab color | `sheets[i].tabColor` updated |
| Insert row/column | `sheets[i].data` keys shift; `rowCount` or `colCount` updated |
| Delete row/column | `sheets[i].data` keys shift; `rowCount` or `colCount` updated |
| Resize column | `sheets[i].columnWidths[colIndex]` updated |
| Sort by column | `sheets[i].sortColumn`, `.sortDirection` updated; data reordered |
| Apply filter | `sheets[i].filterRange` set; `filterCriteria` populated |
| Freeze panes | `sheets[i].frozenRows` / `.frozenCols` updated |
| Merge cells | Anchor cell gets `isMergeAnchor: true`, `mergeSpan`; other cells get `mergedWith` |
| Copy/cut cells | `clipboard` populated |
| Paste cells | Target `sheets[i].data` cells updated; clipboard may clear (cut) |
| Undo | `undoStack` shrinks; `redoStack` grows; `sheets[i].data` reverted |
| Redo | `redoStack` shrinks; `undoStack` grows; `sheets[i].data` reapplied |
| Toggle gridlines | `showGridlines` toggled |
| Toggle formula view | `showFormulas` toggled |
| Change zoom | `zoom` updated |
| Add cell note | `sheets[i].data[cellId].note` set |
| Clear cell contents | `sheets[i].data[cellId]` value/formula cleared |
