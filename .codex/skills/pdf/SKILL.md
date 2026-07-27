---
name: pdf
description: "How to programmatically create, modify, and verify PDF files using Python PyMuPDF (fitz), pikepdf, and reportlab. For setup-gen and reward-gen agents."
user-invocable: false
---

# PDF — Python Manipulation Guide

This skill teaches **setup-gen** (create/modify PDFs) and **reward-gen** (read/verify PDF properties) how to work with PDF files using pure Python code.

- Libraries: `PyMuPDF` (fitz), `pikepdf`, `reportlab`
- Install: `pip3 install PyMuPDF pikepdf reportlab`
- File formats: `.pdf`
- PDF viewers on VM: `evince` (GNOME default), `okular`, `xdg-open`

**Library roles:**
| Library | Strength | Use for |
|---------|----------|---------|
| **PyMuPDF (fitz)** | Read/write/annotate/render | Most setup & all reward tasks |
| **pikepdf** | Low-level PDF structure, encryption, metadata | Encryption, metadata, merge/split |
| **reportlab** | Create PDFs from scratch with complex layouts | Rich document generation |

---

## 0. GUI Startup on VM (for setup-gen)

After generating `/home/user/<task_id>_initial.pdf`, setup-gen should open the PDF in Evince for the GUI agent.

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

# Open initial PDF in Evince (GNOME default PDF viewer)
launch_gui('evince "/home/user/<task_id>_initial.pdf"', delay_sec=2.0)

# Open at a specific page
launch_gui('evince --page-index=3 "/home/user/<task_id>_initial.pdf"', delay_sec=2.0)

# Open in presentation mode
launch_gui('evince --presentation "/home/user/<task_id>_initial.pdf"', delay_sec=2.0)

# Alternative: use xdg-open (system default)
launch_gui('xdg-open "/home/user/<task_id>_initial.pdf"', delay_sec=2.0)
```

Guidelines:
- Open `*_initial.pdf`, never `*_golden.pdf`.
- Use non-blocking launch (`Popen`) and short delays.
- Evince is preferred over okular for GNOME desktops.

---

## 1. Creating & Modifying PDFs (setup-gen)

### 1.1 PyMuPDF (fitz) — Primary Tool

#### Creating a New PDF

```python
import pymupdf  # or: import fitz
import shutil

# Create blank PDF with one page
doc = pymupdf.open()  # new empty PDF
page = doc.new_page(width=595, height=842)  # A4 size in points (72 pts/inch)
# Letter size: width=612, height=792
doc.save("/home/user/Desktop/blank.pdf")
doc.close()
```

#### Page Size Constants

```python
# Common sizes in points (72 pts = 1 inch)
A4_WIDTH, A4_HEIGHT = 595, 842          # 210mm x 297mm
LETTER_WIDTH, LETTER_HEIGHT = 612, 792  # 8.5" x 11"
A3_WIDTH, A3_HEIGHT = 842, 1191         # 297mm x 420mm
LEGAL_WIDTH, LEGAL_HEIGHT = 612, 1008   # 8.5" x 14"
```

#### Inserting Text

```python
doc = pymupdf.open()
page = doc.new_page(width=595, height=842)

# Simple text insertion at a point (x, y from top-left)
page.insert_text(
    pymupdf.Point(72, 72),      # position (1 inch from top-left)
    "Hello, World!",
    fontsize=16,
    fontname="helv",             # Helvetica (built-in)
    color=(0, 0, 0),             # black, RGB floats 0-1
)

# Text with different fonts
page.insert_text(pymupdf.Point(72, 100), "Bold Helvetica", fontsize=12, fontname="hebo")  # Helvetica-Bold
page.insert_text(pymupdf.Point(72, 120), "Italic Times", fontsize=12, fontname="tiit")    # Times-Italic
page.insert_text(pymupdf.Point(72, 140), "Courier", fontsize=12, fontname="cour")         # Courier

# Text in a bounded rectangle (auto-wraps)
rect = pymupdf.Rect(72, 200, 523, 400)  # (x0, y0, x1, y1)
excess = page.insert_textbox(
    rect,
    "This is a long paragraph that will automatically wrap within the rectangle boundaries. "
    "The function returns excess text that didn't fit.",
    fontsize=11,
    fontname="helv",
    color=(0, 0, 0),
    align=pymupdf.TEXT_ALIGN_JUSTIFY,  # LEFT=0, CENTER=1, RIGHT=2, JUSTIFY=3
)

doc.save("/home/user/Desktop/text.pdf")
doc.close()
```

#### Built-in Font Names

```
helv     = Helvetica              hebo = Helvetica-Bold
heit     = Helvetica-Oblique      hebi = Helvetica-BoldOblique
tiro     = Times-Roman            tibo = Times-Bold
tiit     = Times-Italic           tibi = Times-BoldItalic
cour     = Courier                cobo = Courier-Bold
coit     = Courier-Oblique        cobi = Courier-BoldOblique
symb     = Symbol                 zadb = ZapfDingbats
```

#### Using Custom/External Fonts

```python
import pymupdf

doc = pymupdf.open()
page = doc.new_page()

# Register an external TrueType font
font = pymupdf.Font(fontfile="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
# Or use a built-in font by name:
# font = pymupdf.Font("helv")

tw = pymupdf.TextWriter(page.rect)
tw.append(pymupdf.Point(72, 72), "Custom font text", font=font, fontsize=14)
tw.write_text(page, color=(0, 0, 0))

doc.save("/home/user/Desktop/custom_font.pdf")
doc.close()
```

#### Inserting HTML Content (Stories)

```python
import pymupdf

doc = pymupdf.open()

# Create formatted content from HTML
html = """
<h1 style="color: navy;">Quarterly Report</h1>
<p style="font-size: 12px;">This report covers Q1 2024 performance metrics.</p>
<table border="1">
    <tr><th>Month</th><th>Revenue</th><th>Growth</th></tr>
    <tr><td>January</td><td>$50,000</td><td>+5%</td></tr>
    <tr><td>February</td><td>$55,000</td><td>+10%</td></tr>
    <tr><td>March</td><td>$60,000</td><td>+9%</td></tr>
</table>
<p><b>Summary:</b> Strong growth trajectory across all metrics.</p>
"""

story = pymupdf.Story(html=html)
body = story.body

# Layout story onto pages
writer = pymupdf.DocumentWriter(doc)
content_rect = pymupdf.Rect(72, 72, 523, 770)  # margins: ~1 inch

more = True
while more:
    dev = writer.begin_page(pymupdf.Rect(0, 0, 595, 842))
    more, _ = story.place(content_rect)
    story.draw(dev)
    writer.end_page()

writer.close()
doc.save("/home/user/Desktop/html_report.pdf")
doc.close()
```

#### Drawing Shapes

```python
doc = pymupdf.open()
page = doc.new_page()
shape = page.new_shape()

# Rectangle
rect = pymupdf.Rect(100, 100, 300, 200)
shape.draw_rect(rect)
shape.finish(color=(0, 0, 1), fill=(0.8, 0.8, 1), width=2)  # blue border, light blue fill

# Circle
shape.draw_circle(pymupdf.Point(400, 150), 50)  # center, radius
shape.finish(color=(1, 0, 0), fill=(1, 0.8, 0.8), width=1.5)

# Line
shape.draw_line(pymupdf.Point(72, 300), pymupdf.Point(523, 300))
shape.finish(color=(0, 0, 0), width=1, dashes="[3 3]")  # dashed line

# Polygon (triangle)
shape.draw_polyline([
    pymupdf.Point(200, 400),
    pymupdf.Point(150, 500),
    pymupdf.Point(250, 500),
    pymupdf.Point(200, 400),  # close the polygon
])
shape.finish(color=(0, 0.5, 0), fill=(0, 1, 0), width=1)

# Bezier curve
shape.draw_bezier(
    pymupdf.Point(300, 400),  # start
    pymupdf.Point(350, 350),  # control 1
    pymupdf.Point(450, 450),  # control 2
    pymupdf.Point(500, 400),  # end
)
shape.finish(color=(0.5, 0, 0.5), width=2)

shape.commit()  # CRITICAL: must commit all shapes to page
doc.save("/home/user/Desktop/shapes.pdf")
doc.close()
```

#### Inserting Images

```python
doc = pymupdf.open()
page = doc.new_page()

# Insert image from file into a rectangle
img_rect = pymupdf.Rect(72, 72, 300, 250)
page.insert_image(img_rect, filename="/home/user/Desktop/photo.png")

# Insert image from bytes
with open("/home/user/Desktop/logo.png", "rb") as f:
    img_data = f.read()
page.insert_image(pymupdf.Rect(350, 72, 523, 200), stream=img_data)

# Insert with rotation (0, 90, 180, 270)
page.insert_image(pymupdf.Rect(72, 300, 250, 500), filename="/home/user/Desktop/photo.png", rotate=90)

# Insert keeping aspect ratio — use Rect.fit() to calculate
img_doc = pymupdf.open("/home/user/Desktop/photo.png")
img_page = img_doc[0]
img_w, img_h = img_page.rect.width, img_page.rect.height
target = pymupdf.Rect(72, 500, 300, 700)
# Scale image rect to fit within target maintaining aspect ratio
scale = min(target.width / img_w, target.height / img_h)
img_doc.close()

doc.save("/home/user/Desktop/images.pdf")
doc.close()
```

#### Adding Annotations

```python
doc = pymupdf.open("/home/user/Desktop/document.pdf")
page = doc[0]

# Highlight text (search first, then highlight)
text_instances = page.search_for("important")
for inst in text_instances:
    highlight = page.add_highlight_annot(inst)
    highlight.set_colors(stroke=(1, 1, 0))  # yellow
    highlight.update()

# Underline text
for inst in page.search_for("underline this"):
    annot = page.add_underline_annot(inst)
    annot.update()

# Strikeout text
for inst in page.search_for("delete this"):
    annot = page.add_strikeout_annot(inst)
    annot.update()

# Sticky note (text annotation)
annot = page.add_text_annot(
    pymupdf.Point(100, 100),
    "This is a comment note",
    icon="Note"  # "Comment", "Key", "Note", "Help", "NewParagraph", "Paragraph", "Insert"
)
annot.set_colors(stroke=(1, 0.8, 0))  # orange icon
annot.update()

# FreeText annotation (text directly on page)
annot = page.add_freetext_annot(
    pymupdf.Rect(72, 600, 300, 640),
    "This is an inline comment",
    fontsize=10,
    fontname="helv",
    text_color=(1, 0, 0),     # red text
    fill_color=(1, 1, 0.8),   # light yellow background
    border_color=(0, 0, 0),   # black border
)
annot.update()

# Rectangle annotation (box around area)
annot = page.add_rect_annot(pymupdf.Rect(350, 200, 500, 300))
annot.set_colors(stroke=(1, 0, 0))  # red border
annot.set_border(width=2)
annot.update()

# Ink annotation (freehand drawing)
annot = page.add_ink_annot([
    [pymupdf.Point(100, 400), pymupdf.Point(150, 380), pymupdf.Point(200, 420)],
])
annot.set_colors(stroke=(0, 0, 1))  # blue ink
annot.set_border(width=2)
annot.update()

# Stamp annotation
annot = page.add_stamp_annot(
    pymupdf.Rect(350, 400, 500, 460),
    stamp=0  # 0=Approved, 1=AsIs, 2=Confidential, 3=Departmental, etc.
)
annot.update()

doc.save("/home/user/Desktop/annotated.pdf")
doc.close()
```

#### Adding Links

```python
doc = pymupdf.open("/home/user/Desktop/document.pdf")
page = doc[0]

# Link to external URL
link_rect = pymupdf.Rect(72, 700, 250, 720)
page.insert_link({
    "kind": pymupdf.LINK_URI,
    "from": link_rect,
    "uri": "https://www.example.com",
})

# Link to another page within PDF (internal link)
page.insert_link({
    "kind": pymupdf.LINK_GOTO,
    "from": pymupdf.Rect(72, 730, 250, 750),
    "page": 2,           # target page number (0-indexed)
    "to": pymupdf.Point(72, 72),  # position on target page
})

# Add visible text for the link
page.insert_text(pymupdf.Point(72, 715), "Click here for example.com",
                 fontsize=10, color=(0, 0, 1))

doc.save("/home/user/Desktop/links.pdf")
doc.close()
```

#### Table of Contents (Bookmarks)

```python
doc = pymupdf.open("/home/user/Desktop/document.pdf")

# Get existing TOC
toc = doc.get_toc()  # returns [[level, title, page_num], ...]

# Set new TOC
new_toc = [
    [1, "Chapter 1: Introduction", 1],
    [2, "1.1 Background", 1],
    [2, "1.2 Objectives", 2],
    [1, "Chapter 2: Methods", 3],
    [2, "2.1 Data Collection", 3],
    [2, "2.2 Analysis", 4],
    [1, "Chapter 3: Results", 5],
]
doc.set_toc(new_toc)

doc.save("/home/user/Desktop/with_toc.pdf")
doc.close()
```

#### Page Manipulation

```python
doc = pymupdf.open("/home/user/Desktop/document.pdf")

# Rotate a page (0, 90, 180, 270)
doc[0].set_rotation(90)

# Delete pages
doc.delete_page(2)            # delete page at index 2
doc.delete_pages(from_page=5, to_page=8)  # delete pages 5-8

# Move page (page 5 to position after page 1)
doc.move_page(5, 1)

# Copy page (copy page 0 to end)
doc.copy_page(0)              # appends copy to end
doc.copy_page(0, 3)           # inserts copy before page 3

# Insert blank pages
doc.new_page(pno=2, width=595, height=842)  # insert A4 blank at index 2
doc.new_page(pno=-1)  # append to end

# Select specific pages (keep only these, remove rest)
doc.select([0, 2, 4, 6])     # keep pages 0, 2, 4, 6 only

# Rearrange pages (reverse order)
page_count = doc.page_count
doc.select(list(range(page_count - 1, -1, -1)))

doc.save("/home/user/Desktop/modified.pdf")
doc.close()
```

#### Merging PDFs

```python
doc1 = pymupdf.open("/home/user/Desktop/file1.pdf")
doc2 = pymupdf.open("/home/user/Desktop/file2.pdf")

# Append all pages of doc2 to doc1
doc1.insert_pdf(doc2)

# Insert specific pages from doc2
doc1.insert_pdf(doc2, from_page=0, to_page=2, start_at=1)  # insert doc2 pages 0-2 after page 0 of doc1

doc1.save("/home/user/Desktop/merged.pdf")
doc1.close()
doc2.close()
```

#### Splitting PDF

```python
doc = pymupdf.open("/home/user/Desktop/big.pdf")

# Split into individual pages
for i in range(doc.page_count):
    new_doc = pymupdf.open()
    new_doc.insert_pdf(doc, from_page=i, to_page=i)
    new_doc.save(f"/home/user/Desktop/page_{i+1}.pdf")
    new_doc.close()

# Split into chunks of N pages
chunk_size = 5
for start in range(0, doc.page_count, chunk_size):
    end = min(start + chunk_size - 1, doc.page_count - 1)
    new_doc = pymupdf.open()
    new_doc.insert_pdf(doc, from_page=start, to_page=end)
    new_doc.save(f"/home/user/Desktop/chunk_{start//chunk_size + 1}.pdf")
    new_doc.close()

doc.close()
```

#### Watermarks & Overlays

```python
doc = pymupdf.open("/home/user/Desktop/document.pdf")

for page in doc:
    # Text watermark (diagonal)
    # Insert with rotation using a text writer
    page.insert_text(
        pymupdf.Point(150, 500),
        "CONFIDENTIAL",
        fontsize=60,
        fontname="helv",
        color=(1, 0, 0),       # red
        rotate=45,             # degrees counter-clockwise
        overlay=True,          # on top of existing content
    )

    # Or use opacity for semi-transparent watermark
    shape = page.new_shape()
    shape.insert_text(
        pymupdf.Point(100, 400),
        "DRAFT",
        fontsize=72,
        fontname="hebo",
        color=(0.8, 0.8, 0.8),
    )
    shape.finish()
    shape.commit()

    # Image watermark
    logo_rect = pymupdf.Rect(400, 700, 520, 770)
    page.insert_image(logo_rect, filename="/home/user/Desktop/watermark.png",
                      overlay=True)

doc.save("/home/user/Desktop/watermarked.pdf")
doc.close()
```

#### Form Fields (Widgets)

```python
import pymupdf

doc = pymupdf.open()
page = doc.new_page()

# Text field
widget = pymupdf.Widget()
widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
widget.field_name = "full_name"
widget.field_value = "John Doe"
widget.rect = pymupdf.Rect(150, 100, 400, 125)
widget.text_fontsize = 12
widget.text_color = (0, 0, 0)
widget.fill_color = (0.95, 0.95, 0.95)
widget.border_color = (0, 0, 0)
widget.border_width = 1
page.add_widget(widget)

# Multi-line text field
widget = pymupdf.Widget()
widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
widget.field_name = "comments"
widget.field_value = ""
widget.field_flags = pymupdf.PDF_TX_FIELD_IS_MULTILINE
widget.rect = pymupdf.Rect(150, 140, 400, 220)
widget.text_fontsize = 10
widget.fill_color = (1, 1, 1)
widget.border_color = (0.5, 0.5, 0.5)
page.add_widget(widget)

# Checkbox
widget = pymupdf.Widget()
widget.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
widget.field_name = "agree_terms"
widget.field_value = "Yes"  # "Yes" = checked, "Off" = unchecked
widget.rect = pymupdf.Rect(150, 240, 170, 260)
widget.border_color = (0, 0, 0)
page.add_widget(widget)

# Combo box (dropdown)
widget = pymupdf.Widget()
widget.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
widget.field_name = "country"
widget.choice_values = ["United States", "Canada", "United Kingdom", "Germany", "Japan"]
widget.field_value = "United States"
widget.rect = pymupdf.Rect(150, 280, 400, 305)
widget.text_fontsize = 11
widget.fill_color = (1, 1, 1)
widget.border_color = (0, 0, 0)
page.add_widget(widget)

# List box
widget = pymupdf.Widget()
widget.field_type = pymupdf.PDF_WIDGET_TYPE_LISTBOX
widget.field_name = "skills"
widget.choice_values = ["Python", "Java", "C++", "JavaScript", "Go", "Rust"]
widget.field_value = "Python"
widget.rect = pymupdf.Rect(150, 320, 400, 420)
widget.text_fontsize = 10
widget.fill_color = (1, 1, 1)
widget.border_color = (0, 0, 0)
page.add_widget(widget)

# Radio button (requires special handling)
widget = pymupdf.Widget()
widget.field_type = pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON
widget.field_name = "priority"
widget.field_value = "High"
widget.rect = pymupdf.Rect(150, 440, 170, 460)
widget.border_color = (0, 0, 0)
page.add_widget(widget)

# Add labels next to fields
page.insert_text(pymupdf.Point(72, 118), "Full Name:", fontsize=12, fontname="hebo")
page.insert_text(pymupdf.Point(72, 158), "Comments:", fontsize=12, fontname="hebo")
page.insert_text(pymupdf.Point(72, 255), "Agree to Terms:", fontsize=12, fontname="hebo")
page.insert_text(pymupdf.Point(72, 298), "Country:", fontsize=12, fontname="hebo")
page.insert_text(pymupdf.Point(72, 338), "Skills:", fontsize=12, fontname="hebo")
page.insert_text(pymupdf.Point(72, 455), "Priority:", fontsize=12, fontname="hebo")

doc.save("/home/user/Desktop/form.pdf")
doc.close()
```

#### Modifying Existing Form Field Values

```python
doc = pymupdf.open("/home/user/Desktop/form.pdf")
page = doc[0]

for widget in page.widgets():
    if widget.field_name == "full_name":
        widget.field_value = "Jane Smith"
        widget.update()
    elif widget.field_name == "country":
        widget.field_value = "Canada"
        widget.update()
    elif widget.field_name == "agree_terms":
        widget.field_value = "Yes"
        widget.update()

doc.save("/home/user/Desktop/filled_form.pdf")
doc.close()
```

#### Setting Metadata

```python
doc = pymupdf.open("/home/user/Desktop/document.pdf")

doc.set_metadata({
    "title": "Annual Report 2024",
    "author": "John Smith",
    "subject": "Financial Performance",
    "keywords": "finance, annual, report, 2024",
    "creator": "CUA-Gym Setup",
    "producer": "PyMuPDF",
})

doc.save("/home/user/Desktop/with_metadata.pdf")
doc.close()
```

#### Page Cropping & CropBox

```python
doc = pymupdf.open("/home/user/Desktop/document.pdf")
page = doc[0]

# Get original mediabox (full page) and cropbox (visible area)
print(page.mediabox)  # Rect(0, 0, 595, 842)
print(page.cropbox)   # Rect(0, 0, 595, 842) — same by default

# Crop page to specific area (trims visible content)
page.set_cropbox(pymupdf.Rect(72, 72, 523, 770))  # 1-inch margins

doc.save("/home/user/Desktop/cropped.pdf")
doc.close()
```

### 1.2 pikepdf — Encryption & Low-Level Operations

#### Encryption

```python
import pikepdf

# Encrypt a PDF
pdf = pikepdf.open("/home/user/Desktop/document.pdf")
pdf.save(
    "/home/user/Desktop/encrypted.pdf",
    encryption=pikepdf.Encryption(
        owner="owner_password_123",  # full permissions password
        user="user_password_456",    # open/view password
        R=6,                         # encryption revision (6 = AES-256)
        allow=pikepdf.Permissions(
            extract=False,           # disallow text extraction
            modify_annotation=True,  # allow annotation editing
            print_lowres=True,       # allow low-res printing
            print_highres=True,      # allow high-res printing
            modify_form=True,        # allow form filling
            modify_other=False,      # disallow other modifications
            modify_assembly=False,   # disallow page assembly
        ),
    ),
)

# Open encrypted PDF
pdf = pikepdf.open("/home/user/Desktop/encrypted.pdf", password="user_password_456")

# Remove encryption (need owner password)
pdf = pikepdf.open("/home/user/Desktop/encrypted.pdf", password="owner_password_123")
pdf.save("/home/user/Desktop/decrypted.pdf")  # save without encryption param = no encryption
```

#### Merge & Split with pikepdf

```python
import pikepdf

# Merge PDFs
output = pikepdf.new()
for path in ["/home/user/Desktop/file1.pdf", "/home/user/Desktop/file2.pdf"]:
    src = pikepdf.open(path)
    output.pages.extend(src.pages)

output.save("/home/user/Desktop/merged.pdf")

# Split: extract pages 2-5 (0-indexed)
pdf = pikepdf.open("/home/user/Desktop/big.pdf")
output = pikepdf.new()
output.pages.extend(pdf.pages[1:5])
output.save("/home/user/Desktop/pages_2_to_5.pdf")

# Reverse page order
pdf = pikepdf.open("/home/user/Desktop/document.pdf")
pdf.pages.reverse()
pdf.save("/home/user/Desktop/reversed.pdf")

# Remove specific pages
pdf = pikepdf.open("/home/user/Desktop/document.pdf")
del pdf.pages[2]      # delete page at index 2
del pdf.pages[0:3]    # delete first 3 pages
pdf.save("/home/user/Desktop/trimmed.pdf")
```

#### Metadata with pikepdf

```python
import pikepdf

pdf = pikepdf.open("/home/user/Desktop/document.pdf")

# Read metadata via XMP
with pdf.open_metadata() as meta:
    print(meta.get("dc:title", ""))
    print(meta.get("dc:creator", ""))
    print(meta.get("xmp:CreatorTool", ""))

# Write metadata
with pdf.open_metadata() as meta:
    meta["dc:title"] = "Updated Title"
    meta["dc:creator"] = ["Author Name"]
    meta["dc:description"] = "A detailed description"
    meta["xmp:CreatorTool"] = "CUA-Gym"
    meta["pdf:Producer"] = "pikepdf"
    meta["pdf:Keywords"] = "keyword1, keyword2"

pdf.save("/home/user/Desktop/metadata_updated.pdf")

# Remove all metadata
pdf = pikepdf.open("/home/user/Desktop/document.pdf")
if "/Metadata" in pdf.Root:
    del pdf.Root["/Metadata"]
if pdf.docinfo:
    for key in list(pdf.docinfo.keys()):
        del pdf.docinfo[key]
pdf.save("/home/user/Desktop/no_metadata.pdf")
```

#### Rotate Pages with pikepdf

```python
import pikepdf

pdf = pikepdf.open("/home/user/Desktop/document.pdf")

# Rotate specific page
pdf.pages[0].Rotate = 90    # clockwise rotation in degrees (90, 180, 270)

# Rotate all pages
for page in pdf.pages:
    page.Rotate = 180

pdf.save("/home/user/Desktop/rotated.pdf")
```

### 1.3 reportlab — Creating Rich PDFs from Scratch

#### Simple Canvas Drawing

```python
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red, blue, black, green, HexColor
from reportlab.lib.units import inch, cm, mm

c = canvas.Canvas("/home/user/Desktop/reportlab_basic.pdf", pagesize=A4)
width, height = A4

# Text
c.setFont("Helvetica", 24)
c.drawString(72, height - 72, "Title Text")

c.setFont("Helvetica", 12)
c.drawString(72, height - 120, "Regular paragraph text goes here.")

# Right-aligned text
c.drawRightString(width - 72, height - 120, "Right aligned")

# Centered text
c.drawCentredString(width / 2, height - 160, "Centered text")

# Shapes
c.setStrokeColor(blue)
c.setFillColor(HexColor("#E0E0FF"))
c.rect(72, height - 300, 200, 100, fill=1)  # filled rectangle

c.setStrokeColor(red)
c.circle(400, height - 250, 50, fill=0)  # circle outline

c.setStrokeColor(black)
c.line(72, height - 350, width - 72, height - 350)  # horizontal line

# Image
c.drawImage("/home/user/Desktop/photo.png", 72, height - 550, width=200, height=150)

c.showPage()  # finish page
c.save()
```

#### Platypus Document with Tables

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, grey, lightgrey, HexColor
from reportlab.lib.units import inch

doc = SimpleDocTemplate("/home/user/Desktop/report.pdf", pagesize=A4,
                        leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72)

styles = getSampleStyleSheet()
story = []

# Title
title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                              fontSize=24, textColor=HexColor("#003366"), spaceAfter=20)
story.append(Paragraph("Annual Performance Report", title_style))
story.append(Spacer(1, 12))

# Body text
story.append(Paragraph("This report summarizes the key metrics for the fiscal year.", styles['Normal']))
story.append(Spacer(1, 12))

# Table
data = [
    ["Quarter", "Revenue", "Expenses", "Profit"],
    ["Q1", "$120,000", "$80,000", "$40,000"],
    ["Q2", "$150,000", "$90,000", "$60,000"],
    ["Q3", "$130,000", "$85,000", "$45,000"],
    ["Q4", "$170,000", "$95,000", "$75,000"],
]

table = Table(data, colWidths=[80, 100, 100, 100])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HexColor("#003366")),
    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 11),
    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ('GRID', (0, 0), (-1, -1), 0.5, grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#F0F0F0")]),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(table)
story.append(Spacer(1, 24))

# Page break
story.append(PageBreak())
story.append(Paragraph("Page 2 content", styles['Heading1']))

doc.build(story)
```

### 1.4 Golden File Pattern

```python
import shutil

# ALWAYS copy-then-modify for golden files
shutil.copy("/home/user/Desktop/<task_id>_initial.pdf", "/home/user/Desktop/<task_id>_golden.pdf")

# Then modify the golden copy
import pymupdf
doc = pymupdf.open("/home/user/Desktop/<task_id>_golden.pdf")
page = doc[0]
# ... apply expected modifications ...
doc.save("/home/user/Desktop/<task_id>_golden.pdf")
doc.close()
```

---

## 2. Reading & Verifying PDFs (reward-gen)

### 2.1 Document-Level Verification

#### Page Count

```python
import pymupdf

def verify_page_count(pdf_path: str, expected: int) -> bool:
    try:
        doc = pymupdf.open(pdf_path)
        result = doc.page_count == expected
        doc.close()
        return result
    except Exception:
        return False
```

#### Metadata

```python
def verify_metadata(pdf_path: str, expected: dict) -> bool:
    """Check PDF metadata fields. expected keys: title, author, subject, keywords, creator, producer."""
    try:
        doc = pymupdf.open(pdf_path)
        meta = doc.metadata
        doc.close()
        for key, value in expected.items():
            actual = meta.get(key, "")
            if actual is None:
                actual = ""
            if str(actual).strip().lower() != str(value).strip().lower():
                return False
        return True
    except Exception:
        return False
```

#### Table of Contents (Bookmarks)

```python
def verify_toc(pdf_path: str, expected_toc: list) -> bool:
    """expected_toc: [[level, title, page], ...]. page is 1-indexed."""
    try:
        doc = pymupdf.open(pdf_path)
        toc = doc.get_toc()
        doc.close()
        if len(toc) != len(expected_toc):
            return False
        for actual, expected in zip(toc, expected_toc):
            if actual[0] != expected[0]:  # level
                return False
            if actual[1].strip() != expected[1].strip():  # title
                return False
            if actual[2] != expected[2]:  # page number
                return False
        return True
    except Exception:
        return False

def verify_toc_has_entries(pdf_path: str, min_entries: int = 1) -> bool:
    """Verify TOC exists with at least min_entries."""
    try:
        doc = pymupdf.open(pdf_path)
        toc = doc.get_toc()
        doc.close()
        return len(toc) >= min_entries
    except Exception:
        return False
```

#### Encryption & Permissions

```python
def verify_encrypted(pdf_path: str) -> bool:
    """Check if PDF is encrypted (requires password to open)."""
    try:
        doc = pymupdf.open(pdf_path)
        result = doc.is_encrypted
        doc.close()
        return result
    except Exception:
        return False

def verify_permissions(pdf_path: str, password: str, expected_perms: dict) -> bool:
    """Verify PDF permission flags after opening with password.
    expected_perms keys: print, edit, copy, annotate, form, etc."""
    try:
        import pikepdf
        pdf = pikepdf.open(pdf_path, password=password)
        allow = pdf.allow
        pdf.close()
        for perm, expected in expected_perms.items():
            actual = getattr(allow, perm, None)
            if actual is None:
                # Try alternate names
                perm_map = {
                    "print": "print_lowres",
                    "edit": "modify_other",
                    "copy": "extract",
                    "annotate": "modify_annotation",
                    "form": "modify_form",
                }
                actual = getattr(allow, perm_map.get(perm, perm), None)
            if actual != expected:
                return False
        return True
    except Exception:
        return False

def verify_password_protected(pdf_path: str, password: str) -> bool:
    """Verify that a specific password can open the PDF."""
    try:
        doc = pymupdf.open(pdf_path)
        if not doc.is_encrypted:
            doc.close()
            return False
        result = doc.authenticate(password)
        doc.close()
        return result > 0  # returns int: 0=failed, 1=user, 2=owner
    except Exception:
        return False
```

### 2.2 Page-Level Verification

#### Page Dimensions & Rotation

```python
def verify_page_size(pdf_path: str, page_num: int, expected_width: float,
                     expected_height: float, tolerance: float = 1.0) -> bool:
    """Verify page dimensions in points. page_num is 0-indexed."""
    try:
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]
        w, h = page.rect.width, page.rect.height
        doc.close()
        return (abs(w - expected_width) <= tolerance and
                abs(h - expected_height) <= tolerance)
    except Exception:
        return False

def verify_page_rotation(pdf_path: str, page_num: int, expected_rotation: int) -> bool:
    """expected_rotation: 0, 90, 180, or 270."""
    try:
        doc = pymupdf.open(pdf_path)
        rotation = doc[page_num].rotation
        doc.close()
        return rotation == expected_rotation
    except Exception:
        return False

def verify_page_landscape(pdf_path: str, page_num: int) -> bool:
    """Verify page is landscape (width > height)."""
    try:
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]
        result = page.rect.width > page.rect.height
        doc.close()
        return result
    except Exception:
        return False
```

#### CropBox Verification

```python
def verify_cropbox(pdf_path: str, page_num: int, expected_rect: tuple) -> bool:
    """expected_rect: (x0, y0, x1, y1) in points."""
    try:
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]
        cb = page.cropbox
        doc.close()
        return (abs(cb.x0 - expected_rect[0]) < 1 and
                abs(cb.y0 - expected_rect[1]) < 1 and
                abs(cb.x1 - expected_rect[2]) < 1 and
                abs(cb.y1 - expected_rect[3]) < 1)
    except Exception:
        return False
```

### 2.3 Text Verification

#### Extract & Compare Full Text

```python
def get_page_text(pdf_path: str, page_num: int) -> str:
    """Extract plain text from a page."""
    doc = pymupdf.open(pdf_path)
    text = doc[page_num].get_text("text")
    doc.close()
    return text

def get_all_text(pdf_path: str) -> str:
    """Extract text from all pages."""
    doc = pymupdf.open(pdf_path)
    texts = []
    for page in doc:
        texts.append(page.get_text("text"))
    doc.close()
    return "\n".join(texts)

def verify_text_contains(pdf_path: str, expected_strings: list,
                         page_num: int = None) -> bool:
    """Verify PDF contains all expected strings."""
    try:
        if page_num is not None:
            text = get_page_text(pdf_path, page_num)
        else:
            text = get_all_text(pdf_path)
        return all(s in text for s in expected_strings)
    except Exception:
        return False

def verify_text_not_contains(pdf_path: str, forbidden_strings: list) -> bool:
    """Verify PDF does NOT contain any of the forbidden strings."""
    try:
        text = get_all_text(pdf_path)
        return not any(s in text for s in forbidden_strings)
    except Exception:
        return False

def verify_text_exact(pdf_path: str, page_num: int, expected_text: str,
                      ignore_whitespace: bool = True) -> bool:
    """Compare page text with expected, optionally normalizing whitespace."""
    try:
        import re
        actual = get_page_text(pdf_path, page_num)
        if ignore_whitespace:
            actual = re.sub(r'\s+', ' ', actual).strip()
            expected_text = re.sub(r'\s+', ' ', expected_text).strip()
        return actual == expected_text
    except Exception:
        return False
```

#### Text with Position

```python
def get_text_blocks(pdf_path: str, page_num: int) -> list:
    """Get text blocks with positions: [(x0, y0, x1, y1, text, block_no, block_type), ...]"""
    doc = pymupdf.open(pdf_path)
    blocks = doc[page_num].get_text("blocks")
    doc.close()
    return blocks

def get_text_words(pdf_path: str, page_num: int) -> list:
    """Get individual words with positions: [(x0, y0, x1, y1, word, block_no, line_no, word_no), ...]"""
    doc = pymupdf.open(pdf_path)
    words = doc[page_num].get_text("words")
    doc.close()
    return words

def verify_text_in_region(pdf_path: str, page_num: int,
                          rect: tuple, expected_text: str) -> bool:
    """Verify specific text appears within a rectangular region.
    rect: (x0, y0, x1, y1) in points."""
    try:
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]
        clip = pymupdf.Rect(*rect)
        text = page.get_textbox(clip)
        doc.close()
        return expected_text.strip() in text.strip()
    except Exception:
        return False

def verify_text_position(pdf_path: str, page_num: int,
                         search_text: str, expected_region: str) -> bool:
    """Verify text is in expected region: 'top', 'bottom', 'left', 'right', 'center'.
    Uses page center as dividing point."""
    try:
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]
        instances = page.search_for(search_text)
        doc.close()
        if not instances:
            return False
        rect = instances[0]
        cx, cy = rect.x0 + rect.width / 2, rect.y0 + rect.height / 2
        pw, ph = page.rect.width, page.rect.height
        if expected_region == "top":
            return cy < ph / 2
        elif expected_region == "bottom":
            return cy > ph / 2
        elif expected_region == "left":
            return cx < pw / 2
        elif expected_region == "right":
            return cx > pw / 2
        elif expected_region == "center":
            return (pw * 0.25 < cx < pw * 0.75 and ph * 0.25 < cy < ph * 0.75)
        return False
    except Exception:
        return False
```

#### Font Verification

```python
def get_page_fonts(pdf_path: str, page_num: int) -> list:
    """Get fonts used on a page: [(xref, ext, type, basefont, name, encoding), ...]"""
    doc = pymupdf.open(pdf_path)
    fonts = doc[page_num].get_fonts()
    doc.close()
    return fonts

def verify_font_used(pdf_path: str, page_num: int, font_name: str) -> bool:
    """Check if a specific font is used on the page."""
    try:
        fonts = get_page_fonts(pdf_path, page_num)
        return any(font_name.lower() in str(f).lower() for f in fonts)
    except Exception:
        return False

def get_text_with_font_info(pdf_path: str, page_num: int) -> list:
    """Extract text spans with font details using dict mode.
    Returns list of dicts with keys: text, font, size, color, flags (bold/italic/etc)."""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    data = page.get_text("dict")
    doc.close()

    spans = []
    for block in data["blocks"]:
        if block["type"] != 0:  # 0=text, 1=image
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                spans.append({
                    "text": span["text"],
                    "font": span["font"],
                    "size": span["size"],
                    "color": span["color"],  # integer RGB, convert with (color >> 16 & 0xFF, color >> 8 & 0xFF, color & 0xFF)
                    "flags": span["flags"],  # bitmask: 1=superscript, 2=italic, 4=serif, 8=monospace, 16=bold
                    "bbox": span["bbox"],    # (x0, y0, x1, y1)
                })
    return spans

def verify_text_style(pdf_path: str, page_num: int, search_text: str,
                      expected_font: str = None, expected_size: float = None,
                      expected_bold: bool = None, expected_italic: bool = None,
                      expected_color: tuple = None) -> bool:
    """Verify text style properties. expected_color is (R, G, B) 0-255."""
    try:
        spans = get_text_with_font_info(pdf_path, page_num)
        for span in spans:
            if search_text not in span["text"]:
                continue
            if expected_font and expected_font.lower() not in span["font"].lower():
                return False
            if expected_size and abs(span["size"] - expected_size) > 0.5:
                return False
            if expected_bold is not None:
                is_bold = bool(span["flags"] & 16)
                if is_bold != expected_bold:
                    return False
            if expected_italic is not None:
                is_italic = bool(span["flags"] & 2)
                if is_italic != expected_italic:
                    return False
            if expected_color:
                c = span["color"]
                actual_rgb = (c >> 16 & 0xFF, c >> 8 & 0xFF, c & 0xFF)
                if any(abs(a - e) > 10 for a, e in zip(actual_rgb, expected_color)):
                    return False
            return True
        return False  # text not found
    except Exception:
        return False
```

### 2.4 Image Verification

#### Extract & Count Images

```python
def get_page_images(pdf_path: str, page_num: int) -> list:
    """Get images on a page: [(xref, smask, width, height, bpc, colorspace, ...), ...]"""
    doc = pymupdf.open(pdf_path)
    images = doc[page_num].get_images()
    doc.close()
    return images

def verify_image_count(pdf_path: str, page_num: int, expected: int) -> bool:
    try:
        return len(get_page_images(pdf_path, page_num)) == expected
    except Exception:
        return False

def verify_total_image_count(pdf_path: str, expected: int) -> bool:
    try:
        doc = pymupdf.open(pdf_path)
        total = sum(len(page.get_images()) for page in doc)
        doc.close()
        return total == expected
    except Exception:
        return False

def extract_image(pdf_path: str, page_num: int, image_index: int,
                  output_path: str) -> bool:
    """Extract an image from PDF and save it."""
    try:
        doc = pymupdf.open(pdf_path)
        images = doc[page_num].get_images()
        if image_index >= len(images):
            doc.close()
            return False
        xref = images[image_index][0]
        img_data = doc.extract_image(xref)
        doc.close()
        with open(output_path, "wb") as f:
            f.write(img_data["image"])
        return True
    except Exception:
        return False
```

#### Compare Extracted Images

```python
from PIL import Image
import numpy as np

def verify_image_matches(pdf_path: str, page_num: int, image_index: int,
                         reference_path: str, threshold: float = 0.9) -> bool:
    """Extract image from PDF and compare with reference using SSIM."""
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        if not extract_image(pdf_path, page_num, image_index, tmp_path):
            return False
        from skimage.metrics import structural_similarity as ssim
        img1 = np.array(Image.open(tmp_path).convert("RGB"))
        img2 = np.array(Image.open(reference_path).convert("RGB"))
        if img1.shape != img2.shape:
            img2_pil = Image.open(reference_path).convert("RGB").resize(
                (img1.shape[1], img1.shape[0]), Image.Resampling.LANCZOS)
            img2 = np.array(img2_pil)
        score = ssim(img1, img2, win_size=7, channel_axis=2)
        import os
        os.unlink(tmp_path)
        return score >= threshold
    except Exception:
        return False
```

### 2.5 Annotation Verification

```python
def get_annotations(pdf_path: str, page_num: int) -> list:
    """Get all annotations on a page with their properties."""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    annots = []
    for annot in page.annots():
        annots.append({
            "type": annot.type[1],            # "Highlight", "Text", "FreeText", "Square", etc.
            "type_code": annot.type[0],       # integer type code
            "content": annot.info.get("content", ""),
            "title": annot.info.get("title", ""),
            "rect": tuple(annot.rect),        # (x0, y0, x1, y1)
            "colors": {
                "stroke": annot.colors.get("stroke"),
                "fill": annot.colors.get("fill"),
            },
            "opacity": annot.opacity,
        })
    doc.close()
    return annots

def verify_annotation_count(pdf_path: str, page_num: int,
                             expected: int, annot_type: str = None) -> bool:
    """Verify number of annotations, optionally filtered by type."""
    try:
        annots = get_annotations(pdf_path, page_num)
        if annot_type:
            annots = [a for a in annots if a["type"] == annot_type]
        return len(annots) == expected
    except Exception:
        return False

def verify_highlight_exists(pdf_path: str, page_num: int,
                            text: str, color: tuple = None) -> bool:
    """Verify a highlight annotation exists over specific text.
    color: (R, G, B) as floats 0-1, e.g., (1, 1, 0) for yellow."""
    try:
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]
        # Find text location
        text_instances = page.search_for(text)
        if not text_instances:
            doc.close()
            return False
        # Check annotations
        for annot in page.annots():
            if annot.type[1] != "Highlight":
                continue
            annot_rect = annot.rect
            # Check if annotation overlaps with text
            for inst in text_instances:
                if annot_rect.intersects(inst):
                    if color is None:
                        doc.close()
                        return True
                    # Check color
                    stroke = annot.colors.get("stroke")
                    if stroke and all(abs(a - e) < 0.05 for a, e in zip(stroke, color)):
                        doc.close()
                        return True
        doc.close()
        return False
    except Exception:
        return False

def verify_stamp_exists(pdf_path: str, page_num: int) -> bool:
    """Check if a stamp annotation exists on the page."""
    try:
        annots = get_annotations(pdf_path, page_num)
        return any(a["type"] == "Stamp" for a in annots)
    except Exception:
        return False

def verify_text_annotation(pdf_path: str, page_num: int,
                           expected_content: str) -> bool:
    """Verify a sticky note with specific content exists."""
    try:
        annots = get_annotations(pdf_path, page_num)
        return any(a["type"] == "Text" and expected_content in a["content"]
                   for a in annots)
    except Exception:
        return False
```

### 2.6 Link Verification

```python
def get_links(pdf_path: str, page_num: int) -> list:
    """Get all links on a page."""
    doc = pymupdf.open(pdf_path)
    links = doc[page_num].get_links()
    doc.close()
    return links

def verify_link_exists(pdf_path: str, page_num: int,
                       expected_uri: str = None,
                       expected_page: int = None) -> bool:
    """Verify a link exists. Check URI for external links, page for internal."""
    try:
        links = get_links(pdf_path, page_num)
        for link in links:
            if expected_uri and link.get("uri", "") == expected_uri:
                return True
            if expected_page is not None and link.get("page", -1) == expected_page:
                return True
        return False
    except Exception:
        return False

def verify_link_count(pdf_path: str, page_num: int, expected: int) -> bool:
    try:
        return len(get_links(pdf_path, page_num)) == expected
    except Exception:
        return False
```

### 2.7 Form Field (Widget) Verification

```python
def get_form_fields(pdf_path: str, page_num: int = None) -> list:
    """Get form fields. If page_num is None, get all fields from all pages."""
    doc = pymupdf.open(pdf_path)
    fields = []
    pages = [doc[page_num]] if page_num is not None else doc
    for page in pages:
        for widget in page.widgets():
            fields.append({
                "name": widget.field_name,
                "type": widget.field_type,        # 1=text, 2=checkbox, 3=radio, 4=button, 5=combobox, 6=listbox, 7=signature
                "type_name": widget.field_type_string,  # "Text", "CheckBox", etc.
                "value": widget.field_value,
                "choices": widget.choice_values,   # for combo/list boxes
                "rect": tuple(widget.rect),
                "flags": widget.field_flags,
            })
    doc.close()
    return fields

def verify_form_field_value(pdf_path: str, field_name: str,
                             expected_value: str) -> bool:
    """Verify a form field has a specific value."""
    try:
        fields = get_form_fields(pdf_path)
        for f in fields:
            if f["name"] == field_name:
                return str(f["value"]) == str(expected_value)
        return False
    except Exception:
        return False

def verify_form_field_count(pdf_path: str, expected: int,
                             field_type: str = None) -> bool:
    """Verify total number of form fields, optionally by type."""
    try:
        fields = get_form_fields(pdf_path)
        if field_type:
            fields = [f for f in fields if f["type_name"] == field_type]
        return len(fields) == expected
    except Exception:
        return False

def verify_form_field_exists(pdf_path: str, field_name: str,
                              field_type: str = None) -> bool:
    """Verify a form field with given name (and optionally type) exists."""
    try:
        fields = get_form_fields(pdf_path)
        for f in fields:
            if f["name"] == field_name:
                if field_type and f["type_name"] != field_type:
                    return False
                return True
        return False
    except Exception:
        return False

def verify_checkbox_state(pdf_path: str, field_name: str,
                          expected_checked: bool) -> bool:
    """Verify checkbox is checked or unchecked."""
    try:
        fields = get_form_fields(pdf_path)
        for f in fields:
            if f["name"] == field_name and f["type_name"] == "CheckBox":
                is_checked = f["value"] not in ("Off", "", None, False)
                return is_checked == expected_checked
        return False
    except Exception:
        return False
```

### 2.8 Drawing / Shape Verification

```python
def get_drawings(pdf_path: str, page_num: int) -> list:
    """Get vector drawings on a page. Returns list of path dicts."""
    doc = pymupdf.open(pdf_path)
    drawings = doc[page_num].get_drawings()
    doc.close()
    return drawings

def verify_has_drawings(pdf_path: str, page_num: int, min_count: int = 1) -> bool:
    """Verify page contains at least min_count vector drawings."""
    try:
        return len(get_drawings(pdf_path, page_num)) >= min_count
    except Exception:
        return False

def verify_drawing_color(pdf_path: str, page_num: int,
                         expected_color: tuple, check_fill: bool = True) -> bool:
    """Verify any drawing has the expected color. Color as (R, G, B) 0-1."""
    try:
        drawings = get_drawings(pdf_path, page_num)
        for d in drawings:
            if check_fill and d.get("fill"):
                if all(abs(a - e) < 0.05 for a, e in zip(d["fill"], expected_color)):
                    return True
            if d.get("color"):
                if all(abs(a - e) < 0.05 for a, e in zip(d["color"], expected_color)):
                    return True
        return False
    except Exception:
        return False
```

### 2.9 Visual Comparison (Page Rendering)

```python
def render_page_to_image(pdf_path: str, page_num: int, dpi: int = 150) -> "Image":
    """Render a PDF page to PIL Image."""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img

def compare_pages_visual(pdf1_path: str, pdf2_path: str,
                         page_num: int, threshold: float = 0.95,
                         dpi: int = 150) -> bool:
    """Visually compare a page between two PDFs using SSIM."""
    try:
        from skimage.metrics import structural_similarity as ssim
        img1 = np.array(render_page_to_image(pdf1_path, page_num, dpi))
        img2 = np.array(render_page_to_image(pdf2_path, page_num, dpi))
        # Resize if different
        if img1.shape != img2.shape:
            h = min(img1.shape[0], img2.shape[0])
            w = min(img1.shape[1], img2.shape[1])
            img1 = np.array(Image.fromarray(img1).resize((w, h), Image.Resampling.LANCZOS))
            img2 = np.array(Image.fromarray(img2).resize((w, h), Image.Resampling.LANCZOS))
        score = ssim(img1, img2, win_size=7, channel_axis=2)
        return score >= threshold
    except Exception:
        return False

def compare_all_pages_visual(pdf1_path: str, pdf2_path: str,
                             threshold: float = 0.95) -> float:
    """Compare all pages between two PDFs. Returns average SSIM score."""
    try:
        doc1 = pymupdf.open(pdf1_path)
        doc2 = pymupdf.open(pdf2_path)
        if doc1.page_count != doc2.page_count:
            doc1.close()
            doc2.close()
            return 0.0
        from skimage.metrics import structural_similarity as ssim
        scores = []
        for i in range(doc1.page_count):
            img1 = np.array(render_page_to_image(pdf1_path, i))
            img2 = np.array(render_page_to_image(pdf2_path, i))
            if img1.shape != img2.shape:
                h = min(img1.shape[0], img2.shape[0])
                w = min(img1.shape[1], img2.shape[1])
                img1 = np.array(Image.fromarray(img1).resize((w, h), Image.Resampling.LANCZOS))
                img2 = np.array(Image.fromarray(img2).resize((w, h), Image.Resampling.LANCZOS))
            scores.append(ssim(img1, img2, win_size=7, channel_axis=2))
        doc1.close()
        doc2.close()
        return sum(scores) / len(scores) if scores else 0.0
    except Exception:
        return 0.0
```

### 2.10 Composite Reward Scoring

```python
def compute_reward(pdf_path: str, golden_path: str, checks: list) -> float:
    """Compute a 0.0-1.0 reward score from weighted checks.
    checks: [{"name": str, "func": callable, "weight": float}, ...]
    Each func returns bool or float (0.0-1.0)."""
    total_weight = sum(c["weight"] for c in checks)
    if total_weight == 0:
        return 0.0
    score = 0.0
    for check in checks:
        try:
            result = check["func"]()
            if isinstance(result, bool):
                result = 1.0 if result else 0.0
            score += result * check["weight"]
        except Exception:
            pass  # check failed, contributes 0
    return round(score / total_weight, 2)

# Example usage:
# reward = compute_reward(result_path, golden_path, [
#     {"name": "page_count", "func": lambda: verify_page_count(result_path, 5), "weight": 0.2},
#     {"name": "text_present", "func": lambda: verify_text_contains(result_path, ["Chapter 1"]), "weight": 0.3},
#     {"name": "visual_match", "func": lambda: compare_all_pages_visual(result_path, golden_path), "weight": 0.5},
# ])
# print(f"REWARD: {reward}")
```

### 2.11 Table Extraction & Verification

```python
def extract_tables(pdf_path: str, page_num: int) -> list:
    """Extract tables from a page using PyMuPDF's table finder.
    Returns list of tables, each table is a list of rows, each row is a list of cell strings."""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    tables = page.find_tables()
    result = []
    for table in tables:
        rows = []
        for row in table.extract():
            rows.append([cell if cell else "" for cell in row])
        result.append(rows)
    doc.close()
    return result

def verify_table_content(pdf_path: str, page_num: int,
                         table_index: int, expected_data: list) -> bool:
    """Verify table content matches expected data.
    expected_data: [[row1_cells], [row2_cells], ...]"""
    try:
        tables = extract_tables(pdf_path, page_num)
        if table_index >= len(tables):
            return False
        actual = tables[table_index]
        if len(actual) != len(expected_data):
            return False
        for actual_row, expected_row in zip(actual, expected_data):
            if len(actual_row) != len(expected_row):
                return False
            for actual_cell, expected_cell in zip(actual_row, expected_row):
                if actual_cell.strip() != str(expected_cell).strip():
                    return False
        return True
    except Exception:
        return False

def verify_table_exists(pdf_path: str, page_num: int,
                        min_rows: int = 1, min_cols: int = 1) -> bool:
    """Verify at least one table exists with minimum dimensions."""
    try:
        tables = extract_tables(pdf_path, page_num)
        for table in tables:
            if len(table) >= min_rows and all(len(row) >= min_cols for row in table):
                return True
        return False
    except Exception:
        return False
```

---

## 3. Bitter Lessons

1. **PyMuPDF uses `import pymupdf`, not `import fitz` (since v1.24).** Older code uses `import fitz`. Both work, but `pymupdf` is the canonical import for newer versions. Always try `import pymupdf` first, fall back to `import fitz`.

2. **Shape.commit() is mandatory.** After calling `draw_rect()`, `draw_circle()`, etc., you must call `shape.finish()` (to apply colors/stroke) and then `shape.commit()` (to write to page). Forgetting `commit()` means shapes never appear in the saved PDF.

3. **Colors are float tuples (0-1), not int tuples (0-255).** PyMuPDF uses `(1, 0, 0)` for red, NOT `(255, 0, 0)`. `(255, 0, 0)` will silently clamp or produce unexpected results.

4. **Font span color is an integer, not a tuple.** `get_text("dict")` returns `span["color"]` as an integer. Convert with `(color >> 16 & 0xFF, color >> 8 & 0xFF, color & 0xFF)` to get `(R, G, B)` as 0-255.

5. **`page.search_for()` returns Rect objects, not strings.** The return value is a list of `Rect` that mark where the text is found. Use these Rects for highlighting or position verification.

6. **PDF coordinates: origin is bottom-left in spec, but PyMuPDF uses top-left.** PyMuPDF transforms coordinates so (0,0) is top-left. This is consistent within PyMuPDF but differs from raw PDF specs and reportlab (which uses bottom-left origin).

7. **reportlab Canvas origin is bottom-left.** `drawString(72, 72)` places text 1 inch from the bottom, NOT the top. To place text at the top, use `drawString(72, height - 72)`. This is the opposite of PyMuPDF.

8. **Annotation `.update()` is required after changes.** After `set_colors()`, `set_border()`, `set_opacity()` etc., you must call `annot.update()`. Without it, changes are not rendered in the PDF appearance stream.

9. **pikepdf vs PyMuPDF for encryption.** PyMuPDF can detect encryption and authenticate, but **pikepdf is better for setting encryption** because it provides fine-grained `Permissions` control. Use pikepdf for encrypt/decrypt operations.

10. **`get_text("text")` loses formatting and structure.** It returns plain text with newlines. For structured extraction with fonts, sizes, and colors, use `get_text("dict")` which returns block/line/span hierarchy.

11. **Table extraction requires PyMuPDF >= 1.23.** `page.find_tables()` was added in version 1.23. On older versions, you must parse text blocks and manually reconstruct table structure.

12. **Copy-then-modify for golden PDFs.** Never create golden files from scratch. Always `shutil.copy(initial, golden)` then modify. PyMuPDF preserves internal PDF structure, cross-references, and resources that differ from scratch-created files.

13. **`doc.save()` overwrites in-place only with `incremental=True`.** By default, `doc.save("same_file.pdf")` may fail if the file is still open. Use `doc.save("same_file.pdf", incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)` or save to a temp file first.

14. **Page rotation affects coordinate system.** After `set_rotation(90)`, the page's `rect` dimensions swap (width ↔ height). Text insertion coordinates must account for the new orientation. Use `page.derotation_matrix` if you need original coordinates.

15. **Widget (form field) font support is limited.** PyMuPDF widgets support only the 14 PDF base fonts (Helvetica, Times, Courier variants, Symbol, ZapfDingbats). Custom fonts in widgets require low-level PDF manipulation.

16. **SSIM window size must be odd and ≤ image dimension.** When comparing rendered pages, small pages at low DPI can produce images smaller than the default `win_size=7`. Adapt: `win_size = min(7, min_dim if min_dim % 2 == 1 else min_dim - 1)`.

17. **Evince does NOT support command-line zoom control.** You can specify page (`--page-index`) and mode (`--fullscreen`, `--presentation`) but NOT zoom level. Zoom must be set interactively by the agent.

18. **PDF text extraction may differ from visual text.** Ligatures, kerning, and character encoding can cause extracted text to differ from what's displayed. Use fuzzy matching or normalize Unicode when comparing text.

19. **`doc.insert_pdf()` reindexes pages.** After inserting pages from another PDF, internal references (TOC, links) may break. Always rebuild TOC and links after merge operations.

20. **pikepdf page rotation uses raw PDF values.** `page.Rotate = 90` sets rotation directly. Unlike PyMuPDF, pikepdf does NOT transform coordinates — the visual result depends on how the viewer interprets the rotation flag.
