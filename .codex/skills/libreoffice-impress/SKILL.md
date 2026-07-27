---
name: libreoffice-impress
description: "How to programmatically create, modify, and verify LibreOffice Impress (.pptx) files using Python python-pptx. For setup-gen and reward-gen agents."
user-invocable: false
---

# LibreOffice Impress — Python Manipulation Guide

This skill teaches **setup-gen** (create/modify pptx) and **reward-gen** (read/verify pptx) how to work with presentation files using pure Python code.

- Library: `python-pptx`
- Install: `pip3 install python-pptx Pillow`

---

## 0. GUI Startup on VM (for setup-gen)

After generating `/home/user/<task_id>_initial.pptx`, setup-gen should open it in LibreOffice Impress for the GUI agent.

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

launch_gui('libreoffice --impress "/home/user/<task_id>_initial.pptx"', delay_sec=2.0)
```

Guidelines:
- Open initial artifact, never golden artifact.
- Use non-blocking launch (`Popen`) and short delays.

---

## 1. Creating & Writing Files (setup-gen)

### Basic Presentation & Slides

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE
import shutil, copy, zipfile, xml.etree.ElementTree as ET

prs = Presentation()
# Layouts: 0=Title Slide, 1=Title+Content, 5=Blank, 6=Title Only (default template)
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = "My Presentation"
slide.placeholders[1].text = "Subtitle"

# Portrait orientation: width < height
prs.slide_width = Inches(7.5)
prs.slide_height = Inches(10)

prs.save("/home/user/output.pptx")
```

### Text Boxes & Font Formatting

```python
slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank
txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(2))
tf = txBox.text_frame
tf.word_wrap = True

p = tf.paragraphs[0]
p.text = "Centered text"
p.alignment = PP_ALIGN.CENTER  # LEFT, CENTER, RIGHT, JUSTIFY

# Font on runs
run = p.runs[0]
run.font.name = "Arial"
run.font.size = Pt(24)
run.font.bold = True
run.font.italic = True
run.font.underline = True
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)

# Add run, add paragraph
run2 = p.add_run()
run2.text = " blue text"
run2.font.color.rgb = RGBColor(0x00, 0x00, 0xFF)

p2 = tf.add_paragraph()
p2.text = "Second paragraph"
p2.level = 1  # indent level (0-8), controls bullet depth
```

### Strikethrough & Bullets via XML

```python
from pptx.oxml.ns import qn

# Strikethrough (no direct API)
run.font._element.attrib['strike'] = 'sngStrike'  # 'noStrike', 'sngStrike', 'dblStrike'

# Custom bullet character + color
pPr = p._p.get_or_add_pPr()
pPr.append(pPr.makeelement(qn('a:buChar'), {'char': '●'}))
buClr = pPr.makeelement(qn('a:buClr'), {})
buClr.append(buClr.makeelement(qn('a:srgbClr'), {'val': 'FF0000'}))
pPr.append(buClr)
```

### Tables

```python
table_shape = slide.shapes.add_table(4, 3, Inches(1), Inches(2), Inches(6), Inches(2))
table = table_shape.table
table.cell(0, 0).text = "Header"
table.columns[0].width = Inches(2)

# Style cell text
for run in table.cell(0, 0).text_frame.paragraphs[0].runs:
    run.font.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
```

### Images

```python
# Add with position/size; stretch to fill; center on slide
pic = slide.shapes.add_picture("/home/user/img.png", Inches(1), Inches(1), Inches(4), Inches(3))
pic = slide.shapes.add_picture("/home/user/img.png", 0, 0, prs.slide_width, prs.slide_height)
w, h = Inches(4), Inches(3)
pic = slide.shapes.add_picture("/home/user/img.png", (prs.slide_width-w)//2, (prs.slide_height-h)//2, w, h)
```

### Background Color & Notes

```python
# Background
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

# Notes
slide.notes_slide.notes_text_frame.text = "Speaker notes here"
```

### Duplicate & Reorder Slides

```python
def duplicate_slide(prs, slide):
    new_slide = prs.slides.add_slide(slide.slide_layout)
    for shape in slide.shapes:
        new_slide.shapes._spTree.append(copy.deepcopy(shape.element))
    if slide.background.fill.type is not None:
        new_slide.background._element.getparent().replace(
            new_slide.background._element, copy.deepcopy(slide.background._element))
    return new_slide

def move_slide(prs, old_idx, new_idx):
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    el = slides[old_idx]
    xml_slides.remove(el)
    xml_slides.insert(new_idx, el) if new_idx < len(slides) else xml_slides.append(el)
```

### Modifying Existing Files

```python
shutil.copy("/home/user/original.pptx", "/home/user/modified.pptx")  # ALWAYS copy first
prs = Presentation("/home/user/modified.pptx")
for shape in prs.slides[0].shapes:
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                run.font.name = "Times New Roman"
prs.save("/home/user/modified.pptx")
```

---

## 2. Reading & Verifying Files (reward-gen)

### Loading & Basic Properties

```python
prs = Presentation("/path/to/file.pptx")
num_slides = len(prs.slides)
is_portrait = prs.slide_width < prs.slide_height
```

### Reading Text & Font Properties

```python
for shape in prs.slides[0].shapes:
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            # para.text, para.level, para.alignment (PP_ALIGN or None)
            for run in para.runs:
                # run.text, run.font.name, run.font.size (EMU), run.font.bold/italic/underline (True/False/None)
                if run.font.color.type is not None:
                    rgb = run.font.color.rgb  # RGBColor; str(rgb) → "FF0000"
                strike = run.font._element.attrib.get('strike', 'noStrike')
```

### Verifying Shape Position & Size

```python
def is_approximately_equal(val1, val2, tolerance=0.005):
    if val1 == val2: return True
    if val1 == 0 or val2 == 0: return val1 == val2
    return abs(val1 - val2) / max(abs(val1), abs(val2)) <= tolerance

shape = prs.slides[0].shapes[0]
# shape.left, shape.top, shape.width, shape.height — all in EMU (914400 EMU = 1 inch)
```

### Verifying Tables

```python
for shape in slide.shapes:
    if shape.shape_type == MSO_SHAPE_TYPE.TABLE:
        table = shape.table
        # len(table.rows), len(table.columns), table.cell(r, c).text
        for para in table.cell(0, 0).text_frame.paragraphs:
            for run in para.runs:
                # run.font.bold, run.font.color.rgb, etc.
                pass
```

### Verifying Images

```python
for shape in slide.shapes:
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:  # type 13
        # shape.left, shape.top, shape.width, shape.height
        img_blob = shape.image.blob  # bytes — use for identity comparison
```

### Verifying Background & Notes

```python
def get_slide_background_rgb(slide):
    fill = slide.background.fill
    if fill.type == 1: return fill.fore_color.rgb
    elif fill.type == 5:  # inherited from master
        master_fill = slide.slide_layout.slide_master.background.fill
        return master_fill.fore_color.rgb if master_fill.type == 1 else None
    return None

def get_slide_notes(slide):
    try: return slide.notes_slide.notes_text_frame.text.strip()
    except: return ""
```

### Getting All Text Shapes (Including Groups)

```python
def get_all_text_shapes(slide):
    def extract(shape):
        results = []
        if hasattr(shape, "text") and hasattr(shape, "text_frame"):
            results.append(shape)
        if hasattr(shape, 'shapes'):
            for sub in shape.shapes:
                results.extend(extract(sub))
        return results
    out = []
    for shape in slide.shapes:
        out.extend(extract(shape))
    return out
```

### Verifying Transitions (via ZIP/XML)

```python
def check_transition(pptx_path, slide_idx, expected_type):
    """slide_idx is 0-based. expected_type: 'dissolve', 'fade', 'push', etc."""
    ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
    with zipfile.ZipFile(pptx_path, 'r') as zf:
        try:
            with zf.open(f'ppt/slides/slide{slide_idx + 1}.xml') as f:
                root = ET.parse(f).getroot()
                tr = root.find('.//p:transition', ns)
                return tr is not None and tr.find(f'.//p:{expected_type}', ns) is not None
        except KeyError:
            return False
```

### Verifying Bullets & Page Number Colors (via ZIP/XML)

```python
def extract_bullets(pptx_path, slide_idx):
    ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
    bullets = []
    with zipfile.ZipFile(pptx_path, 'r') as zf:
        with zf.open(f'ppt/slides/slide{slide_idx + 1}.xml') as f:
            root = ET.parse(f).getroot()
            for para in root.findall('.//a:p', ns):
                pPr = para.find('a:pPr', ns)
                lvl = pPr.get('lvl') if pPr is not None else None
                buChar = pPr.find('a:buChar', ns) if pPr is not None else None
                char = buChar.get('char') if buChar is not None else None
                text = "".join(t.text or "" for t in para.findall('.//a:t', ns))
                if text.strip():
                    bullets.append((lvl, char, text))
    return bullets

def get_page_number_color(pptx_path):
    ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
          'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
    with zipfile.ZipFile(pptx_path, 'r') as zf:
        with zf.open('ppt/slideMasters/slideMaster1.xml') as f:
            root = ET.parse(f).getroot()
            for ph in root.findall('.//p:ph[@type="sldNum"]', ns):
                clr = ph.find('.//a:solidFill//a:srgbClr', ns)
                if clr is not None:
                    return clr.get('val')  # e.g. "FF0000"
    return None
```

### Comparison Helpers for reward.py

```python
def check_font_prop(run, prop, expected):
    actual = getattr(run.font, prop)
    if prop in ('bold', 'italic'):  # normalize None→False
        actual = False if actual is None else actual
        expected = False if expected is None else expected
    return actual == expected

def nonempty_runs(para):
    return [r for r in para.runs if (r.text or "").strip()]
```

---

## 3. Bitter Lessons

1. **`None` vs `False` for bold/italic.** `run.font.bold` returns `None` (inherit), `True`, or `False`. Treat `None` and `False` as equivalent ("not bold"). Same for italic.

2. **Alignment `None` means LEFT.** `para.alignment` is `None` when no explicit alignment is set, defaulting to left. Normalize `None` to `PP_ALIGN.LEFT` when comparing.

3. **Strikethrough requires XML access.** No `run.font.strikethrough`. Use `run.font._element.attrib.get('strike', 'noStrike')`. Values: `'noStrike'`, `'sngStrike'`, `'dblStrike'`.

4. **Empty paragraph run normalization.** Empty paragraphs may have 0 runs or 1 empty run. Filter with `[r for r in para.runs if (r.text or "").strip()]` to avoid false mismatches.

5. **Font color can be None or theme-based.** `run.font.color.rgb` raises `AttributeError` if type is not RGB. Always check `run.font.color.type is not None` first, or wrap in try/except.

6. **Shape positions use EMU, not inches.** All values are EMU (914400 = 1 inch). Use `Inches()` / `Emu()`. Never compare to float inches.

7. **Transitions & page number colors need ZIP/XML.** Not accessible via python-pptx API. Parse `ppt/slides/slideN.xml` for transitions, `ppt/slideMasters/slideMaster1.xml` for page number colors.

8. **Background fill type 5 = inherited from master.** Fall back to `slide.slide_layout.slide_master.background.fill` for actual color.

9. **Layout indices vary by template.** When modifying existing files, use the slide's own layout instead of assuming index mappings.

10. **Copy-then-modify for golden files.** `shutil.copy(initial, golden)` then modify. From-scratch files lack theme/master data, causing comparison failures.

11. **GROUP shapes hide nested text.** Recursively traverse `shape.shapes` to find text in GROUP shapes. The evaluator checks these.

12. **Image identity = binary blob.** `shape.image.blob` matches byte-for-byte. Resize/reposition doesn't change the blob.

13. **Position tolerance: 0.5%.** Use relative tolerance `abs(a-b)/max(a,b) <= 0.005` for shape comparisons.

14. **Accessing `slide.notes_slide` creates one.** If notes shouldn't exist, don't access this property during setup.
