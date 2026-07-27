# asana_mock Schema

**Deploy order**: 3 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8002)
**Base URL**: `http://172.17.46.46:8002/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}` or `{"action":"set","merge":true,"state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State check**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | `User` | Logged-in user (default: `user-0`, Alex Johnson) |
| `users` | `User[]` | All users (default 6: user-0 through user-5) |
| `teams` | `Team[]` | Teams (default 3: team-1, team-2, team-3) |
| `projects` | `Project[]` | Projects with sections and custom fields (default 4) |
| `tasks` | `Task[]` | Tasks belonging to projects/sections |
| `comments` | `Comment[]` | Task comments |
| `portfolios` | `Portfolio[]` | Portfolio groupings of projects |
| `goals` | `Goal[]` | Organizational goals with progress tracking |
| `notifications` | `Notification[]` | User inbox notifications |
| `attachments` | `Attachment[]` | File attachments on tasks |

### User fields
`userId`, `name`, `email`, `avatar`, `title`, `department`, `location`, `timezone`, `theme` (`light`|`dark`|`auto`)

### Team fields
`teamId`, `name`, `description`, `memberIds[]`, `ownerId`, `privacy` (`public`|`private`), `createdDate`

### Project fields
`projectId`, `name`, `teamId`, `description`, `color`, `icon`, `ownerId`, `memberIds[]`, `sections[]` (each: `sectionId`, `name`, `collapsed`), `customFields[]`, `privacy`, `startDate`, `dueDate`, `archived`, `starred`, `createdDate`, `modifiedDate`

### Task fields
`taskId`, `name`, `projectId`, `sectionId`, `description`, `assigneeId`, `creatorId`, `dueDate`, `startDate`, `completed`, `completedDate`, `parentTaskId`, `dependencies[]`, `tags[]`, `attachmentIds[]`, `customFieldValues{}`, `likeCount`, `createdDate`, `modifiedDate`

### Goal fields
`goalId`, `name`, `description`, `ownerId`, `timePeriod`, `progress` (0-100), `status` (`on-track`|`at-risk`|`off-track`), `parentGoalId`, `supportingProjectIds[]`, `metrics[]`

### Notification fields
`notificationId`, `userId`, `type` (`task-assigned`|`task-completed`|`task-due-soon`|`comment`|`mention`|`project-invite`|`status-update`), `actorId`, `targetId`, `targetType` (`task`|`project`|`comment`), `read`, `archived`, `createdDate`

## Default IDs (reference)

- Users: `user-0` (Alex Johnson, PM), `user-1` (Sarah Chen, Designer), `user-2` (Mike Rodriguez, Engineer), `user-3` (Emily Watson, Marketing), `user-4` (David Kim, Engineer), `user-5` (Lisa Anderson, Designer)
- Teams: `team-1` (Product), `team-2` (Engineering), `team-3` (Marketing)
- Projects: `project-1` (Q1 Product Launch, sections: `section-1-1/2/3`), `project-2` (Website Redesign, sections: `section-2-1/2/3/4`), `project-3` (Marketing Campaign Q1), `project-4` (Mobile App Development)

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8002/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "userId": "user-0",
          "name": "Alex Johnson",
          "email": "alex.johnson@company.com",
          "avatar": "https://picsum.photos/100/100?random=user0",
          "title": "Product Manager",
          "department": "Product",
          "location": "San Francisco, CA",
          "timezone": "PST",
          "theme": "light"
        },
        "tasks": [
          {
            "taskId": "task-inject-1",
            "name": "Write Q1 report",
            "projectId": "project-1",
            "sectionId": "section-1-1",
            "description": "",
            "creatorId": "user-0",
            "completed": false,
            "dependencies": [],
            "tags": [],
            "attachmentIds": [],
            "customFieldValues": {},
            "likeCount": 0,
            "createdDate": "2026-01-01T00:00:00Z",
            "modifiedDate": "2026-01-01T00:00:00Z"
          }
        ]
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Change |
|-------------|-------------|
| Create task | New entry added to `tasks[]` with matching `projectId`/`sectionId` |
| Complete task | `tasks[i].completed = true`, `tasks[i].completedDate` set |
| Create project | New entry added to `projects[]` |
| Archive project | `projects[i].archived = true` |
| Star/unstar project | `projects[i].starred` toggled |
| Add comment | New entry added to `comments[]` with `taskId` |
| Mark notification read | `notifications[i].read = true` |
| Archive notification | `notifications[i].archived = true` |
| Create goal | New entry added to `goals[]` |
| Update goal progress | `goals[i].progress` changes (0-100) |
| Create portfolio | New entry added to `portfolios[]` |
| Update user settings | `currentUser.theme` / `currentUser.timezone` / etc. changes |
| Move task to section | `tasks[i].sectionId` changes |
| Assign task | `tasks[i].assigneeId` set to a userId |
