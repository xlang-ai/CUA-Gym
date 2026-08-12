# wandb_mock Schema

**Deploy order**: 56 (alphabetical among all *_mock dirs, BASE_PORT=8000 -> port 8056)
**Base URL**: `http://172.17.46.46:8056/`
**Go Endpoint**: `GET /go?sid=<sid>` -> `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Note**: The `/go` route is a React page (client-side) when no `sid` query param is present; the Vite middleware handles `GET /go?sid=<sid>` server-side for state JSON.

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Logged-in user: `id`, `username`, `name`, `email`, `avatar`, `teams[]`, `defaultEntity` |
| `users` | array | All users. Each: `{id, username, name, email, avatar}` |
| `projects` | array | ML projects. Each: `{id, name, displayName, entity, description, visibility, createdAt, updatedAt, totalRuns, totalComputeHours, tags[]}` |
| `runs` | array | Experiment runs. Each: `{id, runId, name, projectId, state, createdAt, updatedAt, duration, color, visible, user, tags[], notes, config{}, summary{}, history[], systemMetrics[], metadata{}, logs[], files[], inputArtifacts[], outputArtifacts[]}` |
| `sweeps` | array | Hyperparameter sweeps. Each: `{id, sweepId, projectId, name, state, createdAt, method, metric{}, parameters{}, runCount, bestRun, sweepRuns[]}` |
| `artifacts` | array | Versioned artifacts (datasets/models). Each: `{id, name, type, projectId, description, createdAt, versions[]}` |
| `reports` | array | Project reports. Each: `{id, title, projectId, description, authorId, createdAt, updatedAt, viewCount, blocks[]}` |
| `activeProjectId` | string | ID of the currently active/selected project (e.g. `"proj-1"`) |
| `activeRunId` | string\|null | ID of currently viewed run, or `null` |
| `selectedRunIds` | array | Array of run IDs currently selected in the workspace |
| `workspace` | object | Workspace configuration: `{panelSections[], runTableColumns[], sortBy, sortOrder, filters[], groupBy}` |
| `notifications` | array | User notifications. Each: `{id, type, runName, timestamp, read}` |

### `currentUser` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"user-1"` | User ID |
| `username` | string | `"alex-ml"` | Username |
| `name` | string | `"Alex Chen"` | Display name |
| `email` | string | `"alex@example.com"` | Email address |
| `avatar` | string\|null | `null` | Avatar URL |
| `teams` | string[] | `["ml-team"]` | Team memberships |
| `defaultEntity` | string | `"alex-ml"` | Default entity namespace for projects |

### `users[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | User ID (`user-1` through `user-4`) |
| `username` | string | Username (e.g. `"alex-ml"`, `"sarah-ds"`, `"mike-eng"`, `"lisa-res"`) |
| `name` | string | Full name |
| `email` | string | Email address |
| `avatar` | string\|null | Avatar URL (all `null` by default) |

### `projects[]` Items

| Field | Type | Default Example | Description |
|-------|------|-----------------|-------------|
| `id` | string | `"proj-1"` | Project ID |
| `name` | string | `"image-classifier"` | URL-safe project slug |
| `displayName` | string | `"Image Classifier"` | Human-readable name |
| `entity` | string | `"alex-ml"` | Owner entity/namespace |
| `description` | string | | Project description |
| `visibility` | string | `"public"` | `"public"` or `"private"` |
| `createdAt` | string | | ISO 8601 timestamp |
| `updatedAt` | string | | ISO 8601 timestamp |
| `totalRuns` | number | `6` | Total run count |
| `totalComputeHours` | number | `47.3` | Cumulative GPU hours |
| `tags` | string[] | `["computer-vision", "classification"]` | Project tags |

### `runs[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Internal run ID (`run-1` through `run-12`) |
| `runId` | string | Short run ID hash (e.g. `"a1b2c3d4"`) |
| `name` | string | Auto-generated run name (e.g. `"golden-sunset-1"`) |
| `projectId` | string | Parent project ID |
| `state` | string | `"finished"`, `"running"`, or `"crashed"` |
| `createdAt` | string | ISO 8601 timestamp |
| `updatedAt` | string | ISO 8601 timestamp |
| `duration` | number | Duration in seconds |
| `color` | string | Hex color for charts (e.g. `"#ff6384"`) |
| `visible` | boolean | Whether run is visible in workspace charts |
| `user` | string | Username of the run creator |
| `tags` | string[] | Run tags (e.g. `["baseline", "resnet"]`) |
| `notes` | string | Free-text notes about the run |
| `config` | object | Hyperparameter configuration (see below) |
| `summary` | object | Final metric summary (see below) |
| `history` | array | Training history data points (see below) |
| `systemMetrics` | array | System resource metrics (see below) |
| `metadata` | object | Environment metadata (see below) |
| `logs` | array | Log entries (see below) |
| `files` | array | Run files (see below) |
| `inputArtifacts` | string[] | IDs of input artifact references |
| `outputArtifacts` | string[] | IDs of output artifact references |

#### `runs[].config` (varies by project type)

**Image Classifier runs** (proj-1):

| Key | Type | Example |
|-----|------|---------|
| `model` | string | `"resnet50"`, `"efficientnet-b0"`, `"efficientnet-b2"`, `"resnet101"` |
| `dataset` | string | `"cifar10"` |
| `learning_rate` | number | `0.001` |
| `batch_size` | number | `64` |
| `epochs` | number | `50` |
| `optimizer` | string | `"adam"`, `"adamw"` |
| `weight_decay` | number | `0.0001` |
| `dropout` | number | `0.3` |
| `augmentation` | boolean | `true` |
| `seed` | number | `42` |

**NLP Sentiment runs** (proj-2):

| Key | Type | Example |
|-----|------|---------|
| `model` | string | `"bert-base-uncased"`, `"distilbert-base-uncased"`, `"bert-large-uncased"`, `"roberta-base"` |
| `dataset` | string | `"imdb"` |
| `learning_rate` | number | `2e-5` |
| `batch_size` | number | `16` |
| `epochs` | number | `5` |
| `optimizer` | string | `"adamw"` |
| `max_length` | number | `512` |
| `warmup_steps` | number | `500` |

**RL CartPole runs** (proj-3):

| Key | Type | Example |
|-----|------|---------|
| `algorithm` | string | `"PPO"`, `"DQN"` |
| `env` | string | `"CartPole-v1"` |
| `learning_rate` | number | `0.0003` |
| `n_steps` | number | `2048` (PPO) |
| `batch_size` | number | `64` |
| `n_epochs` | number | `10` (PPO) |
| `gamma` | number | `0.99` |
| `clip_range` | number | `0.2` (PPO) |
| `buffer_size` | number | `50000` (DQN) |
| `exploration_fraction` | number | `0.1` (DQN) |
| `target_update_interval` | number | `1000` (DQN) |

#### `runs[].summary` (varies by project type)

**Image Classifier** (`proj-1`): `{train_loss, train_acc, val_loss, val_acc, best_val_acc, epoch, total_params, learning_rate}`

**NLP Sentiment** (`proj-2`): `{train_loss, eval_loss, f1, accuracy, epoch, total_params}`

**RL CartPole** (`proj-3`): `{mean_reward, episode_length, value_loss, policy_loss, epoch, total_timesteps}`

#### `runs[].history[]` Items (per-step training metrics)

**Image Classifier**: `{step, train_loss, train_acc, val_loss, val_acc, epoch}`

**NLP Sentiment**: `{step, train_loss, eval_loss, f1, accuracy, epoch}`

**RL CartPole**: `{step, mean_reward, episode_length, value_loss, policy_loss, epoch}`

#### `runs[].systemMetrics[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | number | Seconds since start |
| `gpu_util` | number | GPU utilization % (0-100) |
| `gpu_memory` | number | GPU memory in GB |
| `cpu_util` | number | CPU utilization % (0-100) |
| `memory_util` | number | System memory % (0-100) |
| `disk_io` | number | Disk I/O in MB/s |
| `network_sent` | number | Network sent in MB/s |
| `network_recv` | number | Network received in MB/s |

#### `runs[].metadata` Object

| Field | Type | Example |
|-------|------|---------|
| `os` | string | `"Linux-5.15.0-x86_64"` |
| `python` | string | `"3.10.12"` |
| `gpu` | string | `"NVIDIA A100 40GB"` |
| `gpuCount` | number | `1` |
| `cudaVersion` | string | `"11.8"` |
| `framework` | string | `"PyTorch 2.1.0"` |
| `gitCommit` | string | `"a3f7e2b"` |
| `gitBranch` | string | `"main"` |

#### `runs[].logs[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp |
| `level` | string | `"INFO"`, `"WARNING"`, or `"ERROR"` |
| `message` | string | Log message text |

#### `runs[].files[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Filename (e.g. `"model.pt"`, `"config.yaml"`) |
| `size` | number | File size in bytes |
| `updatedAt` | string | ISO 8601 timestamp |

### `sweeps[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Internal sweep ID (`sweep-1`) |
| `sweepId` | string | Short sweep ID (e.g. `"abc123xy"`) |
| `projectId` | string | Parent project ID |
| `name` | string | Sweep name (e.g. `"ResNet LR Sweep"`) |
| `state` | string | `"running"` or `"finished"` |
| `createdAt` | string | ISO 8601 timestamp |
| `method` | string | `"bayes"`, `"grid"`, or `"random"` |
| `metric` | object | `{name: string, goal: "maximize"\|"minimize"}` |
| `parameters` | object | Parameter search space definitions (see below) |
| `runCount` | number | Number of runs in the sweep |
| `bestRun` | object\|null | `{runId, name, val_acc, config{}}` or `null` |
| `sweepRuns` | array | Array of sweep run results (see below) |

#### `sweeps[].parameters` Object

Keys are parameter names. Each value is one of:
- Continuous: `{min: number, max: number, distribution: "log_uniform"|"uniform"}`
- Categorical: `{values: (string|number)[]}`

#### `sweeps[].sweepRuns[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `runId` | string | Short run ID (e.g. `"sr-1"`) |
| `config` | object | Parameter values used for this run |
| `val_acc` | number | Metric value (key matches `sweep.metric.name`) |

### `artifacts[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Artifact ID (`art-1` through `art-3`) |
| `name` | string | Artifact name (e.g. `"cifar10-dataset"`) |
| `type` | string | `"dataset"` or `"model"` |
| `projectId` | string | Parent project ID |
| `description` | string | Artifact description |
| `createdAt` | string | ISO 8601 timestamp |
| `versions` | array | Array of version objects (see below) |

#### `artifacts[].versions[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Version tag (e.g. `"v0"`, `"v1"`) |
| `alias` | string[] | Version aliases (e.g. `["latest"]`, `["latest", "best"]`) |
| `size` | number | Total size in bytes |
| `createdAt` | string | ISO 8601 timestamp |
| `createdBy` | string | Username of creator |
| `metadata` | object | Arbitrary key-value metadata (varies by artifact) |
| `files` | array | Array of `{name: string, size: number}` |
| `usedBy` | string[] | Array of run IDs that used this version |

### `reports[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Report ID (`report-1`, `report-2`) |
| `title` | string | Report title |
| `projectId` | string | Parent project ID |
| `description` | string | Short description |
| `authorId` | string | Author user ID |
| `createdAt` | string | ISO 8601 timestamp |
| `updatedAt` | string | ISO 8601 timestamp |
| `viewCount` | number | Number of views |
| `blocks` | array | Content blocks (see below) |

#### `reports[].blocks[]` Items

Blocks have a `type` field determining their shape:

| Type | Fields | Description |
|------|--------|-------------|
| `"heading"` | `{type, level: 1\|2\|3, text: string}` | Section heading |
| `"paragraph"` | `{type, text: string}` | Text paragraph |
| `"panel_grid"` | `{type, panels: [{type: "line_chart", metric, title, runIds[]}]}` | Grid of chart panels |
| `"code_block"` | `{type, language: string, code: string}` | Code snippet |
| `"image"` | `{type}` | Image placeholder |

### `workspace` Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `panelSections` | array | 1 section with 4 panels | Panel sections for the workspace (see below) |
| `runTableColumns` | string[] | `["name", "state", "createdAt", "duration", "train_loss", "val_acc", "config.learning_rate", "config.model"]` | Columns shown in runs table |
| `sortBy` | string | `"createdAt"` | Current sort column |
| `sortOrder` | string | `"desc"` | `"asc"` or `"desc"` |
| `filters` | array | `[]` | Active filters (each: `{column, operator, value}`) |
| `groupBy` | string\|null | `null` | Column to group runs by, or `null` |

#### `workspace.panelSections[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Section ID (e.g. `"section-1"`) |
| `name` | string | Section name (e.g. `"Charts"`) |
| `collapsed` | boolean | Whether the section is collapsed |
| `panels` | array | Array of panel objects (see below) |

#### `workspace.panelSections[].panels[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Panel ID (e.g. `"panel-1"`) |
| `type` | string | `"line_chart"`, `"bar_chart"`, `"scatter_plot"`, or `"run_table"` |
| `metric` | string | Metric name for line/bar charts (e.g. `"train_loss"`) |
| `title` | string | Panel display title |
| `xMetric` | string | X-axis metric (scatter_plot only) |
| `yMetric` | string | Y-axis metric (scatter_plot only) |

### `notifications[]` Items

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Notification ID (`notif-1` through `notif-3`) |
| `type` | string | `"run_finished"` or `"run_crashed"` |
| `runName` | string | Name of the associated run |
| `timestamp` | string | ISO 8601 timestamp |
| `read` | boolean | Whether notification has been read |

## Default Data Summary

- **4 users**: `user-1` (alex-ml/Alex Chen), `user-2` (sarah-ds/Sarah Kim), `user-3` (mike-eng/Mike Johnson), `user-4` (lisa-res/Lisa Wang)
- **3 projects**:
  - `proj-1` "Image Classifier" (public, 6 runs, tags: computer-vision, classification)
  - `proj-2` "NLP Sentiment" (public, 4 runs, tags: nlp, sentiment-analysis)
  - `proj-3` "RL CartPole" (private, 2 runs, tags: reinforcement-learning)
- **12 runs** total:
  - Runs 1-6 in proj-1 (image classification with ResNet/EfficientNet on CIFAR-10; 4 finished, 1 crashed, 1 running)
  - Runs 7-10 in proj-2 (NLP sentiment with BERT variants on IMDB; 3 finished, 1 running)
  - Runs 11-12 in proj-3 (RL CartPole with PPO/DQN; 2 finished)
- **1 sweep**: `sweep-1` in proj-1, Bayesian search over learning_rate/batch_size/dropout/optimizer, 8 runs
- **3 artifacts**: `art-1` cifar10-dataset (2 versions), `art-2` resnet50-model (2 versions), `art-3` efficientnet-model (2 versions)
- **2 reports**: "CIFAR-10 Baseline Comparison" and "Sentiment Analysis Results"
- **3 notifications**: 2 unread (run_finished, run_crashed), 1 read
- **Default workspace**: 1 panel section "Charts" with 4 line chart panels (train_loss, train_acc, val_loss, val_acc)

## Routes

| Route Pattern | Page | Description |
|---------------|------|-------------|
| `/` | Home | Project listing with create-project form |
| `/go` | Go | State inspection endpoint (client-side, no sid) |
| `/:entity/:project/workspace` | Workspace | Charts + runs sidebar with panel management |
| `/:entity/:project/runs` | RunsTable | Tabular run listing with sort/filter/group/export |
| `/:entity/:project/runs/:runId/overview` | RunOverview | Run config, summary, tags, notes, metadata |
| `/:entity/:project/runs/:runId/charts` | RunCharts | Per-metric line charts for a single run |
| `/:entity/:project/runs/:runId/system` | RunSystem | System resource utilization charts |
| `/:entity/:project/runs/:runId/logs` | RunLogs | Searchable log viewer with download |
| `/:entity/:project/runs/:runId/files` | RunFiles | Sortable file listing |
| `/:entity/:project/sweeps` | Sweeps | Sweep listing with create-sweep modal |
| `/:entity/:project/sweeps/:sweepId` | SweepDetail | Parallel coordinates, parameter importance, run table |
| `/:entity/:project/artifacts` | Artifacts | Artifact browser grouped by type |
| `/:entity/:project/artifacts/:artifactName/:version` | ArtifactDetail | Version metadata, files, lineage, usage |
| `/:entity/:project/reports` | Reports | Report listing with create button |
| `/:entity/:project/reports/:reportId` | ReportDetail | Editable report with block-based content |
| `/:entity/:project/overview` | ProjectOverview | Basic project overview |

## Reducer Actions (State Mutations)

| Action Type | Payload | Effect |
|-------------|---------|--------|
| `INIT_STATE` | `{...state}` | Replace entire state |
| `SET_ACTIVE_PROJECT` | `projectId` | Set `activeProjectId`, clear `activeRunId` |
| `SET_ACTIVE_RUN` | `runId` | Set `activeRunId` |
| `TOGGLE_RUN_VISIBILITY` | `runId` | Toggle `runs[].visible` for given run |
| `SET_RUN_COLOR` | `{runId, color}` | Update `runs[].color` |
| `UPDATE_RUN_TAGS` | `{runId, tags}` | Replace `runs[].tags` array |
| `ADD_RUN_TAG` | `{runId, tag}` | Append tag to `runs[].tags` |
| `REMOVE_RUN_TAG` | `{runId, tag}` | Remove tag from `runs[].tags` |
| `UPDATE_RUN_NOTES` | `{runId, notes}` | Update `runs[].notes` |
| `UPDATE_RUN_NAME` | `{runId, name}` | Update `runs[].name` |
| `UPDATE_RUN_STATE` | `{runId, state}` | Update `runs[].state` |
| `DELETE_RUN` | `runId` | Remove run from `runs[]` and `selectedRunIds[]` |
| `ADD_PANEL` | `{sectionId, panel}` | Add panel to workspace section |
| `REMOVE_PANEL` | `panelId` | Remove panel from all sections |
| `REORDER_PANELS` | `{sectionId, panels}` | Replace panels array in section |
| `TOGGLE_SECTION_COLLAPSE` | `sectionId` | Toggle `workspace.panelSections[].collapsed` |
| `SET_SORT` | `{sortBy, sortOrder}` | Update workspace sort settings |
| `SET_FILTER` | `filters[]` | Replace workspace filters |
| `SET_GROUP_BY` | `groupBy` | Set workspace groupBy |
| `ADD_PROJECT` | `{...project}` | Append to `projects[]` |
| `CREATE_REPORT` | `{...report}` | Append to `reports[]` |
| `UPDATE_REPORT` | `{id, ...fields}` | Update matching report |
| `DELETE_REPORT` | `reportId` | Remove report from `reports[]` |
| `ADD_SWEEP` | `{...sweep}` | Append to `sweeps[]` |
| `SET_SELECTED_RUNS` | `runId[]` | Replace `selectedRunIds` |
| `MARK_NOTIFICATION_READ` | `notifId` | Set `notifications[].read = true` |
| `MARK_ALL_NOTIFICATIONS_READ` | (none) | Set all `notifications[].read = true` |
| `UPDATE_WORKSPACE` | `{...fields}` | Shallow merge into `workspace` |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8056/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": "user-1",
          "username": "alex-ml",
          "name": "Alex Chen",
          "email": "alex@example.com",
          "avatar": null,
          "teams": ["ml-team"],
          "defaultEntity": "alex-ml"
        },
        "projects": [
          {
            "id": "proj-1",
            "name": "image-classifier",
            "displayName": "Image Classifier",
            "entity": "alex-ml",
            "description": "ResNet experiments on CIFAR-10",
            "visibility": "public",
            "createdAt": "2025-11-15T10:30:00Z",
            "updatedAt": "2026-03-05T14:22:00Z",
            "totalRuns": 2,
            "totalComputeHours": 10.0,
            "tags": ["computer-vision"]
          }
        ],
        "runs": [
          {
            "id": "run-1",
            "runId": "a1b2c3d4",
            "name": "golden-sunset-1",
            "projectId": "proj-1",
            "state": "finished",
            "createdAt": "2026-03-01T08:15:00Z",
            "updatedAt": "2026-03-01T10:45:00Z",
            "duration": 9000,
            "color": "#ff6384",
            "visible": true,
            "user": "alex-ml",
            "tags": ["baseline", "resnet"],
            "notes": "Initial ResNet-50 baseline",
            "config": {
              "model": "resnet50",
              "dataset": "cifar10",
              "learning_rate": 0.001,
              "batch_size": 64,
              "epochs": 50,
              "optimizer": "adam"
            },
            "summary": {
              "train_loss": 0.234,
              "train_acc": 0.912,
              "val_loss": 0.389,
              "val_acc": 0.876,
              "best_val_acc": 0.881,
              "epoch": 50,
              "total_params": 25557032
            },
            "history": [
              {"step": 0, "train_loss": 2.3, "train_acc": 0.1, "val_loss": 2.3, "val_acc": 0.1, "epoch": 0},
              {"step": 1000, "train_loss": 0.234, "train_acc": 0.912, "val_loss": 0.389, "val_acc": 0.876, "epoch": 50}
            ],
            "systemMetrics": [
              {"timestamp": 0, "gpu_util": 85.0, "gpu_memory": 8.2, "cpu_util": 45.0, "memory_util": 35.0, "disk_io": 120.0, "network_sent": 1.5, "network_recv": 12.0}
            ],
            "metadata": {
              "os": "Linux-5.15.0-x86_64",
              "python": "3.10.12",
              "gpu": "NVIDIA A100 40GB",
              "gpuCount": 1,
              "cudaVersion": "11.8",
              "framework": "PyTorch 2.1.0",
              "gitCommit": "a3f7e2b",
              "gitBranch": "main"
            },
            "logs": [
              {"timestamp": "2026-03-01T08:15:00Z", "level": "INFO", "message": "wandb: Run golden-sunset-1 started"}
            ],
            "files": [
              {"name": "model.pt", "size": 102400000, "updatedAt": "2026-03-01T10:45:00Z"}
            ],
            "inputArtifacts": [],
            "outputArtifacts": []
          }
        ],
        "sweeps": [],
        "artifacts": [],
        "reports": [],
        "activeProjectId": "proj-1",
        "activeRunId": null,
        "selectedRunIds": ["run-1"],
        "workspace": {
          "panelSections": [
            {
              "id": "section-1",
              "name": "Charts",
              "collapsed": false,
              "panels": [
                {"id": "panel-1", "type": "line_chart", "metric": "train_loss", "title": "train_loss"},
                {"id": "panel-2", "type": "line_chart", "metric": "val_acc", "title": "val_acc"}
              ]
            }
          ],
          "runTableColumns": ["name", "state", "createdAt", "duration", "train_loss", "val_acc"],
          "sortBy": "createdAt",
          "sortOrder": "desc",
          "filters": [],
          "groupBy": null
        },
        "notifications": []
      }
    }
  }
}
```

## Key IDs Reference

### Users
| ID | Username | Name |
|----|----------|------|
| `user-1` | `alex-ml` | Alex Chen |
| `user-2` | `sarah-ds` | Sarah Kim |
| `user-3` | `mike-eng` | Mike Johnson |
| `user-4` | `lisa-res` | Lisa Wang |

### Projects
| ID | Name | Runs |
|----|------|------|
| `proj-1` | `image-classifier` | run-1 through run-6 |
| `proj-2` | `nlp-sentiment` | run-7 through run-10 |
| `proj-3` | `rl-cartpole` | run-11, run-12 |

### Runs
| ID | Name | Project | State |
|----|------|---------|-------|
| `run-1` | `golden-sunset-1` | proj-1 | finished |
| `run-2` | `electric-wood-2` | proj-1 | finished |
| `run-3` | `snowy-oath-3` | proj-1 | finished |
| `run-4` | `crimson-breeze-4` | proj-1 | finished |
| `run-5` | `quiet-river-5` | proj-1 | crashed |
| `run-6` | `bright-dawn-6` | proj-1 | running |
| `run-7` | `misty-forest-1` | proj-2 | finished |
| `run-8` | `wandering-star-2` | proj-2 | finished |
| `run-9` | `silver-moon-3` | proj-2 | finished |
| `run-10` | `amber-wave-4` | proj-2 | running |
| `run-11` | `dancing-leaf-1` | proj-3 | finished |
| `run-12` | `frozen-lake-2` | proj-3 | finished |

### Artifacts
| ID | Name | Type | Versions |
|----|------|------|----------|
| `art-1` | `cifar10-dataset` | dataset | v0, v1 |
| `art-2` | `resnet50-model` | model | v0, v1 |
| `art-3` | `efficientnet-model` | model | v0, v1 |

### Sweeps
| ID | Name | Method | Project |
|----|------|--------|---------|
| `sweep-1` | `ResNet LR Sweep` | bayes | proj-1 |
