# github_mock Schema

**Deploy order**: 15 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8015)
**Base URL**: `http://172.17.46.46:8015/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}` (optionally add `"merge":true`)
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State inspect**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Logged-in user: `{id, username, name, email, avatar, bio, location, company, website, joinedAt}` |
| `users` | array | All users with same fields as `currentUser` |
| `repos` | array | Repositories: `{id, ownerId, name, description, language, languages{}, stars, forks, watchers, isPrivate, defaultBranch, topics[], license, homepage, hasWiki, hasIssues, hasProjects, updatedAt, createdAt}` |
| `branches` | array | `{id, repoId, name, lastCommitId}` |
| `files` | array | `{id, repoId, branch, path, content, language}` |
| `commits` | array | `{id, repoId, branch, message, authorId, date, additions, deletions}` |
| `issues` | array | `{id, repoId, number, title, description, status("open"\|"closed"), authorId, assignees[], labels[], milestone, column("todo"\|"inprogress"\|"done"), isPinned, reactions{}, createdAt, closedAt, comments[{id,authorId,content,date,reactions{}}]}` |
| `pullRequests` | array | `{id, repoId, number, title, description, baseBranch, compareBranch, status, isDraft, authorId, assignees[], labels[], milestone, mergeStrategy, mergedAt, mergedBy, createdAt, closedAt, comments[], reviewers[{userId,status,date,body}], checks[{name,status,detail}]}` |
| `wiki` | array | `{id, repoId, title, content, createdAt, updatedAt}` |
| `actions` | array | CI runs: `{id, repoId, name, status, runNumber, branch, event, duration, date, triggeredBy}` |
| `notifications` | array | `{id, type, repoId, issueNumber, title, isRead, date}` |
| `labels` | array | `{id, repoId, name, color, description}` |
| `milestones` | array | `{id, repoId, title, description, dueDate, state, createdAt}` |
| `discussions` | array | `{id, repoId, title, body, category, authorId, replies[], createdAt}` |
| `releases` | array | `{id, repoId, tag, title, body, authorId, date, isDraft, assets[]}` |

Default data: 3 repos (r1=hello-world, r2=spoon-knife, r3=private-notes), 5 users, 5 issues, 2 PRs, 3 wiki pages, 5 action runs.

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8015/?sid=task001",
    "inject_state": true,
    "state_content": {"action": "set", "state": {
      "currentUser": {"id": "u1", "username": "octocat", "name": "The Octocat", "email": "octocat@github.com", "avatar": "https://avatars.githubusercontent.com/u/583231?v=4"},
      "repos": [{"id": "r1", "ownerId": "u1", "name": "hello-world", "description": "A sample repo", "language": "JavaScript", "stars": 0, "forks": 0, "watchers": 1, "isPrivate": false, "defaultBranch": "main"}],
      "issues": [{"id": "i1", "repoId": "r1", "number": 1, "title": "Test issue", "status": "open", "authorId": "u1", "assignees": [], "labels": [], "column": "todo", "comments": []}],
      "pullRequests": [],
      "wiki": [],
      "branches": [{"id": "b1", "repoId": "r1", "name": "main", "lastCommitId": "abc123"}],
      "files": [], "commits": [], "actions": [], "notifications": [], "labels": [], "milestones": [], "discussions": [], "releases": [], "users": []
    }}
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|-------------------|
| Star/unstar repo | `repos[i].stars` incremented/decremented |
| Watch repo | `repos[i].watchers` changes |
| Fork repo | `repos[i].forks` incremented |
| Create issue | `issues` array gains new entry with `status:"open"` |
| Close/reopen issue | `issues[i].status` → `"closed"` / `"open"`, `closedAt` set/cleared |
| Add issue comment | `issues[i].comments` array gains new entry |
| Edit issue title/description | `issues[i].title`, `issues[i].description` updated |
| Change issue assignees/labels | `issues[i].assignees[]`, `issues[i].labels[]` updated |
| Move issue on project board | `issues[i].column` changes (`"todo"`, `"inprogress"`, `"done"`) |
| Create pull request | `pullRequests` array gains new entry |
| Merge PR | `pullRequests[i].status` → `"merged"`, `mergedAt` set, `mergedBy` set |
| Close/reopen PR | `pullRequests[i].status` → `"closed"` / `"open"` |
| Add PR comment | `pullRequests[i].comments` gains new entry |
| Update repo settings | `repos[i].name`, `repos[i].description`, `repos[i].isPrivate` updated |
| Delete repo | `repos` array loses entry; associated `issues`, `pullRequests`, `branches`, `files`, `commits` removed |
| Create/edit wiki page | `wiki` array gains/updates entry with new `title`, `content`, `updatedAt` |
