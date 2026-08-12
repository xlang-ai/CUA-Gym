# jira_mock Schema

**Deploy order**: 29 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8029)
**Base URL**: `http://172.17.46.46:8029/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Merge**: `POST /post?sid=<sid>` with body `{"action":"set","merge":true,"state":{...}}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `users` | `User[]` | All team members. Default: u1 (Admin), u2 (Jane), u3 (John), u4 (Sarah) |
| `projects` | `Project[]` | Projects. Default: p1 (KAN / Kanban Project), p2 (SCRUM / Scrum Alpha) |
| `issues` | `Issue[]` | All issues (Stories, Tasks, Bugs, Epics). 25 defaults (i1–i25) |
| `sprints` | `Sprint[]` | Sprints. Default: s1 (active), s2 (future), s3 (closed) |
| `comments` | `Comment[]` | Issue comments. 18 defaults (c1–c18) |
| `workflows` | `Workflow[]` | Status transition rules. Default: w1 (Software Workflow) |
| `notifications` | `Notification[]` | Per-user notifications. 8 defaults (n1–n8; n1–n3 unread) |
| `currentUser` | `User` | Logged-in user object. Default: u1 (Admin User) |

### User fields
`{ id, name, email, avatar }`

### Project fields
`{ id, key, name, leadId, category, icon }`

### Issue fields
`{ id, key, projectId, summary, description, type, status, priority, storyPoints, reporterId, assigneeId, sprintId, epicId, createdAt, updatedAt, labels[], subtasks[], linkedIssueIds[] }`
- `type`: `"Story" | "Task" | "Bug" | "Epic"`
- `status`: `"To Do" | "In Progress" | "In Review" | "Done"`
- `priority`: `"Highest" | "High" | "Medium" | "Low" | "Lowest"`
- `subtask`: `{ id, title, completed }`

### Sprint fields
`{ id, projectId, name, goal, startDate, endDate, state }` — `state`: `"active" | "future" | "closed"`

### Comment fields
`{ id, issueId, userId, content, createdAt }`

### Notification fields
`{ id, type, issueId, actorId, message, read, createdAt }` — `type`: `"comment" | "status_change" | "assignment" | "mention"`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8029/",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {"id": "u1", "name": "Admin User", "email": "admin@example.com", "avatar": "https://picsum.photos/100/100?random=u1"},
        "users": [
          {"id": "u1", "name": "Admin User", "email": "admin@example.com", "avatar": "https://picsum.photos/100/100?random=u1"},
          {"id": "u2", "name": "Jane Doe", "email": "jane@example.com", "avatar": "https://picsum.photos/100/100?random=u2"}
        ],
        "projects": [
          {"id": "p1", "key": "KAN", "name": "Kanban Project", "leadId": "u1", "category": "Software", "icon": "https://picsum.photos/64/64?random=p1"}
        ],
        "sprints": [
          {"id": "s1", "projectId": "p1", "name": "Sprint 1", "goal": "Setup core infrastructure", "startDate": "2026-02-23T12:00:00.000Z", "endDate": "2026-03-09T12:00:00.000Z", "state": "active"}
        ],
        "issues": [
          {"id": "i1", "key": "KAN-1", "projectId": "p1", "summary": "Set up CI/CD pipeline", "description": "", "type": "Story", "status": "To Do", "priority": "High", "storyPoints": 5, "reporterId": "u1", "assigneeId": "u2", "sprintId": "s1", "epicId": null, "labels": [], "subtasks": [], "linkedIssueIds": [], "createdAt": "2026-02-28T12:00:00.000Z", "updatedAt": "2026-02-28T12:00:00.000Z"}
        ],
        "comments": [],
        "workflows": [{"id": "w1", "name": "Software Workflow", "transitions": [{"from": "To Do", "to": ["In Progress"]}, {"from": "In Progress", "to": ["In Review", "To Do", "Done"]}, {"from": "In Review", "to": ["Done", "In Progress"]}, {"from": "Done", "to": ["In Progress", "To Do"]}]}],
        "notifications": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Change issue status (e.g., To Do → In Progress) | `issues[*].status`, `issues[*].updatedAt` |
| Assign issue to user | `issues[*].assigneeId`, `issues[*].updatedAt` |
| Change issue priority | `issues[*].priority`, `issues[*].updatedAt` |
| Add/edit comment | `comments` (new entry added or content changed) |
| Mark subtask complete | `issues[*].subtasks[*].completed` |
| Mark notification as read | `notifications[*].read` |
| Update issue summary/description | `issues[*].summary`, `issues[*].description`, `issues[*].updatedAt` |
| Move issue to sprint (or backlog) | `issues[*].sprintId` |
| Create new issue | `issues` (new entry appended) |
| Update sprint (name/goal/dates/state) | `sprints[*].*` |
