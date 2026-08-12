# PACS-viewer_mock Schema

**Deploy order**: 34 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8034)
**Base URL**: `http://172.17.46.46:8034/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State inspect (client-side)**: Navigate to `/go` route in browser for `{initial_state, current_state, state_diff}` rendered as JSON.

## Application Overview

A PACS (Picture Archiving and Communication System) medical image viewer mock simulating a radiology workstation. Features a study worklist, multi-viewport DICOM image viewer with procedurally generated medical images (CT, MR, CR, US), measurement/annotation tools, window/level adjustment, and series tracking. State is managed via React Context with `useReducer`, persisted to localStorage under key `pacs_viewer_state`.

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Redirect | Redirects to `/studies` |
| `/studies` | `StudyList` | Study worklist with filtering, sorting, pagination |
| `/viewer/:studyId` | `Viewer` | Multi-viewport image viewer with toolbar, left panel (series list), right panel (measurements) |
| `/go` | `StateInspector` | State inspection endpoint returning JSON with `initial_state`, `current_state`, `state_diff` |

## State Schema

All state is stored as a single flat object. Top-level keys are described below.

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Logged-in radiologist user info |
| `settings` | object | Application display settings (layout, overlays, interpolation) |
| `patients` | object (map) | Patient records keyed by patient ID |
| `studies` | object (map) | Imaging studies keyed by study ID |
| `series` | object (map) | Image series keyed by series ID |
| `measurements` | object (map) | Measurements/annotations keyed by measurement ID |
| `viewports` | object (map) | Viewport display state keyed by viewport ID |
| `toolState` | object | Currently active tool and mouse button bindings |
| `uiState` | object | UI navigation state, panel visibility, study list filters/sort/pagination |

---

### `currentUser`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | `"Dr. Sarah Chen"` | Radiologist display name |
| `role` | string | `"radiologist"` | User role |
| `institution` | string | `"Mercy General Hospital"` | Institution name |

---

### `settings`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `language` | string | `"en"` | UI language |
| `layoutColumns` | number | `1` | Number of viewport columns in grid |
| `layoutRows` | number | `1` | Number of viewport rows in grid |
| `showOverlays` | boolean | `true` | Whether to show DICOM text overlays on viewports |
| `showOrientationMarkers` | boolean | `true` | Whether to show R/L/A/P orientation markers |
| `interpolation` | string | `"bilinear"` | Image interpolation mode |
| `cineFrameRate` | number | `24` | Cine playback frame rate |

---

### `patients`

Keyed by patient ID (e.g., `"PAT-001"`). Default: 6 patients.

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"PAT-001"` | Unique patient ID |
| `name` | string | `"SMITH^JOHN^A"` | DICOM-format patient name (Last^First^Middle) |
| `displayName` | string | `"Smith, John A."` | Human-readable display name |
| `mrn` | string | `"MRN-2847561"` | Medical record number |
| `dateOfBirth` | string | `"1958-03-15"` | Date of birth (YYYY-MM-DD) |
| `sex` | string | `"M"` | Patient sex: `"M"` or `"F"` |
| `age` | string | `"67Y"` | Patient age string |

Default patient IDs: `PAT-001` through `PAT-006`.

---

### `studies`

Keyed by study ID (e.g., `"STU-001"`). Default: 8 studies.

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"STU-001"` | Unique study ID |
| `studyInstanceUID` | string | `"1.2.840.113619..."` | DICOM Study Instance UID |
| `patientId` | string | `"PAT-001"` | Reference to patient record |
| `studyDate` | string | `"2024-11-15"` | Study date (YYYY-MM-DD) |
| `studyTime` | string | `"09:33:16"` | Study time (HH:MM:SS) |
| `studyDescription` | string | `"CT ABDOMEN AND PELVIS W CONTRAST"` | Study description |
| `accessionNumber` | string | `"ACC-74177"` | Accession number |
| `institution` | string | `"Mercy General Hospital"` | Performing institution |
| `referringPhysician` | string | `"Dr. Robert Martinez"` | Referring physician |
| `modalities` | string[] | `["CT"]` | Modalities used: `"CT"`, `"MR"`, `"CR"`, `"US"` |
| `numberOfSeries` | number | `4` | Total series count |
| `numberOfInstances` | number | `842` | Total image instance count |
| `status` | string | `"unread"` | Study read status: `"unread"`, `"in_progress"`, `"read"`, `"reported"` |

Default study IDs: `STU-001` through `STU-008`. Patient PAT-001 has two studies (STU-001, STU-007). Patient PAT-005 has two studies (STU-005, STU-008).

---

### `series`

Keyed by series ID (e.g., `"SER-001"`). Default: 28 series across 8 studies.

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"SER-001"` | Unique series ID |
| `seriesInstanceUID` | string | `"1.2.840.113619.2.55.3.001"` | DICOM Series Instance UID |
| `studyId` | string | `"STU-001"` | Parent study ID |
| `seriesNumber` | number | `1` | Series number within study |
| `seriesDescription` | string | `"Scout"` | Series description (e.g., "Axial 2.0mm", "T1W Axial", "PA") |
| `modality` | string | `"CT"` | Series modality: `"CT"`, `"MR"`, `"CR"`, `"US"` |
| `numberOfInstances` | number | `2` | Number of images in this series |
| `thumbnailType` | string | `"xr_chest_pa"` | Procedural image generator type (see below) |
| `bodyPart` | string | `"ABDOMEN"` | Body part: `"ABDOMEN"`, `"BRAIN"`, `"CHEST"`, `"HEAD"`, `"LIVER"`, `"GALLBLADDER"`, `"KIDNEY"` |
| `sliceThickness` | number\|null | `10.0` | Slice thickness in mm (null for CR/US) |
| `pixelSpacing` | number[] | `[0.488, 0.488]` | Pixel spacing [row, col] in mm |
| `rows` | number | `512` | Image matrix rows |
| `columns` | number | `512` | Image matrix columns |
| `windowCenter` | number | `40` | Default window center (level) |
| `windowWidth` | number | `400` | Default window width |
| `isTracked` | boolean | `false` | Whether this series is tracked for RECIST measurements |

**Thumbnail types** (procedural image generators):
`ct_axial_head`, `ct_axial_chest`, `ct_axial_abdomen`, `ct_coronal_chest`, `mr_axial_brain`, `mr_sagittal_brain`, `mr_coronal_brain`, `xr_chest_pa`, `xr_chest_lateral`, `us_abdomen`

Default series IDs: `SER-001` through `SER-028`.

---

### `measurements`

Keyed by measurement ID (e.g., `"MEAS-001"`). Default: 5 measurements on study STU-001.

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `"MEAS-001"` | Unique measurement ID |
| `type` | string | `"bidirectional"` | Measurement type: `"bidirectional"`, `"length"`, `"ellipse"`, `"angle"`, `"annotation"` |
| `label` | string | `"Lymph Node"` | User-assigned label for the measurement |
| `studyId` | string | `"STU-001"` | Study this measurement belongs to |
| `seriesId` | string | `"SER-003"` | Series this measurement is on |
| `instanceNumber` | number | `45` | Image instance number where measurement is placed |
| `points` | object[] | `[{x:0.42, y:0.38}, ...]` | Normalized coordinates (0-1) defining the measurement geometry |
| `value` | number | `24.4` | Primary measurement value |
| `secondaryValue` | number\|null | `16.4` | Secondary value (e.g., short axis for bidirectional; null for length/ellipse) |
| `unit` | string | `"mm"` | Measurement unit: `"mm"`, `"mm\u00B2"` (mm squared) |
| `text` | string\|null | `null` | Text content for annotation type measurements |
| `huMean` | number\|null | `null` | Mean Hounsfield Unit value (for ellipse ROI) |
| `huStd` | number\|null | `null` | Hounsfield Unit standard deviation (for ellipse ROI) |
| `color` | string | `"#ffeb3b"` | Display color hex string |
| `isTarget` | boolean | `true` | Whether this is a RECIST target lesion |
| `targetCategory` | string\|null | `"target"` | Category: `"target"`, `"non-target"`, or `null` |
| `createdAt` | string | `"2024-11-15T09:45:00Z"` | ISO timestamp of creation |
| `createdBy` | string | `"Dr. Sarah Chen"` | Creator name |

Default measurement IDs: `MEAS-001` through `MEAS-005` (3 targets: two "Lymph Node" bidirectional, one "Spleen" bidirectional; 2 non-targets: one "Reference" length, one "Liver lesion" ellipse).

---

### `viewports`

Keyed by viewport ID (e.g., `"VP-0"`). Default: 1 viewport in a 1x1 layout.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"VP-0"` | Viewport identifier (format: `VP-{index}`) |
| `seriesId` | string\|null | `null` | Currently loaded series ID (null if empty) |
| `currentInstanceNumber` | number | `1` | Current displayed image instance (1-based) |
| `windowCenter` | number | `40` | Current window center (level) value |
| `windowWidth` | number | `400` | Current window width value |
| `zoom` | number | `1.0` | Zoom factor (1.0 = 100%) |
| `panX` | number | `0` | Horizontal pan offset in pixels |
| `panY` | number | `0` | Vertical pan offset in pixels |
| `rotation` | number | `0` | Rotation angle in degrees (0, 90, 180, 270) |
| `flipH` | boolean | `false` | Horizontal flip state |
| `flipV` | boolean | `false` | Vertical flip state |
| `invert` | boolean | `false` | Image invert (negative) state |
| `isActive` | boolean | `true` | Whether this viewport is the active/selected one |

When layout changes to NxM (e.g., 2x2), viewports `VP-0` through `VP-{N*M-1}` are created.

---

### `toolState`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `activeTool` | string | `"windowLevel"` | Currently active tool: `"zoom"`, `"windowLevel"`, `"pan"`, `"length"`, `"bidirectional"`, `"ellipse"`, `"angle"`, `"annotation"` |
| `activeLeftClick` | string | `"windowLevel"` | Tool bound to left mouse click (mirrors `activeTool`) |
| `activeRightClick` | string | `"zoom"` | Tool bound to right mouse click |
| `activeMiddleClick` | string | `"pan"` | Tool bound to middle mouse click |
| `windowLevelPreset` | string | `"softTissue"` | Active W/L preset name: `"softTissue"`, `"lung"`, `"bone"`, `"brain"`, `"abdomen"`, `"liver"`, `"mediastinum"`, `"stroke"` |

**Window/Level Presets**:

| Preset | Window Width | Window Center |
|--------|-------------|---------------|
| `softTissue` | 400 | 40 |
| `lung` | 1500 | -600 |
| `bone` | 2000 | 300 |
| `brain` | 80 | 40 |
| `abdomen` | 350 | 50 |
| `liver` | 150 | 30 |
| `mediastinum` | 350 | 50 |
| `stroke` | 8 | 32 |

---

### `uiState`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `currentView` | string | `"studyList"` | Current view: `"studyList"` or `"viewer"` |
| `activeStudyId` | string\|null | `null` | Currently open study ID in the viewer |
| `leftPanelOpen` | boolean | `true` | Left panel (series list) visibility |
| `rightPanelOpen` | boolean | `true` | Right panel (measurements) visibility |
| `leftPanelTab` | string | `"primary"` | Active tab in left panel: `"primary"`, `"recent"`, `"all"` |
| `cineIsPlaying` | boolean | `false` | Whether cine mode is active |
| `cineFrameRate` | number | `24` | Cine playback frame rate |
| `showPreferencesDialog` | boolean | `false` | Whether preferences dialog is open |
| `studyListFilters` | object | _(see below)_ | Study worklist filter values |
| `studyListSort` | object | `{field:"studyDate", direction:"desc"}` | Sort configuration |
| `studyListPage` | number | `1` | Current page number (1-based) |
| `studyListPageSize` | number | `25` | Items per page |

**`studyListFilters`**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `patientName` | string | `""` | Filter by patient display name (case-insensitive substring) |
| `mrn` | string | `""` | Filter by MRN (case-insensitive substring) |
| `studyDate` | string | `""` | Filter by study date |
| `description` | string | `""` | Filter by study description (case-insensitive substring) |
| `modality` | string | `""` | Filter by modality: `""` (all), `"CT"`, `"MR"`, `"CR"`, `"US"` |
| `accession` | string | `""` | Filter by accession number (case-insensitive substring) |

**`studyListSort`**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `field` | string | `"studyDate"` | Sort field: `"patientName"`, `"mrn"`, `"studyDate"`, `"description"`, `"modality"`, `"status"`, `"seriesCount"`, `"numberOfInstances"`, `"accession"` |
| `direction` | string | `"desc"` | Sort direction: `"asc"` or `"desc"` |

---

## State Diff Tracking

The `/go` endpoint computes state diffs for these categories:

| Diff Category | What Is Tracked |
|--------------|-----------------|
| `measurements` | Added (`status:"added"`), deleted (`status:"deleted"`), or modified (`status:"modified"`) measurement entries |
| `studies` | Changes to `status` field only (e.g., `"unread"` -> `"in_progress"`) |
| `viewports` | Any viewport property changes (series loaded, window/level, zoom, pan, rotation, flip, invert) |
| `toolState` | Changes to active tool, mouse bindings, W/L preset |
| `uiState` | Changes to view, panels, tabs, filters, sort, pagination |
| `settings` | Changes to layout, overlays, interpolation settings |
| `series` | Changes to `isTracked` field only |

---

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8034/?sid=task001",
    "inject_state": true,
    "state_content": {"action": "set", "state": {
      "currentUser": {"name": "Dr. Sarah Chen", "role": "radiologist", "institution": "Mercy General Hospital"},
      "settings": {"language": "en", "layoutColumns": 1, "layoutRows": 1, "showOverlays": true, "showOrientationMarkers": true, "interpolation": "bilinear", "cineFrameRate": 24},
      "patients": {
        "PAT-001": {"id": "PAT-001", "name": "SMITH^JOHN^A", "displayName": "Smith, John A.", "mrn": "MRN-2847561", "dateOfBirth": "1958-03-15", "sex": "M", "age": "67Y"}
      },
      "studies": {
        "STU-001": {"id": "STU-001", "studyInstanceUID": "1.2.840.113619.2.55.3.604688119.992.1416340160.810", "patientId": "PAT-001", "studyDate": "2024-11-15", "studyTime": "09:33:16", "studyDescription": "CT ABDOMEN AND PELVIS W CONTRAST", "accessionNumber": "ACC-74177", "institution": "Mercy General Hospital", "referringPhysician": "Dr. Robert Martinez", "modalities": ["CT"], "numberOfSeries": 2, "numberOfInstances": 562, "status": "unread"}
      },
      "series": {
        "SER-001": {"id": "SER-001", "seriesInstanceUID": "1.2.840.113619.2.55.3.001", "studyId": "STU-001", "seriesNumber": 1, "seriesDescription": "Scout", "modality": "CT", "numberOfInstances": 2, "thumbnailType": "xr_chest_pa", "bodyPart": "ABDOMEN", "sliceThickness": 10.0, "pixelSpacing": [0.488, 0.488], "rows": 512, "columns": 512, "windowCenter": 40, "windowWidth": 400, "isTracked": false},
        "SER-002": {"id": "SER-002", "seriesInstanceUID": "1.2.840.113619.2.55.3.002", "studyId": "STU-001", "seriesNumber": 2, "seriesDescription": "Axial 2.0mm", "modality": "CT", "numberOfInstances": 280, "thumbnailType": "ct_axial_abdomen", "bodyPart": "ABDOMEN", "sliceThickness": 2.0, "pixelSpacing": [0.488, 0.488], "rows": 512, "columns": 512, "windowCenter": 40, "windowWidth": 400, "isTracked": true}
      },
      "measurements": {},
      "viewports": {
        "VP-0": {"id": "VP-0", "seriesId": null, "currentInstanceNumber": 1, "windowCenter": 40, "windowWidth": 400, "zoom": 1.0, "panX": 0, "panY": 0, "rotation": 0, "flipH": false, "flipV": false, "invert": false, "isActive": true}
      },
      "toolState": {"activeTool": "windowLevel", "activeLeftClick": "windowLevel", "activeRightClick": "zoom", "activeMiddleClick": "pan", "windowLevelPreset": "softTissue"},
      "uiState": {"currentView": "studyList", "activeStudyId": null, "leftPanelOpen": true, "rightPanelOpen": true, "leftPanelTab": "primary", "cineIsPlaying": false, "cineFrameRate": 24, "showPreferencesDialog": false, "studyListFilters": {"patientName": "", "mrn": "", "studyDate": "", "description": "", "modality": "", "accession": ""}, "studyListSort": {"field": "studyDate", "direction": "desc"}, "studyListPage": 1, "studyListPageSize": 25}
    }}
  }
}
```

---

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Click study in worklist | `uiState.currentView` → `"viewer"`, `uiState.activeStudyId` set, `viewports` populated with first series |
| Navigate back to study list | `uiState.currentView` → `"studyList"` |
| Select tool (zoom, pan, W/L, measurement) | `toolState.activeTool` changes, `toolState.activeLeftClick` updated |
| Scroll through images | `viewports[vpId].currentInstanceNumber` changes |
| Drag to adjust window/level | `viewports[vpId].windowCenter` and `viewports[vpId].windowWidth` change |
| Drag to pan image | `viewports[vpId].panX` and `viewports[vpId].panY` change |
| Drag to zoom image | `viewports[vpId].zoom` changes |
| Click "More > Invert" | `viewports[vpId].invert` toggles |
| Click "More > Rotate CW/CCW" | `viewports[vpId].rotation` changes by +90/-90 degrees |
| Click "More > Flip H/V" | `viewports[vpId].flipH` or `viewports[vpId].flipV` toggles |
| Click "More > Reset" | Viewport reset to series defaults (zoom=1, pan=0, rotation=0, no flip/invert) |
| Change viewport layout (1x1, 1x2, 2x1, 2x2) | `settings.layoutRows` and `settings.layoutColumns` change, `viewports` map is rebuilt |
| Click series in left panel | `viewports[activeVpId].seriesId` changes, viewport properties reset to series defaults |
| Click left panel tab (primary/recent/all) | `uiState.leftPanelTab` changes |
| Toggle left panel | `uiState.leftPanelOpen` toggles |
| Toggle right panel | `uiState.rightPanelOpen` toggles |
| Click on viewport to activate | `viewports[*].isActive` -- only clicked viewport becomes `true`, others `false` |
| Add measurement | `measurements` gains new entry with auto-generated ID |
| Delete measurement | `measurements` loses entry |
| Update measurement | `measurements[id]` fields updated |
| Change study status | `studies[studyId].status` changes |
| Toggle series tracking | `series[seriesId].isTracked` toggles |
| Set W/L preset | `toolState.windowLevelPreset` changes |
| Toggle cine play | `uiState.cineIsPlaying` toggles |
| Filter study list | `uiState.studyListFilters.{field}` updated, `uiState.studyListPage` resets to 1 |
| Sort study list | `uiState.studyListSort.field` and `uiState.studyListSort.direction` change |
| Change study list page | `uiState.studyListPage` changes |
| Update settings | `settings.{field}` updated |

---

## Default Data Summary

- **6 patients**: PAT-001 through PAT-006
- **8 studies**: STU-001 through STU-008 (modalities: CT, MR, CR, US; statuses: unread, in_progress, read, reported)
- **28 series**: SER-001 through SER-028 across all studies
- **5 measurements**: MEAS-001 through MEAS-005, all on study STU-001 (3 target bidirectional, 1 non-target length, 1 non-target ellipse)
- **1 viewport**: VP-0 (empty, no series loaded initially)
- **Active tool**: windowLevel with softTissue preset
- **UI starts on**: study list view (`currentView: "studyList"`)
