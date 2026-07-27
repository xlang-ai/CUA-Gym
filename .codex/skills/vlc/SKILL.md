---
name: vlc
description: "How to programmatically configure, control, and verify VLC media player state using Python (vlcrc config, HTTP interface, media comparison). For setup-gen and reward-gen agents."
user-invocable: false
---

# VLC — Python Manipulation Guide

This skill teaches **setup-gen** (configure/launch VLC) and **reward-gen** (verify playback/config/media) how to work with VLC using Python.

- Libraries: `subprocess`, `requests`, `xml.etree.ElementTree`, `librosa`, `cv2`, `imagehash`, `Pillow`
- Install: `pip3 install requests librosa fastdtw scipy scikit-image opencv-python imagehash Pillow`
- Config path (Linux): `~/.config/vlc/vlcrc`

---

## 0. GUI Startup on VM (for setup-gen)

After preparing media/config, setup-gen should open VLC (and target media if required) for the GUI agent.

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

# Launch VLC with a target file
launch_gui('vlc "/home/user/Desktop/video.mp4"', delay_sec=2.0)
```

Guidelines:
- Use non-blocking launch (`Popen`) so script exits cleanly.
- Keep startup deterministic with short sleeps.

---

## 0.5. Media Asset Library (setup-gen)

Use the **real video/audio library** at `assets/media/vlc/` instead of generating synthetic test patterns.

### Available Categories

| Category | Count | Description | Good for |
|----------|-------|-------------|----------|
| `videos` | ~30 | Real short clips: nature, city, cooking, aerial, rain, sunset | Playback, format conversion, trimming, effects |
| `subtitles` | 5 | Sample .srt files (English dialogue, tutorial, movie, cooking, multilingual) | Subtitle loading, track switching, delay settings |

Audio files can be extracted from videos on the VM using FFmpeg (see Section 1).

### Upload Pattern

```bash
# Upload video to BOTH VMs
python3 scripts/env_cli.py -c "<workdir>/env_config_initial.json" upload \
    "assets/media/vlc/videos/nature_timelapse_001.mp4" "/home/user/<task_id>.mp4"
python3 scripts/env_cli.py -c "<workdir>/env_config_golden.json"  upload \
    "assets/media/vlc/videos/nature_timelapse_001.mp4" "/home/user/<task_id>.mp4"

# Upload subtitle if needed
python3 scripts/env_cli.py -c "<workdir>/env_config_initial.json" upload \
    "assets/media/vlc/subtitles/english_dialogue.srt" "/home/user/<task_id>.srt"
```

Then in `initial_setup.py`:
```python
import shutil
shutil.copy(f'{WORKDIR}/{TASK_ID}.mp4', f'{WORKDIR}/{TASK_ID}_initial_reference.mp4')
launch_gui(f'vlc "{WORKDIR}/{TASK_ID}.mp4"', delay_sec=2.0)
```

### Picking Assets from Manifest

```python
import json, random
manifest = json.load(open("assets/media/manifest.json"))
vlc_videos = [a for a in manifest["assets"] if a["domain"] == "vlc" and a["category"] == "videos"]
# Pick a nature video
nature = [v for v in vlc_videos if "nature" in v.get("tags", [])]
asset = random.choice(nature)
```

---

## 1. Creating & Configuring (setup-gen)

### vlcrc Configuration File

The vlcrc file uses `key=value` format. Commented lines start with `#`. A commented-out key means "use default".

```python
import os, re, shutil, subprocess

VLCRC_PATH = os.path.expanduser("~/.config/vlc/vlcrc")

def read_vlcrc() -> str:
    with open(VLCRC_PATH, "r") as f:
        return f.read()

def set_vlcrc_option(key: str, value: str):
    """Set a vlcrc option. Uncomments the key if commented out."""
    content = read_vlcrc()
    # Pattern: match both commented (#key=...) and uncommented (key=...)
    pattern = re.compile(rf'^(#?\s*){re.escape(key)}=.*$', re.MULTILINE)
    replacement = f'{key}={value}'
    if pattern.search(content):
        content = pattern.sub(replacement, content)
    else:
        content += f'\n{key}={value}\n'
    with open(VLCRC_PATH, "w") as f:
        f.write(content)

# Examples — all config keys the evaluator checks:
set_vlcrc_option("qt-bgcone", "0")                          # splash screen cone: 0=off, 1=on (default: 1)
set_vlcrc_option("qt-max-volume", "200")                     # max volume: integer (default: 125)
set_vlcrc_option("qt-minimal-view", "1")                     # minimal interface: 0=normal, 1=minimal (default: 0)
set_vlcrc_option("qt-slider-colours", "10;10;10;10;10;10;10;10;10;10;10;10")  # R;G;B groups
set_vlcrc_option("global-key-play-pause", "Space")           # global hotkey: empty=""=disabled, key=enabled
set_vlcrc_option("one-instance-when-started-from-file", "0") # single instance: 0=off, 1=on (default: 1)
set_vlcrc_option("play-and-exit", "0")                       # auto-close after playback: 0=off, 1=on (default: 0)
set_vlcrc_option("input-record-path", "/home/user/Desktop")  # recording output path
```

### Launching VLC

```python
# Play a local file
subprocess.Popen(["vlc", "/home/user/Desktop/video.mp4"])

# Play with specific options
subprocess.Popen([
    "vlc",
    "--no-audio",                    # mute audio
    "--no-video-title-show",         # hide title overlay
    "--start-time=10",               # start at 10 seconds
    "--stop-time=30",                # stop at 30 seconds
    "--play-and-pause",              # pause when reaching stop time
    "/home/user/Desktop/video.mp4"
])

# Play with HTTP interface enabled (for status monitoring)
subprocess.Popen([
    "vlc",
    "--extraintf=http",
    "--http-password=password",
    "--http-port=8080",
    "/home/user/Desktop/video.mp4"
])

# Stream an HLS URL
subprocess.Popen(["vlc", "https://example.com/stream/master.m3u8"])

# Suppress verbose output
env = os.environ.copy()
env["VLC_VERBOSE"] = "-1"
subprocess.Popen(["vlc", "/home/user/Desktop/video.mp4"], env=env)
```

### Killing and Restarting VLC

```python
# Kill VLC (needed before modifying vlcrc)
subprocess.run(["pkill", "-f", "vlc"], capture_output=True)
import time; time.sleep(2)

# Restart VLC to pick up config changes
subprocess.Popen(["vlc", "--extraintf=http", "--http-password=password"])
```

### Creating Media Files for Testing

```python
# Generate silent audio with ffmpeg
subprocess.run([
    "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
    "-t", "5", "-q:a", "9", "/home/user/Desktop/silence.mp3"
], check=True)

# Generate test video (color bars)
subprocess.run([
    "ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=5:size=640x480:rate=30",
    "-pix_fmt", "yuv420p", "/home/user/Desktop/test.mp4"
], check=True)

# Extract audio from video
subprocess.run([
    "ffmpeg", "-i", "/home/user/Desktop/video.mp4",
    "-vn", "-acodec", "libmp3lame", "/home/user/Desktop/audio.mp3"
], check=True)

# Capture a frame as screenshot
subprocess.run([
    "ffmpeg", "-i", "/home/user/Desktop/video.mp4",
    "-ss", "00:00:05", "-frames:v", "1", "/home/user/Desktop/frame.png"
], check=True)

# Rotate video
subprocess.run([
    "ffmpeg", "-i", "/home/user/Desktop/input.mp4",
    "-vf", "transpose=1", "/home/user/Desktop/rotated.mp4"
], check=True)
```

---

## 2. Reading & Verifying (reward-gen)

### Verifying vlcrc Config Options

```python
def get_vlcrc_option(key: str, default: str = None) -> str:
    """Read a vlcrc option value. Returns default if key is commented or missing."""
    content = read_vlcrc()
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if f"{key}=" in stripped:
            return stripped.split("=", 1)[-1].strip()
    return default

# Config verification helpers with correct defaults
CONFIG_DEFAULTS = {
    "qt-bgcone": "1",
    "qt-max-volume": "125",
    "qt-minimal-view": "0",
    "qt-slider-colours": "153;210;153;20;210;20;255;199;15;245;39;29",
    "one-instance-when-started-from-file": "1",
    "play-and-exit": "0",
}

def verify_vlcrc_option(key: str, expected: str) -> bool:
    actual = get_vlcrc_option(key, CONFIG_DEFAULTS.get(key))
    return str(actual) == str(expected)

# Verify global-key-play-pause (special: empty = disabled, non-empty = enabled)
def verify_global_key_enabled(expected_enabled: bool) -> bool:
    val = get_vlcrc_option("global-key-play-pause", "")
    is_enabled = val != ""
    return is_enabled == expected_enabled

# Verify slider colors are "blackish" (all RGB values < 100)
def verify_slider_blackish() -> bool:
    colours = get_vlcrc_option("qt-slider-colours", CONFIG_DEFAULTS["qt-slider-colours"])
    values = [int(x) for x in colours.split(";")]
    return all(v < 100 for v in values)

# Verify recording path
def verify_recording_path(expected_path: str) -> bool:
    return get_vlcrc_option("input-record-path") == expected_path
```

### Verifying VLC Playback Status (HTTP Interface)

```python
import requests
from xml.etree import ElementTree

def get_vlc_status(host: str = "localhost", port: int = 8080, password: str = "password") -> ElementTree.Element:
    """Fetch VLC status XML via HTTP interface."""
    resp = requests.get(f"http://{host}:{port}/requests/status.xml", auth=("", password), timeout=5)
    return ElementTree.fromstring(resp.content)

def verify_vlc_playing(expected_filename: str = None, expected_url: str = None,
                       host: str = "localhost", port: int = 8080) -> bool:
    tree = get_vlc_status(host, port)
    state = tree.find("state").text
    if state != "playing":
        return False
    if expected_filename:
        # Check multiple XML paths for filename
        for xpath in [
            'information/category[@name="meta"]/info[@name="filename"]',
            'information/category[@name="meta"]/info[@name="title"]',
            'information/category[@name="meta"]/info[@name="uri"]',
            'information/category[@name="meta"]/info[@name="name"]',
        ]:
            elem = tree.find(xpath)
            if elem is not None and elem.text:
                if os.path.basename(elem.text) == expected_filename or elem.text.endswith(expected_filename):
                    return True
        return False
    if expected_url:
        from urllib.parse import urlparse
        for xpath in [
            'information/category[@name="meta"]/info[@name="url"]',
            'information/category[@name="meta"]/info[@name="filename"]',
            'information/category[@name="meta"]/info[@name="title"]',
        ]:
            elem = tree.find(xpath)
            if elem is not None and elem.text:
                if expected_url in elem.text:
                    return True
                # HLS streams may show just the filename
                if elem.text == os.path.basename(urlparse(expected_url).path):
                    return True
        return False
    return True  # just verify playing state
```

### Verifying Fullscreen Mode

```python
def verify_fullscreen(window_size: dict, screen_size: dict) -> bool:
    """Compare window size to screen size."""
    if not window_size or not screen_size:
        return False
    return (window_size["width"] == screen_size["width"] and
            window_size["height"] == screen_size["height"])
```

### Comparing Audio Files (MFCC + DTW)

```python
import librosa
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import cosine

def compare_audios(audio1: str, audio2: str) -> float:
    """Compare two audio files using MFCC features + DTW. Returns 0.0-1.0."""
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
```

### Comparing Video Files (Perceptual Hashing)

```python
import cv2, imagehash
from PIL import Image

def compare_videos(video1: str, video2: str, max_frames: int = 100, threshold: int = 5) -> float:
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
```

### Comparing Images (SSIM)

```python
from skimage.metrics import structural_similarity as ssim

def compare_images(img1_path: str, img2_path: str, base_score: float = None) -> float:
    """Compare two images using SSIM. Returns 0.0-1.0."""
    img1 = Image.open(img1_path).convert("L")
    img2 = Image.open(img2_path).convert("L")
    # Resize both to the smaller width and height independently
    new_size = (min(img1.size[0], img2.size[0]), min(img1.size[1], img2.size[1]))
    img1 = img1.resize(new_size, Image.Resampling.LANCZOS)
    img2 = img2.resize(new_size, Image.Resampling.LANCZOS)
    score = ssim(np.array(img1), np.array(img2))
    if base_score is not None:
        return max(0, (score - base_score) / (1 - base_score)) if score >= base_score + 0.01 else 0
    return score
```

---

## 3. Playlist Operations (setup-gen & reward-gen)

### Reading Playlist via HTTP Interface

```python
def get_vlc_playlist(host: str = "localhost", port: int = 8080, password: str = "password") -> list:
    """Fetch VLC playlist as list of dicts with id, name, uri, duration."""
    resp = requests.get(f"http://{host}:{port}/requests/playlist.xml", auth=("", password), timeout=5)
    tree = ElementTree.fromstring(resp.content)
    items = []
    for leaf in tree.iter("leaf"):
        items.append({
            "id": leaf.get("id"),
            "name": leaf.get("name", ""),
            "uri": leaf.get("uri", ""),
            "duration": int(leaf.get("duration", 0)),
        })
    return items

def verify_playlist_count(expected_count: int, host: str = "localhost", port: int = 8080) -> bool:
    """Verify the number of items in the playlist."""
    items = get_vlc_playlist(host, port)
    return len(items) == expected_count

def verify_playlist_order(expected_names: list, host: str = "localhost", port: int = 8080) -> bool:
    """Verify playlist item order by filename substrings."""
    items = get_vlc_playlist(host, port)
    if len(items) != len(expected_names):
        return False
    for item, expected in zip(items, expected_names):
        if expected.lower() not in item["name"].lower() and expected.lower() not in item["uri"].lower():
            return False
    return True

def verify_playlist_contains(filename: str, host: str = "localhost", port: int = 8080) -> bool:
    """Check if a specific file is in the playlist."""
    items = get_vlc_playlist(host, port)
    return any(filename.lower() in item["name"].lower() or filename.lower() in item["uri"].lower()
               for item in items)
```

### Adding Items to Playlist via HTTP

```python
def vlc_playlist_add(uri: str, host: str = "localhost", port: int = 8080, password: str = "password"):
    """Add a media file to VLC playlist via HTTP interface."""
    from urllib.parse import quote
    requests.get(
        f"http://{host}:{port}/requests/status.xml?command=in_enqueue&input={quote(uri)}",
        auth=("", password), timeout=5
    )

def vlc_playlist_clear(host: str = "localhost", port: int = 8080, password: str = "password"):
    """Clear the VLC playlist."""
    requests.get(
        f"http://{host}:{port}/requests/status.xml?command=pl_empty",
        auth=("", password), timeout=5
    )
```

---

## 4. Subtitle Operations (setup-gen & reward-gen)

### Creating Subtitle Files

```python
def create_srt_file(output_path: str, entries: list):
    """Create an SRT subtitle file.
    entries: list of (index, start_time, end_time, text) tuples
    start_time/end_time format: "HH:MM:SS,mmm"
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, start, end, text in entries:
            f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")

# Example
create_srt_file("/home/user/Desktop/subs.srt", [
    (1, "00:00:01,000", "00:00:04,000", "Hello, welcome!"),
    (2, "00:00:05,000", "00:00:08,000", "This is a subtitle test."),
    (3, "00:00:09,000", "00:00:12,000", "Goodbye!"),
])
```

### VLC Subtitle Configuration (vlcrc)

```python
# Subtitle-related vlcrc options
set_vlcrc_option("sub-auto-detect-file", "1")           # auto-detect subtitle files: 0=off, 1=on
set_vlcrc_option("sub-autodetect-path", ".")             # subtitle search paths
set_vlcrc_option("sub-language", "en")                   # preferred subtitle language
set_vlcrc_option("freetype-fontsize", "24")              # subtitle font size
set_vlcrc_option("freetype-color", "16777215")           # subtitle color (decimal RGB, 16777215 = white)
set_vlcrc_option("freetype-rel-fontsize", "16")          # relative font size: 10=smaller, 20=small, 16=normal
set_vlcrc_option("sub-margin", "50")                     # subtitle margin from bottom (pixels)
```

### Verifying Subtitle State via HTTP

```python
def verify_subtitle_track(expected_track_id: int = None,
                          host: str = "localhost", port: int = 8080) -> bool:
    """Verify current subtitle track. track_id=-1 means subtitles disabled."""
    tree = get_vlc_status(host, port)
    for cat in tree.findall('information/category'):
        if "subtitle" in cat.get("name", "").lower() or cat.get("name") == "Subtitle":
            return True  # subtitle track exists
    # Check via streams info
    for info in tree.findall('.//info[@name="Type"]'):
        if info.text and "subtitle" in info.text.lower():
            return True
    return expected_track_id == -1  # if expecting disabled, return True when not found

def verify_srt_content(srt_path: str, expected_entries: int = None,
                       contains_text: str = None) -> bool:
    """Verify SRT file content."""
    if not os.path.isfile(srt_path):
        return False
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = [b.strip() for b in content.strip().split("\n\n") if b.strip()]
    if expected_entries is not None and len(blocks) != expected_entries:
        return False
    if contains_text is not None and contains_text not in content:
        return False
    return True
```

---

## 5. Audio Metadata Verification

```python
import json, subprocess

def get_audio_info(audio_path: str) -> dict:
    """Extract audio metadata using FFprobe."""
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", audio_path
    ], capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout else {}

def verify_audio_sample_rate(audio_path: str, expected_rate: int) -> bool:
    """Verify audio sample rate (e.g., 44100, 48000)."""
    info = get_audio_info(audio_path)
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "audio":
            return int(stream.get("sample_rate", 0)) == expected_rate
    return False

def verify_audio_channels(audio_path: str, expected_channels: int) -> bool:
    """Verify audio channel count (1=mono, 2=stereo)."""
    info = get_audio_info(audio_path)
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "audio":
            return stream.get("channels") == expected_channels
    return False

def verify_audio_bitrate(audio_path: str, min_bitrate: int = None, max_bitrate: int = None) -> bool:
    """Verify audio bitrate (bits/sec). Use format-level bitrate as fallback."""
    info = get_audio_info(audio_path)
    bitrate = None
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "audio" and stream.get("bit_rate"):
            bitrate = int(stream["bit_rate"])
            break
    if bitrate is None:
        bitrate = int(info.get("format", {}).get("bit_rate", 0))
    if bitrate == 0:
        return False
    if min_bitrate is not None and bitrate < min_bitrate:
        return False
    if max_bitrate is not None and bitrate > max_bitrate:
        return False
    return True

def verify_audio_duration(audio_path: str, expected_duration: float, tolerance: float = 1.0) -> bool:
    """Verify audio file duration in seconds."""
    info = get_audio_info(audio_path)
    duration = float(info.get("format", {}).get("duration", 0))
    return abs(duration - expected_duration) <= tolerance

def verify_audio_codec(audio_path: str, expected_codec: str) -> bool:
    """Verify audio codec (e.g., 'mp3', 'aac', 'vorbis', 'pcm_s16le')."""
    info = get_audio_info(audio_path)
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "audio":
            return expected_codec.lower() in stream.get("codec_name", "").lower()
    return False
```

---

## 6. Gradual Scoring Pattern (reward-gen)

```python
def compute_reward(task_type: str = "config", config_checks: list = None,
                   media_src: str = None, media_golden: str = None,
                   playback_checks: list = None) -> float:
    """Compute a 0.0-1.0 reward score for VLC tasks.

    task_type: "config" (vlcrc settings), "media" (audio/video manipulation),
               "playback" (player state), "mixed" (combination)
    config_checks: list of (check_fn, weight) tuples for vlcrc verification
    playback_checks: list of (check_fn, weight) tuples for HTTP status checks
    """
    score = 0.0
    total_weight = 0.0

    # Dimension 1: Config verification (weight: 0.4 for config tasks)
    if config_checks:
        w = 0.4 if task_type == "config" else 0.2
        total_weight += w
        passed = sum(1 for fn, _ in config_checks if fn())
        score += w * (passed / len(config_checks))

    # Dimension 2: Media file comparison (weight: 0.4 for media tasks)
    if media_src and media_golden:
        w = 0.4 if task_type == "media" else 0.25
        total_weight += w
        sub_score = 0.0

        # Check file existence
        if os.path.isfile(media_src):
            sub_score += 0.2

            # Duration match
            src_info = get_audio_info(media_src) if media_src.endswith((".mp3", ".wav", ".ogg")) else {}
            gld_info = get_audio_info(media_golden) if media_golden.endswith((".mp3", ".wav", ".ogg")) else {}
            src_dur = float(src_info.get("format", {}).get("duration", 0))
            gld_dur = float(gld_info.get("format", {}).get("duration", 0))
            if gld_dur > 0 and abs(src_dur - gld_dur) < 2.0:
                sub_score += 0.3

            # Content similarity (audio or video)
            try:
                if media_src.endswith((".mp3", ".wav", ".ogg", ".flac")):
                    similarity = compare_audios(media_src, media_golden)
                else:
                    similarity = compare_videos(media_src, media_golden)
                sub_score += 0.5 * similarity
            except Exception:
                pass

        score += w * sub_score

    # Dimension 3: Playback state (weight: 0.3 for playback tasks)
    if playback_checks:
        w = 0.3 if task_type == "playback" else 0.15
        total_weight += w
        passed = sum(1 for fn, _ in playback_checks if fn())
        score += w * (passed / len(playback_checks))

    # Dimension 4: VLC process is running (weight: 0.1 — sanity check)
    w = 0.1
    total_weight += w
    result = subprocess.run(["pgrep", "-f", "vlc"], capture_output=True)
    if result.returncode == 0:
        score += w

    return score / total_weight if total_weight > 0 else 0.0
```

---

## 7. Bitter Lessons

1. **VLC must be killed before modifying vlcrc.** VLC overwrites vlcrc on exit. If you edit vlcrc while VLC is running, your changes are lost when VLC closes. Always `pkill -f vlc`, wait, then edit.

2. **Commented-out vlcrc keys use default values.** A line `#qt-bgcone=1` means "use default (1)". To change a setting, you must uncomment it (remove `#`) AND set the value. Just appending a new line won't work if the commented line is parsed first.

3. **vlcrc key matching must check for exact `key=`.** Searching for `"play-and-exit"` in a line also matches `"play-and-exit-title"`. Always match `f"{key}="` to avoid false positives.

4. **global-key-play-pause uses empty string for "disabled".** An empty value (`global-key-play-pause=`) means disabled. Any non-empty value (e.g., `Space`) means enabled. This differs from other boolean 0/1 keys.

5. **qt-slider-colours is semicolon-separated RGB triplets.** Format: `R;G;B;R;G;B;R;G;B;R;G;B` (4 color groups of 3 values = 12 values). Parse with `split(";")` then group by 3.

6. **VLC HTTP interface status XML paths vary by media type.** Filename may appear under `info[@name="filename"]`, `info[@name="title"]`, or `info[@name="uri"]` depending on whether it's local file, network stream, or HLS. Always check multiple paths.

7. **HLS streams show filename, not full URL.** When playing `https://cdn.example.com/stream/master.m3u8`, VLC status may show just `master.m3u8` as the filename. Compare basename of the expected URL as fallback.

8. **Config changes need VLC restart to take effect.** After modifying vlcrc, kill and restart VLC. The evaluator often uses a `postconfig` step that restarts VLC to verify persistence.

9. **Audio comparison uses MFCC + DTW, not waveform.** Direct waveform comparison fails due to encoding differences. The evaluator extracts MFCC features and uses Dynamic Time Warping. Similarity score uses exponential decay: `exp(-normalized_distance)`.

10. **Video comparison uses perceptual hashing, not pixel diff.** The evaluator computes `imagehash.phash()` per frame and tolerates hash distance up to a threshold. This handles minor encoding artifacts but requires both videos to have matching frame counts.

11. **Image SSIM comparison resizes to smaller image.** When comparing images of different sizes, both are resized to `min(size1, size2)`. The `reference_base_result` option provides incremental scoring above a baseline.

12. **VLC HTTP auth uses empty username.** The HTTP interface uses basic auth with username `""` (empty string) and a password. Default password is `"password"`. Forgetting this causes 401 errors.

13. **`VLC_VERBOSE=-1` suppresses console spam.** Without this environment variable, VLC prints hundreds of debug lines. Set it in the subprocess environment to keep logs clean.

14. **vlcrc uses `=` without spaces.** The format is `key=value` with no spaces around `=`. Adding spaces breaks parsing. When writing, always use `f"{key}={value}"` directly.

15. **Playlist XML uses `<leaf>` elements, not `<item>`.** VLC's playlist XML nests `<leaf>` inside `<node>` elements. Each `<leaf>` has `id`, `name`, `uri`, `duration` attributes. Don't search for `<item>` tags.

16. **Playlist duration is in seconds (integer), not milliseconds.** Unlike some media APIs, VLC playlist XML reports duration in whole seconds. `-1` means unknown/live stream.

17. **Subtitle auto-detection requires matching filenames.** VLC looks for `.srt`/`.sub` files with the same base name as the video (e.g., `video.mp4` → `video.srt`). Setting `sub-auto-detect-file=1` alone won't work if filenames differ.

18. **Audio bitrate from FFprobe may be at stream or format level.** Some codecs (e.g., VBR MP3) don't report per-stream bitrate. Fall back to `format.bit_rate` when `stream.bit_rate` is missing.

19. **SRT files must use CRLF or LF line endings and `-->` separator.** Malformed SRT with wrong arrow (`->`, `—>`) or missing blank lines between entries will not load in VLC.

20. **For vision-based reward, read BEFORE from `_initial_reference`.** The agent and golden_patch both overwrite the canonical artifact. `initial_setup.py` saves a reference copy at `{TASK_ID}_initial_reference.<ext>` for reward.py to use as the BEFORE image in `call_vision_judge()` / `call_video_vision_judge()`.
