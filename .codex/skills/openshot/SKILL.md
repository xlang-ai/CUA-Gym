---
name: openshot
description: "How to programmatically set up, manipulate, and verify OpenShot Video Editor project state using Python (JSON .osp files, libopenshot API, FFmpeg/FFprobe, OpenCV). For setup-gen and reward-gen agents."
user-invocable: false
---

# OpenShot Video Editor — Python Manipulation Guide

This skill teaches **setup-gen** (create project files, prepare media, launch GUI) and **reward-gen** (verify project structure, exported video/audio) how to work with OpenShot using Python.

- Libraries: `json`, `subprocess`, `cv2`, `numpy`, `Pillow`, `imagehash`, `librosa`
- Install: `pip3 install opencv-python numpy Pillow imagehash librosa fastdtw scipy scikit-image`
- System: `sudo apt install openshot-qt python3-openshot ffmpeg` (VM)
- Project format: `.osp` (plain JSON)
- Config path (Linux): `~/.openshot_qt/`

---

## 0. GUI Startup on VM (for setup-gen)

After preparing the `.osp` project file and media assets, setup-gen should launch OpenShot with the project loaded for the GUI agent.

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

# Launch OpenShot with a pre-built project
launch_gui('openshot-qt "/home/user/Desktop/project.osp"', delay_sec=3.0)

# Or launch OpenShot and auto-import media files (no project)
launch_gui('openshot-qt "/home/user/Desktop/video1.mp4" "/home/user/Desktop/image.png"', delay_sec=3.0)
```

Guidelines:
- OpenShot auto-loads `.osp` files passed as arguments, or imports non-.osp files as media.
- Use non-blocking launch (`Popen`) so script exits cleanly.
- OpenShot is heavier than VLC/GIMP — use `delay_sec=3.0` or higher.
- Open initial project, never golden project.

---

---

## 0.5. Media Asset Library (setup-gen)

Use the **real video/image library** at `assets/media/openshot/` instead of generating synthetic media.

### Available Categories

| Category | Count | Description | Good for |
|----------|-------|-------------|----------|
| `clips` | ~30 | Real video clips: interview, sports, craft, abstract, aerial, dance | Timeline editing, trimming, effects, transitions |
| `overlays` | ~10 | Photos for overlays: transparent backgrounds, light effects | Logo overlays, title cards, compositing |

Audio can be extracted from clips on the VM via FFmpeg. Also share assets from `assets/media/vlc/` for additional variety.

### Upload Pattern

```bash
# Upload multiple clips for a multi-track editing task
python3 scripts/env_cli.py -c "<workdir>/env_config_initial.json" upload \
    "assets/media/openshot/clips/interview_talking_person_001.mp4" "/home/user/Desktop/clip_a.mp4"
python3 scripts/env_cli.py -c "<workdir>/env_config_initial.json" upload \
    "assets/media/openshot/clips/drone_aerial_landscape_016.mp4" "/home/user/Desktop/clip_b.mp4"
python3 scripts/env_cli.py -c "<workdir>/env_config_initial.json" upload \
    "assets/media/openshot/overlays/particle_light_effect_006.jpg" "/home/user/Desktop/overlay.jpg"
# Repeat for golden_env
```

Then `initial_setup.py` creates the .osp project referencing these uploaded media files.

### Picking Assets from Manifest

```python
import json, random
manifest = json.load(open("assets/media/manifest.json"))
openshot_clips = [a for a in manifest["assets"] if a["domain"] == "openshot" and a["category"] == "clips"]
# Pick clips with different themes for a multi-clip project
interview = random.choice([c for c in openshot_clips if "interview" in c.get("tags", [])])
broll = random.choice([c for c in openshot_clips if "aerial" in c.get("tags", []) or "nature" in c.get("tags", [])])
```

---

## 1. Project File (.osp) — JSON Structure (setup-gen & reward-gen)

OpenShot project files are **plain JSON** with `.osp` extension. This is the primary mechanism for both setup and verification.

### Complete .osp Schema

```python
import json
import uuid
import os

def new_id():
    return str(uuid.uuid4().hex[:10])

def create_empty_project(
    width=1920, height=1080,
    fps_num=30, fps_den=1,
    sample_rate=44100, channels=2,
    channel_layout=3,  # LAYOUT_STEREO
    profile="HD 1080p 30 fps"
):
    """Create a minimal valid .osp project."""
    return {
        "id": new_id(),
        "version": {
            "openshot-qt": "3.4.0",
            "libopenshot": "0.4.0"
        },
        "profile": profile,
        "width": width,
        "height": height,
        "fps": {"num": fps_num, "den": fps_den},
        "display_ratio": {"num": 16, "den": 9},
        "pixel_ratio": {"num": 1, "den": 1},
        "sample_rate": sample_rate,
        "channels": channels,
        "channel_layout": channel_layout,
        "files": [],
        "clips": [],
        "effects": [],
        "transitions": [],
        "markers": [],
        "history": {"undo": [], "redo": []}
    }

def save_project(project: dict, path: str):
    with open(path, "w") as f:
        json.dump(project, f, indent=2)

def load_project(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)
```

### Adding Files (Media References)

```python
def add_file(project: dict, file_path: str, media_type: str = "video",
             width: int = 1920, height: int = 1080,
             has_audio: bool = True, has_video: bool = True,
             duration: float = None) -> str:
    """Register a media file in the project. Returns file ID.
    duration: media duration in seconds. If None, must be set manually or OpenShot infers it.
    """
    file_id = new_id()
    file_entry = {
        "id": file_id,
        "path": os.path.abspath(file_path),
        "media_type": media_type,  # "video", "audio", "image"
        "has_audio": has_audio,
        "has_video": has_video,
        "width": width,
        "height": height,
        "display_ratio": {"num": 16, "den": 9},
    }
    if duration is not None:
        file_entry["duration"] = duration
    project["files"].append(file_entry)
    return file_id

# Examples
file_id = add_file(project, "/home/user/Desktop/interview.mp4")
img_id = add_file(project, "/home/user/Desktop/logo.png",
                  media_type="image", width=800, height=600,
                  has_audio=False, has_video=True)
audio_id = add_file(project, "/home/user/Desktop/bgm.mp3",
                    media_type="audio", has_audio=True, has_video=False)
```

### Keyframe System

All animatable properties use this structure:

```python
def make_keyframe(value, frame=1, interpolation=2):
    """Create a single-point keyframe.
    interpolation: 0=Bezier, 1=Linear, 2=Constant
    """
    return {
        "Points": [{
            "co": {"X": float(frame), "Y": float(value)},
            "handle_left": {"X": float(frame) - 0.5, "Y": float(value)},
            "handle_right": {"X": float(frame) + 0.5, "Y": float(value)},
            "interpolation": interpolation
        }]
    }

def make_keyframe_animated(points):
    """Create a multi-point animated keyframe.
    points: list of (frame, value, interpolation) tuples
    """
    return {
        "Points": [{
            "co": {"X": float(f), "Y": float(v)},
            "handle_left": {"X": float(f) - 0.5, "Y": float(v)},
            "handle_right": {"X": float(f) + 0.5, "Y": float(v)},
            "interpolation": interp
        } for f, v, interp in points]
    }

# Constant value (opacity = 1.0 always)
kf_full_alpha = make_keyframe(1.0)

# Fade in: 0.0 at frame 1 → 1.0 at frame 30 (linear)
kf_fade_in = make_keyframe_animated([(1, 0.0, 1), (30, 1.0, 1)])

# Fade out: 1.0 at frame 1 → 0.0 at frame 30 (linear)
kf_fade_out = make_keyframe_animated([(1, 1.0, 1), (30, 0.0, 1)])

# Smooth zoom using Bezier interpolation
kf_zoom = make_keyframe_animated([(1, 0.5, 0), (60, 1.0, 0)])
```

### Adding Clips to Timeline

```python
def add_clip(project: dict, file_id: str, file_path: str,
             position: float = 0.0, start: float = 0.0, end: float = 10.0,
             layer: int = 0, volume: float = 1.0, alpha: float = 1.0,
             scale_x: float = 1.0, scale_y: float = 1.0,
             location_x: float = 0.0, location_y: float = 0.0,
             rotation: float = 0.0) -> str:
    """Add a clip to the timeline. Returns clip ID.

    position: where clip starts on timeline (seconds)
    start/end: trim points within source media (seconds)
    layer: track number (0 = bottom, higher = on top)
    """
    clip_id = new_id()
    project["clips"].append({
        "id": clip_id,
        "file_id": file_id,
        "title": os.path.basename(file_path),
        "position": position,
        "start": start,
        "end": end,
        "layer": layer,
        "reader": {"path": os.path.abspath(file_path)},
        # Keyframe properties
        "alpha": make_keyframe(alpha),
        "volume": make_keyframe(volume),
        "scale_x": make_keyframe(scale_x),
        "scale_y": make_keyframe(scale_y),
        "location_x": make_keyframe(location_x),
        "location_y": make_keyframe(location_y),
        "rotation": make_keyframe(rotation),
        "origin_x": make_keyframe(0.5),
        "origin_y": make_keyframe(0.5),
        "shear_x": make_keyframe(0.0),
        "shear_y": make_keyframe(0.0),
        "time": make_keyframe(1.0),
        "channel_filter": make_keyframe(-1),
        "channel_mapping": make_keyframe(-1),
        "has_audio": make_keyframe(-1),
        "has_video": make_keyframe(-1),
        "effects": [],
        # Scale/gravity/anchor enums
        "scale": 0,       # CROP (0=Crop, 1=BestFit, 2=Stretch, 3=None)
        "gravity": 4,     # CENTER (0-8 = TL,T,TR,L,C,R,BL,B,BR)
        "anchor": 0,
        "display": 0,
        "mixing": 0,
        "wave_color": {"red": make_keyframe(0), "green": make_keyframe(123), "blue": make_keyframe(255), "alpha": make_keyframe(255)},
    })
    return clip_id

# Example: place a 10-second clip at the start of track 0
clip1_id = add_clip(project, file_id, "/home/user/Desktop/interview.mp4",
                    position=0.0, start=0.0, end=10.0, layer=0)

# Example: overlay a logo on track 1 with 70% opacity, scaled down
logo_id = add_clip(project, img_id, "/home/user/Desktop/logo.png",
                   position=0.0, start=0.0, end=10.0, layer=1,
                   alpha=0.7, scale_x=0.2, scale_y=0.2,
                   location_x=0.35, location_y=0.35)
```

### Adding Effects to Clips

```python
# Available effects (name → class):
# Bars, Blur, Brightness, Caption, ChromaKey, ColorMap, ColorShift, Crop,
# Deinterlace, Hue, LensFlare, Mask, Negate, Noise, Pixelate, Saturation,
# Sharpen, Shift, SphericalProjection, Wave
# OpenCV-dependent: ObjectDetection, Outline, Stabilizer, Tracker

def add_effect_to_clip(project: dict, clip_id: str,
                       effect_name: str, effect_params: dict) -> str:
    """Add an effect to a specific clip. Returns effect ID."""
    effect_id = new_id()
    effect = {
        "id": effect_id,
        "name": effect_name,
        **effect_params
    }
    for clip in project["clips"]:
        if clip["id"] == clip_id:
            clip["effects"].append(effect)
            break
    return effect_id

# --- Effect parameter examples ---

# Blur effect
blur_params = {
    "horizontal_radius": make_keyframe(10),    # 0-100
    "vertical_radius": make_keyframe(10),      # 0-100
    "sigma": make_keyframe(3),                 # 0-100
    "iterations": make_keyframe(3),            # 1-100
}

# Brightness effect
brightness_params = {
    "brightness": make_keyframe(1.2),          # 0.0-4.0 (1.0 = no change)
}

# ChromaKey (green screen removal)
chromakey_params = {
    "color": {"red": make_keyframe(0), "green": make_keyframe(255),
              "blue": make_keyframe(0), "alpha": make_keyframe(255)},
    "fuzz": make_keyframe(25),                 # 0-100 tolerance
}

# Saturation effect
saturation_params = {
    "saturation": make_keyframe(1.5),          # 0.0-4.0 (1.0 = no change)
    "saturation_R": make_keyframe(1.0),
    "saturation_G": make_keyframe(1.0),
    "saturation_B": make_keyframe(1.0),
}

# Hue effect
hue_params = {
    "hue": make_keyframe(0.0),                 # 0-360 degrees of hue shift
}

# Crop effect
crop_params = {
    "left": make_keyframe(0.1),                # 0.0-1.0 (fraction of width)
    "right": make_keyframe(0.1),
    "top": make_keyframe(0.1),
    "bottom": make_keyframe(0.1),
}

# Negate (invert colors)
negate_params = {}  # no parameters needed

# Pixelate
pixelate_params = {
    "pixelization": make_keyframe(20),         # 0-100
    "left": make_keyframe(0.0),
    "right": make_keyframe(0.0),
    "top": make_keyframe(0.0),
    "bottom": make_keyframe(0.0),
}

# Wave
wave_params = {
    "wavelength": make_keyframe(30),           # 0-200
    "amplitude": make_keyframe(10),            # 0-100
    "multiplier": make_keyframe(0.02),
    "shift_x": make_keyframe(0),
    "speed_y": make_keyframe(0.2),
}

# ColorShift
colorshift_params = {
    "red_x": make_keyframe(5),                 # pixel shift per channel
    "red_y": make_keyframe(0),
    "green_x": make_keyframe(-5),
    "green_y": make_keyframe(0),
    "blue_x": make_keyframe(0),
    "blue_y": make_keyframe(5),
}

# Apply blur to clip1
add_effect_to_clip(project, clip1_id, "Blur", blur_params)
```

### Adding Transitions

```python
def add_transition(project: dict,
                   position: float, start: float = 0.0, end: float = 2.0,
                   layer: int = 0,
                   brightness_start: float = -1.0, brightness_end: float = 1.0,
                   transition_type: str = "Mask",
                   resource: str = "") -> str:
    """Add a transition between clips.

    position: where the transition starts on the timeline (seconds)
    start/end: trim points within the transition resource (seconds).
        NOTE: end is NOT the timeline end position — it is the duration of the transition
        effect relative to its own start. For a 2-second cross-dissolve, use end=2.0.
    brightness_start/end: -1.0 (fully visible) to 1.0 (fully transparent)
    resource: path to wipe/mask image (common transitions use gradients)
    """
    trans_id = new_id()
    project["transitions"].append({
        "id": trans_id,
        "title": "Transition",
        "type": transition_type,
        "position": position,
        "start": start,
        "end": end,
        "layer": layer,
        "brightness": make_keyframe_animated([
            (1, brightness_start, 1),
            (int(end * 30), brightness_end, 1)  # end frame = end * fps
        ]),
        "contrast": make_keyframe(3.0),
        "reader": {"path": resource} if resource else {},
        "replace_image": False,
    })
    return trans_id

# Common OpenShot transition wipe images are in:
# /usr/share/openshot-qt/transitions/ (or /usr/lib/python3/dist-packages/openshot_qt/transitions/)
# Examples: common/fade.svg, extra/wipe_down.svg, extra/wipe_right.svg

# Fade transition at 5 seconds (2 second duration)
add_transition(project, position=5.0, end=2.0, layer=0)
```

### Adding Markers

```python
def add_marker(project: dict, position: float, title: str = "Marker") -> str:
    """Add a timeline marker."""
    marker_id = new_id()
    project["markers"].append({
        "id": marker_id,
        "position": position,
        "title": title,
    })
    return marker_id

add_marker(project, 0.0, "Intro Start")
add_marker(project, 15.0, "Chapter 2")
```

### Complete Setup Example

```python
# Full example: create a project with 2 clips and a transition
project = create_empty_project(width=1920, height=1080, fps_num=30, fps_den=1)

# Register media
vid_id = add_file(project, "/home/user/Desktop/clip_a.mp4")
vid2_id = add_file(project, "/home/user/Desktop/clip_b.mp4")
music_id = add_file(project, "/home/user/Desktop/bgm.mp3",
                    media_type="audio", has_video=False)

# Place clips on timeline
add_clip(project, vid_id, "/home/user/Desktop/clip_a.mp4",
         position=0.0, start=0.0, end=8.0, layer=0)
add_clip(project, vid2_id, "/home/user/Desktop/clip_b.mp4",
         position=6.0, start=0.0, end=8.0, layer=0)  # 2-second overlap
add_clip(project, music_id, "/home/user/Desktop/bgm.mp3",
         position=0.0, start=0.0, end=14.0, layer=1, volume=0.3)

# Cross-dissolve transition in the overlap region
add_transition(project, position=6.0, end=2.0, layer=0)

# Add marker
add_marker(project, 6.0, "Transition Point")

# Save
save_project(project, "/home/user/Desktop/project.osp")
```

---

## 2. Creating Media Assets (setup-gen)

### Generating Test Videos with FFmpeg

```python
import subprocess

def create_test_video(output_path: str, duration: int = 10,
                      width: int = 1920, height: int = 1080,
                      fps: int = 30, pattern: str = "testsrc"):
    """Generate a test video. pattern: testsrc, testsrc2, smptebars, color=c=blue"""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"{pattern}=duration={duration}:size={width}x{height}:rate={fps}",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "fast",
        output_path
    ], check=True, capture_output=True)

def create_video_with_audio(output_path: str, duration: int = 10,
                            width: int = 1920, height: int = 1080, fps: int = 30):
    """Generate test video with sine wave audio."""
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"testsrc2=duration={duration}:size={width}x{height}:rate={fps}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", output_path
    ], check=True, capture_output=True)

def create_color_video(output_path: str, color: str = "blue",
                       duration: int = 5, width: int = 1920, height: int = 1080):
    """Generate a solid color video."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={color}:duration={duration}:size={width}x{height}:rate=30",
        "-pix_fmt", "yuv420p", "-c:v", "libx264", output_path
    ], check=True, capture_output=True)

def create_text_video(output_path: str, text: str = "Hello World",
                      duration: int = 5, fontsize: int = 72):
    """Generate a video with text overlay on black background."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=black:duration={duration}:size=1920x1080:rate=30",
        "-vf", f"drawtext=text='{text}':fontsize={fontsize}:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        "-pix_fmt", "yuv420p", "-c:v", "libx264", output_path
    ], check=True, capture_output=True)

# Create test media files
create_test_video("/home/user/Desktop/clip_a.mp4", duration=10)
create_video_with_audio("/home/user/Desktop/clip_b.mp4", duration=8)
create_color_video("/home/user/Desktop/title_bg.mp4", color="darkblue", duration=3)
```

### Generating Test Audio

```python
def create_test_audio(output_path: str, duration: int = 10,
                      frequency: int = 440, format: str = "mp3"):
    """Generate a sine wave audio file."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"sine=frequency={frequency}:duration={duration}",
        "-c:a", "libmp3lame" if format == "mp3" else "aac",
        output_path
    ], check=True, capture_output=True)

def create_silence(output_path: str, duration: int = 10):
    """Generate a silent audio file."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=stereo",
        "-t", str(duration), "-c:a", "libmp3lame",
        output_path
    ], check=True, capture_output=True)

create_test_audio("/home/user/Desktop/bgm.mp3", duration=30)
```

### Generating Test Images

```python
from PIL import Image, ImageDraw, ImageFont

def create_test_image(output_path: str, width: int = 1920, height: int = 1080,
                      color: str = "white", text: str = None):
    img = Image.new("RGB", (width, height), color=color)
    if text:
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 72)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((width - tw) / 2, (height - th) / 2), text,
                  fill="black" if color == "white" else "white", font=font)
    img.save(output_path)

create_test_image("/home/user/Desktop/logo.png", 400, 300, "yellow", "LOGO")
create_test_image("/home/user/Desktop/title_card.png", 1920, 1080, "black", "My Video")
```

### Video Manipulation with FFmpeg

```python
def trim_video(input_path: str, output_path: str,
               start_time: str = "00:00:00", duration: str = "00:00:10"):
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-ss", start_time, "-t", duration,
        "-c", "copy", output_path
    ], check=True, capture_output=True)

def concat_videos(input_paths: list, output_path: str):
    """Concatenate videos using FFmpeg concat demuxer."""
    list_file = "/tmp/concat_list.txt"
    with open(list_file, "w") as f:
        for p in input_paths:
            f.write(f"file '{p}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output_path
    ], check=True, capture_output=True)

def extract_frame(input_path: str, output_path: str, timestamp: str = "00:00:01"):
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-ss", timestamp, "-frames:v", "1", output_path
    ], check=True, capture_output=True)

def extract_audio(input_path: str, output_path: str):
    subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-vn", "-c:a", "libmp3lame", "-q:a", "2", output_path
    ], check=True, capture_output=True)

def add_audio_to_video(video_path: str, audio_path: str, output_path: str):
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-shortest", output_path
    ], check=True, capture_output=True)
```

### Golden File Pattern

```python
import shutil

# For project-level golden files: save the expected .osp state
save_project(golden_project, "/home/user/Desktop/golden_project.osp")

# For export-level golden files: render expected output
# (use libopenshot or FFmpeg to produce the expected video)
shutil.copy("/home/user/Desktop/expected_output.mp4",
            "/home/user/Desktop/golden_output.mp4")
```

---

## 3. libopenshot Python API (setup-gen & reward-gen) — Quick Reference

The `python3-openshot` package provides SWIG bindings for headless rendering and verification. Install: `sudo apt install python3-openshot` (not on PyPI).

### Timeline Export (Headless Render)

```python
import openshot, json

# From scratch
t = openshot.Timeline(1920, 1080, openshot.Fraction(30, 1), 44100, 2, openshot.LAYOUT_STEREO)
clip = openshot.Clip("/home/user/Desktop/video.mp4")
clip.Position(0.0); clip.Start(0.0); clip.End(10.0); clip.Layer(0)
t.AddClip(clip)
t.Open()

w = openshot.FFmpegWriter("/home/user/Desktop/output.mp4")
w.SetVideoOptions(True, "libx264", openshot.Fraction(30, 1), 1920, 1080,
                  openshot.Fraction(1, 1), False, False, 5000000)
w.SetAudioOptions(True, "aac", 44100, 2, openshot.LAYOUT_STEREO, 192000)
w.Open()
for frame_num in range(1, t.GetMaxFrame() + 1):
    w.WriteFrame(t.GetFrame(frame_num))
w.Close(); t.Close()

# From .osp file — all media paths must be absolute and exist on disk
with open("/home/user/Desktop/project.osp") as f:
    project_json = f.read()
project = json.loads(project_json)
fps = openshot.Fraction(project["fps"]["num"], project["fps"]["den"])
t = openshot.Timeline(project["width"], project["height"], fps,
                      project["sample_rate"], project["channels"], project["channel_layout"])
t.SetJson(project_json); t.Open()
# ... export same as above
```

### Effects & Keyframe Animations

```python
# Effects: Blur, Brightness, ChromaKey, Saturation, Hue, Negate, etc.
blur = openshot.Blur()
blur.horizontal_radius = openshot.Keyframe(10.0)
blur.vertical_radius = openshot.Keyframe(10.0)
clip.AddEffect(blur)

sat = openshot.Saturation()
sat.saturation = openshot.Keyframe(0.0)  # 0 = grayscale
clip.AddEffect(sat)

# Animated keyframes
kf = openshot.Keyframe()
kf.AddPoint(1, 0.0, openshot.LINEAR)    # frame 1: value 0.0
kf.AddPoint(30, 1.0, openshot.LINEAR)   # frame 30: value 1.0
clip.alpha = kf  # fade in over 1 second at 30fps
# Interpolation: openshot.LINEAR, openshot.BEZIER, openshot.CONSTANT
```

### Read Media Information

```python
r = openshot.FFmpegReader("/home/user/Desktop/video.mp4")
r.Open()
# r.info.duration, r.info.width, r.info.height, r.info.fps.num/den
# r.info.vcodec, r.info.acodec, r.info.sample_rate, r.info.channels, r.info.video_length
r.Close()
```

---

## 4. Reading & Verifying (reward-gen)

### Verifying .osp Project Structure

```python
def verify_project_has_clips(osp_path: str, min_clips: int = 1) -> bool:
    """Check that project has at least min_clips clips."""
    project = load_project(osp_path)
    return len(project.get("clips", [])) >= min_clips

def verify_clip_count(osp_path: str, expected: int) -> bool:
    project = load_project(osp_path)
    return len(project.get("clips", [])) == expected

def verify_project_has_transitions(osp_path: str, min_transitions: int = 1) -> bool:
    project = load_project(osp_path)
    return len(project.get("transitions", [])) >= min_transitions

def verify_project_has_effects(osp_path: str) -> bool:
    """Check that at least one clip has at least one effect."""
    project = load_project(osp_path)
    for clip in project.get("clips", []):
        if clip.get("effects", []):
            return True
    return False

def verify_project_resolution(osp_path: str, width: int, height: int) -> bool:
    project = load_project(osp_path)
    return project.get("width") == width and project.get("height") == height

def verify_project_fps(osp_path: str, fps_num: int, fps_den: int = 1) -> bool:
    project = load_project(osp_path)
    fps = project.get("fps", {})
    return fps.get("num") == fps_num and fps.get("den") == fps_den
```

### Verifying Clip Properties

```python
def get_clip_by_index(osp_path: str, index: int) -> dict:
    project = load_project(osp_path)
    clips = project.get("clips", [])
    if index < len(clips):
        return clips[index]
    return None

def get_clip_by_title(osp_path: str, title_substring: str) -> dict:
    """Find clip by filename/title substring."""
    project = load_project(osp_path)
    for clip in project.get("clips", []):
        if title_substring.lower() in clip.get("title", "").lower():
            return clip
    return None

def get_keyframe_value(keyframe_data: dict) -> float:
    """Extract the first keyframe Y value from a keyframe property."""
    points = keyframe_data.get("Points", [])
    if points:
        return points[0].get("co", {}).get("Y", 0.0)
    return 0.0

def verify_clip_position(osp_path: str, clip_index: int,
                         expected_position: float, tolerance: float = 0.1) -> bool:
    clip = get_clip_by_index(osp_path, clip_index)
    if not clip:
        return False
    return abs(clip.get("position", -1) - expected_position) <= tolerance

def verify_clip_layer(osp_path: str, clip_index: int, expected_layer: int) -> bool:
    clip = get_clip_by_index(osp_path, clip_index)
    if not clip:
        return False
    return clip.get("layer") == expected_layer

def verify_clip_trimmed(osp_path: str, clip_index: int,
                        expected_start: float, expected_end: float,
                        tolerance: float = 0.1) -> bool:
    clip = get_clip_by_index(osp_path, clip_index)
    if not clip:
        return False
    return (abs(clip.get("start", -1) - expected_start) <= tolerance and
            abs(clip.get("end", -1) - expected_end) <= tolerance)

def verify_clip_volume(osp_path: str, clip_index: int,
                       expected_volume: float, tolerance: float = 0.05) -> bool:
    clip = get_clip_by_index(osp_path, clip_index)
    if not clip:
        return False
    actual = get_keyframe_value(clip.get("volume", {}))
    return abs(actual - expected_volume) <= tolerance

def verify_clip_alpha(osp_path: str, clip_index: int,
                      expected_alpha: float, tolerance: float = 0.05) -> bool:
    clip = get_clip_by_index(osp_path, clip_index)
    if not clip:
        return False
    actual = get_keyframe_value(clip.get("alpha", {}))
    return abs(actual - expected_alpha) <= tolerance

def verify_clip_has_effect(osp_path: str, clip_index: int,
                           effect_name: str) -> bool:
    """Check if a clip has a specific effect applied."""
    clip = get_clip_by_index(osp_path, clip_index)
    if not clip:
        return False
    for effect in clip.get("effects", []):
        if effect.get("name", "").lower() == effect_name.lower():
            return True
    return False

def verify_clip_effect_param(osp_path: str, clip_index: int,
                             effect_name: str, param_name: str,
                             expected_value: float, tolerance: float = 0.1) -> bool:
    """Check a specific effect parameter value on a clip."""
    clip = get_clip_by_index(osp_path, clip_index)
    if not clip:
        return False
    for effect in clip.get("effects", []):
        if effect.get("name", "").lower() == effect_name.lower():
            param = effect.get(param_name, {})
            if isinstance(param, dict) and "Points" in param:
                actual = get_keyframe_value(param)
                return abs(actual - expected_value) <= tolerance
    return False

def verify_clip_has_keyframe_animation(osp_path: str, clip_index: int,
                                       property_name: str) -> bool:
    """Check if a clip property has multiple keyframe points (is animated)."""
    clip = get_clip_by_index(osp_path, clip_index)
    if not clip:
        return False
    prop = clip.get(property_name, {})
    points = prop.get("Points", [])
    return len(points) > 1
```

### Verifying Transition Properties

```python
def verify_transition_at_position(osp_path: str, expected_position: float,
                                  tolerance: float = 0.5) -> bool:
    project = load_project(osp_path)
    for trans in project.get("transitions", []):
        if abs(trans.get("position", -1) - expected_position) <= tolerance:
            return True
    return False

def verify_transition_duration(osp_path: str, trans_index: int,
                               expected_duration: float, tolerance: float = 0.5) -> bool:
    project = load_project(osp_path)
    transitions = project.get("transitions", [])
    if trans_index >= len(transitions):
        return False
    trans = transitions[trans_index]
    duration = trans.get("end", 0) - trans.get("start", 0)
    return abs(duration - expected_duration) <= tolerance
```

### Verifying Markers

```python
def verify_marker_exists(osp_path: str, title: str = None,
                         position: float = None, tolerance: float = 0.5) -> bool:
    project = load_project(osp_path)
    for marker in project.get("markers", []):
        if title and title.lower() not in marker.get("title", "").lower():
            continue
        if position is not None and abs(marker.get("position", -1) - position) > tolerance:
            continue
        return True
    return False
```

### Verifying Exported Video with FFprobe

```python
def get_video_info(video_path: str) -> dict:
    """Extract video metadata using FFprobe."""
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", video_path
    ], capture_output=True, text=True)
    return json.loads(result.stdout)

def verify_video_duration(video_path: str, expected_duration: float,
                          tolerance: float = 1.0) -> bool:
    info = get_video_info(video_path)
    duration = float(info.get("format", {}).get("duration", 0))
    return abs(duration - expected_duration) <= tolerance

def verify_video_resolution(video_path: str, expected_width: int,
                            expected_height: int) -> bool:
    info = get_video_info(video_path)
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            return (stream.get("width") == expected_width and
                    stream.get("height") == expected_height)
    return False

def verify_video_fps(video_path: str, expected_fps: float,
                     tolerance: float = 1.0) -> bool:
    info = get_video_info(video_path)
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            # r_frame_rate is "30/1" format
            r = stream.get("r_frame_rate", "0/1")
            num, den = map(int, r.split("/"))
            actual_fps = num / den if den else 0
            return abs(actual_fps - expected_fps) <= tolerance
    return False

def verify_video_has_audio(video_path: str) -> bool:
    info = get_video_info(video_path)
    return any(s.get("codec_type") == "audio" for s in info.get("streams", []))

def verify_video_codec(video_path: str, expected_vcodec: str = None,
                       expected_acodec: str = None) -> bool:
    info = get_video_info(video_path)
    for stream in info.get("streams", []):
        if expected_vcodec and stream.get("codec_type") == "video":
            if expected_vcodec.lower() not in stream.get("codec_name", "").lower():
                return False
        if expected_acodec and stream.get("codec_type") == "audio":
            if expected_acodec.lower() not in stream.get("codec_name", "").lower():
                return False
    return True
```

### Verifying Video Content with OpenCV

```python
import cv2
import numpy as np

def get_frame_at_time(video_path: str, time_sec: float) -> np.ndarray:
    """Extract a single frame at a given timestamp."""
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None

def verify_frame_brightness(video_path: str, time_sec: float,
                            min_brightness: float = None,
                            max_brightness: float = None) -> bool:
    """Check average brightness of a frame at given time."""
    frame = get_frame_at_time(video_path, time_sec)
    if frame is None:
        return False
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray)
    if min_brightness is not None and avg_brightness < min_brightness:
        return False
    if max_brightness is not None and avg_brightness > max_brightness:
        return False
    return True

def verify_frame_color_dominant(video_path: str, time_sec: float,
                                expected_color_bgr: tuple,
                                tolerance: int = 60) -> bool:
    """Check if a frame is predominantly a certain color."""
    frame = get_frame_at_time(video_path, time_sec)
    if frame is None:
        return False
    avg_color = np.mean(frame, axis=(0, 1))
    return all(abs(avg_color[i] - expected_color_bgr[i]) < tolerance for i in range(3))

def verify_fade_in(video_path: str, start_sec: float = 0.0,
                   end_sec: float = 1.0, num_samples: int = 5) -> bool:
    """Verify brightness increases monotonically (fade in effect)."""
    times = np.linspace(start_sec, end_sec, num_samples)
    brightnesses = []
    for t in times:
        frame = get_frame_at_time(video_path, t)
        if frame is None:
            return False
        brightnesses.append(np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)))
    # Check monotonically increasing with some tolerance
    for i in range(1, len(brightnesses)):
        if brightnesses[i] < brightnesses[i - 1] - 5:
            return False
    return brightnesses[-1] - brightnesses[0] > 20  # significant increase

def verify_fade_out(video_path: str, start_sec: float, end_sec: float,
                    num_samples: int = 5) -> bool:
    """Verify brightness decreases monotonically (fade out effect)."""
    times = np.linspace(start_sec, end_sec, num_samples)
    brightnesses = []
    for t in times:
        frame = get_frame_at_time(video_path, t)
        if frame is None:
            return False
        brightnesses.append(np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)))
    for i in range(1, len(brightnesses)):
        if brightnesses[i] > brightnesses[i - 1] + 5:
            return False
    return brightnesses[0] - brightnesses[-1] > 20
```

### Comparing Videos (Perceptual Hashing)

```python
import imagehash
from PIL import Image

def compare_videos(video1: str, video2: str,
                   max_frames: int = 100, threshold: int = 5) -> float:
    """Compare two videos frame-by-frame using perceptual hashing. Returns 0.0-1.0."""
    cap1, cap2 = cv2.VideoCapture(video1), cv2.VideoCapture(video2)
    total, matches = 0, 0
    for _ in range(max_frames):
        ret1, f1 = cap1.read()
        ret2, f2 = cap2.read()
        if not ret1 or not ret2:
            if ret1 == ret2:  # both ended
                break
            cap1.release(); cap2.release()
            return matches / max(total, 1)
        h1 = imagehash.phash(Image.fromarray(cv2.cvtColor(f1, cv2.COLOR_BGR2RGB)))
        h2 = imagehash.phash(Image.fromarray(cv2.cvtColor(f2, cv2.COLOR_BGR2RGB)))
        total += 1
        if h1 - h2 <= threshold:
            matches += 1
    cap1.release(); cap2.release()
    return matches / max(total, 1)

def compare_video_frames_at_times(video1: str, video2: str,
                                  times: list, threshold: int = 5) -> float:
    """Compare specific timestamps between two videos."""
    matches = 0
    for t in times:
        f1 = get_frame_at_time(video1, t)
        f2 = get_frame_at_time(video2, t)
        if f1 is None or f2 is None:
            continue
        h1 = imagehash.phash(Image.fromarray(cv2.cvtColor(f1, cv2.COLOR_BGR2RGB)))
        h2 = imagehash.phash(Image.fromarray(cv2.cvtColor(f2, cv2.COLOR_BGR2RGB)))
        if h1 - h2 <= threshold:
            matches += 1
    return matches / max(len(times), 1)
```

### Comparing Audio (MFCC + DTW)

```python
import librosa
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import cosine

def compare_audios(audio1: str, audio2: str) -> float:
    """Compare two audio files using MFCC + DTW. Returns 0.0-1.0."""
    try:
        y1, sr1 = librosa.load(audio1)
        y2, sr2 = librosa.load(audio2)
    except Exception:
        return 0.0
    if y1.shape[0] == 0 or y2.shape[0] == 0:
        return 0.0
    mfcc1 = librosa.util.normalize(librosa.feature.mfcc(y=y1, sr=sr1), axis=1)
    mfcc2 = librosa.util.normalize(librosa.feature.mfcc(y=y2, sr=sr2), axis=1)
    distance, path = fastdtw(mfcc1.T, mfcc2.T, dist=lambda x, y: cosine(x, y))
    normalized = distance / len(path) if path else float("inf")
    return float(np.exp(-normalized))

def compare_audio_from_video(video1: str, video2: str) -> float:
    """Extract audio tracks and compare."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav") as t1, \
         tempfile.NamedTemporaryFile(suffix=".wav") as t2:
        subprocess.run(["ffmpeg", "-y", "-i", video1, "-vn", "-c:a", "pcm_s16le", t1.name],
                       capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-i", video2, "-vn", "-c:a", "pcm_s16le", t2.name],
                       capture_output=True)
        return compare_audios(t1.name, t2.name)
```

### Verifying Image-Level Properties via Frame Extraction

```python
from skimage.metrics import structural_similarity as ssim

def compare_frame_ssim(video1: str, video2: str,
                       time_sec: float, threshold: float = 0.9) -> bool:
    """Compare frames from two videos at a specific time using SSIM."""
    f1 = get_frame_at_time(video1, time_sec)
    f2 = get_frame_at_time(video2, time_sec)
    if f1 is None or f2 is None:
        return False
    # Resize to same dimensions
    if f1.shape != f2.shape:
        f2 = cv2.resize(f2, (f1.shape[1], f1.shape[0]))
    gray1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    score = ssim(gray1, gray2)
    return score >= threshold

def verify_video_not_blank(video_path: str, num_samples: int = 5) -> bool:
    """Verify video has non-trivial content (not all black/white)."""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        cap.release()
        return False
    for i in range(num_samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * (i + 1) / (num_samples + 1)))
        ret, frame = cap.read()
        if not ret:
            continue
        std = np.std(frame)
        if std > 10:  # has variation = not blank
            cap.release()
            return True
    cap.release()
    return False
```

### OpenShot Config Verification

```python
OPENSHOT_CONFIG_DIR = os.path.expanduser("~/.openshot_qt/")
OPENSHOT_SETTINGS = os.path.join(OPENSHOT_CONFIG_DIR, "openshot.settings")

def read_openshot_settings() -> dict:
    """Read OpenShot settings (JSON format)."""
    if not os.path.exists(OPENSHOT_SETTINGS):
        return {}
    with open(OPENSHOT_SETTINGS, "r") as f:
        return json.load(f)

def set_openshot_setting(key: str, value):
    """Set an OpenShot setting. Creates the config file/dir if needed."""
    os.makedirs(OPENSHOT_CONFIG_DIR, exist_ok=True)
    settings = read_openshot_settings()
    settings[key] = value
    with open(OPENSHOT_SETTINGS, "w") as f:
        json.dump(settings, f, indent=2)

# Setup examples:
# set_openshot_setting("default_profile", "HD 1080p 30 fps")
# set_openshot_setting("autosave_interval", 3)
# set_openshot_setting("default_theme", "Humanity: Dark")
# set_openshot_setting("hardware_decoder", 0)
# set_openshot_setting("cache_mode", "CacheMemory")

def verify_openshot_setting(key: str, expected_value) -> bool:
    settings = read_openshot_settings()
    return settings.get(key) == expected_value

# Common settings to verify:
# "default_profile" - project profile name
# "default_theme" - UI theme
# "autosave_interval" - auto-save interval in minutes
# "cache_mode" - cache mode (CacheMemory or CacheDisk)
# "debug_enabled" - debug mode
# "hardware_decoder" - hardware acceleration
```

---

## 5. Gradual Scoring Pattern (reward-gen)

```python
def compute_reward(osp_path: str, golden_osp_path: str = None,
                   output_video: str = None, golden_video: str = None) -> float:
    """Compute a 0.0-1.0 reward score with multiple verification dimensions."""
    score = 0.0
    total_weight = 0.0

    # Dimension 1: Project structure (weight: 0.3)
    if osp_path and os.path.exists(osp_path):
        project = load_project(osp_path)
        w = 0.3
        total_weight += w
        sub_score = 0.0
        # Check clips exist
        if project.get("clips"):
            sub_score += 0.4
        # Check correct number of clips
        if golden_osp_path:
            golden = load_project(golden_osp_path)
            if len(project.get("clips", [])) == len(golden.get("clips", [])):
                sub_score += 0.3
            # Check effects match
            p_effects = sum(len(c.get("effects", [])) for c in project.get("clips", []))
            g_effects = sum(len(c.get("effects", [])) for c in golden.get("clips", []))
            if p_effects >= g_effects:
                sub_score += 0.3
        else:
            sub_score += 0.6  # no golden, just check structure
        score += w * sub_score

    # Dimension 2: Exported video comparison (weight: 0.5)
    if output_video and golden_video and os.path.exists(output_video):
        w = 0.5
        total_weight += w
        sub_score = 0.0
        # Duration match
        if verify_video_duration(output_video, get_video_duration(golden_video), tolerance=2.0):
            sub_score += 0.3
        # Resolution match
        info1 = get_video_info(output_video)
        info2 = get_video_info(golden_video)
        if info1 and info2:
            sub_score += 0.2
        # Visual similarity
        vsim = compare_videos(output_video, golden_video)
        sub_score += 0.5 * vsim
        score += w * sub_score

    # Dimension 3: Audio comparison (weight: 0.2)
    if output_video and golden_video:
        w = 0.2
        total_weight += w
        asim = compare_audio_from_video(output_video, golden_video)
        score += w * asim

    return score / total_weight if total_weight > 0 else 0.0

def get_video_duration(video_path: str) -> float:
    info = get_video_info(video_path)
    return float(info.get("format", {}).get("duration", 0))
```

---

## 6. Bitter Lessons

1. **`.osp` files are plain JSON — always verify via JSON, not GUI.** The `.osp` file is the single source of truth for project state. The reward-gen should parse it with `json.load()` rather than trying to inspect the GUI. This is far more reliable than screenshot-based verification.

2. **Clip `position` is timeline position, `start`/`end` are source trim points.** `position=5.0` means the clip appears at 5 seconds on the timeline. `start=2.0, end=8.0` means it plays source frames from 2s to 8s. Confusing these causes wrong timeline layouts.

3. **Layer 0 is the bottom layer.** Higher layer numbers render on top. Two clips on the same layer at the same position will cause only one to be visible. For overlay tasks (logo, text), use a higher layer number.

4. **Keyframe X values are frame numbers, not seconds.** In the JSON keyframe format, `"co": {"X": 30, "Y": 1.0}` means "at frame 30, value is 1.0". To convert: `frame = seconds * fps`. The API's `Keyframe.AddPoint(frame, value)` also uses frame numbers.

5. **OpenShot must be closed before modifying `.osp` files.** Like VLC with vlcrc, OpenShot will overwrite the `.osp` file on auto-save or exit. Kill OpenShot first, modify the file, then relaunch.

6. **`python3-openshot` is not on PyPI.** Must install via `apt install python3-openshot` or build from source. The `import openshot` module comes from system packages only. Setup scripts that assume `pip install` will fail.

7. **`Timeline.SetJson()` requires absolute file paths.** When loading a `.osp` via `SetJson()`, all media file paths in clips/readers must be absolute and the files must exist on disk. Relative paths or missing files cause silent failures (blank frames).

8. **Transition brightness range is -1.0 to 1.0, not 0.0 to 1.0.** `-1.0` = fully visible, `1.0` = fully transparent. A fade-out transition goes from `-1.0` to `1.0`. Getting this wrong produces inverted transitions.

9. **FFprobe returns duration as string.** Always `float()` the duration value from FFprobe JSON output. Forgetting this causes string comparison bugs.

10. **OpenShot startup is slow (3-5 seconds).** Unlike VLC which starts in <1s, OpenShot has a heavy Qt initialization. Use `delay_sec=3.0` minimum after launch, or `5.0` for complex projects. Checking too early may find no window.

11. **Clip `file_id` must match a file in `files` array.** If you add a clip referencing a `file_id` that doesn't exist in `project["files"]`, OpenShot will fail to load the clip. Always `add_file()` before `add_clip()`.

12. **Effect parameter names vary between JSON and Python API.** In JSON `.osp`, blur uses `"horizontal_radius"`. In the Python API, it's `blur.horizontal_radius`. The names are the same, but the access patterns differ. Always test both paths.

13. **Video comparison should use perceptual hashing, not pixel diff.** Re-encoding introduces minor artifacts. Use `imagehash.phash()` with a threshold of 5 for frame comparison. SSIM works for single-frame checks but is slow for full video comparison.

14. **Audio comparison must use MFCC+DTW, not waveform.** Re-encoding changes the raw waveform. Extract MFCC features and compare with Dynamic Time Warping for encoding-invariant similarity. Score via `exp(-normalized_distance)`.

15. **OpenShot's `scale` enum affects how clips fill the frame.** `0=CROP` (fill frame, crop overflow), `1=BEST_FIT` (fit inside, letterbox), `2=STRETCH` (distort to fill), `3=NONE` (original size). Using the wrong mode causes unexpected framing in export verification.

16. **Marker positions in `.osp` are in seconds, not frames.** Unlike keyframe X values (which are frame numbers), marker `position` is in seconds. This inconsistency is a common source of bugs when converting between the two.

17. **OpenShot auto-imports CLI file arguments as media, not project.** Only `.osp` files are loaded as projects. All other file types (`.mp4`, `.png`, `.mp3`) are imported into the file panel. `openshot-qt video.mp4` opens OpenShot with `video.mp4` in the media panel, NOT on the timeline.

18. **Transition `end` is duration relative to start, not absolute timeline time.** `end=2.0` means the transition lasts 2 seconds from its own `start` point, not that it ends at timeline second 2. Combined with `position`, the timeline end is `position + (end - start)`.

19. **`add_file` should include `duration` for video/audio.** Without it, OpenShot may miscalculate clip bounds. Use FFprobe to get the actual duration: `float(get_video_info(path)["format"]["duration"])`.

20. **OpenShot settings are JSON, unlike VLC's key=value.** The file `~/.openshot_qt/openshot.settings` is valid JSON. Use `json.load()`/`json.dump()` — don't try regex-based editing. OpenShot must be closed before modifying this file.

21. **For vision-based reward, read BEFORE from `_initial_reference`.** The agent and golden_patch both overwrite the canonical artifact. `initial_setup.py` saves a reference copy at `{TASK_ID}_initial_reference.<ext>` for reward.py to use as the BEFORE in `call_vision_judge()` / `call_video_vision_judge()`.
