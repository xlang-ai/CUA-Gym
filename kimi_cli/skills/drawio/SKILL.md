---
name: drawio
description: "How to programmatically set up, manipulate, and verify draw.io diagram state using Python (Playwright CDP, XML injection via Edit Diagram menu, DOM verification). For setup-gen and reward-gen agents."
user-invocable: false
---

# Draw.io — Python Manipulation Guide

This skill teaches **setup-gen** (inject initial diagram) and **reward-gen** (verify diagram state after agent actions) how to work with a self-hosted draw.io instance via Playwright CDP.

- Libraries: `playwright`, `xml.etree.ElementTree`
- Install: `pip3 install playwright && playwright install chromium`
- Deployed at: `https://cua-gym-drawio.xlang.ai`
- State format: **mxGraphModel XML** (mxGraph/JGraph format)
- Editor instance: **NOT exposed on `window`** — state injection uses the Edit Diagram dialog

---

## 0. GUI Startup on VM (for setup-gen)

Draw.io runs as a web app inside Chrome. Setup-gen must:
1. Connect to Chrome via CDP
2. Open a new tab with `?splash=0` (CRITICAL: do NOT use `?offline=1` — it prevents editor loading)
3. Wait 10–40 seconds for the editor to fully initialize
4. Inject XML via Extras → Edit Diagram dialog
5. Leave the tab open for the CUA agent

```python
import json, time
from playwright.sync_api import sync_playwright

DRAWIO_URL = "https://cua-gym-drawio.xlang.ai"

def setup_drawio(diagram_xml, host="localhost", port=9222):
    """Open draw.io in existing Chrome and inject initial diagram."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{host}:{port}")
        context = browser.contexts[0]
        page = context.new_page()

        # Load draw.io — splash=0 skips the start screen
        page.goto(f"{DRAWIO_URL}/?splash=0", wait_until="domcontentloaded", timeout=60000)

        # Wait for editor to fully initialize (10-40s)
        wait_for_editor(page, timeout=60)
        time.sleep(2)

        # Inject diagram via Edit Diagram menu
        inject_via_edit_diagram(page, diagram_xml)
        time.sleep(2)

        # Close blank tabs
        for pg in context.pages:
            if pg.url in ("about:blank", "chrome://newtab/"):
                pg.close()
                break
        # Do NOT close browser — agent needs it


def wait_for_editor(page, timeout=60):
    """Poll until draw.io editor is fully loaded."""
    start = time.time()
    while time.time() - start < timeout:
        ready = page.evaluate("""() => ({
            container: !!document.querySelector('.geDiagramContainer'),
            menubar: !!document.querySelector('.geMenubar'),
        })""")
        if ready.get("container") and ready.get("menubar"):
            return True
        time.sleep(1)
    raise TimeoutError(f"draw.io editor did not load within {timeout}s")


def inject_via_edit_diagram(page, xml):
    """Inject XML via Extras > Edit Diagram dialog."""
    # Open Extras menu
    page.click('text=Extras')
    time.sleep(1)

    # Click "Edit Diagram..." menu item
    page.locator("text=Edit Diagram").first.click(timeout=3000)
    time.sleep(2)

    # Find textarea and inject XML
    page.evaluate("""(xml) => {
        const ta = document.querySelector('textarea');
        if (!ta) throw new Error('Edit Diagram textarea not found');
        const setter = Object.getOwnPropertyDescriptor(
            HTMLTextAreaElement.prototype, 'value'
        ).set;
        setter.call(ta, xml);
        ta.dispatchEvent(new Event('input', {bubbles: true}));
        ta.dispatchEvent(new Event('change', {bubbles: true}));
    }""", xml)
    time.sleep(0.5)

    # Click OK button
    page.evaluate("""() => {
        const btns = document.querySelectorAll('.geDialog button, button');
        for (const btn of btns) {
            if (btn.textContent.trim().toLowerCase() === 'ok') {
                btn.click();
                return;
            }
        }
    }""")
    time.sleep(2)
```

Guidelines:
- **NEVER use `?offline=1`** — it prevents the editor from loading.
- Use `?splash=0` to skip the start screen.
- Editor takes 10–40 seconds to load. Always use `wait_for_editor()` with adequate timeout.
- The `EditorUi` instance is NOT on `window.ui` — it lives in a closure. XML injection must go through the Edit Diagram dialog.
- Do NOT call `browser.close()`.

---

## 1. Creating draw.io Diagrams (setup-gen)

### XML Format: mxGraphModel

All draw.io diagrams use the mxGraph XML format. The root structure:

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
              tooltips="1" connect="1" arrows="1" fold="1"
              page="1" pageScale="1" pageWidth="1169" pageHeight="827">
  <root>
    <mxCell id="0"/>                    <!-- root cell (required) -->
    <mxCell id="1" parent="0"/>         <!-- default layer (required) -->
    <!-- your shapes and edges here -->
  </root>
</mxGraphModel>
```

### Building XML with Python

```python
import xml.etree.ElementTree as ET

def new_diagram():
    """Create a new empty mxGraphModel."""
    root = ET.Element("mxGraphModel", {
        "dx": "1422", "dy": "762",
        "grid": "1", "gridSize": "10", "guides": "1",
        "tooltips": "1", "connect": "1", "arrows": "1", "fold": "1",
        "page": "1", "pageScale": "1",
        "pageWidth": "1169", "pageHeight": "827",
    })
    root_cells = ET.SubElement(root, "root")
    ET.SubElement(root_cells, "mxCell", {"id": "0"})
    ET.SubElement(root_cells, "mxCell", {"id": "1", "parent": "0"})
    return root, root_cells


def add_vertex(parent, id, value, x, y, w, h, style):
    """Add a shape (vertex) to the diagram."""
    cell = ET.SubElement(parent, "mxCell", {
        "id": id, "value": value, "style": style,
        "vertex": "1", "parent": "1",
    })
    ET.SubElement(cell, "mxGeometry", {
        "x": str(x), "y": str(y),
        "width": str(w), "height": str(h),
        "as": "geometry",
    })
    return cell


def add_edge(parent, id, source, target, value="", style="edgeStyle=orthogonalEdgeStyle;strokeWidth=2;"):
    """Add a connection (edge) between two vertices."""
    ET.SubElement(parent, "mxCell", {
        "id": id, "value": value, "style": style,
        "edge": "1", "source": source, "target": target, "parent": "1",
    })


def to_xml_string(root):
    return ET.tostring(root, encoding="unicode")
```

### Shape Styles Reference

Styles are semicolon-separated key=value pairs:

```python
# Rounded rectangle (most common shape)
STYLE_RECT = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=13;"

# Ellipse / circle
STYLE_ELLIPSE = "shape=ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=14;"

# Diamond / rhombus (decision)
STYLE_DIAMOND = "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=13;"

# Hexagon
STYLE_HEXAGON = "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"

# Cylinder (database)
STYLE_CYLINDER = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;fillColor=#f5f5f5;strokeColor=#666666;size=15;"

# Note / sticky
STYLE_NOTE = "shape=note;whiteSpace=wrap;html=1;backgroundOutline=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;align=left;spacingLeft=8;size=14;"

# Text label (no border)
STYLE_TEXT = "text;html=1;fontSize=22;fontStyle=1;align=center;verticalAlign=middle;"

# Swimlane / container
STYLE_SWIMLANE = "swimlane;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"

# Dashed border
STYLE_DASHED = "rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;fillColor=#fff2cc;strokeColor=#d6b656;"

# Edge styles
STYLE_EDGE = "edgeStyle=orthogonalEdgeStyle;strokeWidth=2;"
STYLE_EDGE_DASHED = "edgeStyle=orthogonalEdgeStyle;strokeWidth=2;dashed=1;"
STYLE_EDGE_LABELED = "edgeStyle=orthogonalEdgeStyle;strokeWidth=2;fontStyle=1;fontSize=12;"
```

### Color Palette Reference

| Name | fillColor | strokeColor | Use |
|------|-----------|-------------|-----|
| Blue | `#dae8fc` | `#6c8ebf` | Process, default |
| Green | `#d5e8d4` | `#82b366` | Success, start |
| Red | `#f8cecc` | `#b85450` | Error, end |
| Yellow | `#fff2cc` | `#d6b656` | Decision, warning |
| Purple | `#e1d5e7` | `#9673a6` | Verify, special |
| Orange | `#fce5cd` | `#d79b00` | Important |
| Gray | `#f5f5f5` | `#666666` | Notes, neutral |
| Dark | `#647687` | `#314354` | Headers |

### Building a Complete Diagram

```python
def build_architecture_diagram():
    root, cells = new_diagram()

    # Title
    add_vertex(cells, "title", "System Architecture",
               300, 20, 350, 40, STYLE_TEXT)

    # Shapes
    add_vertex(cells, "client", "Client App",
               100, 100, 160, 70, STYLE_RECT)
    add_vertex(cells, "api", "API Gateway",
               400, 100, 160, 70,
               "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=13;")
    add_vertex(cells, "db", "Database",
               400, 300, 120, 80, STYLE_CYLINDER)
    add_vertex(cells, "decide", "Auth?",
               200, 250, 120, 80, STYLE_DIAMOND)

    # Edges
    add_edge(cells, "e1", "client", "api")
    add_edge(cells, "e2", "api", "decide")
    add_edge(cells, "e3", "decide", "db", value="Yes", style=STYLE_EDGE_LABELED)

    return to_xml_string(root)
```

### Multi-Page Diagrams

```python
def build_multipage_xml():
    """Multi-page diagrams use the mxfile wrapper."""
    pages = []
    for name, builder in [("Overview", build_overview), ("Details", build_details)]:
        root, cells = new_diagram()
        builder(cells)
        pages.append(f'<diagram name="{name}" id="{name.lower()}">{ET.tostring(root, encoding="unicode")}</diagram>')
    return f'<mxfile>{"".join(pages)}</mxfile>'
```

---

## 2. Reading & Verifying Diagrams (reward-gen)

### Reading Diagram State via DOM

Since the editor JS instance is not accessible, reward-gen reads state from the rendered DOM.

```python
def read_diagram_dom(page):
    """Read diagram state from rendered DOM elements."""
    return page.evaluate("""() => {
        const container = document.querySelector('.geDiagramContainer');
        if (!container) return null;

        const result = {
            svg_count: container.querySelectorAll('svg').length,
            shapes: [],
            texts: [],
            edges: 0,
            total_elements: container.querySelectorAll('*').length,
        };

        // foreignObject contains rendered text labels
        container.querySelectorAll('foreignObject').forEach(fo => {
            const div = fo.querySelector('div');
            if (div) {
                result.texts.push({
                    text: div.textContent.trim(),
                    x: parseFloat(fo.getAttribute('x') || 0),
                    y: parseFloat(fo.getAttribute('y') || 0),
                    width: parseFloat(fo.getAttribute('width') || 0),
                    height: parseFloat(fo.getAttribute('height') || 0),
                });
            }
        });

        // Count shape types by SVG elements
        result.rects = container.querySelectorAll('rect').length;
        result.ellipses = container.querySelectorAll('ellipse').length;
        result.paths = container.querySelectorAll('path').length;
        result.polygons = container.querySelectorAll('polygon').length;

        return result;
    }""")
```

### Reading Diagram State via Edit Diagram XML

More reliable: read the XML back from the Edit Diagram dialog.

```python
def read_diagram_xml(page):
    """Open Edit Diagram, read XML, close dialog. Returns XML string."""
    # Open Edit Diagram
    page.click('text=Extras')
    time.sleep(1)
    page.locator("text=Edit Diagram").first.click(timeout=3000)
    time.sleep(2)

    # Read textarea content
    xml = page.evaluate("""() => {
        const ta = document.querySelector('textarea');
        return ta ? ta.value : null;
    }""")

    # Close dialog (Cancel to avoid accidental changes)
    page.evaluate("""() => {
        const btns = document.querySelectorAll('.geDialog button, button');
        for (const btn of btns) {
            const txt = btn.textContent.trim().toLowerCase();
            if (txt === 'cancel' || txt === 'close') {
                btn.click();
                return;
            }
        }
    }""")
    time.sleep(1)
    return xml
```

### XML Parsing for Verification

```python
import xml.etree.ElementTree as ET

def parse_diagram(xml_string):
    """Parse mxGraphModel XML and extract cells."""
    root = ET.fromstring(xml_string)
    cells = root.findall('.//mxCell')

    vertices = []
    edges = []
    for cell in cells:
        cell_data = {
            "id": cell.get("id"),
            "value": cell.get("value", ""),
            "style": cell.get("style", ""),
            "parent": cell.get("parent"),
        }
        geo = cell.find("mxGeometry")
        if geo is not None:
            cell_data["x"] = float(geo.get("x", 0))
            cell_data["y"] = float(geo.get("y", 0))
            cell_data["width"] = float(geo.get("width", 0))
            cell_data["height"] = float(geo.get("height", 0))

        if cell.get("vertex") == "1":
            vertices.append(cell_data)
        elif cell.get("edge") == "1":
            cell_data["source"] = cell.get("source")
            cell_data["target"] = cell.get("target")
            edges.append(cell_data)

    return {"vertices": vertices, "edges": edges}


def get_vertex_by_id(parsed, vertex_id):
    return next((v for v in parsed["vertices"] if v["id"] == vertex_id), None)

def get_vertex_by_value(parsed, text):
    """Find vertex by its label text (case-insensitive partial match)."""
    text_lower = text.lower()
    return next((v for v in parsed["vertices"]
                 if text_lower in v.get("value", "").lower()), None)
```

### Property Verification

```python
def verify_vertex_exists(parsed, vertex_id=None, value=None):
    if vertex_id:
        return get_vertex_by_id(parsed, vertex_id) is not None
    if value:
        return get_vertex_by_value(parsed, value) is not None
    return False

def verify_vertex_style(parsed, vertex_id, expected_style_parts):
    """Check that a vertex style contains all expected key=value parts."""
    v = get_vertex_by_id(parsed, vertex_id)
    if not v:
        return False
    style = v.get("style", "")
    for part in expected_style_parts:
        if part not in style:
            return False
    return True

def verify_vertex_color(parsed, vertex_id, fill_color=None, stroke_color=None):
    v = get_vertex_by_id(parsed, vertex_id)
    if not v:
        return False
    style = v.get("style", "")
    if fill_color and f"fillColor={fill_color}" not in style:
        return False
    if stroke_color and f"strokeColor={stroke_color}" not in style:
        return False
    return True

def verify_edge_exists(parsed, source_id, target_id):
    return any(e["source"] == source_id and e["target"] == target_id
               for e in parsed["edges"])

def verify_vertex_count(parsed, expected=None, min_count=None):
    count = len(parsed["vertices"])
    if expected is not None:
        return count == expected
    if min_count is not None:
        return count >= min_count
    return count > 0

def verify_edge_count(parsed, expected=None, min_count=None):
    count = len(parsed["edges"])
    if expected is not None:
        return count == expected
    if min_count is not None:
        return count >= min_count
    return count > 0

def verify_vertex_position(parsed, vertex_id, expected_x, expected_y, tolerance=30):
    v = get_vertex_by_id(parsed, vertex_id)
    if not v:
        return False
    return abs(v.get("x", 0) - expected_x) <= tolerance and abs(v.get("y", 0) - expected_y) <= tolerance

def verify_shape_type(parsed, vertex_id, expected_shape):
    """Check shape type: ellipse, rhombus, cylinder3, hexagon, note, etc."""
    v = get_vertex_by_id(parsed, vertex_id)
    if not v:
        return False
    style = v.get("style", "")
    if expected_shape == "rectangle":
        return "shape=" not in style or "rounded=" in style
    return f"shape={expected_shape}" in style
```

### Diff-Based Verification

```python
def diff_diagrams(initial_xml, final_xml):
    """Compare initial and final diagram states."""
    initial = parse_diagram(initial_xml)
    final = parse_diagram(final_xml)

    initial_ids = {v["id"] for v in initial["vertices"]}
    final_ids = {v["id"] for v in final["vertices"]}

    added_vertices = [v for v in final["vertices"] if v["id"] not in initial_ids]
    removed_vertices = [v for v in initial["vertices"] if v["id"] not in final_ids]

    initial_edges = {(e["source"], e["target"]) for e in initial["edges"]}
    final_edges = {(e["source"], e["target"]) for e in final["edges"]}

    added_edges = final_edges - initial_edges
    removed_edges = initial_edges - final_edges

    return {
        "added_vertices": added_vertices,
        "removed_vertices": removed_vertices,
        "added_edges": list(added_edges),
        "removed_edges": list(removed_edges),
        "vertex_count_delta": len(final_ids) - len(initial_ids),
        "edge_count_delta": len(final_edges) - len(initial_edges),
    }
```

### Gradual Scoring

```python
def score_task(checks):
    """Given a list of (weight, bool) tuples, return 0.0-1.0 score."""
    total = sum(w for w, _ in checks)
    earned = sum(w for w, passed in checks if passed)
    return round(earned / total, 2) if total > 0 else 0.0

# Example reward.py:
# xml = read_diagram_xml(page)
# parsed = parse_diagram(xml)
# checks = [
#     (0.3, verify_vertex_exists(parsed, value="Database")),
#     (0.2, verify_shape_type(parsed, "db", "cylinder3")),
#     (0.2, verify_edge_exists(parsed, "api", "db")),
#     (0.15, verify_vertex_color(parsed, "db", fill_color="#f5f5f5")),
#     (0.15, verify_vertex_count(parsed, min_count=5)),
# ]
# print(score_task(checks))
```

---

## 3. Bitter Lessons

1. **NEVER use `?offline=1` in the URL.** This prevents the editor from loading entirely. The editor stays stuck on "Loading..." forever. Use only `?splash=0`.

2. **Editor takes 10–40 seconds to load.** draw.io is a heavy Java/Tomcat app. The load time is inconsistent — sometimes 5s, sometimes 40s. Always poll with `wait_for_editor()` up to 60s.

3. **The editor JS instance is NOT accessible.** `window.ui`, `window.geEditor`, and all global variables do NOT hold the EditorUi instance. It lives inside a closure. You cannot call `ui.editor.setGraphXml()` or `graph.insertVertex()` programmatically.

4. **XML injection must go through Edit Diagram dialog.** The only reliable way to load a diagram is: Extras menu → Edit Diagram → paste XML in textarea → click OK. Keyboard shortcut Ctrl+E does NOT work reliably.

5. **Use `page.locator("text=Edit Diagram").first.click()` for menu items.** draw.io menus use mxPopupMenu with `<td>` cells, not standard HTML buttons. Playwright's text locator works; manual `querySelector` on `<td>` is fragile.

6. **Textarea value must be set via native setter.** Standard `ta.value = xml` does not trigger draw.io's event handlers. Use `Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(ta, xml)` followed by dispatching `input` and `change` events.

7. **Reading XML back also requires the Edit Diagram dialog.** Open the dialog, read `textarea.value`, then close with Cancel (not OK) to avoid accidental changes.

8. **mxGraphModel requires root cells `id="0"` and `id="1"`.** Cell 0 is the root, cell 1 is the default layer. Every vertex/edge must have `parent="1"`. Missing these causes blank diagrams.

9. **Style strings are semicolon-separated, no spaces.** `fillColor=#dae8fc;strokeColor=#6c8ebf;` — adding spaces breaks parsing. Always use `f"key={value};"` format.

10. **Vertex values support HTML.** The `value` attribute can contain HTML entities (`&amp;`, `&#xa;` for newline). For multi-line labels use `&#xa;` between lines and set `whiteSpace=wrap;html=1;` in style.

11. **Edge routing uses `edgeStyle`.** `orthogonalEdgeStyle` = right-angle routing (most common), `entityRelationEdgeStyle` = ER diagram style, no edgeStyle = straight lines. Always specify to avoid unpredictable routing.

12. **DOM verification is less precise than XML.** The rendered SVG has transformed coordinates that differ from the XML geometry. For position/size checks, always prefer XML-based verification over DOM inspection.

13. **draw.io autosaves to localStorage key `.drawio-autosave-1`.** But this autosave data is encoded/compressed and not suitable for direct injection. Always use the Edit Diagram dialog for both read and write.

14. **Multi-page diagrams need `<mxfile>` wrapper.** Single-page diagrams can use bare `<mxGraphModel>`. Multi-page diagrams must wrap each page in `<diagram name="..." id="...">` inside `<mxfile>`.
