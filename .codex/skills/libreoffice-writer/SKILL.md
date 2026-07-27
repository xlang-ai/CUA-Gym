---
name: libreoffice-writer
description: "How to programmatically create, modify, and verify LibreOffice Writer (.docx) files using Python python-docx. For setup-gen and reward-gen agents."
user-invocable: false
---

# LibreOffice Writer — Python Manipulation Guide

This skill teaches **setup-gen** (create/modify docx) and **reward-gen** (read/verify docx) how to work with document files using pure Python code.

- Library: `python-docx`
- Install: `pip3 install python-docx Pillow`

---

## 0. GUI Startup on VM (for setup-gen)

After generating `/home/user/<task_id>_initial.docx`, setup-gen should open it in LibreOffice Writer for the GUI agent.

CRITICAL VM LIMIT: GUI launches must set `DISPLAY=:0`.

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

launch_gui('libreoffice --writer "/home/user/<task_id>_initial.docx"', delay_sec=2.0)
```

Guidelines:
- Open initial artifact, never golden artifact.
- Use non-blocking launch (`Popen`) and short delays.

---

## 1. Creating & Writing Files (setup-gen)

### Basic Document

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_TAB_ALIGNMENT, WD_TAB_LEADER, WD_COLOR_INDEX
from docx.enum.section import WD_ORIENT, WD_SECTION_START
from docx.oxml.ns import qn
import shutil

doc = Document()
doc.add_heading("Title", level=0)
para = doc.add_paragraph("First paragraph.")
doc.add_paragraph("Bullet item", style="List Bullet")
doc.add_paragraph("Numbered item", style="List Number")
doc.save("/home/user/output.docx")
```

### Font Formatting (Runs)

```python
para = doc.add_paragraph()
run = para.add_run("Styled text")
run.bold = True
run.italic = True
run.underline = True
run.font.strike = True           # strikethrough
run.font.name = "Times New Roman"
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

run_sub = para.add_run("2")
run_sub.font.subscript = True    # or .superscript = True
```

### Paragraph Formatting

```python
para = doc.add_paragraph("Centered")
para.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # LEFT, RIGHT, JUSTIFY
para.paragraph_format.line_spacing = 2.0      # 1.0=single, 1.5, 2.0=double
para.paragraph_format.space_before = Pt(12)
para.paragraph_format.space_after = Pt(6)
para.paragraph_format.left_indent = Inches(0.5)
para.paragraph_format.first_line_indent = Inches(0.25)
para.paragraph_format.page_break_before = True
```

### Tab Stops

```python
tab_stops = para.paragraph_format.tab_stops
tab_stops.add_tab_stop(Inches(2), WD_TAB_ALIGNMENT.LEFT)
tab_stops.add_tab_stop(Inches(3.5), WD_TAB_ALIGNMENT.CENTER)
tab_stops.add_tab_stop(Inches(6), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
para.add_run("Col1\tCol2\tCol3")
```

### Tables

```python
table = doc.add_table(rows=3, cols=4)
table.style = "Table Grid"
table.cell(0, 0).text = "Header"
# Formatted cell text
cell = table.cell(1, 0)
run = cell.paragraphs[0].add_run("Bold red")
run.bold = True
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
# Add row, merge cells
table.add_row().cells[0].text = "New row"
table.cell(0, 0).merge(table.cell(0, 1))
```

### Images

```python
doc.add_picture("/home/user/image.png", width=Inches(4))
# In a table cell
run = table.cell(1, 2).paragraphs[0].add_run()
run.add_picture("/home/user/image.png", width=Inches(1.5))
```

### Page Breaks

```python
doc.add_page_break()  # simplest
# Or via run
run = para.add_run()
br = run._element.makeelement(qn('w:br'), {qn('w:type'): 'page'})
run._element.append(br)
```

### Headers, Footers & Page Numbers

```python
section = doc.sections[0]
header = section.header
header.is_linked_to_previous = False
header.paragraphs[0].text = "Document Header"

footer = section.footer
footer.is_linked_to_previous = False
fp = footer.paragraphs[0]
fp.text = "Page "
# Page number field code
r1 = fp.add_run()
r1._element.append(r1._element.makeelement(qn('w:fldChar'), {qn('w:fldCharType'): 'begin'}))
r2 = fp.add_run()
instr = r2._element.makeelement(qn('w:instrText'), {})
instr.text = ' PAGE '
r2._element.append(instr)
r3 = fp.add_run()
r3._element.append(r3._element.makeelement(qn('w:fldChar'), {qn('w:fldCharType'): 'end'}))
```

### Page Setup

```python
section = doc.sections[0]
section.page_width = Inches(8.5)
section.page_height = Inches(11)
section.left_margin = Inches(1)
section.right_margin = Inches(1)
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)
# Landscape
section.orientation = WD_ORIENT.LANDSCAPE
section.page_width, section.page_height = section.page_height, section.page_width
```

### Highlighting

```python
run = para.add_run("Highlighted")
run.font.highlight_color = WD_COLOR_INDEX.YELLOW  # GREEN, CYAN, PINK, RED, etc.
run.font.highlight_color = None  # remove
```

### Modifying Existing Files

```python
shutil.copy("/home/user/original.docx", "/home/user/modified.docx")  # ALWAYS copy first
doc = Document("/home/user/modified.docx")
for para in doc.paragraphs:
    for run in para.runs:
        run.font.name = "Calibri"
doc.save("/home/user/modified.docx")
```

---

## 2. Reading & Verifying Files (reward-gen)

### Loading & Structure

```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_TAB_ALIGNMENT

doc = Document("/path/to/file.docx")
num_paras = len(doc.paragraphs)
num_tables = len(doc.tables)
num_sections = len(doc.sections)
```

### Reading Text & Font Properties

```python
for para in doc.paragraphs:
    # para.text — full text (all runs concatenated)
    for run in para.runs:
        run.text                    # run text
        run.font.name               # "Arial" or None
        run.font.size               # EMU value; use .pt for float (e.g. 12.0)
        run.font.bold               # True / False / None (None=inherit)
        run.font.italic             # True / False / None
        run.font.underline          # True / False / None
        run.font.strike             # True / False / None (strikethrough)
        run.font.subscript          # True / False / None
        run.font.superscript        # True / False / None
        run.font.color.rgb          # RGBColor or None
        run.font.highlight_color    # WD_COLOR_INDEX or None
```

### Verifying Paragraph Format

```python
pf = para.paragraph_format
pf.alignment              # WD_PARAGRAPH_ALIGNMENT enum or None
pf.line_spacing           # float (1.0, 2.0) or Pt or None
pf.space_before           # Pt or None
pf.space_after            # Pt or None
pf.left_indent            # EMU or None
pf.first_line_indent      # EMU or None
pf.page_break_before      # True / False / None
```

### Verifying Tab Stops

```python
for ts in para.paragraph_format.tab_stops:
    # Filter defaults: skip CLEAR and LEFT+position=0
    if ts.alignment == WD_TAB_ALIGNMENT.CLEAR: continue
    if ts.alignment == WD_TAB_ALIGNMENT.LEFT and ts.position == 0: continue
    print(f"Alignment={ts.alignment}, Position={ts.position}")
```

### Verifying Tables

```python
for table in doc.tables:
    for i, row in enumerate(table.rows):
        for j, cell in enumerate(row.cells):
            text = cell.text.strip()
            for para in cell.paragraphs:
                for run in para.runs:
                    # run.font.bold, .color.rgb, etc.
                    pass
```

### Verifying Images

```python
from io import BytesIO
from PIL import Image

def extract_images(doc):
    images = []
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            images.append(BytesIO(rel.target_part.blob))
    return images

# Check inline image in run via XML
has_image = 'graphicData' in run._element.xml
```

### Verifying Page Breaks

```python
def count_page_breaks(doc):
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    count = 0
    for para in doc.paragraphs:
        for run in para.runs:
            for br in run.element.findall('.//w:br', ns):
                if br.attrib.get(f'{{{ns["w"]}}}type') == 'page':
                    count += 1
    return count
```

### Verifying Headers, Footers & Page Numbers

```python
section = doc.sections[0]
header_text = section.header.paragraphs[0].text if section.header.paragraphs else ""
footer_text = section.footer.paragraphs[0].text if section.footer.paragraphs else ""
has_page_num = any(c.isdigit() for c in footer_text)
```

### Verifying Page Setup

```python
s = doc.sections[0]
# s.page_width, s.page_height, s.left_margin, s.right_margin, s.top_margin, s.bottom_margin (EMU)
from docx.enum.section import WD_ORIENT
is_landscape = s.orientation == WD_ORIENT.LANDSCAPE
```

### Verifying Highlighting & Strikethrough

```python
# Highlight check
for run in para.runs:
    if run.font.highlight_color is not None:
        print(f"Highlighted: '{run.text}' color={run.font.highlight_color}")

# Strikethrough on last paragraph
last_para = doc.paragraphs[-1]
all_strike = all(run.font.strike for run in last_para.runs if run.text.strip())
```

### Verifying Case Conversion

```python
def has_uppercase(doc):
    for para in doc.paragraphs:
        for run in para.runs:
            if run.text.strip() and run.text.isupper(): return True
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if run.text.strip() and run.text.isupper(): return True
    return False
```

### Verifying Colored Words in Tables

```python
from math import sqrt

def color_distance(c1, c2):
    return sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    if run.text and run.font.color.rgb:
                        first = run.text[0].lower()
                        if first in 'aeiou':
                            assert color_distance(run.font.color.rgb, RGBColor(255,0,0)) < 50
                        else:
                            assert color_distance(run.font.color.rgb, RGBColor(0,0,255)) < 50
```

### ODF (.odt) File Verification

```python
from odf.opendocument import load
from odf.text import P, Span

odt_doc = load("/path/to/file.odt")
for para in odt_doc.getElementsByType(P):
    text_parts = []
    for node in para.childNodes:
        if node.nodeType == node.TEXT_NODE:
            text_parts.append(node.data)
        elif node.nodeType == node.ELEMENT_NODE and node.tagName == 'text:span':
            for child in node.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    text_parts.append(child.data)

# Check ODT highlighting (background color in automatic styles)
for span in odt_doc.getElementsByType(Span):
    style_name = span.getAttribute('stylename')
    if style_name:
        for auto_style in odt_doc.automaticstyles.childNodes:
            if auto_style.getAttribute('name') == style_name:
                for prop in auto_style.childNodes:
                    if prop.getAttribute('backgroundcolor') == '#ffff00':
                        print("Yellow highlight found!")
```

### Common Helpers for reward.py

```python
import re

def compare_text(doc1, doc2, ignore_blanks=True):
    p1 = [p.text for p in doc1.paragraphs]
    p2 = [p.text for p in doc2.paragraphs]
    if ignore_blanks:
        return re.sub(r'\s+', ' ', '\n'.join(p1)).strip() == re.sub(r'\s+', ' ', '\n'.join(p2)).strip()
    return p1 == p2

def check_all_font_name(doc, expected):
    return all(run.font.name == expected for para in doc.paragraphs for run in para.runs if run.font.name)

def check_italic_size(doc, expected_pt):
    return all(run.font.size and run.font.size.pt == expected_pt
               for para in doc.paragraphs for run in para.runs if run.italic)
```

---

## 3. Bitter Lessons

1. **`run.font.size` is EMU, not points.** `run.font.size == 14` fails. Use `run.font.size.pt == 14` or `run.font.size == Pt(14)`.

2. **`para.text` concatenates runs, losing formatting.** To check per-run formatting (bold word + normal), iterate `para.runs`. Never rely on `para.text` for style checks.

3. **`None` means "inherited" for font properties.** `run.font.bold is None` means "inherit from style". If the style is bold, None means bold. Usually treat None as False, but be aware.

4. **Page breaks are inside runs, not paragraphs.** Manual breaks are `<w:br w:type="page"/>` in run elements. Use XML parsing: `run.element.findall('.//w:br', ns)`. Cannot detect via `para.text`.

5. **Highlighting differs between .docx and .odt.** `run.font.highlight_color` works for .docx. ODT stores highlights in automatic styles as `backgroundcolor`. Need different code paths.

6. **Copy-then-modify for golden files.** `shutil.copy(initial, golden)` then modify. Scratch files lack styles, numbering, and metadata causing comparison failures.

7. **Tab stop comparison must filter defaults.** LibreOffice adds default LEFT@0 and CLEAR stops. Filter them out to avoid false mismatches.

8. **`ignore_blanks=True` collapses all whitespace.** When paragraph structure (empty lines) matters, use `ignore_blanks=False` and compare paragraph-by-paragraph.

9. **Footer page numbers are field codes, not text.** `<w:fldChar>` + `<w:instrText> PAGE </w:instrText>`. The `.text` property shows cached values. Check for digit presence, not exact number.

10. **`doc.part.rels` images include ALL images.** Headers, footers, textboxes too. Not just body. Filter if needed.

11. **`para.runs` may miss hyperlink/field text.** `para.text` includes all text, but `''.join(r.text for r in para.runs)` may be shorter. Use `para.text` for full text comparison.

12. **Color comparison: use perceptual distance.** The evaluator uses CIEDE2000 (Delta E) with threshold ~3.5 from `skimage.color.deltaE_ciede2000`. Simple RGB distance is imprecise.

13. **Equations are OLE objects.** Detect with `run.element.xpath('.//w:object')`. No readable text via python-docx.

14. **Multiple gold files for tolerance.** LibreOffice formatting varies by version/fonts. Provide 2-4 gold files with OR logic in reward scripts.
