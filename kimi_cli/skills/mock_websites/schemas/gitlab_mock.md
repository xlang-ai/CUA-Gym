# gitlab_mock Schema

**Deploy order**: 17 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8017)
**Base URL**: `http://172.17.46.46:8017/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State check**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## Routes

| Path | Component |
|------|-----------|
| `/` | Dashboard (project list) |
| `/projects/:projectId` | ProjectOverview |
| `/projects/:projectId/pipelines` | Pipelines |
| `/projects/:projectId/pipelines/:pipelineId` | PipelineDetail |
| `/projects/:projectId/merge_requests` | MergeRequests |
| `/projects/:projectId/merge_requests/new` | CreateMergeRequest |
| `/projects/:projectId/merge_requests/:mrId` | MergeRequestDetail |
| `/projects/:projectId/issues` | Issues |
| `/projects/:projectId/wiki` | Wiki |
| `/projects/:projectId/registry` | Registry |
| `/projects/:projectId/security` | Security |
| `/projects/:projectId/analytics` | Analytics |
| `/projects/:projectId/milestones` | Milestones |
| `/projects/:projectId/releases` | Releases |
| `/snippets` | Snippets |
| `/go` | State inspector (UI) |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Logged-in user: `{id, name, username, avatarUrl}` |
| `projects` | array | Projects: `{id, name, description, visibility, stars, forks, updatedAt, branches[], files[]}` |
| `pipelines` | array | CI pipelines: `{id, projectId, status, branch, commit, message, duration, createdAt, stages[]}` |
| `issues` | array | Issues: `{id, projectId, title, description, status, labels[], assignee}` |
| `mergeRequests` | array | MRs: `{id, projectId, title, sourceBranch, targetBranch, status, author, createdAt, reviewers[]}` |
| `registry` | array | Container registry images: `{id, projectId, name, tags[], size, updatedAt}` |
| `snippets` | array | Code snippets: `{id, title, code, language, author}` |
| `wiki` | array | Wiki pages: `{id, projectId, title, content}` |
| `vulnerabilities` | array | Security findings: `{id, projectId, severity, name, status}` |
| `milestones` | array | Milestones: `{id, projectId, title, dueDate, progress}` |
| `releases` | array | Releases: `{id, projectId, tagName, name, description, createdAt, author}` |

### Key sub-field values

- `projects[].visibility`: `"private"` | `"internal"` | `"public"`
- `pipelines[].status`: `"success"` | `"failed"` | `"running"` | `"pending"`
- `issues[].status`: `"open"` | `"closed"` | `"in_progress"`
- `mergeRequests[].status`: `"open"` | `"merged"` | `"closed"`
- `vulnerabilities[].severity`: `"critical"` | `"medium"` | `"low"`
- `vulnerabilities[].status`: `"detected"` | `"resolved"`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8017/",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {"id": 1, "name": "Admin User", "username": "admin", "avatarUrl": ""},
        "projects": [
          {"id": 1, "name": "frontend-monorepo", "description": "Main repo", "visibility": "private", "stars": 0, "forks": 0, "updatedAt": "2026-01-01T00:00:00.000Z", "branches": ["main"], "files": []}
        ],
        "pipelines": [],
        "issues": [],
        "mergeRequests": [],
        "registry": [],
        "snippets": [],
        "wiki": [],
        "vulnerabilities": [],
        "milestones": [],
        "releases": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State field(s) that change |
|-------------|---------------------------|
| Create issue | `issues` array gains new entry; `issues[].id`, `title`, `status`, `labels` |
| Close/reopen issue | `issues[n].status` changes to `"closed"` or `"open"` |
| Create merge request | `mergeRequests` array gains new entry |
| Merge / close MR | `mergeRequests[n].status` changes to `"merged"` or `"closed"` |
| Retry/cancel pipeline | `pipelines[n].status` changes |
| Create wiki page | `wiki` array gains new entry with `title` and `content` |
| Edit wiki page | `wiki[n].content` changes |
| Create snippet | `snippets` array gains new entry |
| Create release | `releases` array gains new entry with `tagName` and `name` |
| Create milestone | `milestones` array gains new entry |
| Star project | `projects[n].stars` increments |
| Mark vulnerability resolved | `vulnerabilities[n].status` changes to `"resolved"` |
