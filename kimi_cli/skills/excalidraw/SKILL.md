---
name: excalidraw
description: "How to programmatically set up, manipulate, and verify Excalidraw whiteboard state using Python (Playwright CDP, localStorage JSON, scene elements). For setup-gen and reward-gen agents."
user-invocable: false
---

# Excalidraw — Python Manipulation Guide

This skill teaches **setup-gen** (inject initial drawing scene) and **reward-gen** (verify drawing state after agent actions) how to work with a self-hosted Excalidraw instance via Playwright CDP + localStorage.

- Libraries: `playwright`
- Install: `pip3 install playwright && playwright install chromium`
- Deployed at: `https://cua-gym-excalidraw.xlang.ai`
- State storage: **browser localStorage** (key `excalidraw` = JSON array of elements)

---

## 0. GUI Startup on VM (for setup-gen)

Excalidraw runs as a web app inside Chrome. Setup-gen must:
1. Connect to Chrome via CDP (Chrome is already running with `--remote-debugging-port`)
2. Open a new tab to the Excalidraw URL
3. Wait for the React app to mount
4. Inject scene via localStorage
5. Reload to apply
6. Leave the tab open for the CUA agent

```python
import json, time
from playwright.sync_api import sync_playwright

EXCALIDRAW_URL = "https://cua-gym-excalidraw.xlang.ai"

def setup_excalidraw(elements, host="localhost", port=9222):
    """Open Excalidraw in existing Chrome and inject initial scene."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{host}:{port}")
        context = browser.contexts[0]
        page = context.new_page()

        # Load Excalidraw and wait for React mount
        page.goto(EXCALIDRAW_URL, wait_until="load", timeout=60000)
        page.wait_for_selector(".excalidraw", timeout=30000)
        time.sleep(2)

        # Inject scene via JS argument passing (avoids JSON escaping issues)
        page.evaluate("(data) => { window.__scene = data; }", elements)
        page.evaluate("""() => {
            localStorage.setItem('excalidraw', JSON.stringify(window.__scene));
            localStorage.setItem('excalidraw-state', JSON.stringify({
                viewBackgroundColor: "#ffffff",
                gridSize: null
            }));
            delete window.__scene;
        }""")

        # Reload to let Excalidraw read the injected state
        page.reload(wait_until="load", timeout=60000)
        page.wait_for_selector(".excalidraw", timeout=30000)
        time.sleep(2)

        # Close blank tabs
        for pg in context.pages:
            if pg.url in ("about:blank", "chrome://newtab/"):
                pg.close()
                break
        # Do NOT close browser — agent needs it
```

Guidelines:
- ALWAYS use `page.evaluate("(data) => ...", elements)` to pass scene data as a JS argument. Never embed JSON in template strings — it breaks on special characters.
- ALWAYS reload after setting localStorage. Excalidraw only reads localStorage on initialization.
- Do NOT call `browser.close()` — the CUA agent needs the tab.

---

## 1. Creating Excalidraw Scenes (setup-gen)

### Element Schema

Every element in the `elements` array must have these fields:

```python
def make_element(type, id, x, y, w, h, extra=None):
    """Base element factory. All Excalidraw elements share these fields."""
    el = {
        "type": type,           # "rectangle"|"ellipse"|"diamond"|"line"|"arrow"|"text"|"freedraw"
        "id": id,               # unique string ID
        "x": x, "y": y,        # position (top-left corner)
        "width": w, "height": h,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",   # "solid"|"hachure"|"cross-hatch"
        "strokeWidth": 2,       # 1, 2, or 4
        "roughness": 0,         # 0=architect, 1=artist, 2=cartoonist
        "opacity": 100,         # 0-100
        "angle": 0,             # rotation in radians
        "seed": abs(hash(id)) % 999999,
        "version": 1,
        "versionNonce": abs(hash(id + "v")) % 999999,
        "isDeleted": False,
        "boundElements": [],    # list of {id, type} for bound text/arrows
        "updated": 1700000000000,
        "link": None,
        "locked": False,
    }
    if extra:
        el.update(extra)
    return el
```

### Shape Elements

```python
def rect(id, x, y, w, h, bg="#a5d8ff", stroke="#1971c2", text_id=None):
    extra = {"backgroundColor": bg, "strokeColor": stroke, "roundness": {"type": 3}}
    if text_id:
        extra["boundElements"] = [{"id": text_id, "type": "text"}]
    return make_element("rectangle", id, x, y, w, h, extra)

def ellipse(id, x, y, w, h, bg="#d0bfff", stroke="#7950f2", text_id=None):
    extra = {"backgroundColor": bg, "strokeColor": stroke}
    if text_id:
        extra["boundElements"] = [{"id": text_id, "type": "text"}]
    return make_element("ellipse", id, x, y, w, h, extra)

def diamond(id, x, y, w, h, bg="#fff3bf", stroke="#e67700", text_id=None):
    extra = {"backgroundColor": bg, "strokeColor": stroke}
    if text_id:
        extra["boundElements"] = [{"id": text_id, "type": "text"}]
    return make_element("diamond", id, x, y, w, h, extra)
```

### Text Elements

```python
def text(id, x, y, txt, font_size=20, container_id=None):
    """Text element. Set container_id to bind to a shape."""
    return make_element("text", id, x, y,
        len(txt) * font_size * 0.55,    # approximate width
        font_size * 1.4,                 # approximate height
        {
            "text": txt,
            "originalText": txt,
            "fontSize": font_size,       # common: 16, 20, 28, 36
            "fontFamily": 1,             # 1=Virgil, 2=Helvetica, 3=Cascadia
            "textAlign": "center",       # "left"|"center"|"right"
            "verticalAlign": "middle",   # "top"|"middle"
            "strokeColor": "#1e1e1e",
            "backgroundColor": "transparent",
            "containerId": container_id, # ID of parent shape, or None for freestanding
            "lineHeight": 1.25,
        })
```

### Arrow and Line Elements

```python
def arrow(id, x1, y1, x2, y2, start_id=None, end_id=None):
    """Arrow connecting two points (optionally bound to shapes)."""
    extra = {
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "startArrowhead": None,
        "endArrowhead": "arrow",       # "arrow"|"bar"|"dot"|"triangle"|None
        "lastCommittedPoint": None,
    }
    if start_id:
        extra["startBinding"] = {"elementId": start_id, "focus": 0, "gap": 5}
    if end_id:
        extra["endBinding"] = {"elementId": end_id, "focus": 0, "gap": 5}
    return make_element("arrow", id, x1, y1, abs(x2 - x1) or 1, abs(y2 - y1) or 1, extra)

def line(id, x1, y1, x2, y2):
    return make_element("line", id, x1, y1, abs(x2 - x1) or 1, abs(y2 - y1) or 1, {
        "points": [[0, 0], [x2 - x1, y2 - y1]],
        "lastCommittedPoint": None,
    })
```

### Building a Complete Scene

```python
def build_flowchart():
    """Example: a simple flowchart with 3 shapes and arrows."""
    elements = []

    # Shapes with bound text
    elements.append(ellipse("start", 200, 50, 140, 80, "#d0bfff", "#7950f2", "start_t"))
    elements.append(text("start_t", 230, 75, "Start", container_id="start"))

    elements.append(rect("process", 200, 200, 140, 70, "#a5d8ff", "#1971c2", "proc_t"))
    elements.append(text("proc_t", 225, 220, "Process", container_id="process"))

    elements.append(diamond("decide", 195, 340, 150, 110, "#fff3bf", "#e67700", "dec_t"))
    elements.append(text("dec_t", 230, 378, "Done?", container_id="decide"))

    # Arrows
    elements.append(arrow("a1", 270, 130, 270, 200, "start", "process"))
    elements.append(arrow("a2", 270, 270, 270, 340, "process", "decide"))

    return elements
```

### Color Palette Reference

| Color | Hex | Use |
|-------|-----|-----|
| Light blue | `#a5d8ff` / `#1971c2` | Default shapes |
| Light green | `#b2f2bb` / `#2f9e44` | Success, approved |
| Light red | `#ffc9c9` / `#e03131` | Error, rejected |
| Light purple | `#d0bfff` / `#7950f2` | Start nodes |
| Light yellow | `#fff3bf` / `#e67700` | Decisions |
| Gray | `#e9ecef` / `#868e96` | Notes, background |

### App State Options

```python
app_state = {
    "viewBackgroundColor": "#ffffff",  # canvas background: any hex color
    "gridSize": None,                  # null=no grid, 20=grid
}
```

---

## 2. Reading & Verifying Scenes (reward-gen)

### Reading Scene State

```python
def read_scene(host="localhost", port=9222):
    """Read current Excalidraw scene from localStorage."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{host}:{port}")
        context = browser.contexts[0]

        # Find the Excalidraw tab
        page = None
        for pg in context.pages:
            if "excalidraw" in pg.url:
                page = pg
                break
        if not page:
            return None

        return page.evaluate("""() => {
            const stored = localStorage.getItem('excalidraw');
            if (!stored) return null;
            try { return JSON.parse(stored); }
            catch(e) { return null; }
        }""")
```

### Element Queries

```python
def get_elements_by_type(elements, type_name):
    """Filter elements by type (rectangle, ellipse, arrow, text, etc.)."""
    return [e for e in elements if e.get("type") == type_name and not e.get("isDeleted")]

def get_element_by_id(elements, id):
    return next((e for e in elements if e["id"] == id), None)

def get_text_in_container(elements, container_id):
    """Get text content of a text element bound to a container."""
    for e in elements:
        if e.get("type") == "text" and e.get("containerId") == container_id:
            return e.get("text", "")
    return None
```

### Property Verification

```python
def verify_element_color(elements, element_id, expected_bg=None, expected_stroke=None):
    el = get_element_by_id(elements, element_id)
    if not el:
        return False
    if expected_bg and el.get("backgroundColor") != expected_bg:
        return False
    if expected_stroke and el.get("strokeColor") != expected_stroke:
        return False
    return True

def verify_element_position(elements, element_id, expected_x, expected_y, tolerance=20):
    el = get_element_by_id(elements, element_id)
    if not el:
        return False
    return abs(el["x"] - expected_x) <= tolerance and abs(el["y"] - expected_y) <= tolerance

def verify_element_size(elements, element_id, expected_w, expected_h, tolerance=20):
    el = get_element_by_id(elements, element_id)
    if not el:
        return False
    return abs(el["width"] - expected_w) <= tolerance and abs(el["height"] - expected_h) <= tolerance

def verify_element_text(elements, container_id, expected_text):
    actual = get_text_in_container(elements, container_id)
    if actual is None:
        return False
    return actual.strip() == expected_text.strip()
```

### Structural Verification

```python
def verify_element_count(elements, type_name=None, expected_count=None, min_count=None):
    filtered = get_elements_by_type(elements, type_name) if type_name else [
        e for e in elements if not e.get("isDeleted")
    ]
    if expected_count is not None:
        return len(filtered) == expected_count
    if min_count is not None:
        return len(filtered) >= min_count
    return len(filtered) > 0

def verify_connection(elements, from_id, to_id):
    """Verify an arrow connects from_id to to_id."""
    arrows = get_elements_by_type(elements, "arrow")
    for a in arrows:
        start = a.get("startBinding", {})
        end = a.get("endBinding", {})
        if start.get("elementId") == from_id and end.get("elementId") == to_id:
            return True
    return False

def verify_no_element(elements, element_id):
    """Verify element was deleted or doesn't exist."""
    el = get_element_by_id(elements, element_id)
    return el is None or el.get("isDeleted", False)

def verify_background_color(page, expected_color):
    """Verify canvas background color."""
    state = page.evaluate("""() => {
        const s = localStorage.getItem('excalidraw-state');
        return s ? JSON.parse(s) : null;
    }""")
    if not state:
        return False
    return state.get("viewBackgroundColor") == expected_color
```

### Diff-Based Verification (comparing initial vs final state)

```python
def diff_scenes(initial_elements, final_elements):
    """Compare two scenes, return added/removed/modified elements."""
    initial_map = {e["id"]: e for e in initial_elements if not e.get("isDeleted")}
    final_map = {e["id"]: e for e in final_elements if not e.get("isDeleted")}

    added = [final_map[id] for id in final_map if id not in initial_map]
    removed = [initial_map[id] for id in initial_map if id not in final_map]
    modified = []
    for id in set(initial_map) & set(final_map):
        if initial_map[id] != final_map[id]:
            modified.append({"id": id, "before": initial_map[id], "after": final_map[id]})

    return {"added": added, "removed": removed, "modified": modified}
```

### Gradual Scoring

```python
def score_task(checks):
    """Given a list of (weight, bool) tuples, return 0.0-1.0 score."""
    total_weight = sum(w for w, _ in checks)
    earned = sum(w for w, passed in checks if passed)
    return round(earned / total_weight, 2) if total_weight > 0 else 0.0

# Example reward.py scoring:
# elements = read_scene()
# checks = [
#     (0.3, verify_element_count(elements, "rectangle", expected_count=4)),
#     (0.3, verify_element_text(elements, "title_box", "System Design")),
#     (0.2, verify_connection(elements, "box_a", "box_b")),
#     (0.2, verify_element_color(elements, "box_a", expected_bg="#b2f2bb")),
# ]
# print(score_task(checks))
```

---

## 3. Bitter Lessons

1. **Excalidraw overwrites localStorage on init.** If you set localStorage and then navigate to Excalidraw, the app reads it once during React mount. But if the app is *already loaded* when you set localStorage, it ignores the change. You MUST reload after setting localStorage.

2. **`window.excalidrawAPI` is NOT exposed on the self-hosted instance.** The public excalidraw.com exposes this API, but the self-hosted build does not. All state manipulation must go through localStorage, not the JS API.

3. **Never embed JSON in f-strings or template literals.** Scene data contains quotes, braces, and backslashes that break string interpolation. Always pass data as a JS function argument: `page.evaluate("(data) => { ... }", elements)`.

4. **localStorage is per-browser-context.** Playwright's `browser.new_context()` creates isolated storage. On the VM, always use `browser.contexts[0]` (the existing Chrome profile) to share state with the CUA agent.

5. **Element IDs must be unique.** Duplicate IDs cause silent overwrites. Use descriptive string IDs (`"start_node"`, `"arrow_1"`) rather than auto-generated UUIDs for easier reward verification.

6. **Bound text requires bidirectional linking.** A text element needs `containerId: "shape_id"`, AND the parent shape needs `boundElements: [{id: "text_id", type: "text"}]`. Missing either side causes rendering bugs.

7. **Arrow bindings use `startBinding` / `endBinding`, not `boundElements`.** Arrows store their connections differently from shapes. The binding object has `{elementId, focus, gap}`.

8. **`isDeleted: true` elements persist in localStorage.** Excalidraw soft-deletes elements. When counting elements, always filter by `not e.get("isDeleted")`. The diff-based verifier must handle this.

9. **Element `version` must increment on modification.** When updating an element, increment its `version` field. Excalidraw uses version numbers for conflict resolution and undo/redo.

10. **`roughness: 0` gives clean lines, `1-2` gives hand-drawn style.** Tasks about "making it look hand-drawn" should change roughness. Tasks about "clean/professional diagrams" should use `roughness: 0`.

11. **Text width/height are approximate.** Excalidraw calculates exact text dimensions at render time. The values in localStorage are estimates. For reward verification, compare text *content*, not dimensions.

12. **Canvas background is in `excalidraw-state`, not `excalidraw`.** The `excalidraw` key stores elements. The `excalidraw-state` key stores app state including `viewBackgroundColor`. Both must be set during setup.

13. **Excalidraw loads in ~3 seconds.** Much faster than draw.io. Use `page.wait_for_selector(".excalidraw", timeout=30000)` as the readiness check.

14. **`fillStyle` affects visual appearance significantly.** `"solid"` = flat fill, `"hachure"` = diagonal lines, `"cross-hatch"` = cross lines. Changing this is a valid task dimension.
