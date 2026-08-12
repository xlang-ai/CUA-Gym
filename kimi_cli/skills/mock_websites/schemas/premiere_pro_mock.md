# premiere_pro_mock Schema

**Deploy order**: 38 (alphabetical among all *_mock dirs, BASE_PORT=8000 -> port 8038)
**Base URL**: `http://172.17.46.46:8038/`
**Go Endpoint**: `GET /go?sid=<sid>` -> `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` -> `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `project` | object | Project metadata: `{id, name, createdAt, lastModified, settings}` |
| `mediaItems` | array | Imported media files in the project panel |
| `bins` | array | Organizational folders for media items |
| `tracks` | array | Timeline tracks (video and audio) |
| `clips` | array | Clips placed on the timeline (references media via `mediaId`) |
| `effectPresets` | array | Available effect/transition presets (built-in catalog) |
| `appliedEffects` | array | Effects applied to specific clips |
| `appliedTransitions` | array | Transitions applied to clip edges |
| `markers` | array | Timeline markers for navigation/annotation |
| `player` | object | Playback state: `{currentTime, isPlaying, volume, playbackRate, inPoint, outPoint, loop}` |
| `exportSettings` | object | Export/render configuration |
| `ui` | object | UI state (excluded from `/go` state diff) |

### `project` object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"proj_1"` | Project identifier |
| `name` | string | `"Travel Vlog - Summer 2026"` | Project display name |
| `createdAt` | string (ISO) | `"2026-02-20T10:00:00Z"` | Creation timestamp |
| `lastModified` | string (ISO) | `"2026-02-20T12:00:00Z"` | Last modification timestamp (auto-updated on clip/media changes) |
| `settings` | object | see below | Project-level settings |

#### `project.settings`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | number | `1920` | Sequence frame width in pixels |
| `height` | number | `1080` | Sequence frame height in pixels |
| `frameRate` | number | `30` | Frames per second |
| `sampleRate` | number | `48000` | Audio sample rate in Hz |

### `mediaItems[]` array

Each media item:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, e.g. `"media_1"` |
| `name` | string | Filename with extension, e.g. `"Beach_Sunset_4K.mp4"` |
| `type` | string | One of: `"video"`, `"audio"`, `"image"` |
| `duration` | number | Duration in seconds |
| `width` | number\|null | Frame width (null for audio) |
| `height` | number\|null | Frame height (null for audio) |
| `frameRate` | number\|null | FPS of source (null for audio/image) |
| `thumbnail` | string\|null | Path to thumbnail image (null for audio) |
| `binId` | string\|null | ID of containing bin folder, or null for root |
| `inPoint` | number | Source in point (seconds), default `0` |
| `outPoint` | number | Source out point (seconds), default = `duration` |

**Default media IDs**: `media_1` (Beach_Sunset_4K.mp4, video, 62.5s, 4K), `media_2` (City_Walk.mp4, video, 45s, 1080p), `media_3` (Interview_A.mp4, video, 120s, 1080p), `media_4` (Background_Music.mp3, audio, 180s), `media_5` (Voiceover_Intro.wav, audio, 15s), `media_6` (Title_Card.png, image, 5s, 1080p), `media_7` (Drone_Mountains.mp4, video, 35s, 4K), `media_8` (Ocean_Waves_SFX.wav, audio, 30s)

### `bins[]` array

Each bin:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, e.g. `"bin_1"` |
| `name` | string | Display name, e.g. `"Footage"` |
| `parentBinId` | string\|null | Parent bin ID for nesting, null for root-level bins |

**Default bin IDs**: `bin_1` (Footage), `bin_2` (Interviews), `bin_3` (Audio), `bin_4` (Graphics)

### `tracks[]` array

Each track:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, e.g. `"track_v1"`, `"track_a1"` |
| `name` | string | Display label, e.g. `"V1"`, `"A1"` |
| `type` | string | One of: `"video"`, `"audio"` |
| `order` | number | Sort order within its type group (0-based) |
| `muted` | boolean | Whether track output is muted |
| `locked` | boolean | Whether track is locked (prevents editing) |
| `visible` | boolean | Whether track is visible (video tracks only, always `true` for audio) |
| `height` | number | Track row height in pixels (default: 60 for video, 40 for audio) |
| `volume` | number | (audio tracks only) Volume level 0.0-1.0, default `1.0` |
| `pan` | number | (audio tracks only) Stereo pan -1.0 to 1.0, default `0` |

**Default track IDs**: `track_v1`, `track_v2`, `track_v3` (video), `track_a1`, `track_a2`, `track_a3` (audio)

### `clips[]` array

Each clip on the timeline:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, e.g. `"clip_1"` |
| `mediaId` | string | Reference to source `mediaItems[].id` |
| `trackId` | string | Reference to `tracks[].id` where this clip resides |
| `startTime` | number | Position on timeline in seconds (left edge) |
| `duration` | number | Clip duration on timeline in seconds |
| `inPoint` | number | Source media in point in seconds |
| `outPoint` | number | Source media out point in seconds |
| `label` | string | Display name, e.g. `"Beach Sunset"` |
| `color` | string | Hex color for clip bar, e.g. `"#4A90D9"` |
| `effectIds` | array | Array of `appliedEffects[].id` strings applied to this clip |
| `transitionInId` | string\|null | Reference to `appliedTransitions[].id` for incoming transition |
| `transitionOutId` | string\|null | Reference to `appliedTransitions[].id` for outgoing transition |

**Default clip IDs**: `clip_1` (Title Card on V2, 0-5s), `clip_2` (Beach Sunset on V1, 3-23s), `clip_3` (City Walk on V1, 23-38s), `clip_4` (Drone Mountains on V1, 38-58s), `clip_5` (Voiceover Intro on A1, 0-15s), `clip_6` (Background Music on A3, 0-58s), `clip_7` (Ocean Waves on A2, 3-28s)

**Available clip colors**: Mango `#E6A23C`, Iris `#4A90D9`, Caribbean `#4DB6AC`, Lavender `#b39ddb`, Forest `#67C23A`, Rose `#E57373`, Cerulean `#00BCD4`, Violet `#9C27B0`

### `effectPresets[]` array

Built-in effect catalog (read-only reference):

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique preset ID, e.g. `"fx_gaussian_blur"` |
| `name` | string | Display name, e.g. `"Gaussian Blur"` |
| `category` | string | Group name: `"Blur & Sharpen"`, `"Color Correction"`, `"Transform"`, `"Audio Effects"`, `"Dissolve"`, `"Wipe"`, `"Slide"` |
| `type` | string | One of: `"video"`, `"audio"`, `"transition"` |
| `defaultParams` | object | Default parameter key-value pairs |

**Default preset IDs**:
- Video: `fx_gaussian_blur` (Gaussian Blur), `fx_brightness` (Brightness & Contrast), `fx_hue_saturation` (Hue/Saturation), `fx_crop` (Crop), `fx_opacity` (Opacity), `fx_sharpen` (Sharpen)
- Audio: `fx_echo` (Echo), `fx_eq` (Parametric Equalizer)
- Transitions: `fx_cross_dissolve` (Cross Dissolve), `fx_dip_to_black` (Dip to Black), `fx_wipe` (Wipe), `fx_push` (Push)

### `appliedEffects[]` array

Effects applied to clips:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique instance ID, e.g. `"applied_fx_1"` |
| `presetId` | string | Reference to `effectPresets[].id` |
| `clipId` | string | Reference to `clips[].id` |
| `enabled` | boolean | Whether the effect is active |
| `params` | object | Current parameter values (cloned from preset's `defaultParams`, then user-modified) |

**Default applied effects**: `applied_fx_1` (Brightness & Contrast on clip_2, brightness=10, contrast=5)

### `appliedTransitions[]` array

Transitions on clip edges:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique instance ID, e.g. `"trans_1"` |
| `presetId` | string | Reference to `effectPresets[].id` (transition type) |
| `clipId` | string | Reference to `clips[].id` |
| `position` | string | One of: `"in"`, `"out"` |
| `duration` | number | Transition duration in seconds |

**Default transitions**: `trans_1` (Cross Dissolve out on clip_1, 1.0s), `trans_2` (Cross Dissolve in on clip_3, 1.0s)

### `markers[]` array

Timeline markers:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier, e.g. `"marker_1"` |
| `time` | number | Position on timeline in seconds |
| `name` | string | Marker label |
| `color` | string | Hex color for marker |
| `comment` | string | Optional annotation text |

**Default markers**: `marker_1` (Intro at 0s, orange), `marker_2` (Act 2 at 23s, blue), `marker_3` (Act 3 at 38s, green)

### `player` object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `currentTime` | number | `0` | Playhead position in seconds |
| `isPlaying` | boolean | `false` | Whether playback is active |
| `volume` | number | `0.8` | Master volume 0.0-1.0 |
| `playbackRate` | number | `1.0` | Playback speed multiplier (0.25, 0.5, 1, 1.5, 2) |
| `inPoint` | number\|null | `null` | In point for region playback |
| `outPoint` | number\|null | `null` | Out point for region playback |
| `loop` | boolean | `false` | Whether to loop between in/out points |

### `exportSettings` object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `format` | string | `"H.264"` | Video codec: `"H.264"`, `"HEVC"`, `"ProRes"`, `"DNxHR"` |
| `preset` | string | `"YouTube 1080p"` | Export preset: `"YouTube 1080p"`, `"YouTube 4K"`, `"Vimeo 1080p"`, `"Vimeo 4K"`, `"Custom"` |
| `resolution` | object | `{width:1920, height:1080}` | Output resolution in pixels |
| `frameRate` | number | `30` | Output frame rate |
| `bitrate` | number | `16` | Video bitrate in Mbps (1-100) |
| `audioCodec` | string | `"AAC"` | Audio codec: `"AAC"`, `"PCM"`, `"MP3"` |
| `audioBitrate` | number | `320` | Audio bitrate in kbps: `128`, `192`, `256`, `320` |
| `outputName` | string | `"Travel_Vlog_Summer_2026.mp4"` | Output filename |

### `ui` object (excluded from state diff)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `activePanel` | string | `"timeline"` | Currently focused panel: `"timeline"`, `"project"`, `"effects"`, `"effectControls"`, `"sourceMonitor"`, `"programMonitor"` |
| `selectedClipId` | string\|null | `null` | Currently selected clip on the timeline |
| `selectedClipIds` | array | `[]` | Multiple selected clip IDs (for Select All) |
| `selectedMediaId` | string\|null | `null` | Currently selected media item in project panel |
| `selectedEffectPresetId` | string\|null | `null` | Currently selected effect preset in effects panel |
| `activeTool` | string | `"selection"` | Active editing tool: `"selection"`, `"trackSelect"`, `"rippleEdit"`, `"rollingEdit"`, `"rateStretch"`, `"razor"`, `"slip"`, `"slide"`, `"pen"`, `"hand"`, `"zoom"`, `"type"` |
| `timelineZoom` | number | `1.0` | Timeline zoom level (0.1-10.0) |
| `timelineScrollX` | number | `0` | Horizontal scroll offset in pixels |
| `effectsSearchQuery` | string | `""` | Search filter for effects panel |
| `mediaSearchQuery` | string | `""` | Search filter for project panel media |
| `sourceMonitorMediaId` | string\|null | `null` | Media loaded in source monitor (set by double-clicking media) |
| `isExportModalOpen` | boolean | `false` | Whether the export dialog is open |
| `snapToClips` | boolean | `true` | Whether snapping is enabled in timeline |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8038/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "project": {
          "id": "proj_1",
          "name": "My Video Project",
          "createdAt": "2026-03-01T10:00:00Z",
          "lastModified": "2026-03-01T10:00:00Z",
          "settings": {"width": 1920, "height": 1080, "frameRate": 30, "sampleRate": 48000}
        },
        "mediaItems": [
          {"id": "media_1", "name": "Interview.mp4", "type": "video", "duration": 60, "width": 1920, "height": 1080, "frameRate": 30, "thumbnail": null, "binId": null, "inPoint": 0, "outPoint": 60}
        ],
        "bins": [],
        "tracks": [
          {"id": "track_v1", "name": "V1", "type": "video", "order": 0, "muted": false, "locked": false, "visible": true, "height": 60},
          {"id": "track_a1", "name": "A1", "type": "audio", "order": 0, "muted": false, "locked": false, "visible": true, "height": 40, "volume": 1.0, "pan": 0}
        ],
        "clips": [
          {"id": "clip_1", "mediaId": "media_1", "trackId": "track_v1", "startTime": 0, "duration": 60, "inPoint": 0, "outPoint": 60, "label": "Interview", "color": "#4A90D9", "effectIds": [], "transitionInId": null, "transitionOutId": null}
        ],
        "effectPresets": [
          {"id": "fx_brightness", "name": "Brightness & Contrast", "category": "Color Correction", "type": "video", "defaultParams": {"brightness": 0, "contrast": 0}},
          {"id": "fx_cross_dissolve", "name": "Cross Dissolve", "category": "Dissolve", "type": "transition", "defaultParams": {}}
        ],
        "appliedEffects": [],
        "appliedTransitions": [],
        "markers": [],
        "player": {"currentTime": 0, "isPlaying": false, "volume": 0.8, "playbackRate": 1.0, "inPoint": null, "outPoint": null, "loop": false},
        "exportSettings": {
          "format": "H.264", "preset": "YouTube 1080p", "resolution": {"width": 1920, "height": 1080},
          "frameRate": 30, "bitrate": 16, "audioCodec": "AAC", "audioBitrate": 320, "outputName": "output.mp4"
        },
        "ui": {
          "activePanel": "timeline", "selectedClipId": null, "selectedClipIds": [], "selectedMediaId": null,
          "selectedEffectPresetId": null, "activeTool": "selection", "timelineZoom": 1.0, "timelineScrollX": 0,
          "effectsSearchQuery": "", "mediaSearchQuery": "", "sourceMonitorMediaId": null,
          "isExportModalOpen": false, "snapToClips": true
        }
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Move playhead / scrub timeline ruler | `player.currentTime` updated |
| Play / pause (Space) | `player.isPlaying` toggled; `player.currentTime` advances while playing |
| Step frame forward/backward | `player.currentTime` incremented/decremented by `1/frameRate` |
| Go to start/end | `player.currentTime` set to 0 or max clip end; `player.isPlaying` = false |
| Set playback rate | `player.playbackRate` updated |
| Set volume | `player.volume` updated |
| Set in/out point (I/O keys) | `player.inPoint` / `player.outPoint` updated |
| Select clip on timeline | `ui.selectedClipId` updated |
| Select all clips (Ctrl+A) | `ui.selectedClipIds` populated with all unlocked clip IDs |
| Move clip (drag) | `clips[i].trackId` and/or `clips[i].startTime` updated; `project.lastModified` updated |
| Trim clip in/out edge | `clips[i].startTime`, `clips[i].inPoint`, `clips[i].outPoint`, `clips[i].duration` updated; `project.lastModified` updated |
| Split clip at playhead (Ctrl+K or razor tool) | `clips[]` array: original clip shortened, new clip added after split point; `project.lastModified` updated |
| Delete clip (Delete key) | `clips[]` shrinks; related `appliedEffects[]` and `appliedTransitions[]` removed; `ui.selectedClipId` cleared if it was selected; `project.lastModified` updated |
| Rename clip | `clips[i].label` updated; `project.lastModified` updated |
| Set clip speed/duration | `clips[i].duration` and `clips[i].outPoint` recalculated; `project.lastModified` updated |
| Set clip color | `clips[i].color` updated; `project.lastModified` updated |
| Copy clip (Ctrl+C) | No state change (clipboard is in-memory ref only) |
| Paste clip (Ctrl+V) | `clips[]` array grows with new clip at `player.currentTime`; `project.lastModified` updated |
| Cut clip (Ctrl+X) | `clips[]` shrinks (clip deleted after copy); `project.lastModified` updated |
| Add clip to timeline (from source monitor or project panel drag) | `clips[]` array grows; `project.lastModified` updated |
| Toggle track mute | `tracks[i].muted` toggled |
| Toggle track lock | `tracks[i].locked` toggled |
| Toggle track visibility | `tracks[i].visible` toggled (video tracks only) |
| Add video/audio track | `tracks[]` array grows with new track entry |
| Delete track | `tracks[]` shrinks; all `clips[]` on that track also removed |
| Import media (File > Import Media) | `mediaItems[]` array grows; `project.lastModified` updated |
| Delete media item | `mediaItems[]` shrinks; `ui.selectedMediaId` / `ui.sourceMonitorMediaId` cleared if affected; `project.lastModified` updated |
| Select media in project panel | `ui.selectedMediaId` updated |
| Load media in source monitor (double-click) | `ui.sourceMonitorMediaId` updated |
| Search media | `ui.mediaSearchQuery` updated |
| Create bin | `bins[]` array grows |
| Rename bin | `bins[i].name` updated |
| Delete bin | `bins[]` shrinks; orphaned `mediaItems[].binId` set to null |
| Apply effect to clip (double-click or drag) | `appliedEffects[]` grows; `clips[i].effectIds` gains new ID; `project.lastModified` updated |
| Update effect parameter | `appliedEffects[i].params[key]` updated; `project.lastModified` updated |
| Toggle effect enabled | `appliedEffects[i].enabled` toggled |
| Remove effect | `appliedEffects[]` shrinks; `clips[i].effectIds` loses removed ID; `project.lastModified` updated |
| Select effect preset | `ui.selectedEffectPresetId` updated |
| Search effects | `ui.effectsSearchQuery` updated |
| Change active tool (V/C/B/etc.) | `ui.activeTool` updated |
| Change timeline zoom (slider or Ctrl+scroll) | `ui.timelineZoom` updated |
| Toggle snap | `ui.snapToClips` toggled |
| Add marker (M key) | `markers[]` array grows |
| Delete marker | `markers[]` shrinks |
| Open export modal (Ctrl+M or File > Export) | `ui.isExportModalOpen` = true |
| Update export settings | `exportSettings` fields updated |
| Close export modal | `ui.isExportModalOpen` = false |
| Undo (Ctrl+Z) | Data keys (`project`, `mediaItems`, `bins`, `tracks`, `clips`, `effectPresets`, `appliedEffects`, `appliedTransitions`, `markers`, `exportSettings`) restored from undo stack; `ui` and `player` preserved |
| Redo (Ctrl+Shift+Z) | Data keys restored from redo stack; `ui` and `player` preserved |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| V | Selection Tool |
| C | Razor Tool |
| B | Ripple Edit Tool |
| N | Rolling Edit Tool |
| R | Rate Stretch Tool |
| Y | Slip Tool |
| U | Slide Tool |
| P | Pen Tool |
| H | Hand Tool |
| Z | Zoom Tool |
| T | Type Tool |
| A (no Ctrl) | Track Select Forward Tool |
| I | Mark In Point |
| O | Mark Out Point |
| J | Shuttle Reverse |
| K | Stop Playback |
| L | Shuttle Forward |
| M | Add Marker |
| Delete / Backspace | Delete Selected Clip |
| ArrowLeft / ArrowRight | Step Frame Back / Forward |
| Home | Go to Start |
| End | Go to End |
| Ctrl+Z | Undo |
| Ctrl+Shift+Z | Redo |
| Ctrl+C | Copy Clip |
| Ctrl+V | Paste Clip |
| Ctrl+X | Cut Clip |
| Ctrl+A | Select All Clips |
| Ctrl+K | Split Clip at Playhead |
| Ctrl+M | Open Export Dialog |

## State Diff Keys

The `/go` endpoint compares these top-level keys between initial and current state:
`project`, `mediaItems`, `bins`, `tracks`, `clips`, `effectPresets`, `appliedEffects`, `appliedTransitions`, `markers`, `player`, `exportSettings`

Note: The `ui` key is **excluded** from the state diff returned by `/go`.
