---
name: grafana
description: "How to set up and manipulate Grafana dashboard, alerting, and admin state via HTTP APIs for CUA-Gym tasks. For setup-gen and reward-gen agents."
user-invocable: false
---

# Grafana — Setup & Verification Guide

This skill teaches **setup-gen** and **reward-gen** how to create, manipulate, and verify Grafana state for monitoring/observability tasks. Grafana tasks involve **HTTP state management** through a shared Grafana instance.

- Libraries: `requests`, `json`, `uuid`, `copy`
- Grafana instance: `https://cua-gym-grafana.xlang.ai`
- Admin credentials: `admin` / `cua-gym-admin-2024`
- Grafana version: 12.4.1

---

## 0. Architecture Overview

```
Admin creates session org + user  →  User logs in via browser  →  CUA agent interacts with Grafana UI
         ↓                                    ↓                              ↓
  Inject dashboards/alerts            setup-gen configures state      reward-gen verifies via API
         ↓                                    ↓                              ↓
  TestData datasource               initial_setup.py runs              reward.py reads back state
         ↓                                                                   ↓
  csv_content = controlled data                                   DELETE org + user (cleanup)
```

**Key design**: Each training session gets its own **Grafana Organization** for complete isolation. Dashboards, datasources, alerts, and folders are org-scoped — a user in org N cannot see org M's resources.

**Key difference from mock_websites**: Grafana is a real application (not a mock). State is injected via Grafana's native REST API, not a custom `/post?sid=` endpoint. Verification reads state back via the same API.

---

## 1. Session Isolation via Organizations

Every training episode uses a dedicated Grafana Organization with its own user. This provides complete state isolation.

### 1.1 Session Setup Flow

```python
import requests
import uuid
import json

GRAFANA_URL = 'https://cua-gym-grafana.xlang.ai'
ADMIN_AUTH = ('admin', 'cua-gym-admin-2024')

session_id = str(uuid.uuid4())[:8]
org_name = f'session_{session_id}'
user_login = f'agent_{session_id}'
user_password = f'agent_pass_{session_id}'
user_email = f'{user_login}@cua-gym.local'

# 1. Create organization
resp = requests.post(
    f'{GRAFANA_URL}/api/orgs',
    json={'name': org_name},
    auth=ADMIN_AUTH, timeout=15
)
assert resp.status_code == 200, f'Org creation failed: {resp.text}'
org_id = resp.json()['orgId']

# 2. Create user
resp = requests.post(
    f'{GRAFANA_URL}/api/admin/users',
    json={
        'name': f'Agent {session_id}',
        'login': user_login,
        'password': user_password,
        'email': user_email,
    },
    auth=ADMIN_AUTH, timeout=15
)
assert resp.status_code == 200, f'User creation failed: {resp.text}'
user_id = resp.json()['id']

# 3. Add user to org as Editor
resp = requests.post(
    f'{GRAFANA_URL}/api/orgs/{org_id}/users',
    json={'loginOrEmail': user_login, 'role': 'Editor'},
    auth=ADMIN_AUTH, timeout=15
)
assert resp.status_code == 200

# 4. Switch user's active org
resp = requests.post(
    f'{GRAFANA_URL}/api/users/{user_id}/using/{org_id}',
    auth=ADMIN_AUTH, timeout=15
)
assert resp.status_code == 200

# 5. Create TestData datasource in the new org
resp = requests.post(
    f'{GRAFANA_URL}/api/datasources',
    json={
        'name': 'TestData',
        'type': 'grafana-testdata-datasource',
        'access': 'proxy',
        'isDefault': True,
    },
    auth=ADMIN_AUTH,
    headers={'X-Grafana-Org-Id': str(org_id)},
    timeout=15
)
assert resp.status_code == 200
ds_uid = resp.json()['datasource']['uid']
```

### 1.2 Session Cleanup

```python
def cleanup_session(org_id, user_id):
    """Delete org and user. Order matters: org first, then user."""
    requests.delete(f'{GRAFANA_URL}/api/orgs/{org_id}', auth=ADMIN_AUTH, timeout=15)
    requests.delete(f'{GRAFANA_URL}/api/admin/users/{user_id}', auth=ADMIN_AUTH, timeout=15)
```

### 1.3 Persisting Session Info

```python
# Save session info for golden_patch.py and reward.py
session_info = {
    'grafana_url': GRAFANA_URL,
    'org_id': org_id,
    'org_name': org_name,
    'user_id': user_id,
    'user_login': user_login,
    'user_password': user_password,
    'ds_uid': ds_uid,
}
with open('/tmp/task_grafana_session', 'w') as f:
    json.dump(session_info, f)
```

---

## 2. Dashboard API

The primary setup and verification surface. Dashboards are JSON documents containing panels, variables, and layout.

### 2.1 Create Dashboard

```python
def create_dashboard(dashboard_json, org_id, folder_uid=''):
    """Create or overwrite a dashboard."""
    payload = {
        'dashboard': dashboard_json,
        'overwrite': True,
        'folderUid': folder_uid,
    }
    resp = requests.post(
        f'{GRAFANA_URL}/api/dashboards/db',
        json=payload,
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    assert resp.status_code == 200, f'Dashboard creation failed: {resp.text}'
    return resp.json()  # {'uid', 'url', 'id', 'status', 'version'}
```

### 2.2 Read Dashboard (for reward verification)

```python
def get_dashboard(uid, org_id):
    """Read back a dashboard. Returns full JSON model."""
    resp = requests.get(
        f'{GRAFANA_URL}/api/dashboards/uid/{uid}',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    assert resp.status_code == 200, f'Dashboard read failed: {resp.text}'
    result = resp.json()
    return result['dashboard'], result['meta']
    # dashboard = full JSON model (panels, templating, time, tags, etc.)
    # meta = {folderUid, folderTitle, slug, url, version, ...}
```

### 2.3 Delete Dashboard

```python
def delete_dashboard(uid, org_id):
    resp = requests.delete(
        f'{GRAFANA_URL}/api/dashboards/uid/{uid}',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.status_code == 200
```

### 2.4 List Dashboards (search)

```python
def search_dashboards(org_id, query='', tag=''):
    params = {}
    if query:
        params['query'] = query
    if tag:
        params['tag'] = tag
    resp = requests.get(
        f'{GRAFANA_URL}/api/search',
        params=params,
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()  # [{uid, title, url, tags, type, folderUid, ...}]
```

---

## 3. Controlled Data via csv_content

The TestData datasource's `csv_content` scenario embeds exact data inline in the dashboard JSON. This makes data fully deterministic and verifiable.

### 3.1 CSV Content Target

```python
def make_csv_target(ref_id, csv_data):
    """Create a panel target with exact inline data.

    csv_data: str with header row + data rows.
    First column should be 'time' for timeseries panels.
    """
    return {
        'refId': ref_id,
        'scenarioId': 'csv_content',
        'csvContent': csv_data,
    }

# Example: CPU metrics for 3 servers over 8 hours
csv = (
    "time,web-server-01,web-server-02,db-primary\n"
    "2024-01-15T00:00:00Z,25,30,45\n"
    "2024-01-15T01:00:00Z,28,32,48\n"
    "2024-01-15T02:00:00Z,35,29,52\n"
    "2024-01-15T03:00:00Z,72,31,55\n"
    "2024-01-15T04:00:00Z,95,33,90\n"  # anomaly!
    "2024-01-15T05:00:00Z,88,35,85\n"
    "2024-01-15T06:00:00Z,42,30,50\n"
    "2024-01-15T07:00:00Z,30,28,47"
)
target = make_csv_target('A', csv)
```

### 3.2 Random Walk Target (for visual richness, non-verifiable data)

```python
def make_random_walk_target(ref_id, alias, start_value=50, spread=10):
    """Random walk — produces live-updating data. NOT deterministic."""
    return {
        'refId': ref_id,
        'scenarioId': 'random_walk',
        'alias': alias,
        'seriesCount': 1,
        'startValue': start_value,
        'spread': spread,
    }
```

### 3.3 When to Use Which

| Scenario | Use Case | Verifiable? |
|----------|----------|-------------|
| `csv_content` | Task requires specific data patterns (anomalies, trends) | Yes — data is in the JSON |
| `random_walk` | Visual richness, background panels | No — data changes on each load |

---

## 4. Panel Types & Configuration

### 4.1 Supported Panel Types

| Type Key | Display Name | Typical Use |
|----------|-------------|-------------|
| `timeseries` | Time Series | Metrics over time (default) |
| `stat` | Stat | Single big number with sparkline |
| `gauge` | Gauge | Dial showing value vs threshold |
| `bargauge` | Bar Gauge | Horizontal/vertical bar |
| `table` | Table | Tabular data display |
| `barchart` | Bar Chart | Categorical comparison |
| `piechart` | Pie Chart | Proportional breakdown |
| `heatmap` | Heatmap | 2D density visualization |
| `histogram` | Histogram | Value distribution |
| `state-timeline` | State Timeline | State changes over time |
| `status-history` | Status History | Periodic state display |
| `geomap` | Geomap | Geographic data |
| `candlestick` | Candlestick | Financial data |
| `xychart` | XY Chart | Arbitrary x/y plotting |
| `canvas` | Canvas | Free-form layout |
| `text` | Text | Markdown/HTML content |
| `logs` | Logs | Log data display |
| `nodeGraph` | Node Graph | Network/graph visualization |
| `alertlist` | Alert List | Active alerts display |
| `dashlist` | Dashboard List | Dashboard links |
| `news` | News | RSS feed |

### 4.2 Panel JSON Structure

```python
def make_panel(panel_id, title, panel_type, grid_x, grid_y, grid_w, grid_h,
               targets, ds_uid, field_config=None, options=None, transformations=None):
    """Build a complete panel JSON object."""
    panel = {
        'id': panel_id,
        'title': title,
        'type': panel_type,
        'gridPos': {'x': grid_x, 'y': grid_y, 'w': grid_w, 'h': grid_h},
        'datasource': {
            'type': 'grafana-testdata-datasource',
            'uid': ds_uid,
        },
        'targets': targets,
        'fieldConfig': field_config or {
            'defaults': {},
            'overrides': [],
        },
        'options': options or {},
    }
    if transformations:
        panel['transformations'] = transformations
    return panel
```

### 4.3 Field Config — Units, Thresholds, Overrides

```python
# Standard field config with thresholds
field_config = {
    'defaults': {
        'unit': 'percent',        # bytes, ms, reqps, short, etc.
        'decimals': 1,
        'min': 0,
        'max': 100,
        'color': {'mode': 'palette-classic'},
        'custom': {
            'lineWidth': 2,
            'fillOpacity': 10,
            'stacking': {'mode': 'none'},  # 'normal' for stacked
        },
        'thresholds': {
            'mode': 'absolute',    # or 'percentage'
            'steps': [
                {'color': 'green', 'value': None},   # base (always None)
                {'color': 'yellow', 'value': 60},
                {'color': 'red', 'value': 80},
            ],
        },
        'links': [
            # data links
            {
                'title': 'View Details',
                'url': 'https://example.com/details?server=${__field.name}',
                'targetBlank': True,
            },
        ],
    },
    'overrides': [
        {
            'matcher': {'id': 'byName', 'options': 'web-server-01'},
            'properties': [
                {'id': 'color', 'value': {'fixedColor': 'red', 'mode': 'fixed'}},
                {'id': 'custom.lineWidth', 'value': 3},
            ],
        },
    ],
}
```

### 4.4 Panel Options (per visualization type)

```python
# Time series options
timeseries_options = {
    'tooltip': {'mode': 'multi'},           # 'single', 'multi', 'none'
    'legend': {
        'displayMode': 'table',             # 'list', 'table', 'hidden'
        'placement': 'bottom',              # 'bottom', 'right'
        'calcs': ['mean', 'max', 'last'],   # legend calculations
    },
}

# Stat options
stat_options = {
    'graphMode': 'area',        # 'area', 'none'
    'colorMode': 'background',  # 'none', 'value', 'background'
    'textMode': 'value',        # 'auto', 'value', 'value_and_name', 'name', 'none'
    'orientation': 'auto',      # 'auto', 'horizontal', 'vertical'
}

# Gauge options
gauge_options = {
    'showThresholdLabels': True,
    'showThresholdMarkers': True,
    'orientation': 'auto',
}

# Pie chart options
pie_options = {
    'pieType': 'pie',           # 'pie', 'donut'
    'tooltip': {'mode': 'single'},
    'legend': {'displayMode': 'list', 'placement': 'right'},
}

# Bar chart options
bar_options = {
    'orientation': 'auto',      # 'auto', 'horizontal', 'vertical'
    'stacking': 'none',         # 'none', 'normal', 'percent'
    'showValue': 'auto',        # 'auto', 'always', 'never'
    'barWidth': 0.97,
    'groupWidth': 0.7,
}

# Table options
table_options = {
    'showHeader': True,
    'footer': {'show': False},
    'cellHeight': 'sm',         # 'sm', 'md', 'lg'
}
```

### 4.5 Transformations

```python
# Organize fields (rename, reorder, hide)
transform_organize = {
    'id': 'organize',
    'options': {
        'excludeByName': {'Time': True},
        'renameByName': {'web-server-01': 'Web Server 1'},
        'indexByName': {'web-server-01': 0, 'web-server-02': 1},
    },
}

# Filter by value
transform_filter = {
    'id': 'filterByValue',
    'options': {
        'filters': [
            {
                'fieldName': 'web-server-01',
                'config': {
                    'id': 'greater',
                    'options': {'value': 50},
                },
            },
        ],
        'type': 'include',
        'match': 'any',
    },
}
```

---

## 5. Template Variables

Dashboard variables enable dynamic filtering via dropdown menus.

### 5.1 Custom Variable (static options)

```python
templating = {
    'list': [
        {
            'type': 'custom',
            'name': 'server',
            'label': 'Server',
            'query': 'web-server-01,web-server-02,web-server-03',
            'current': {'text': 'web-server-01', 'value': 'web-server-01'},
            'options': [
                {'text': 'web-server-01', 'value': 'web-server-01', 'selected': True},
                {'text': 'web-server-02', 'value': 'web-server-02', 'selected': False},
                {'text': 'web-server-03', 'value': 'web-server-03', 'selected': False},
            ],
            'multi': False,          # True for multi-select
            'includeAll': False,     # True to add "All" option
            'hide': 0,              # 0=show, 1=hide label, 2=hide entirely
        },
        {
            'type': 'interval',
            'name': 'interval',
            'label': 'Interval',
            'query': '1m,5m,15m,30m,1h',
            'current': {'text': '5m', 'value': '5m'},
            'auto': False,
            'hide': 0,
        },
    ],
}
```

---

## 6. Alerting API

### 6.1 Prerequisites

Alert rules require a folder. Always create the folder first.

```python
def create_folder(title, uid, org_id):
    resp = requests.post(
        f'{GRAFANA_URL}/api/folders',
        json={'title': title, 'uid': uid},
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    assert resp.status_code == 200, f'Folder creation failed: {resp.text}'
    return resp.json()
```

### 6.2 Create Alert Rule

```python
def create_alert_rule(title, folder_uid, ds_uid, org_id,
                      threshold=80, pending_for='5m',
                      labels=None, annotations=None):
    """Create a threshold-based alert rule."""
    rule = {
        'title': title,
        'ruleGroup': 'cua-gym-alerts',
        'folderUID': folder_uid,
        'condition': 'C',
        'data': [
            {
                'refId': 'A',
                'relativeTimeRange': {'from': 600, 'to': 0},
                'datasourceUid': ds_uid,
                'model': {
                    'scenarioId': 'random_walk',
                    'seriesCount': 1,
                    'startValue': 50,
                    'spread': 20,
                    'refId': 'A',
                },
            },
            {
                'refId': 'C',
                'relativeTimeRange': {'from': 600, 'to': 0},
                'datasourceUid': '__expr__',
                'model': {
                    'type': 'threshold',
                    'expression': 'A',
                    'conditions': [
                        {
                            'evaluator': {
                                'type': 'gt',
                                'params': [threshold],
                            },
                        },
                    ],
                    'refId': 'C',
                },
            },
        ],
        'for': pending_for,
        'noDataState': 'NoData',
        'execErrState': 'Error',
        'labels': labels or {},
        'annotations': annotations or {},
    }
    resp = requests.post(
        f'{GRAFANA_URL}/api/v1/provisioning/alert-rules',
        json=rule,
        auth=ADMIN_AUTH,
        headers={
            'X-Grafana-Org-Id': str(org_id),
            'X-Disable-Provenance': 'true',
        },
        timeout=15,
    )
    assert resp.status_code == 201, f'Alert rule creation failed: {resp.text}'
    return resp.json()  # includes 'uid'
```

### 6.3 Read Alert Rule (for reward verification)

```python
def get_alert_rule(rule_uid, org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/v1/provisioning/alert-rules/{rule_uid}',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    assert resp.status_code == 200
    return resp.json()
    # Fields: uid, title, condition, data, for, labels, annotations, isPaused, ...
```

### 6.4 List All Alert Rules

```python
def list_alert_rules(org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/v1/provisioning/alert-rules',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()  # list of alert rule objects
```

### 6.5 Delete Alert Rule

```python
def delete_alert_rule(rule_uid, org_id):
    requests.delete(
        f'{GRAFANA_URL}/api/v1/provisioning/alert-rules/{rule_uid}',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
```

---

## 7. Contact Points & Notification Policies

### 7.1 Create Contact Point

```python
def create_contact_point(name, cp_type, settings, org_id):
    """Create a contact point.

    cp_type: 'email', 'webhook', 'slack', etc.
    settings: type-specific dict (see examples below).
    """
    resp = requests.post(
        f'{GRAFANA_URL}/api/v1/provisioning/contact-points',
        json={
            'name': name,
            'type': cp_type,
            'settings': settings,
            'disableResolveMessage': False,
        },
        auth=ADMIN_AUTH,
        headers={
            'X-Grafana-Org-Id': str(org_id),
            'X-Disable-Provenance': 'true',
        },
        timeout=15,
    )
    assert resp.status_code == 202, f'Contact point creation failed: {resp.text}'
    return resp.json()

# Email settings
email_settings = {'addresses': 'oncall@example.com;alerts@example.com'}

# Webhook settings
webhook_settings = {
    'url': 'https://hooks.example.com/grafana',
    'httpMethod': 'POST',
}
```

### 7.2 Read Contact Points (for verification)

```python
def list_contact_points(org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/v1/provisioning/contact-points',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()  # list of {uid, name, type, settings, ...}
```

### 7.3 Notification Policy Tree

```python
def get_notification_policies(org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/v1/provisioning/policies',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()  # full routing tree

def update_notification_policies(policy_tree, org_id):
    """WARNING: This replaces the ENTIRE policy tree.
    Always GET first to preserve the root receiver."""
    resp = requests.put(
        f'{GRAFANA_URL}/api/v1/provisioning/policies',
        json=policy_tree,
        auth=ADMIN_AUTH,
        headers={
            'X-Grafana-Org-Id': str(org_id),
            'X-Disable-Provenance': 'true',
        },
        timeout=15,
    )
    assert resp.status_code == 202

# Example: route critical alerts to a specific contact point
policy_tree = {
    'receiver': 'grafana-default-email',  # keep existing default
    'group_by': ['alertname'],
    'routes': [
        {
            'receiver': 'oncall-webhook',
            'object_matchers': [
                ['severity', '=', 'critical'],
            ],
            'continue': False,
        },
    ],
}
```

---

## 8. Mute Timings

```python
def create_mute_timing(name, time_intervals, org_id):
    resp = requests.post(
        f'{GRAFANA_URL}/api/v1/provisioning/mute-timings',
        json={'name': name, 'time_intervals': time_intervals},
        auth=ADMIN_AUTH,
        headers={
            'X-Grafana-Org-Id': str(org_id),
            'X-Disable-Provenance': 'true',
        },
        timeout=15,
    )
    assert resp.status_code == 201
    return resp.json()

# Weekend mute
weekend_intervals = [
    {
        'weekdays': ['saturday', 'sunday'],
        'times': [{'start_time': '00:00', 'end_time': '23:59'}],
    },
]

# Maintenance window
maintenance_intervals = [
    {
        'weekdays': ['wednesday'],
        'times': [{'start_time': '02:00', 'end_time': '06:00'}],
    },
]

def list_mute_timings(org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/v1/provisioning/mute-timings',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()
```

---

## 9. Annotations

```python
def create_annotation(text, tags, org_id, dashboard_uid=None, panel_id=None,
                      time_ms=None, time_end_ms=None):
    body = {'text': text, 'tags': tags}
    if dashboard_uid:
        body['dashboardUID'] = dashboard_uid
    if panel_id:
        body['panelId'] = panel_id
    if time_ms:
        body['time'] = time_ms
    if time_end_ms:
        body['timeEnd'] = time_end_ms
    resp = requests.post(
        f'{GRAFANA_URL}/api/annotations',
        json=body,
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    assert resp.status_code == 200
    return resp.json()  # {'id', 'message'}

def query_annotations(org_id, tags=None, dashboard_uid=None):
    """Query annotations. Tags use repeated params: tags=a&tags=b."""
    params = {}
    if dashboard_uid:
        params['dashboardUID'] = dashboard_uid
    resp = requests.get(
        f'{GRAFANA_URL}/api/annotations',
        params=params,
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    results = resp.json()
    if tags:
        results = [a for a in results if set(tags).issubset(set(a.get('tags', [])))]
    return results
```

---

## 10. Folders

```python
def create_folder(title, uid, org_id, parent_uid=None):
    body = {'title': title, 'uid': uid}
    if parent_uid:
        body['parentUid'] = parent_uid
    resp = requests.post(
        f'{GRAFANA_URL}/api/folders',
        json=body,
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    assert resp.status_code == 200, f'Folder creation failed: {resp.text}'
    return resp.json()

def get_folder(uid, org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/folders/{uid}',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()

def set_folder_permissions(uid, org_id, items):
    """WARNING: This replaces ALL permissions.
    Always include admin user: {'userId': 1, 'permission': 4}
    or you lose access to the folder."""
    resp = requests.post(
        f'{GRAFANA_URL}/api/folders/{uid}/permissions',
        json={'items': items},
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()

def get_folder_permissions(uid, org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/folders/{uid}/permissions',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()
```

---

## 11. Playlists

```python
def create_playlist(title, interval, dashboard_uids, org_id):
    items = [
        {'type': 'dashboard_by_uid', 'value': uid}
        for uid in dashboard_uids
    ]
    resp = requests.post(
        f'{GRAFANA_URL}/api/playlists',
        json={'name': title, 'interval': interval, 'items': items},
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    assert resp.status_code == 200
    return resp.json()

def get_playlist(uid, org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/playlists/{uid}',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()
```

---

## 12. Snapshots

```python
def create_snapshot(dashboard_json, name, org_id, expires=3600):
    resp = requests.post(
        f'{GRAFANA_URL}/api/snapshots',
        json={
            'dashboard': dashboard_json,
            'name': name,
            'expires': expires,
        },
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    assert resp.status_code == 200
    return resp.json()  # {'key', 'deleteKey', 'url'}

def get_snapshot(key, org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/snapshots/{key}',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()  # includes full 'dashboard' JSON
```

---

## 13. Library Panels

```python
def create_library_panel(name, model, org_id, folder_uid=''):
    resp = requests.post(
        f'{GRAFANA_URL}/api/library-elements',
        json={
            'name': name,
            'kind': 1,  # 1 = panel
            'model': model,
            'folderUid': folder_uid,
        },
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    assert resp.status_code == 200
    return resp.json()['result']  # includes 'uid'

def get_library_panel(uid, org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/library-elements/{uid}',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()['result']

def get_library_panel_connections(uid, org_id):
    """Check which dashboards use this library panel."""
    resp = requests.get(
        f'{GRAFANA_URL}/api/library-elements/{uid}/connections/',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()['result']
```

---

## 14. Dashboard Version History

```python
def get_dashboard_versions(uid, org_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/dashboards/uid/{uid}/versions',
        auth=ADMIN_AUTH,
        headers={'X-Grafana-Org-Id': str(org_id)},
        timeout=15,
    )
    return resp.json()['versions']  # list of {id, version, message, created, data, ...}
```

---

## 15. User & Team Management

These APIs are for tasks where the CUA agent is expected to manage users/teams in the Grafana UI.

```python
def create_team(name, email, org_id):
    # Admin must be in the target org to create a team
    requests.post(
        f'{GRAFANA_URL}/api/user/using/{org_id}',
        auth=ADMIN_AUTH, timeout=15,
    )
    resp = requests.post(
        f'{GRAFANA_URL}/api/teams',
        json={'name': name, 'email': email},
        auth=ADMIN_AUTH, timeout=15,
    )
    assert resp.status_code == 200
    return resp.json()  # {'teamId', 'message'}

def get_team(team_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/teams/{team_id}',
        auth=ADMIN_AUTH, timeout=15,
    )
    return resp.json()

def add_team_member(team_id, user_id):
    resp = requests.post(
        f'{GRAFANA_URL}/api/teams/{team_id}/members',
        json={'userId': user_id},
        auth=ADMIN_AUTH, timeout=15,
    )
    return resp.json()

def get_team_members(team_id):
    resp = requests.get(
        f'{GRAFANA_URL}/api/teams/{team_id}/members',
        auth=ADMIN_AUTH, timeout=15,
    )
    return resp.json()

def set_org_preferences(org_id, theme=None, timezone=None, home_dashboard_uid=None):
    """Set org preferences. Must switch admin to target org first."""
    requests.post(
        f'{GRAFANA_URL}/api/user/using/{org_id}',
        auth=ADMIN_AUTH, timeout=15,
    )
    prefs = {}
    if theme:
        prefs['theme'] = theme
    if timezone:
        prefs['timezone'] = timezone
    if home_dashboard_uid:
        prefs['homeDashboardUID'] = home_dashboard_uid
    resp = requests.patch(
        f'{GRAFANA_URL}/api/org/preferences',
        json=prefs,
        auth=ADMIN_AUTH, timeout=15,
    )
    return resp.json()

def get_org_preferences(org_id):
    requests.post(
        f'{GRAFANA_URL}/api/user/using/{org_id}',
        auth=ADMIN_AUTH, timeout=15,
    )
    resp = requests.get(
        f'{GRAFANA_URL}/api/org/preferences',
        auth=ADMIN_AUTH, timeout=15,
    )
    return resp.json()
```

---

## 16. initial_setup.py Template

```python
"""
Initial Setup: <task_description>
Task ID: <task_id>
Domain: grafana
"""
import json
import os
import shlex
import subprocess
import time
import uuid

import requests

# --- Config ---
GRAFANA_URL = 'https://cua-gym-grafana.xlang.ai'
ADMIN_AUTH = ('admin', 'cua-gym-admin-2024')
session_id = str(uuid.uuid4())[:8]

# --- Create isolated session ---
org_name = f'session_{session_id}'
user_login = f'agent_{session_id}'
user_password = f'agent_pass_{session_id}'

# Create org
resp = requests.post(f'{GRAFANA_URL}/api/orgs', json={'name': org_name},
                     auth=ADMIN_AUTH, timeout=15)
assert resp.status_code == 200
org_id = resp.json()['orgId']

# Create user
resp = requests.post(f'{GRAFANA_URL}/api/admin/users', json={
    'name': f'Agent {session_id}', 'login': user_login,
    'password': user_password, 'email': f'{user_login}@cua-gym.local',
}, auth=ADMIN_AUTH, timeout=15)
assert resp.status_code == 200
user_id = resp.json()['id']

# Add user to org + switch
requests.post(f'{GRAFANA_URL}/api/orgs/{org_id}/users',
              json={'loginOrEmail': user_login, 'role': 'Editor'},
              auth=ADMIN_AUTH, timeout=15)
requests.post(f'{GRAFANA_URL}/api/users/{user_id}/using/{org_id}',
              auth=ADMIN_AUTH, timeout=15)

# Create TestData datasource
resp = requests.post(f'{GRAFANA_URL}/api/datasources', json={
    'name': 'TestData', 'type': 'grafana-testdata-datasource',
    'access': 'proxy', 'isDefault': True,
}, auth=ADMIN_AUTH, headers={'X-Grafana-Org-Id': str(org_id)}, timeout=15)
assert resp.status_code == 200
ds_uid = resp.json()['datasource']['uid']

# --- Build dashboard ---
dashboard = {
    'uid': f'dash-{session_id}',
    'title': 'Production API Monitoring',
    'tags': ['production', 'api'],
    'time': {'from': '2024-01-15T00:00:00Z', 'to': '2024-01-15T08:00:00Z'},
    'refresh': '',
    'panels': [
        # ... build panels using make_panel() / make_csv_target() ...
    ],
    'templating': {'list': []},
}

# Inject dashboard
resp = requests.post(f'{GRAFANA_URL}/api/dashboards/db', json={
    'dashboard': dashboard, 'overwrite': True,
}, auth=ADMIN_AUTH, headers={'X-Grafana-Org-Id': str(org_id)}, timeout=15)
assert resp.status_code == 200
print(f'Dashboard created: {resp.json()["url"]}')

# --- Persist session info ---
session_info = {
    'grafana_url': GRAFANA_URL,
    'org_id': org_id, 'org_name': org_name,
    'user_id': user_id, 'user_login': user_login,
    'user_password': user_password,
    'ds_uid': ds_uid,
    'dashboard_uid': f'dash-{session_id}',
}
with open('/tmp/task_grafana_session', 'w') as f:
    json.dump(session_info, f)

# --- Launch browser ---
def launch_gui(command, delay_sec=1.0):
    env = os.environ.copy()
    env['DISPLAY'] = ':0'
    subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
    )
    time.sleep(delay_sec)

# Login URL with org context
login_url = f'{GRAFANA_URL}/login'
launch_gui(f'google-chrome "{login_url}"', delay_sec=2.0)
print(f'GUI_READY: launched browser at {login_url}')
print(f'Login: {user_login} / {user_password}')
```

---

## 17. golden_patch.py Template

```python
"""
Golden Patch: <task_description>
Task ID: <task_id>
Domain: grafana
Changes: <brief list of what this patch does>
"""
import copy
import json

import requests

# --- Load session ---
with open('/tmp/task_grafana_session') as f:
    session = json.load(f)

GRAFANA_URL = session['grafana_url']
ADMIN_AUTH = ('admin', 'cua-gym-admin-2024')
org_id = session['org_id']
headers = {'X-Grafana-Org-Id': str(org_id)}

# --- Read current state ---
resp = requests.get(
    f'{GRAFANA_URL}/api/dashboards/uid/{session["dashboard_uid"]}',
    auth=ADMIN_AUTH, headers=headers, timeout=15,
)
dashboard = resp.json()['dashboard']

# --- Apply golden changes ---
# Example: change panel title
# dashboard['panels'][0]['title'] = 'Updated Panel Title'

# Example: add a threshold
# dashboard['panels'][0]['fieldConfig']['defaults']['thresholds'] = {
#     'mode': 'absolute',
#     'steps': [
#         {'color': 'green', 'value': None},
#         {'color': 'red', 'value': 90},
#     ],
# }

# --- Save updated dashboard ---
resp = requests.post(f'{GRAFANA_URL}/api/dashboards/db', json={
    'dashboard': dashboard, 'overwrite': True,
}, auth=ADMIN_AUTH, headers=headers, timeout=15)
assert resp.status_code == 200
print('Golden state applied')
```

---

## 18. reward.py Template

```python
"""
Reward: <task_description>
Task ID: <task_id>
Domain: grafana
"""
import json
import sys

import requests

# --- Load session ---
with open('/tmp/task_grafana_session') as f:
    session = json.load(f)

GRAFANA_URL = session['grafana_url']
ADMIN_AUTH = ('admin', 'cua-gym-admin-2024')
org_id = session['org_id']
headers = {'X-Grafana-Org-Id': str(org_id)}

score = 0.0
checks_passed = 0
total_checks = 0

def check(name, condition, weight=1.0):
    global score, checks_passed, total_checks
    total_checks += 1
    if condition:
        checks_passed += 1
        score += weight
        print(f'  PASS: {name}')
    else:
        print(f'  FAIL: {name}')

# --- Read current state ---
resp = requests.get(
    f'{GRAFANA_URL}/api/dashboards/uid/{session["dashboard_uid"]}',
    auth=ADMIN_AUTH, headers=headers, timeout=15,
)
if resp.status_code != 200:
    print(f'Dashboard not found: {resp.status_code}')
    print(f'reward: 0.0')
    sys.exit(0)

dashboard = resp.json()['dashboard']
meta = resp.json()['meta']

# --- Verification checks ---
# Example: verify panel title was changed
# check('Panel title updated',
#        dashboard['panels'][0]['title'] == 'Updated Panel Title')

# Example: verify threshold was added
# thresholds = dashboard['panels'][0].get('fieldConfig', {}).get('defaults', {}).get('thresholds', {})
# steps = thresholds.get('steps', [])
# check('Threshold has 2 steps', len(steps) == 2)
# check('Red threshold at 90', any(s.get('value') == 90 and s.get('color') == 'red' for s in steps))

# --- Final score ---
final_score = score / total_checks if total_checks > 0 else 0.0
print(f'\nChecks: {checks_passed}/{total_checks}')
print(f'reward: {final_score:.2f}')

# --- Cleanup ---
try:
    requests.delete(f'{GRAFANA_URL}/api/orgs/{org_id}', auth=ADMIN_AUTH, timeout=15)
    requests.delete(f'{GRAFANA_URL}/api/admin/users/{session["user_id"]}',
                    auth=ADMIN_AUTH, timeout=15)
    print('Session cleaned up')
except Exception:
    pass
```

---

## 19. Task Design Space

### Category 1: Dashboard Editing

| Difficulty | Task | Setup State | Reward Check |
|-----------|------|-------------|--------------|
| Easy | Rename panel title | Panel with old title | `panels[i].title == new_title` |
| Easy | Change time range to "Last 24h" | Dashboard with default time | `time.from == 'now-24h'` |
| Easy | Add a tag to the dashboard | Dashboard without tag | `tag in dashboard.tags` |
| Easy | Change refresh interval to 30s | Dashboard with no refresh | `refresh == '30s'` |
| Medium | Change panel type (timeseries → gauge) | Timeseries panel | `panels[i].type == 'gauge'` |
| Medium | Rearrange panel layout | Panels at positions A | `panels[i].gridPos == expected` |
| Medium | Add threshold (green<60, red>=80) | Panel without thresholds | Check `thresholds.steps` |
| Medium | Configure legend as table with calcs | Default legend | Check `options.legend` |
| Hard | Add field override (color per series) | Multi-series panel | Check `fieldConfig.overrides` |
| Hard | Add data link to panel | Panel without links | Check `fieldConfig.defaults.links` |
| Hard | Add transformation (organize fields) | Panel with raw data | Check `transformations` array |

### Category 2: Template Variables

| Difficulty | Task | Setup State | Reward Check |
|-----------|------|-------------|--------------|
| Medium | Create custom variable with options | No variables | Check `templating.list` |
| Medium | Enable multi-select on variable | Single-select variable | `variable.multi == True` |
| Hard | Create interval variable | No variables | Check type + query |

### Category 3: Alerting

| Difficulty | Task | Setup State | Reward Check |
|-----------|------|-------------|--------------|
| Easy | Pause an alert rule | Active alert rule | `isPaused == True` |
| Medium | Create threshold alert (CPU > 80%) | Dashboard + folder | Check rule condition |
| Medium | Change alert threshold 80→90 | Rule with threshold=80 | Check evaluator.params |
| Medium | Add alert label (severity: critical) | Rule without labels | Check labels dict |
| Hard | Create notification policy route | Contact points exist | Check policy tree |
| Hard | Create mute timing (weekends) | No mute timings | Check time_intervals |

### Category 4: Contact Points

| Difficulty | Task | Setup State | Reward Check |
|-----------|------|-------------|--------------|
| Medium | Create email contact point | None | Check type + addresses |
| Medium | Create webhook contact point | None | Check type + url |
| Hard | Configure notification routing | Multiple CPs | Check policy routes |

### Category 5: Organization & Folders

| Difficulty | Task | Setup State | Reward Check |
|-----------|------|-------------|--------------|
| Easy | Create folder | None | Check folder title/uid |
| Easy | Move dashboard to folder | Dashboard in root | Check `meta.folderUid` |
| Medium | Create nested folder structure | None | Check parentUid |
| Medium | Set folder permissions | Folder exists | Check permissions list |
| Medium | Create playlist of 3 dashboards | 3 dashboards | Check playlist items |

### Category 6: User & Team Admin

| Difficulty | Task | Setup State | Reward Check |
|-----------|------|-------------|--------------|
| Easy | Create new user | None | Check user exists |
| Medium | Create team and add member | Users exist | Check team members |
| Medium | Change user role in org | User in org | Check role field |
| Medium | Set org dark theme | Default preferences | Check theme preference |

---

## 20. Bitter Lessons

1. **`X-Grafana-Org-Id` header is essential.** Without it, all operations go to org 1 (Main Org). Always include it when operating on session orgs.

2. **`X-Disable-Provenance: true` for alerting resources.** Without this header, resources created via API get a provenance lock and cannot be modified in the UI — defeating the purpose of training tasks.

3. **Notification policy PUT replaces the entire tree.** Always GET first to read the current root `receiver`, then build the new tree on top. Otherwise you break the default routing.

4. **Folder permissions POST replaces ALL permissions.** Always include `{'userId': 1, 'permission': 4}` (admin) in the items array, or you'll lock yourself out.

5. **`for` field format inconsistency.** Creating with `"5m"` may read back as `"5m0s"`. Reward verification should normalize: `for_value.replace('0s', '') == '5m'`.

6. **Alert rules require a folder first.** Create folder → create alert rule. Never try to create an alert rule without a valid `folderUID`.

7. **Annotation tag filtering uses repeated params.** Not `tags=a,b` but `tags=a&tags=b`. In Python requests: `params=[('tags', 'a'), ('tags', 'b')]`.

8. **Org preferences need context switch.** Use `/api/org/preferences` (current org), NOT `/api/orgs/:id/preferences` (returns 404). Admin must switch to target org first via `POST /api/user/using/{org_id}`.

9. **Dashboard save requires `overwrite: true` for updates.** Without it, updating an existing dashboard UID returns 412 Precondition Failed.

10. **TestData datasource type is `grafana-testdata-datasource`.** Not `testdata`. When verifying, match on substring `testdata`.

11. **Cleanup order matters.** Delete org first, then user. Deleting user first leaves orphaned org memberships.

12. **csv_content is the key to verifiable data.** For any task that involves reading or interpreting data (find anomaly, compare trends), always use `csv_content` so reward scripts can verify the data was actually present and correct.

13. **Session info goes to `/tmp/task_grafana_session`.** This file links initial_setup.py, golden_patch.py, and reward.py to the same Grafana session (org_id, user credentials, dashboard UIDs, etc.).
