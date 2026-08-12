# aws_console_mock Schema

**Deploy order**: 3 (0-indexed, alphabetical among *_mock dirs; BASE_PORT=8000 → port 8003)
**Base URL**: `http://172.17.46.46:8003/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**State check**: `GET /state?sid=<sid>` → `{stored_state, has_custom_state, sid}`

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `user` | object | Account info: `name`, `email`, `accountId`, `region`, `accountAlias` |
| `recentServices` | array | Recently visited services: `{id, name, path, lastVisited}` |
| `favorites` | array | Favorited services (same shape as recentServices) |
| `ec2` | array | EC2 instances: `{id, name, type, state, publicIp, privateIp, az, vpcId, subnetId, ami, amiName, platform, keyPair, securityGroups[], launchTime, monitoring, tags[]}` |
| `s3` | array | S3 buckets: `{name, region, created, access, versioning, encryption, objects[{key, size, lastModified, storageClass, type}]}` |
| `lambda` | array | Lambda functions: `{name, description, runtime, handler, memorySize, timeout, lastModified, codeSize, code, environment, layers, role, tags}` |
| `rds` | array | RDS instances: `{id, engine, engineVersion, class, status, role, endpoint, port, az, multiAZ, storage, storageType, vpcId, created, tags[]}` |
| `iam` | object | IAM resources: `users[]`, `roles[]`, `policies[]`, `groups[]` |
| `iam.users[]` | array | `{name, arn, created, lastActivity, groups[], policies[], mfaEnabled, accessKeyAge, passwordLastUsed, path, tags[]}` |
| `iam.roles[]` | array | `{name, arn, created, lastActivity, trustedEntities, description, policies[], path, maxSessionDuration}` |
| `iam.policies[]` | array | `{name, arn, type, description, attachedEntities, created, updated}` |
| `iam.groups[]` | array | `{name, arn, created, users[], policies[], path}` |
| `billing` | object | `{currentMonth, forecast, lastMonth, currency, history[], byService[], freeTier[]}` |
| `securityGroups` | array | `{id, name, description, vpcId, inboundRules[], outboundRules[]}` |
| `keyPairs` | array | `{name, id, type, fingerprint, created}` |
| `notifications` | array | `{id, title, message, type, timestamp, read, service}` |
| `flash` | array | Transient flash messages (usually empty) |

## Minimal Inject Example

```json
{
  "type": "chrome_open_url",
  "parameters": {
    "url": "http://172.17.46.46:8003/?sid=task-001",
    "inject_state": true,
    "state_content": {
      "action": "set",
      "state": {
        "user": {
          "name": "Admin User",
          "email": "admin@company.com",
          "accountId": "1234-5678-9012",
          "region": "us-east-1",
          "accountAlias": "my-company-prod"
        },
        "ec2": [
          {
            "id": "i-0a1b2c3d4e5f6g7h8",
            "name": "Web-Server-01",
            "type": "t2.micro",
            "state": "stopped",
            "publicIp": "-",
            "privateIp": "10.0.1.42",
            "az": "us-east-1a",
            "vpcId": "vpc-0abc1234def56789",
            "subnetId": "subnet-0def5678abc12345",
            "ami": "ami-0abcdef1234567890",
            "amiName": "Amazon Linux 2023 AMI",
            "platform": "Linux/UNIX",
            "keyPair": "my-key-pair",
            "securityGroups": ["sg-web-server"],
            "launchTime": "2024-03-10T08:30:00Z",
            "monitoring": "disabled",
            "tags": [{"Key": "Environment", "Value": "Production"}]
          }
        ],
        "s3": [],
        "lambda": [],
        "rds": [],
        "iam": {"users": [], "roles": [], "policies": [], "groups": []},
        "billing": {"currentMonth": 0, "forecast": 0, "lastMonth": 0, "currency": "USD", "history": [], "byService": [], "freeTier": []},
        "securityGroups": [],
        "keyPairs": [],
        "recentServices": [],
        "favorites": [],
        "notifications": [],
        "flash": []
      }
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed |
|-------------|---------------------|
| Start/stop EC2 instance | `ec2[].state` ("running" ↔ "stopped") |
| Create/delete S3 bucket | `s3` array length; bucket `name` present/absent |
| Upload object to S3 bucket | `s3[].objects` array gains entry |
| Create/delete Lambda function | `lambda` array length; function `name` present/absent |
| Update Lambda code or env vars | `lambda[].code`, `lambda[].environment` |
| Start/stop RDS instance | `rds[].status` ("available" ↔ "stopped") |
| Create IAM user | `iam.users` array gains entry |
| Add user to IAM group | `iam.users[].groups[]`, `iam.groups[].users[]` |
| Attach policy to user/role | `iam.users[].policies[]` or `iam.roles[].policies[]` |
| Mark notification as read | `notifications[].read` true |
| Add to favorites | `favorites` array gains service entry |
| Change region | `user.region` |
