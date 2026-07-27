# docusign_mock Schema

**Deploy order**: 12 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8012)
**Base URL**: `http://172.17.46.46:8012/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}` (use `"merge":true` for partial update)
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`

Note: vite.config.js uses `port: 0` (random). Actual port depends on deployment config. The inject endpoint is `/post`, not `/go`.

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Logged-in user profile |
| `envelopes` | array | All envelopes (9 in default state) |
| `templates` | array | Reusable document templates (4 in default) |
| `folders` | array | Folder organization (2 in default) |
| `contacts` | array | Address book entries (8 in default) |
| `auditLog` | array | System-wide audit trail |

### `user` subfields
- `id`, `name`, `email`, `title`, `company`, `avatar`
- `signatureDataUrl`, `initialsDataUrl` — base64 PNG for signing
- `memberSince` — ISO date string
- `settings`: `{defaultReminderDays, defaultExpirationDays, timezone}`

### `envelopes[]` subfields
- `id`, `subject`, `message`, `status` — status enum: `draft | sent | delivered | signed | completed | voided | declined`
- `createdAt`, `sentAt`, `completedAt`, `voidedAt`, `declinedAt`, `lastActivityAt`, `expiresAt` — ISO timestamps
- `senderId`, `folderId`, `templateId`
- `reminderEnabled`, `reminderDays`, `reminderFrequency`
- `documents[]`: `{id, name, pageCount, order, fileUrl, fileType}`
- `recipients[]`: `{id, name, email, role (signer|cc), routingOrder, status, signedAt, viewedAt, deliveredAt, declinedAt, declineReason}`
- `fields[]`: `{id, type (signature|dateSigned|name|initial|title|company|text|email|checkbox), recipientId, documentId, pageNumber, x, y, width, height, value, required, label, readOnly, fontSize, fontColor}`
- `history[]`: `{id, timestamp, action, actorName, actorEmail, details}`

### `templates[]` subfields
- `id`, `name`, `description`, `createdAt`, `lastUsedAt`, `usageCount`, `ownerId`, `shared`
- `documents[]`, `roles[]`, `fields[]` — similar shape to envelope equivalents

### `folders[]` subfields
- `id`, `name`, `parentFolder`, `createdAt`

### `contacts[]` subfields
- `id`, `name`, `email`, `company`, `title`

### `auditLog[]` subfields
- `id`, `timestamp`, `action` (e.g. `CREATE_ENVELOPE`, `SEND_ENVELOPE`, `COMPLETE_ENVELOPE`, `VOID_ENVELOPE`, `DECLINE_ENVELOPE`), `details`, `envelopeId`

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8012/?sid=task01",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "id": "user_1",
          "name": "Sarah Chen",
          "email": "sarah.chen@acmecorp.com",
          "title": "VP of Operations",
          "company": "Acme Corporation",
          "settings": {"defaultReminderDays": 3, "defaultExpirationDays": 120, "timezone": "America/Los_Angeles"}
        },
        "envelopes": [
          {
            "id": "env_1",
            "subject": "Acme Corp - Q1 Sales Agreement",
            "message": "Please sign.",
            "status": "draft",
            "createdAt": "2025-02-10T09:15:00Z",
            "sentAt": null, "completedAt": null, "voidedAt": null, "declinedAt": null,
            "lastActivityAt": "2025-02-10T09:15:00Z", "expiresAt": null,
            "senderId": "user_1", "folderId": null, "templateId": null,
            "reminderEnabled": false, "reminderDays": 3, "reminderFrequency": 2,
            "documents": [{"id": "doc_1_1", "name": "Agreement.pdf", "pageCount": 4, "order": 1, "fileUrl": "https://picsum.photos/seed/doc1/800/1100", "fileType": "pdf"}],
            "recipients": [{"id": "rec_1_1", "name": "Michael Torres", "email": "m.torres@example.com", "role": "signer", "routingOrder": 1, "status": "created", "signedAt": null, "viewedAt": null, "deliveredAt": null, "declinedAt": null, "declineReason": null}],
            "fields": [],
            "history": [{"id": "evt_1_1", "timestamp": "2025-02-10T09:15:00Z", "action": "created", "actorName": "Sarah Chen", "actorEmail": "sarah.chen@acmecorp.com", "details": "Envelope created"}]
          }
        ],
        "templates": [],
        "folders": [],
        "contacts": [],
        "auditLog": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field(s) Changed |
|-------------|------------------------|
| Send a draft envelope | `envelopes[i].status` → `"sent"`, `envelopes[i].sentAt` set, `envelopes[i].recipients[j].status` → `"sent"`, `envelopes[i].history` appended, `auditLog` appended |
| Void an envelope | `envelopes[i].status` → `"voided"`, `envelopes[i].voidedAt` set, `history` appended |
| Complete signing (all recipients signed) | `envelopes[i].status` → `"completed"`, `envelopes[i].completedAt` set, `recipients[j].status` → `"signed"`, `recipients[j].signedAt` set, field `value` populated with signature data |
| Move envelope to folder | `envelopes[i].folderId` set to target folder id |
| Update user settings | `user.settings.defaultReminderDays`, `user.settings.defaultExpirationDays`, `user.settings.timezone` |
| Create new envelope | `envelopes` array gains new entry with `status: "draft"` |
| Add/remove recipient | `envelopes[i].recipients` array modified |
| Use template | New envelope created with `templateId` set, `envelopes` array grows |
