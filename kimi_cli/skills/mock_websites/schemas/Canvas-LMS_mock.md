# Canvas-LMS_mock Schema

**Deploy order**: 7 (BASE_PORT=8000 → port 8007)
**Base URL**: `http://172.17.46.46:8007/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State read**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | object | Active user; `{id, name, short_name, sortable_name, email, avatar_url, role, pronouns, bio, last_login}` |
| `users` | array | All users (teachers, students, TAs); each: `{id, name, short_name, sortable_name, email, avatar_url, role, pronouns, bio}` |
| `courses` | array | All courses; each: `{id, name, course_code, term, workflow_state, start_at, end_at, color, default_view, syllabus_body, total_students, image_url}` |
| `enrollments` | array | Course enrollments; each: `{id, user_id, course_id, type, enrollment_state, course_section_id, created_at}` |
| `assignmentGroups` | array | Assignment groupings per course; each: `{id, course_id, name, weight, position}` |
| `assignments` | array | All assignments across courses; each: `{id, course_id, assignment_group_id, name, description, due_at, points_possible, grading_type, submission_types[], published, position, needs_grading_count, allowed_extensions[], workflow_state}` |
| `submissions` | array | Student submissions; each: `{id, assignment_id, user_id, score, grade, submitted_at, graded_at, workflow_state, submission_type, late, missing, excused, attempt, body}` |
| `modules` | array | Course modules; each: `{id, course_id, name, position, published, items_count, state}` |
| `moduleItems` | array | Items within modules; each: `{id, module_id, title, type, content_id, position, indent, published, external_url?}` |
| `announcements` | array | Course announcements; each: `{id, course_id, title, message, author_id, posted_at, read_state, published}` |
| `announcementReplies` | array | Replies to announcements (dynamically created); each: `{id, announcement_id, user_id, message, created_at}` |
| `discussionTopics` | array | Discussion topics; each: `{id, course_id, title, message, author_id, posted_at, last_reply_at, discussion_type, published, pinned, locked, allow_rating, require_initial_post, read_state, unread_count, discussion_subentry_count, assignment_id}` |
| `discussionEntries` | array | Discussion replies; each: `{id, discussion_topic_id, user_id, message, created_at, parent_id, read_state, rating_count, rating_sum}` |
| `conversations` | array | Inbox conversations; each: `{id, subject, workflow_state, last_message, last_message_at, message_count, starred, private, participants[], context_name, context_id}` |
| `conversationMessages` | array | Messages within conversations; each: `{id, conversation_id, author_id, body, created_at, generated, attachments[]}` |
| `calendarEvents` | array | Calendar events; each: `{id, title, description, start_at, end_at, all_day, location_name, context_code, context_name, workflow_state}` |
| `pages` | array | Wiki pages per course; each: `{id, course_id, title, url, body, published, front_page, created_at, updated_at, editing_roles, last_edited_by}` |
| `files` | array | Course files; each: `{id, course_id, display_name, filename, content_type, size, folder_id, created_at, updated_at, url}` |
| `folders` | array | Course folder structure; each: `{id, course_id, name, parent_folder_id, position, files_count, folders_count}` |
| `todoItems` | array | Teacher to-do grading items; each: `{id, type, assignment_id, course_id, title, needs_grading_count, due_at, points_possible}` |
| `dashboardView` | string | Dashboard display mode: `"cards"` or `"list"` |
| `activeCourseNav` | object | Per-course navigation customization; keyed by course_id → `{shown: string[], hidden: string[]}` |

### Default user IDs
| ID | Name | Role |
|----|------|------|
| 1 | Sarah Johnson | teacher (currentUser) |
| 2 | James Chen | student |
| 3 | Maria Garcia | student |
| 4 | Alex Kim | student |
| 5 | Emily Watson | student |
| 6 | David Brown | student |
| 7 | Sophia Patel | student |
| 8 | Ryan O'Brien | student |
| 9 | Lisa Nguyen | ta |
| 10 | Michael Torres | student |

### Default course IDs
| ID | Code | Name | Status |
|----|------|------|--------|
| 1 | CS 101 | Introduction to Computer Science | available |
| 2 | CS 201 | Data Structures and Algorithms | available |
| 3 | CS 150 | Web Development Fundamentals | available |
| 4 | CS 480 | Machine Learning | available |
| 5 | CS 350 | Software Engineering | completed |

### Default assignment IDs (CS 101)
| ID | Group | Name |
|----|-------|------|
| 1 | Homework (1) | HW 1: Variables and Data Types |
| 2 | Homework (1) | HW 2: Control Flow |
| 3 | Homework (1) | HW 3: Functions and Modules |
| 4 | Homework (1) | HW 4: Object-Oriented Programming |
| 5 | Homework (1) | HW 5: File I/O and Exceptions (unpublished) |
| 6 | Quizzes (2) | Quiz 1: Python Basics |
| 7 | Quizzes (2) | Quiz 2: Control Structures |
| 8 | Midterm Exam (3) | Midterm Exam |
| 9 | Final Project (4) | Final Project Proposal |
| 10 | Final Project (4) | Final Project Submission (unpublished) |

### Default assignment IDs (CS 201)
| ID | Group | Name |
|----|-------|------|
| 11 | Programming Assignments (6) | PA 1: Linked Lists |
| 12 | Programming Assignments (6) | PA 2: Stacks and Queues |
| 13 | Exams (7) | Midterm Exam |

### Default module IDs
| ID | Course | Name |
|----|--------|------|
| 1 | CS 101 | Week 1: Introduction to Python |
| 2 | CS 101 | Week 2: Variables and Data Types |
| 3 | CS 101 | Week 3: Control Flow |
| 4 | CS 101 | Week 4: Functions |
| 5 | CS 101 | Week 5: Object-Oriented Programming |
| 6 | CS 101 | Week 6: File I/O and Exceptions (unpublished) |
| 7 | CS 201 | Unit 1: Arrays and Complexity |
| 8 | CS 201 | Unit 2: Linked Lists |
| 9 | CS 201 | Unit 3: Stacks and Queues |

### Default conversation IDs
| ID | Subject | Participants | Status |
|----|---------|-------------|--------|
| 1 | Question about HW 2 | User 1 ↔ User 2 | read |
| 2 | Office Hours This Week | User 1 ↔ User 3 | unread |
| 3 | Final Project Ideas | User 1 ↔ User 4 | read, starred |
| 4 | Grading Concern - PA 1 | User 1 ↔ User 5 | unread |
| 5 | TA Schedule Update | User 1 ↔ User 9 | read |

### Default discussion topic IDs
| ID | Course | Title |
|----|--------|-------|
| 1 | CS 101 | Share Your First Program (pinned) |
| 2 | CS 101 | Best Practices for Code Comments |
| 3 | CS 101 | Midterm Study Group |
| 4 | CS 101 | Final Project Brainstorm |

### Default calendar event IDs
| ID | Title | Context |
|----|-------|---------|
| 1 | Office Hours | course_1 (CS 101) |
| 2 | CS Department Meeting | user_1 (Personal) |
| 3 | Guest Lecture: AI Ethics | course_4 (CS 480) |
| 4 | Midterm Review Session | course_1 (CS 101) |
| 5 | Fall Break - No Classes | user_1 (Personal) |

## Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | redirect → `/dashboard` | Home redirect |
| `/dashboard` | Dashboard | Course cards/list view, to-do items, upcoming events |
| `/courses` | Courses | All enrolled courses table |
| `/courses/:courseId` | CourseHome | Course landing page (modules or syllabus) |
| `/courses/:courseId/modules` | Modules | Course modules with items |
| `/courses/:courseId/assignments` | Assignments | Assignment groups and list |
| `/courses/:courseId/assignments/new` | AssignmentForm | Create new assignment |
| `/courses/:courseId/assignments/:assignmentId` | AssignmentDetail | Assignment details |
| `/courses/:courseId/assignments/:assignmentId/edit` | AssignmentForm | Edit assignment |
| `/courses/:courseId/announcements` | Announcements | Course announcements list |
| `/courses/:courseId/announcements/new` | AnnouncementForm | Create new announcement |
| `/courses/:courseId/announcements/:announcementId` | AnnouncementDetail | Announcement detail with replies |
| `/courses/:courseId/discussion_topics` | Discussions | Discussion topics list |
| `/courses/:courseId/discussion_topics/new` | DiscussionForm | Create new discussion |
| `/courses/:courseId/discussion_topics/:topicId` | DiscussionDetail | Discussion with threaded replies |
| `/courses/:courseId/grades` | Gradebook | Grade spreadsheet view |
| `/courses/:courseId/users` | People | Enrolled users table |
| `/courses/:courseId/pages` | Pages | Wiki pages list |
| `/courses/:courseId/pages/:pageUrl` | PageDetail | Page content view |
| `/courses/:courseId/pages/:pageUrl/edit` | PageEditor | Create/edit page |
| `/courses/:courseId/files` | Files | File browser with folder tree |
| `/courses/:courseId/syllabus` | Syllabus | Course syllabus display |
| `/courses/:courseId/settings` | Settings | Course details, navigation, features |
| `/calendar` | Calendar | Monthly calendar with events |
| `/conversations` | Inbox | Messaging system with compose |
| `/go` | Go | State inspection endpoint |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8007/?sid=task001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "currentUser": {
          "id": 1,
          "name": "Sarah Johnson",
          "short_name": "Prof. Johnson",
          "sortable_name": "Johnson, Sarah",
          "email": "sjohnson@university.edu",
          "avatar_url": null,
          "role": "teacher",
          "pronouns": "She/Her",
          "bio": "Professor of Computer Science",
          "last_login": "2025-10-10T14:30:00Z"
        },
        "users": [
          {"id": 1, "name": "Sarah Johnson", "short_name": "Prof. Johnson", "sortable_name": "Johnson, Sarah", "email": "sjohnson@university.edu", "avatar_url": null, "role": "teacher", "pronouns": "She/Her", "bio": "Professor of Computer Science"},
          {"id": 2, "name": "James Chen", "short_name": "James", "sortable_name": "Chen, James", "email": "jchen@university.edu", "avatar_url": null, "role": "student", "pronouns": "He/Him", "bio": ""}
        ],
        "courses": [
          {"id": 1, "name": "Introduction to Computer Science", "course_code": "CS 101", "term": "Fall 2025", "workflow_state": "available", "start_at": "2025-08-25T00:00:00Z", "end_at": "2025-12-15T00:00:00Z", "color": "#0374B5", "default_view": "modules", "syllabus_body": "<h2>CS 101</h2>", "total_students": 35, "image_url": null}
        ],
        "enrollments": [
          {"id": 1, "user_id": 1, "course_id": 1, "type": "TeacherEnrollment", "enrollment_state": "active", "course_section_id": 1, "created_at": "2025-08-20T00:00:00Z"},
          {"id": 2, "user_id": 2, "course_id": 1, "type": "StudentEnrollment", "enrollment_state": "active", "course_section_id": 1, "created_at": "2025-08-22T00:00:00Z"}
        ],
        "assignmentGroups": [
          {"id": 1, "course_id": 1, "name": "Homework", "weight": 30, "position": 1}
        ],
        "assignments": [
          {"id": 1, "course_id": 1, "assignment_group_id": 1, "name": "HW 1: Variables", "description": "<p>Complete exercises</p>", "due_at": "2025-09-08T23:59:00Z", "points_possible": 100, "grading_type": "points", "submission_types": ["online_upload"], "published": true, "position": 1, "needs_grading_count": 0, "workflow_state": "published"}
        ],
        "submissions": [],
        "modules": [
          {"id": 1, "course_id": 1, "name": "Week 1", "position": 1, "published": true, "items_count": 1, "state": "completed"}
        ],
        "moduleItems": [
          {"id": 1, "module_id": 1, "title": "HW 1: Variables", "type": "Assignment", "content_id": 1, "position": 1, "indent": 0, "published": true}
        ],
        "announcements": [],
        "discussionTopics": [],
        "discussionEntries": [],
        "conversations": [],
        "conversationMessages": [],
        "calendarEvents": [],
        "pages": [],
        "files": [],
        "folders": [],
        "todoItems": [],
        "dashboardView": "cards",
        "activeCourseNav": {}
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Switch dashboard view (cards/list) | `dashboardView` toggled between `"cards"` and `"list"` |
| Dismiss todo item | `todoItems` array shrinks by 1 |
| Change course color via modal | `courses[i].color` updated |
| Set course nickname | `courses[i].nickname` set |
| Toggle assignment publish/unpublish | `assignments[i].published` toggled; `workflow_state` → `"published"`/`"unpublished"` |
| Delete assignment | `assignments` array shrinks by 1 |
| Create new assignment | `assignments` array grows by 1 |
| Edit assignment details | `assignments[i]` fields updated (name, description, points, due_at, etc.) |
| Grade a submission (gradebook cell edit) | `submissions[i].score`, `grade`, `workflow_state` → `"graded"`, `graded_at` updated |
| Create new submission via gradebook | `submissions` array grows by 1 |
| Toggle module publish | `modules[i].published` toggled |
| Delete module | `modules` array shrinks; `moduleItems` entries for that module removed |
| Add new module | `modules` array grows by 1 |
| Edit module name | `modules[i].name` updated |
| Toggle module item publish | `moduleItems[i].published` toggled |
| Add module item | `moduleItems` array grows by 1 |
| Create new announcement | `announcements` array grows by 1 |
| View announcement (mark read) | `announcements[i].read_state` → `"read"` |
| Reply to announcement | `announcementReplies` array grows by 1 |
| Create new discussion topic | `discussionTopics` array grows by 1 |
| View discussion (mark read) | `discussionTopics[i].read_state` → `"read"`, `unread_count` → 0; `discussionEntries` read_state updated |
| Post discussion reply (top-level or nested) | `discussionEntries` grows by 1; `discussionTopics[i].discussion_subentry_count` incremented; `last_reply_at` updated |
| Like a discussion entry | `discussionEntries[i].rating_count` and `rating_sum` incremented |
| Select inbox conversation (mark read) | `conversations[i].workflow_state` → `"read"` |
| Toggle conversation star | `conversations[i].starred` toggled |
| Reply in inbox conversation | `conversationMessages` grows by 1; `conversations[i].last_message`, `last_message_at`, `message_count` updated |
| Archive inbox conversation | `conversations[i].workflow_state` → `"archived"` |
| Delete inbox conversation | `conversations` and `conversationMessages` entries removed |
| Compose new inbox message | `conversations` grows by 1; `conversationMessages` grows by 1 |
| Add calendar event | `calendarEvents` array grows by 1 |
| Create new page | `pages` array grows by 1 |
| Edit existing page | `pages[i]` fields updated (title, body, front_page, updated_at, last_edited_by) |
| Set page as front page | `pages[i].front_page` toggled; other pages in same course set to `false` |
| Create folder | `folders` array grows by 1 |
| Upload file (mock) | `files` array grows by 1 |
| Save course settings | `courses[i]` fields updated (name, course_code, default_view, start_at, end_at) |
| Save course navigation | `activeCourseNav[courseId]` updated with `{shown, hidden}` |
