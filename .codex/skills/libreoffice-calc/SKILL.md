---
name: libreoffice-calc
description: "How to programmatically create, modify, and verify LibreOffice Calc (.xlsx) files using Python openpyxl. For setup-gen and reward-gen agents."
user-invocable: false
---

# LibreOffice Calc — Python Manipulation Guide

This skill teaches **setup-gen** (create/modify xlsx) and **reward-gen** (read/verify xlsx) how to work with spreadsheet files using pure Python code.

- Library: `openpyxl` (+ `pandas` for bulk data)
- Install: `pip3 install openpyxl pandas`

---

## 0. GUI Startup on VM (for setup-gen)

After generating `/home/user/<task_id>_initial.xlsx`, setup-gen should leave the task in a GUI-ready state by opening Calc (and any additional required app windows).

**CRITICAL VM LIMIT**: GUI apps must use `DISPLAY=:0`, otherwise open commands may fail silently or open nowhere.

```python
import os
import shlex
import subprocess
import time

def launch_gui(command: str, delay_sec: float = 1.0):
    env = os.environ.copy()
    env["DISPLAY"] = ":0"
    subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    time.sleep(delay_sec)

# Open the initial workbook for the GUI agent
launch_gui(f'libreoffice --calc "{output_path}"', delay_sec=2.0)

# Optional multi-app startup example
# launch_gui('nautilus "/home/user"', delay_sec=1.0)
```

Guidelines:
- Open `*_initial.xlsx`, never `*_golden.xlsx`.
- Use non-blocking launch (`Popen`) so `initial_setup.py` can exit.
- Add short delays between app launches for stability.

---

## 1. Creating & Writing Files (setup-gen)

### Basic Workbook

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Sales"

# Write cell by cell
ws.cell(row=1, column=1, value="Name")
ws["B1"] = "Revenue"

# Write rows in bulk
data = [["Alice", 50000], ["Bob", 72000], ["Carol", 61000]]
for r, row in enumerate(data, 2):
    for c, val in enumerate(row, 1):
        ws.cell(row=r, column=c, value=val)

# Add sheets
ws2 = wb.create_sheet("Summary")
ws3 = wb.create_sheet("Charts")

# Reorder sheets (optional)
wb.move_sheet("Summary", offset=-1)  # move left

wb.save("/home/user/output.xlsx")
```

### Styling Cells

```python
# --- Font ---
cell.font = Font(name="Arial", size=12, bold=True, italic=False,
                 color="FF0000")  # 6-char RGB for Font constructor

# --- Background Color (PatternFill) ---
# CRITICAL: use start_color/end_color, openpyxl maps this to fgColor internally
cell.fill = PatternFill(start_color="FF4472C4", end_color="FF4472C4",
                        fill_type="solid")
# 8-char ARGB: FF=alpha, 44=R, 72=G, C4=B

# --- Alignment ---
cell.alignment = Alignment(horizontal="center", vertical="center",
                           wrap_text=True)

# --- Borders ---
thin = Side(style="thin", color="000000")
cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)

# --- Number Formats ---
cell.number_format = '#,##0.00'       # 1,234.56
cell.number_format = '0.00%'          # 12.50%
cell.number_format = 'yyyy-mm-dd'     # 2024-01-15
cell.number_format = '$#,##0.00'      # $1,234.56
cell.number_format = '0'              # integer
```

### Color Gotchas (CRITICAL)

openpyxl stores colors in **ARGB hex** (8 characters):
```
FF4472C4 = alpha(FF) + R(44) + G(72) + B(C4)
FFFF0000 = opaque red
FF00FF00 = opaque green
FF0000FF = opaque blue
```

- `PatternFill(start_color="4472C4")` → openpyxl prepends `00` → stored as `004472C4` (transparent!)
- **Always use 8-char ARGB**: `PatternFill(start_color="FF4472C4", ...)`
- `Font(color="FF0000")` → stored as `00FF0000`. For Font, 6-char is fine since alpha doesn't matter visually.
- When **reading back**, `cell.fill.fgColor.rgb` returns the 8-char ARGB string.

### Merged Cells

```python
ws.merge_cells("A1:D1")
ws["A1"] = "Quarterly Report"
ws["A1"].font = Font(size=16, bold=True)
ws["A1"].alignment = Alignment(horizontal="center")
# Only A1 holds data; B1,C1,D1 become MergedCell (value=None)
```

### Formulas

```python
ws["C2"] = "=A2+B2"
ws["D10"] = "=SUM(D2:D9)"
ws["E2"] = "=VLOOKUP(A2,Sheet2!A:B,2,FALSE)"

# GOTCHA: openpyxl does NOT evaluate formulas.
# The .value will be the formula string, not the computed result.
# To get computed values, you need LibreOffice to open & save the file first.
```

### Charts

```python
from openpyxl.chart import BarChart, LineChart, PieChart, ScatterChart, Reference, Series

# --- Bar/Column Chart ---
chart = BarChart()
chart.type = "col"          # "col"=vertical columns, "bar"=horizontal bars
chart.title = "Monthly Sales"
chart.y_axis.title = "Revenue ($)"
chart.x_axis.title = "Month"
data = Reference(ws, min_col=2, min_row=1, max_col=3, max_row=13)
cats = Reference(ws, min_col=1, min_row=2, max_row=13)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "F2")

# --- Line Chart ---
line = LineChart()
line.title = "Trend"
line.add_data(Reference(ws, min_col=2, min_row=1, max_row=13), titles_from_data=True)
line.set_categories(Reference(ws, min_col=1, min_row=2, max_row=13))
ws.add_chart(line, "F18")

# --- Pie Chart ---
pie = PieChart()
pie.title = "Distribution"
pie.add_data(Reference(ws, min_col=2, min_row=1, max_row=6), titles_from_data=True)
pie.set_categories(Reference(ws, min_col=1, min_row=2, max_row=6))
ws.add_chart(pie, "F34")

# --- Scatter Chart ---
scatter = ScatterChart()
scatter.title = "X vs Y"
x_vals = Reference(ws, min_col=1, min_row=2, max_row=10)
y_vals = Reference(ws, min_col=2, min_row=2, max_row=10)
series = Series(y_vals, x_vals, title="Series 1")
scatter.series.append(series)
ws.add_chart(scatter, "F50")
```

### Freeze Panes

```python
ws.freeze_panes = "A2"    # freeze row 1 (header row)
ws.freeze_panes = "B1"    # freeze column A
ws.freeze_panes = "C3"    # freeze rows 1-2 and columns A-B
ws.freeze_panes = None     # no freeze
```

### Row/Column Dimensions

```python
ws.row_dimensions[1].height = 30       # row height in points
ws.row_dimensions[5].hidden = True     # hide row 5
ws.column_dimensions["A"].width = 25   # column width in characters
ws.column_dimensions["C"].hidden = True # hide column C
```

### Zoom

```python
ws.sheet_view.zoomScale = 150  # 150%
```

### Auto-Filter

```python
ws.auto_filter.ref = "A1:F20"
# NOTE: openpyxl can define the filter range but cannot actually
# apply/execute the filter. The filtering only takes effect when
# the file is opened in LibreOffice/Excel.
```

### Data Validation (Dropdowns)

```python
from openpyxl.worksheet.datavalidation import DataValidation

dv = DataValidation(
    type="list",
    formula1='"High,Medium,Low"',
    allow_blank=True,
    showDropDown=False,  # COUNTERINTUITIVE: False = show the dropdown!
)
dv.error = "Invalid priority"
dv.errorTitle = "Error"
dv.prompt = "Select priority level"
dv.promptTitle = "Priority"
dv.add("C2:C100")
ws.add_data_validation(dv)
```

### Conditional Formatting

```python
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles.differential import DifferentialStyle

# Highlight cells > 100 in red
red_fill = PatternFill(start_color="FFFF0000", end_color="FFFF0000", fill_type="solid")
ws.conditional_formatting.add("B2:B50",
    CellIsRule(operator="greaterThan", formula=["100"],
              fill=red_fill))

# Formula-based rule
green_fill = PatternFill(start_color="FF00FF00", end_color="FF00FF00", fill_type="solid")
ws.conditional_formatting.add("A2:A50",
    FormulaRule(formula=['ISBLANK(A2)'], fill=green_fill))
```

### Sheet Visibility

```python
ws.sheet_state = "visible"      # default
ws.sheet_state = "hidden"       # hidden from UI, accessible via menu
ws.sheet_state = "veryHidden"   # only accessible via macro
```

### Pivot Tables

**openpyxl cannot create pivot tables from scratch.** It can only preserve existing ones.
If your task needs a pivot table, you must:
1. Create one in a template file using LibreOffice GUI
2. Use that file as the initial file, then copy-and-modify

---

## 2. Reading & Verifying Files (reward-gen)

### Loading and Inspecting

```python
import openpyxl
from openpyxl.cell.cell import MergedCell

wb = openpyxl.load_workbook("/path/to/file.xlsx")

# Sheet names
print(wb.sheetnames)  # ['Sales', 'Summary', 'Charts']

# Access sheet
ws = wb["Sales"]
# or by index: ws = wb.worksheets[0]
```

### Reading Cell Values

```python
# Direct access
val = ws["A1"].value        # returns raw value or formula string
val = ws.cell(row=1, column=1).value

# Read a range
for row in ws.iter_rows(min_row=2, max_row=10, min_col=1, max_col=3):
    for cell in row:
        print(cell.value)

# IMPORTANT: for formula cells, .value returns the formula string "=SUM(...)".
# To get computed values, load with data_only=True:
wb2 = openpyxl.load_workbook("file.xlsx", data_only=True)
val = wb2["Sales"]["C2"].value  # returns cached computed value (or None if never opened by Calc)
```

### Verifying Cell Styles

```python
cell = ws["A1"]

# Font
cell.font.bold        # True/False
cell.font.italic      # True/False
cell.font.underline   # 'single', 'double', None
cell.font.size        # 11, 12, etc.
cell.font.name        # "Arial", "Calibri", etc.
cell.font.color.rgb   # "00FF0000" (ARGB string) — may be None if theme color

# Background color
cell.fill.fgColor.rgb   # "FF4472C4" (ARGB) — THIS is the visible background
cell.fill.fill_type     # "solid", "none", etc. (via .patternType or .tagname)

# Alignment
cell.alignment.horizontal  # "center", "left", "right", "general"
cell.alignment.vertical    # "center", "top", "bottom"
cell.alignment.wrap_text   # True/False

# Border
cell.border.left.style   # "thin", "medium", "thick", None
cell.border.left.color   # Color object

# Number format
cell.number_format  # '#,##0.00', '0.00%', 'yyyy-mm-dd', 'General'

# Merged cell check
isinstance(cell, MergedCell)  # True if part of a merge (not the top-left)
```

### Common Verification Patterns for reward.py

```python
def check_value(ws, coord, expected, tolerance=0.01):
    """Check cell value with numeric tolerance."""
    val = ws[coord].value
    if val is None:
        return False
    if isinstance(expected, (int, float)):
        try:
            return abs(float(val) - expected) <= tolerance
        except (ValueError, TypeError):
            return False
    return str(val).strip() == str(expected).strip()

def check_bold(ws, coord):
    """Check if cell has bold font."""
    return ws[coord].font.bold == True

def check_bgcolor(ws, coord, expected_argb):
    """Check cell background color. expected_argb like 'FF4472C4'."""
    try:
        return ws[coord].fill.fgColor.rgb == expected_argb
    except:
        return False

def check_font_color(ws, coord, expected_argb):
    """Check font color."""
    try:
        return ws[coord].font.color.rgb == expected_argb
    except:
        return False

def check_merged(ws, coord):
    """Check if a cell is part of a merged range (not the top-left)."""
    return isinstance(ws[coord], MergedCell)

def check_formula(ws, coord, expected_formula):
    """Check if cell contains expected formula (case-insensitive)."""
    val = ws[coord].value
    if not isinstance(val, str):
        return False
    return val.upper().replace(" ", "") == expected_formula.upper().replace(" ", "")
```

### Verifying Sheet Structure

```python
# Sheet count and names
assert wb.sheetnames == ["Sales", "Summary"]
assert len(wb.sheetnames) == 2
assert "Sales" in wb.sheetnames

# Row/column count (using pandas for data shape)
import pandas as pd
df = pd.read_excel("file.xlsx", sheet_name="Sales")
assert len(df) >= 10          # at least 10 data rows
assert "Revenue" in df.columns # has expected column
```

### Verifying Charts

```python
ws = wb["Charts"]
charts = ws._charts  # list of chart objects

assert len(charts) >= 1

chart = charts[0]
print(chart.type)      # e.g., "barChart", "lineChart"
print(chart.title)     # chart title string or None
print(chart.y_axis.title)
print(chart.x_axis.title)
print(len(chart.series))  # number of data series
```

### Verifying Freeze Panes

```python
assert ws.freeze_panes == "A2"  # or "B1", "C3", None
```

### Verifying Data Validation

```python
validations = ws.data_validations.dataValidation
assert len(validations) >= 1

dv = validations[0]
print(dv.type)       # "list", "whole", "decimal", etc.
print(dv.formula1)   # '"High,Medium,Low"'
print(dv.sqref)      # CellRange of where it applies
```

### Verifying Row/Column Properties

```python
# Hidden rows
assert ws.row_dimensions[5].hidden == True

# Row height
assert ws.row_dimensions[1].height == 30

# Hidden columns
assert ws.column_dimensions["C"].hidden == True

# Column width
assert ws.column_dimensions["A"].width >= 20
```

### Verifying Filters

```python
if ws.auto_filter.ref:
    print(ws.auto_filter.ref)  # e.g., "A1:F20"
```

### Verifying Conditional Formatting

```python
cf_rules = ws.conditional_formatting
for cf in cf_rules:
    print(cf)           # cell range
    for rule in cf.rules:
        print(rule.type, rule.operator, rule.formula)
```

### Bulk Data Comparison (pandas)

```python
import pandas as pd

df_result = pd.read_excel("result.xlsx", sheet_name="Sales")
df_golden = pd.read_excel("golden.xlsx", sheet_name="Sales")

# Exact match
assert df_result.round(4).equals(df_golden.round(4))

# Or partial: just check specific columns exist and have right shape
assert list(df_result.columns) == list(df_golden.columns)
assert len(df_result) == len(df_golden)
```

---

## 3. Bitter Lessons

1. **Formula values are NOT computed by openpyxl.** `cell.value` returns the formula string `"=SUM(A1:A10)"`, not the result. Use `data_only=True` to get the last-cached value (requires the file to have been opened in Calc/Excel at least once). For reward scripts that check formula outputs: either verify the formula string itself, or use pandas `read_excel` which reads cached values.

2. **Always use 8-char ARGB for colors.** `PatternFill(start_color="4472C4")` silently becomes `004472C4` (alpha=00, transparent). Always write `"FF4472C4"`. When reading back, compare against the 8-char form.

3. **`fgColor` is the visible background, not `bgColor`.** This is counterintuitive. `cell.fill.fgColor.rgb` gives you the background color you see. `bgColor` is rarely what you want.

4. **Merged cells: only top-left has data.** After `merge_cells("A1:D1")`, cells B1/C1/D1 become `MergedCell` objects with `value=None`. Style the top-left cell only.

5. **Copy-then-modify for golden files.** Never create the golden file from scratch if an initial file exists. `shutil.copy(initial, golden)` then open and modify. This preserves metadata, print settings, and other invisible properties that a from-scratch file would lack.

6. **Pivot tables cannot be created by openpyxl.** openpyxl can only read/preserve existing pivot tables. If you need to create one, use a template file with the pivot table already built.

7. **Filters are definition-only.** `ws.auto_filter.ref = "A1:D20"` sets the range, but rows are NOT actually hidden/filtered. Filtering only takes effect when the file is opened in LibreOffice.

8. **`showDropDown=False` means SHOW the dropdown.** In DataValidation, this boolean is inverted from what you'd expect. Set `False` to display the dropdown arrow.

9. **Chart type naming.** `BarChart(type="col")` = vertical column chart. `BarChart(type="bar")` = horizontal bar chart. This does not match LibreOffice's menu names.

10. **Styles are immutable after assignment.** You cannot do `cell.font.bold = True`. You must create a new Font object: `cell.font = Font(bold=True, ...)`. Same for Fill, Alignment, Border.

11. **Theme colors may return None for `.rgb`.** If a cell uses a theme color instead of explicit RGB, `cell.font.color.rgb` can be `None` or a theme index. Always wrap color reads in try/except.

12. **`data_only=True` loses formulas.** Loading with `data_only=True` replaces formulas with their cached values. If you need both the formula and the value, load the file twice — once normally, once with `data_only=True`.
