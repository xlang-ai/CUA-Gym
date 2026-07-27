---
name: gimp
description: "How to programmatically create, modify, and verify images using Python Pillow, NumPy, OpenCV, and scikit-image. For setup-gen and reward-gen agents."
user-invocable: false
---

# GIMP — Python Manipulation Guide

This skill teaches **setup-gen** (create/modify images) and **reward-gen** (read/verify image properties) how to work with image files using pure Python code.

- Libraries: `Pillow`, `numpy`, `opencv-python`, `scikit-image`
- Install: `pip3 install Pillow numpy opencv-python scikit-image`
- File formats: `.png`, `.jpg`, `.bmp`, `.xcf` (GIMP native, read-only via special tools)

---

## 0. GUI Startup on VM (for setup-gen)

After generating image assets, setup-gen should open GIMP with the target initial file for the GUI agent.

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

# Open target image in GIMP
launch_gui('gimp "/home/user/<task_id>_initial.png"', delay_sec=2.0)
```

Guidelines:
- Open initial artifact(s), never golden artifact(s).
- Use non-blocking launch (`Popen`) and short delays.

---

## 0.5. Media Asset Library (setup-gen)

Instead of generating synthetic images (color blocks, `testsrc` patterns), use the **real photo library** at `assets/media/gimp/`. These are high-resolution photos from Pexels (free commercial use).

### Picking Assets from Manifest

```python
import json, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
MANIFEST = os.path.join(ROOT, "assets", "media", "manifest.json")

def pick_asset(domain: str, category: str = None, tags: list = None) -> dict:
    """Pick a random asset matching domain/category/tags from manifest."""
    with open(MANIFEST) as f:
        manifest = json.load(f)
    candidates = [a for a in manifest["assets"] if a["domain"] == domain]
    if category:
        candidates = [a for a in candidates if a["category"] == category]
    if tags:
        candidates = [a for a in candidates if any(t in a.get("tags", []) for t in tags)]
    return random.choice(candidates) if candidates else None

# Pick a landscape photo for a brightness adjustment task
asset = pick_asset("gimp", "photos", tags=["landscape", "nature"])
local_path = os.path.join(ROOT, asset["path"])  # e.g., assets/media/gimp/photos/landscape_mountain_001.jpg
```

### Uploading to VM

```bash
# Upload a photo to the VM before running initial_setup.py
python3 scripts/env_cli.py -c "<workdir>/env_config_initial.json" upload \
    "assets/media/gimp/photos/landscape_mountain_001.jpg" "/home/user/<task_id>.jpg"
python3 scripts/env_cli.py -c "<workdir>/env_config_golden.json" upload \
    "assets/media/gimp/photos/landscape_mountain_001.jpg" "/home/user/<task_id>.jpg"
```

### Available Categories

| Category | Count | Description | Good for |
|----------|-------|-------------|----------|
| `photos` | ~50 | Real high-res photos (landscape, portrait, food, architecture, etc.) | Brightness, contrast, crop, resize, rotate, color grading |
| `graphics` | ~10 | Geometric patterns, gradients, abstract art | Color mode conversion, palette, effects |
| `icons` | ~10 | Logo/icon style images | Transparency, compositing, background removal |

### Pattern: Upload + Reference Copy

```bash
# Setup-gen should upload the asset to BOTH VMs, then initial_setup.py saves the reference copy
python3 scripts/env_cli.py -c "<workdir>/env_config_initial.json" upload "assets/media/gimp/photos/xxx.jpg" "/home/user/<task_id>.jpg"
python3 scripts/env_cli.py -c "<workdir>/env_config_golden.json"  upload "assets/media/gimp/photos/xxx.jpg" "/home/user/<task_id>.jpg"
```

Then in `initial_setup.py`:
```python
import shutil
shutil.copy(f'{WORKDIR}/{TASK_ID}.jpg', f'{WORKDIR}/{TASK_ID}_initial_reference.jpg')
# ... launch GIMP with the file
```

---

## 1. Creating & Modifying Images (setup-gen)

### Basic Image Creation

```python
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageStat, ImageEnhance
from PIL.Image import Resampling
import numpy as np
import shutil, os

# Create blank image
img = Image.new("RGB", (800, 600), color=(255, 255, 255))
img.save("/home/user/Desktop/blank.png")

# Create RGBA image with transparency
img = Image.new("RGBA", (800, 600), color=(0, 0, 0, 0))
img.save("/home/user/Desktop/transparent.png")
```

### Drawing Shapes and Text

```python
draw = ImageDraw.Draw(img)
# Rectangle
draw.rectangle([100, 100, 300, 200], fill="red", outline="black", width=2)
# Circle / ellipse
draw.ellipse([400, 100, 550, 250], fill="blue")
# Triangle (polygon)
draw.polygon([(400, 300), (300, 500), (500, 500)], fill="yellow", outline="black")
# Line
draw.line([(0, 0), (800, 600)], fill="green", width=3)
# Text
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
draw.text((100, 50), "Hello World", fill="black", font=font)
img.save("/home/user/Desktop/shapes.png")
```

### Image Transformations

```python
img = Image.open("/home/user/Desktop/photo.png")

# Resize (maintain aspect ratio)
target_height = 512
ratio = target_height / img.height
new_size = (int(img.width * ratio), target_height)
img_resized = img.resize(new_size, Resampling.LANCZOS)

# Crop
img_cropped = img.crop((left, top, right, bottom))  # box = (left, upper, right, lower)

# Rotate
img_rotated = img.rotate(90, expand=True)  # expand=True to fit full rotated image

# Mirror / flip
img_mirror = img.transpose(Image.FLIP_LEFT_RIGHT)     # horizontal mirror
img_flip = img.transpose(Image.FLIP_TOP_BOTTOM)        # vertical flip

# Convert color mode
img_gray = img.convert("L")         # grayscale
img_rgb = img.convert("RGB")        # RGB (drops alpha)
img_rgba = img.convert("RGBA")      # add alpha channel
img_palette = img.convert("P")      # indexed/palette mode
img_hsv = img.convert("HSV")        # hue-saturation-value
```

### Brightness, Contrast, Saturation Adjustments

```python
# Brightness
enhancer = ImageEnhance.Brightness(img)
img_darker = enhancer.enhance(0.7)    # < 1 = darker, > 1 = brighter

# Contrast
enhancer = ImageEnhance.Contrast(img)
img_contrast = enhancer.enhance(1.5)  # > 1 = more contrast

# Saturation / Color
enhancer = ImageEnhance.Color(img)
img_vivid = enhancer.enhance(1.5)     # > 1 = more saturated

# Sharpness
enhancer = ImageEnhance.Sharpness(img)
img_sharp = enhancer.enhance(2.0)     # > 1 = sharper
```

### Transparency & Background Removal

```python
# Make white background transparent
img = img.convert("RGBA")
data = np.array(img)
# Replace white pixels with transparent
white_mask = (data[:, :, 0] > 240) & (data[:, :, 1] > 240) & (data[:, :, 2] > 240)
data[white_mask, 3] = 0
img = Image.fromarray(data)

# Fill background layer with a color (keeping object intact)
bg = Image.new("RGB", img.size, (0, 255, 0))  # green background
if img.mode == "RGBA":
    bg.paste(img, mask=img.split()[3])  # paste using alpha as mask
```

### Filters

```python
img_blur = img.filter(ImageFilter.GaussianBlur(radius=5))
img_sharp = img.filter(ImageFilter.SHARPEN)
img_edges = img.filter(ImageFilter.FIND_EDGES)
img_emboss = img.filter(ImageFilter.EMBOSS)
```

### Golden File Pattern

```python
# Always copy-then-modify for golden files
shutil.copy("/home/user/Desktop/original.png", "/home/user/Desktop/golden.png")
img = Image.open("/home/user/Desktop/golden.png")
img = img.transpose(Image.FLIP_LEFT_RIGHT)  # example transformation
img.save("/home/user/Desktop/golden.png")
```

### Compositing Multiple Images

```python
bg = Image.open("/home/user/Desktop/background.png").convert("RGBA")
fg = Image.open("/home/user/Desktop/foreground.png").convert("RGBA")
# Paste foreground onto background at position
bg.paste(fg, (100, 100), mask=fg)  # use alpha as mask
bg.save("/home/user/Desktop/composite.png")
```

---

## 2. Reading & Verifying Images (reward-gen)

### Structure Similarity (SSIM)

```python
from skimage.metrics import structural_similarity as ssim

def check_ssim(src_path: str, tgt_path: str, threshold: float = 0.9) -> bool:
    """Compare two same-sized images by SSIM. Returns True if similar."""
    img1 = Image.open(src_path).convert("RGB")
    img2 = Image.open(tgt_path).convert("RGB")
    if img1.size != img2.size:
        return False
    arr1, arr2 = np.array(img1), np.array(img2)
    min_dim = min(arr1.shape[0], arr1.shape[1])
    win_size = min(7, min_dim if min_dim % 2 == 1 else min_dim - 1)
    if win_size < 1:
        return False
    try:
        score = ssim(arr1, arr2, win_size=win_size, channel_axis=2)
    except TypeError:
        score = ssim(arr1, arr2, win_size=win_size, multichannel=True)
    return score >= threshold

def check_ssim_resized(src_path: str, tgt_path: str, threshold: float = 0.9) -> bool:
    """SSIM with auto-resize and transparency handling."""
    img1 = Image.open(src_path)
    img2 = Image.open(tgt_path)
    # Handle transparency: crop to content bounding box
    if img1.mode in ("RGBA", "LA"):
        alpha = img1.split()[-1]
        bbox = alpha.getbbox()
        if bbox:
            img1 = img1.crop(bbox)
    img1 = img1.convert("RGB").resize(img2.size if img2.mode == "RGB" else img2.convert("RGB").size, Resampling.LANCZOS)
    img2 = img2.convert("RGB")
    arr1, arr2 = np.array(img1), np.array(img2)
    try:
        score = ssim(arr1, arr2, win_size=7, channel_axis=2)
    except TypeError:
        score = ssim(arr1, arr2, win_size=7, multichannel=True)
    return score >= threshold
```

### Pixel-Perfect Comparison

```python
def compare_exact(src_path: str, tgt_path: str) -> bool:
    """Binary comparison: True only if all pixels match."""
    img1 = Image.open(src_path)
    img2 = Image.open(tgt_path)
    if img1.size != img2.size:
        img1 = img1.resize(img2.size, Resampling.LANCZOS)
    if img1.mode != img2.mode:
        img1 = img1.convert(img2.mode)
    diff = ImageChops.difference(img1, img2)
    return diff.getbbox() is None
```

### Brightness Verification

```python
def calculate_brightness(img: Image.Image) -> float:
    gray = img.convert("L")
    return ImageStat.Stat(gray).mean[0]

def verify_brightness_decreased(src_path: str, tgt_path: str) -> bool:
    """Verify src is darker than tgt AND structure preserved."""
    img_src = Image.open(src_path)
    img_tgt = Image.open(tgt_path)
    if calculate_brightness(img_src) >= calculate_brightness(img_tgt):
        return False
    # Normalize both to same brightness, then compare structure
    def normalize(img, target=128):
        factor = target / max(calculate_brightness(img), 1)
        return img.point(lambda x: min(255, max(0, int(x * factor))))
    mse = np.mean((np.array(normalize(img_src), dtype=np.float32) / 255 -
                    np.array(normalize(img_tgt), dtype=np.float32) / 255) ** 2)
    return mse < 0.03
```

### Contrast Verification

```python
def calculate_contrast(img: Image.Image) -> float:
    return float(np.std(np.asarray(img, dtype=np.float32)))

def verify_contrast_increased(src_path: str, tgt_path: str) -> bool:
    src, tgt = Image.open(src_path), Image.open(tgt_path)
    return calculate_contrast(src) > calculate_contrast(tgt) and check_ssim(src_path, tgt_path, threshold=0.65)
```

### Saturation Verification

```python
def verify_saturation_increased(src_path: str, tgt_path: str) -> bool:
    src_hsv = Image.open(src_path).convert("HSV")
    tgt_hsv = Image.open(tgt_path).convert("HSV")
    src_sat = np.mean(np.array(src_hsv.split()[1]))
    tgt_sat = np.mean(np.array(tgt_hsv.split()[1]))
    if src_sat <= tgt_sat:
        return False  # saturation did not increase
    # H and V channels must match
    h1, _, v1 = src_hsv.split()
    h2, _, v2 = tgt_hsv.split()
    return check_ssim_channel(h1, h2) and check_ssim_channel(v1, v2)

def check_ssim_channel(ch1, ch2, threshold=0.9):
    arr1, arr2 = np.array(ch1.convert("RGB")), np.array(ch2.convert("RGB"))
    if arr1.shape != arr2.shape:
        return False
    try:
        return ssim(arr1, arr2, win_size=7, channel_axis=2) >= threshold
    except TypeError:
        return ssim(arr1, arr2, win_size=7, multichannel=True) >= threshold
```

### Image Size Verification

```python
def verify_image_size(src_path: str, width: int = None, height: int = None,
                      ignore_transparent: bool = False) -> bool:
    img = Image.open(src_path)
    if ignore_transparent and img.mode in ("RGBA", "LA"):
        alpha = img.split()[-1]
        bbox = alpha.getbbox()
        if bbox is None:
            return False
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    else:
        w, h = img.size
    if width is not None and w != width:
        return False
    if height is not None and h != height:
        return False
    return True
```

### Mirror Verification

```python
def verify_mirror(src_path: str, tgt_path: str) -> bool:
    src = Image.open(src_path)
    tgt = Image.open(tgt_path)
    flipped = src.transpose(Image.FLIP_LEFT_RIGHT)
    arr1, arr2 = np.array(flipped.convert("RGB")), np.array(tgt.convert("RGB"))
    if arr1.shape != arr2.shape:
        return False
    try:
        return ssim(arr1, arr2, win_size=7, channel_axis=2) >= 0.99
    except TypeError:
        return ssim(arr1, arr2, win_size=7, multichannel=True) >= 0.99
```

### Palette Mode Verification

```python
def verify_palette_mode(src_path: str, tgt_path: str) -> bool:
    """Verify image is palette-based and structure matches."""
    img = Image.open(src_path)
    if img.mode != "P":
        return False
    return check_ssim(src_path, tgt_path, threshold=0.9)  # compare after RGB conversion
```

### Green Background Verification

```python
def verify_green_background(src_path: str, tgt_path: str) -> bool:
    """All non-black target pixels must have green source pixels (g > r and g > b)."""
    src = np.array(Image.open(src_path))
    tgt = np.array(Image.open(tgt_path))
    # Vectorized: find non-black pixels in target
    mask = np.any(tgt[:, :, :3] != 0, axis=2)
    if not np.any(mask):
        return True
    r, g, b = src[mask, 0], src[mask, 1], src[mask, 2]
    return bool(np.all(g > r) and np.all(g > b))
```

### Shape Position Verification

```python
def verify_centered(tgt_path: str, tolerance: float = 0.05) -> bool:
    """Verify a colored shape is centered within tolerance of image center."""
    img = np.array(Image.open(tgt_path))
    unique_colors, counts = np.unique(img.reshape(-1, img.shape[2]), axis=0, return_counts=True)
    sorted_colors = unique_colors[np.argsort(counts)]
    shape_color = sorted_colors[1]  # second most common = shape (not background)
    mask = np.all(img == shape_color, axis=2)
    coords = np.argwhere(mask)
    centroid = coords.mean(axis=0)
    center = np.array(img.shape[:2]) / 2
    return bool(np.all(np.abs(centroid - center) < tolerance * np.array(img.shape[:2])))
```

### Text Position Verification

```python
def verify_text_on_left(src_path: str, width_threshold: float = 0.05) -> bool:
    """Verify dark text starts within the left edge of the image."""
    gray = np.array(Image.open(src_path).convert("L"))
    h, w = gray.shape
    dark_mask = gray < 128
    if not np.any(dark_mask):
        return False
    # Find the leftmost dark pixel across all rows
    cols = np.where(dark_mask.any(axis=0))[0]
    left_most = cols[0] if len(cols) > 0 else w
    return left_most < w * width_threshold
```

### Sharpness Verification

```python
import cv2

def verify_sharper(src_path: str, tgt_path: str) -> bool:
    src = cv2.imread(src_path, cv2.IMREAD_GRAYSCALE)
    tgt = cv2.imread(tgt_path, cv2.IMREAD_GRAYSCALE)
    return float(np.var(cv2.Laplacian(src, cv2.CV_64F))) > float(np.var(cv2.Laplacian(tgt, cv2.CV_64F)))
```

### File Existence & Size Verification

```python
def verify_file_exists_and_similar(src_path: str, tgt_path: str) -> bool:
    if not os.path.isfile(src_path):
        return False
    return check_ssim(src_path, tgt_path)

def verify_file_size(src_path: str, max_bytes: int) -> bool:
    return os.path.isfile(src_path) and os.path.getsize(src_path) < max_bytes
```

### GIMP Config Verification

```python
def verify_gimp_config(config_path: str, key, value: str) -> bool:
    """Check GIMP gimprc config file for key-value pair.
    key can be str or list of str (for multi-word keys)."""
    with open(config_path, "r") as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                continue
            items = line.strip().lstrip("(").rstrip(")").split()
            if isinstance(key, str):
                if items[0] == key and items[-1] == value:
                    return True
            elif isinstance(key, list) and len(key) == 2:
                if items[0] == key[0] and items[1] == key[1] and items[-1] == value:
                    return True
    return False
```

---

## 3. XCF (GIMP Native Format) Reading

GIMP's native `.xcf` format stores layers, channels, and paths. Pillow cannot read XCF. Use these approaches:

### Reading XCF with python-xcftools

```python
import subprocess, json, re

def get_xcf_info(xcf_path: str) -> dict:
    """Extract XCF metadata: dimensions, layers, color mode."""
    result = subprocess.run(["xcfinfo", xcf_path], capture_output=True, text=True)
    info = {"layers": [], "width": 0, "height": 0}
    for line in result.stdout.strip().split("\n"):
        # First line: "Version X, WxH RGB color, N layers, ..."
        if line.startswith("Version"):
            m = re.search(r'(\d+)x(\d+)\s+(\w+)', line)
            if m:
                info["width"], info["height"] = int(m.group(1)), int(m.group(2))
                info["color_mode"] = m.group(3)
        # Layer lines: "+ WxH+X+Y RGB-alpha Normal name"
        elif line.startswith("+") or line.startswith("-"):
            parts = line.strip().split()
            visible = parts[0] == "+"
            # Layer name is last quoted or unquoted token
            name = " ".join(parts[4:]) if len(parts) > 4 else ""
            info["layers"].append({"name": name, "visible": visible})
    return info

def get_xcf_layer_count(xcf_path: str) -> int:
    info = get_xcf_info(xcf_path)
    return len(info["layers"])

def verify_xcf_has_layer(xcf_path: str, layer_name: str) -> bool:
    info = get_xcf_info(xcf_path)
    return any(layer_name.lower() in l["name"].lower() for l in info["layers"])
```

### Flattening XCF to PNG for Comparison

```python
def xcf_to_png(xcf_path: str, png_path: str) -> bool:
    """Flatten XCF to PNG using xcf2png (from xcftools package)."""
    result = subprocess.run(["xcf2png", xcf_path, "-o", png_path], capture_output=True)
    return result.returncode == 0

def xcf_extract_layer(xcf_path: str, layer_name: str, png_path: str) -> bool:
    """Extract a single layer from XCF to PNG."""
    result = subprocess.run(
        ["xcf2png", xcf_path, layer_name, "-o", png_path],
        capture_output=True
    )
    return result.returncode == 0

# Install on VM: sudo apt install xcftools
```

---

## 4. GIMP Script-Fu Batch Mode

For tasks that require GIMP-specific operations (filters, layer manipulation), use headless batch mode.

```python
def gimp_batch(script_fu: str, timeout: int = 30) -> str:
    """Run a Script-Fu command in GIMP batch mode (headless)."""
    result = subprocess.run(
        ["gimp", "-i", "-b", script_fu, "-b", "(gimp-quit 0)"],
        capture_output=True, text=True, timeout=timeout,
        env={**os.environ, "DISPLAY": ":0"}
    )
    return result.stdout + result.stderr

# Flatten an XCF and export as PNG
gimp_batch('(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "/home/user/file.xcf" "file.xcf"))) '
           '(drawable (car (gimp-image-flatten image)))) '
           '(file-png-save RUN-NONINTERACTIVE image drawable "/home/user/flat.png" "flat.png" 0 9 1 1 1 1 1))')

# Apply Gaussian blur and export
gimp_batch('(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "/home/user/in.png" "in.png"))) '
           '(drawable (car (gimp-image-flatten image)))) '
           '(plug-in-gauss RUN-NONINTERACTIVE image drawable 10 10 0) '
           '(gimp-file-overwrite RUN-NONINTERACTIVE image drawable "/home/user/out.png" "out.png"))')

# Get image properties (layer count, dimensions)
gimp_batch('(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE "/home/user/file.xcf" "file.xcf")))) '
           '(gimp-message (number->string (car (gimp-image-get-active-layer image)))) '
           '(gimp-message (number->string (car (gimp-image-width image)))))')
```

Guidelines:
- `-i` = no GUI, `-b` = batch command
- Always end with `(gimp-quit 0)` or GIMP hangs
- Script-Fu uses Scheme syntax with `car` to unwrap return lists
- Set timeout — GIMP batch can hang on missing fonts or corrupt files

---

## 5. Color Space & Color Verification

### Color Temperature / White Balance Verification

```python
def calculate_color_temperature_shift(src_path: str, tgt_path: str) -> tuple:
    """Calculate average RGB shift between two images. Returns (dr, dg, db)."""
    src = np.array(Image.open(src_path).convert("RGB"), dtype=np.float32)
    tgt = np.array(Image.open(tgt_path).convert("RGB"), dtype=np.float32)
    if src.shape != tgt.shape:
        tgt = np.array(Image.open(tgt_path).convert("RGB").resize(
            Image.open(src_path).size, Resampling.LANCZOS), dtype=np.float32)
    diff = np.mean(src - tgt, axis=(0, 1))
    return tuple(diff)

def verify_warmer_tone(src_path: str, tgt_path: str) -> bool:
    """Verify src has warmer tone than tgt (more red/yellow, less blue)."""
    dr, dg, db = calculate_color_temperature_shift(src_path, tgt_path)
    return dr > 2 and db < -2  # red increased, blue decreased

def verify_cooler_tone(src_path: str, tgt_path: str) -> bool:
    """Verify src has cooler tone than tgt (more blue, less red)."""
    dr, dg, db = calculate_color_temperature_shift(src_path, tgt_path)
    return dr < -2 and db > 2
```

### Histogram-Based Color Distribution

```python
def get_color_histogram(img_path: str, bins: int = 64) -> np.ndarray:
    """Get normalized RGB histogram."""
    img = np.array(Image.open(img_path).convert("RGB"))
    hist_r = np.histogram(img[:,:,0], bins=bins, range=(0,256))[0]
    hist_g = np.histogram(img[:,:,1], bins=bins, range=(0,256))[0]
    hist_b = np.histogram(img[:,:,2], bins=bins, range=(0,256))[0]
    hist = np.concatenate([hist_r, hist_g, hist_b]).astype(np.float32)
    return hist / hist.sum()

def verify_histogram_similar(src_path: str, tgt_path: str, threshold: float = 0.85) -> bool:
    """Compare color distributions via histogram correlation."""
    h1 = get_color_histogram(src_path)
    h2 = get_color_histogram(tgt_path)
    correlation = float(np.corrcoef(h1, h2)[0, 1])
    return correlation >= threshold

def verify_grayscale(img_path: str) -> bool:
    """Verify image is grayscale (R == G == B for all pixels, or mode is L)."""
    img = Image.open(img_path)
    if img.mode == "L":
        return True
    if img.mode in ("RGB", "RGBA"):
        arr = np.array(img.convert("RGB"))
        return bool(np.all(arr[:,:,0] == arr[:,:,1]) and np.all(arr[:,:,1] == arr[:,:,2]))
    return False

def verify_inverted(src_path: str, tgt_path: str, threshold: float = 0.95) -> bool:
    """Verify src is the color-inverted version of tgt."""
    src = np.array(Image.open(src_path).convert("RGB"), dtype=np.float32)
    tgt = np.array(Image.open(tgt_path).convert("RGB"), dtype=np.float32)
    if src.shape != tgt.shape:
        return False
    inverted_tgt = 255.0 - tgt
    mse = np.mean((src - inverted_tgt) ** 2)
    return mse < (1.0 - threshold) * 255 * 255
```

---

## 6. Gradual Scoring Pattern (reward-gen)

```python
def compute_reward(src_path: str, golden_path: str, task_type: str = "transform",
                   checks: list = None) -> float:
    """Compute a 0.0-1.0 reward score with multiple verification dimensions.

    task_type: "transform" (modify existing), "create" (new image), "config" (GIMP settings)
    checks: optional list of (check_fn, weight) tuples for custom verification
    """
    score = 0.0
    total_weight = 0.0

    # Dimension 1: File existence (weight: 0.1)
    w = 0.1
    total_weight += w
    if os.path.isfile(src_path):
        score += w
        try:
            img = Image.open(src_path)
            img.verify()
            score += 0  # already counted above
        except Exception:
            score -= w * 0.5  # file exists but corrupted — partial credit

    # Dimension 2: Image dimensions match (weight: 0.15)
    if task_type in ("transform", "create"):
        w = 0.15
        total_weight += w
        try:
            src_img = Image.open(src_path)
            golden_img = Image.open(golden_path)
            if src_img.size == golden_img.size:
                score += w
            elif abs(src_img.size[0] - golden_img.size[0]) < 10 and \
                 abs(src_img.size[1] - golden_img.size[1]) < 10:
                score += w * 0.5  # close but not exact
        except Exception:
            pass

    # Dimension 3: Structural similarity (weight: 0.4)
    if task_type in ("transform", "create"):
        w = 0.4
        total_weight += w
        try:
            ssim_score = _compute_ssim(src_path, golden_path)
            score += w * max(0, ssim_score)
        except Exception:
            pass

    # Dimension 4: Color / histogram similarity (weight: 0.2)
    if task_type in ("transform", "create"):
        w = 0.2
        total_weight += w
        try:
            h1 = get_color_histogram(src_path)
            h2 = get_color_histogram(golden_path)
            correlation = float(np.corrcoef(h1, h2)[0, 1])
            score += w * max(0, correlation)
        except Exception:
            pass

    # Dimension 5: Task-specific checks (weight: 0.15)
    if checks:
        w = 0.15
        total_weight += w
        passed = sum(1 for fn, _ in checks if fn())
        score += w * (passed / len(checks))
    else:
        w = 0.15
        total_weight += w
        # Default: pixel-level closeness
        try:
            src_arr = np.array(Image.open(src_path).convert("RGB"), dtype=np.float32)
            gld_arr = np.array(Image.open(golden_path).convert("RGB"), dtype=np.float32)
            if src_arr.shape == gld_arr.shape:
                mse = np.mean((src_arr - gld_arr) ** 2)
                pixel_score = float(np.exp(-mse / 1000))
                score += w * pixel_score
        except Exception:
            pass

    return score / total_weight if total_weight > 0 else 0.0

def _compute_ssim(src_path: str, tgt_path: str) -> float:
    img1 = np.array(Image.open(src_path).convert("RGB"))
    img2 = np.array(Image.open(tgt_path).convert("RGB"))
    if img1.shape != img2.shape:
        img2 = np.array(Image.open(tgt_path).convert("RGB").resize(
            Image.open(src_path).size, Resampling.LANCZOS))
    min_dim = min(img1.shape[0], img1.shape[1])
    win_size = min(7, min_dim if min_dim % 2 == 1 else min_dim - 1)
    if win_size < 3:
        return 0.0
    try:
        return ssim(img1, img2, win_size=win_size, channel_axis=2)
    except TypeError:
        return ssim(img1, img2, win_size=win_size, multichannel=True)
```

### Vision-Based Scoring (for semantic / non-deterministic tasks)

For tasks where the result cannot be exactly predicted (background removal, artistic effects,
retouching, compositing), use `call_vision_judge` from `reward_judge.py` instead of golden
comparison. The LLM compares the BEFORE and AFTER images visually.

**When to use**: task involves subjective or multi-solution operations (remove background,
enhance photo, apply artistic filter, composite images, retouch blemish, etc.)

**When NOT to use**: task has a deterministic outcome (rotate 90°, crop to 800x600, convert
to grayscale). Use `compute_reward` with golden comparison for those.

**CRITICAL — Initial image preservation**: The agent often overwrites the initial file in-place.
`initial_setup.py` MUST save a reference copy at `{TASK_ID}_initial_reference.<ext>` (see Rule 6
in setup-gen.md). The reward script reads the BEFORE image from this reference, not the canonical
artifact path.

```python
import sys
sys.path.insert(0, "/tmp")
from reward_judge import call_vision_judge

def compute_reward_semantic(
    initial_path: str,
    result_path: str,
    task_instruction: str,
    property_checks: list = None,
) -> float:
    """Compute reward for semantic image tasks using vision LLM + property checks.

    initial_path: the BEFORE image (from {TASK_ID}_initial_reference — guaranteed unmodified)
    result_path: the AFTER image (agent's or golden result at {TASK_ID}.<ext>)
    task_instruction: the original task description
    property_checks: optional list of (check_fn, weight) tuples for measurable properties
    """
    score = 0.0
    total_weight = 0.0

    # Dimension 1: File exists and is valid image (weight: 0.1)
    w = 0.1
    total_weight += w
    if os.path.isfile(result_path):
        try:
            img = Image.open(result_path)
            img.verify()
            score += w
        except Exception:
            pass

    # Dimension 2: Something actually changed (weight: 0.1)
    w = 0.1
    total_weight += w
    try:
        src_arr = np.array(Image.open(initial_path).convert("RGB"))
        res_arr = np.array(Image.open(result_path).convert("RGB"))
        if src_arr.shape == res_arr.shape:
            diff = np.mean(np.abs(src_arr.astype(float) - res_arr.astype(float)))
            if diff > 2.0:  # not identical — agent did something
                score += w
        else:
            score += w  # different size = definitely changed
    except Exception:
        pass

    # Dimension 3: Measurable property checks (weight: 0.3)
    if property_checks:
        w = 0.3
        total_weight += w
        passed = sum(1 for fn, _ in property_checks if fn())
        score += w * (passed / len(property_checks))

    # Dimension 4: LLM Vision Judge — compare BEFORE vs AFTER (weight: 0.5)
    w = 0.5
    total_weight += w
    try:
        vision_score = call_vision_judge(
            task_instruction=task_instruction,
            initial_image=initial_path,
            result_image=result_path,
        )
        score += w * vision_score
    except Exception as e:
        print(f"Vision judge failed: {e}")

    return score / total_weight if total_weight > 0 else 0.0

# --- Example: "Remove the background from the image" ---
# reward.py reads _initial_reference (untouched) as BEFORE, canonical artifact as AFTER
#
# def compute_reward():
#     initial = f"/home/user/{TASK_ID}_initial_reference.png"  # BEFORE — saved by initial_setup.py
#     result  = f"/home/user/{TASK_ID}.png"                     # AFTER — overwritten by agent or golden_patch
#
#     property_checks = [
#         (lambda: Image.open(result).mode == "RGBA", 1.0),
#         (lambda: np.mean(np.array(Image.open(result).split()[-1]) < 10) > 0.1, 1.0),
#     ]
#
#     return compute_reward_semantic(
#         initial_path=initial,
#         result_path=result,
#         task_instruction="Remove the background from the image",
#         property_checks=property_checks,
#     )
```

---

## 7. Bitter Lessons

1. **SSIM requires same-size images.** `structure_check_by_ssim` returns `False` if sizes differ. Always resize before comparing. Use `Resampling.LANCZOS` for quality downsampling.

2. **SSIM window size must be odd and <= image dimension.** Default `win_size=7` fails for images smaller than 7px on any side. Adapt: `win_size = min(7, min_dim if min_dim % 2 == 1 else min_dim - 1)`.

3. **`channel_axis` vs `multichannel` in scikit-image.** Newer versions use `channel_axis=2`, older use `multichannel=True`. Always try/except both to support all environments.

4. **Image mode must match for comparison.** Comparing RGB to RGBA fails silently or gives wrong results. Always `.convert("RGB")` both images before SSIM or pixel comparison.

5. **Transparency crops use `alpha.getbbox()`.** To measure content size ignoring transparent pixels, get the alpha channel bounding box. `getbbox()` returns `None` for fully transparent images — handle this case.

6. **`img.convert("P")` creates palette mode, but SSIM needs RGB.** After verifying `mode == "P"`, convert back to RGB for structure comparison. The palette conversion is lossy.

7. **Brightness normalization before structure check.** When comparing brightness-adjusted images, normalize both to the same target brightness (128) before MSE comparison. Otherwise the brightness difference dominates the structural metric.

8. **Saturation comparison inverts direction.** The evaluator checks `tgt_saturation < src_saturation` because `src` is the enhanced image. In GIMP tasks, the "source" result has *higher* saturation than the "target" reference.

9. **Contrast SSIM threshold is lenient (0.65).** Contrast adjustments change many pixels significantly. The evaluator uses 0.65 instead of the default 0.9 to account for this.

10. **`ImageChops.difference().getbbox()` is `None` for identical images.** The bounding box of the difference is `None` when no pixels differ. This is your "exact match" check.

11. **Truncated/corrupted images need retry logic.** GIMP export can produce truncated files if the export dialog times out. Use a retry mechanism: try opening 3 times with 0.5s delay.

12. **Shape detection uses color frequency, not edge detection.** The evaluator finds shapes by sorting pixel colors by frequency. The second-most-common color is the shape (background is most common). This fails if shape color equals background color.

13. **Mirror check uses 0.99 SSIM, not exact match.** GIMP's export introduces minor compression artifacts. Pixel-perfect comparison fails; use SSIM >= 0.99 for mirror verification.

14. **GIMP config (gimprc) uses S-expression format.** Lines are `(key value)` with parentheses, not `key=value`. Parse by stripping parens and splitting on whitespace.

15. **XCF files cannot be read by Pillow.** Use `xcftools` (`xcfinfo`, `xcf2png`) or GIMP batch mode. Install with `sudo apt install xcftools`. Always flatten XCF to PNG before SSIM comparison.

16. **GIMP batch mode hangs without `(gimp-quit 0)`.** Always pass two `-b` flags: one for your command, one for `(gimp-quit 0)`. Set a subprocess timeout (30s) as safety net.

17. **Script-Fu `car` is needed to unwrap return values.** Most GIMP Script-Fu procedures return lists. `(gimp-image-width image)` returns `(1920)`, not `1920`. Use `(car ...)` to get the scalar.

18. **Color temperature shifts need float arithmetic.** When comparing warm/cool tone shifts, use `dtype=np.float32` to avoid uint8 underflow in subtraction (`200 - 210` wraps to `246` in uint8).
