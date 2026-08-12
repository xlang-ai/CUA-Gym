# azure_mock Schema

**Deploy order**: 4 (alphabetical among all *_mock dirs, BASE_PORT=8000 → port 8004)
**Base URL**: `http://172.17.46.46:8004/`
**Go Endpoint**: `GET /go?sid=<sid>` → `{initial_state, current_state, state_diff}`
**Inject**: `POST /post?sid=<sid>` with body `{"action":"set","state":{...}}`
**Update current only**: `POST /post?sid=<sid>` with body `{"action":"set_current","state":{...}}`
**Reset**: `POST /post?sid=<sid>` with body `{"action":"reset"}`
**Upload files**: `POST /upload?sid=<sid>` (multipart/form-data) → `{files: [{url, original_name, stored_name, size}]}`
**Serve files**: `GET /files/<sid>/<filename>` → file content with Content-Type

## State Management

Uses **React Context + useReducer** pattern (`src/context/AppContext.jsx`). State is persisted to `localStorage` under keys `azure_portal_state` (current) and `azure_portal_initialState` (initial), optionally suffixed with `_<sid>`.

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Home | Azure portal home with services grid, recent resources, navigation |
| `/dashboard` | Dashboard | My Dashboard with resource counts, costs, recent activity |
| `/go` | Go | State inspection endpoint (JSON) |
| `/all-resources` | AllResources | Lists all resources across types |
| `/resource-groups` | ResourceGroups | Lists all resource groups |
| `/resource-groups/:name` | ResourceGroupDetail | Resource group detail with resources and delete |
| `/resource-groups/create` | CreateResourceGroup | Create new resource group form |
| `/virtual-machines` | VirtualMachines | Lists all VMs |
| `/virtual-machines/create` | CreateVM | Multi-tab VM creation wizard |
| `/virtual-machines/:id` | VirtualMachineDetail | VM detail with start/stop/restart/delete |
| `/storage-accounts` | StorageAccounts | Lists all storage accounts |
| `/storage-accounts/create` | CreateStorageAccount | Multi-tab storage account creation wizard |
| `/storage-accounts/:id` | StorageAccountDetail | Storage account detail with containers |
| `/app-services` | AppServices | Lists all App Services |
| `/app-services/:id` | AppServiceDetail | App Service detail with overview, activity, config, tags |
| `/sql-databases` | SqlDatabases | Lists all SQL databases |
| `/sql-databases/:id` | SqlDatabaseDetail | SQL database detail with connection strings, query editor |
| `/virtual-networks` | VirtualNetworks | Lists all virtual networks |
| `/network-security-groups` | NetworkSecurityGroups | Lists all NSGs |
| `/network-security-groups/:id` | NsgDetail | NSG detail with inbound/outbound rules |
| `/subscriptions` | Subscriptions | Lists all subscriptions |
| `/subscriptions/:id` | SubscriptionDetail | Subscription details |
| `/cost-management` | CostManagement | Cost management overview |
| `/cost-management/cost-analysis` | CostAnalysis | Cost analysis with charts (uses recharts) |
| `/cost-management/budgets` | CostBudgets | Budgets and invoices |
| `/all-services` | AllServices | All Azure services by category |
| `/activity-log` | ActivityLog | Activity log with time/severity filters |
| `/create-resource` | CreateResource | Create a resource landing page |

## State Schema

| Key | Type | Description |
|-----|------|-------------|
| `currentUser` | `User` | Currently logged-in user |
| `tenant` | `Tenant` | Azure AD tenant info |
| `subscriptions` | `Subscription[]` | Azure subscriptions |
| `resourceGroups` | `ResourceGroup[]` | Resource groups |
| `virtualMachines` | `VirtualMachine[]` | Virtual machines |
| `storageAccounts` | `StorageAccount[]` | Storage accounts (each with containers) |
| `virtualNetworks` | `VirtualNetwork[]` | Virtual networks (each with subnets) |
| `networkSecurityGroups` | `NetworkSecurityGroup[]` | NSGs with inbound/outbound rules |
| `appServices` | `AppService[]` | App Services (web apps) |
| `sqlDatabases` | `SqlDatabase[]` | SQL databases |
| `costManagement` | `CostManagement` | Cost data, budgets, invoices |
| `activityLog` | `ActivityLogEvent[]` | Activity log events |
| `notifications` | `Notification[]` | Portal notifications |
| `favorites` | `Favorite[]` | Sidebar favorites |
| `allServicesCategories` | `ServiceCategory[]` | All services organized by category |
| `recentResources` | `RecentResource[]` | Recently viewed resources (max 10) |
| `portalSettings` | `PortalSettings` | Portal UI settings |

### Sub-type: `User`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"user-001"` | User identifier |
| `displayName` | string | `"Alex Johnson"` | Display name |
| `email` | string | `"alex.johnson@contoso.com"` | Email address |
| `avatarUrl` | string\|null | `null` | Avatar URL |
| `directoryName` | string | `"Contoso"` | Directory/tenant display name |
| `directoryId` | string | `"tenant-contoso-001"` | Directory/tenant ID |

### Sub-type: `Tenant`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | `"tenant-contoso-001"` | Internal tenant ID |
| `displayName` | string | `"Contoso"` | Tenant display name |
| `domain` | string | `"contoso.onmicrosoft.com"` | Tenant domain |
| `tenantId` | string | `"72f988bf-86f1-41af-91ab-2d7cd011db47"` | Azure AD tenant GUID |

### Sub-type: `Subscription`

| Field | Type | Default (sub-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"sub-001"` | Internal subscription ID (used for lookups) |
| `subscriptionId` | string | `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"` | Azure subscription GUID |
| `displayName` | string | `"Pay-As-You-Go"` | Subscription name |
| `state` | string | `"Enabled"` | Subscription state |
| `tenantId` | string | `"tenant-contoso-001"` | Associated tenant |
| `spendingLimit` | string | `"Off"` | Spending limit status |

### Sub-type: `ResourceGroup`

| Field | Type | Default (rg-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"rg-001"` | Internal ID |
| `name` | string | `"rg-web-prod"` | Resource group name (used as route param) |
| `subscriptionId` | string | `"sub-001"` | Owning subscription |
| `location` | string | `"East US"` | Azure region |
| `tags` | object | `{environment:"production",team:"web"}` | Key-value tags |
| `provisioningState` | string | `"Succeeded"` | Provisioning state |
| `createdDate` | string (ISO 8601) | `"2024-06-15T10:30:00Z"` | Creation timestamp |

Default resource groups: `rg-001` ("rg-web-prod"), `rg-002` ("rg-data-dev"), `rg-003` ("rg-networking")

### Sub-type: `VirtualMachine`

| Field | Type | Default (vm-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"vm-001"` | Internal VM ID (used as route param) |
| `name` | string | `"vm-web-server-01"` | VM name |
| `resourceGroup` | string | `"rg-web-prod"` | Owning resource group name |
| `subscriptionId` | string | `"sub-001"` | Owning subscription |
| `location` | string | `"East US"` | Azure region |
| `status` | string | `"Running"` | VM status: `"Running"` or `"Stopped"` |
| `powerState` | string | `"VM running"` | Power state: `"VM running"` or `"VM deallocated"` |
| `size` | string | `"Standard_DS2_v2"` | VM size/SKU |
| `osType` | string | `"Linux"` | OS type: `"Linux"` or `"Windows"` |
| `osImage` | string | `"Ubuntu Server 22.04 LTS"` | OS image name |
| `publicIpAddress` | string\|null | `"52.168.100.45"` | Public IP (null if none) |
| `privateIpAddress` | string | `"10.0.1.4"` | Private IP |
| `virtualNetwork` | string | `"vnet-web-prod"` | Associated VNet name |
| `subnet` | string | `"default"` | Associated subnet name |
| `networkSecurityGroup` | string | `"nsg-web-prod"` | Associated NSG name |
| `osDiskSizeGb` | number | `30` | OS disk size in GB |
| `osDiskType` | string | `"Premium SSD"` | Disk type: `"Premium SSD"`, `"Standard SSD"`, `"Standard HDD"` |
| `computerName` | string | `"vm-web-server-01"` | Computer hostname |
| `adminUsername` | string | `"azureuser"` | Admin username |
| `tags` | object | `{role:"webserver",env:"prod"}` | Key-value tags |
| `createdDate` | string (ISO 8601) | `"2024-07-01T09:00:00Z"` | Creation timestamp |

Default VMs: `vm-001` ("vm-web-server-01", Running), `vm-002` ("vm-web-server-02", Running), `vm-003` ("vm-db-primary", Running), `vm-004` ("vm-jumpbox", Stopped)

### Sub-type: `StorageAccount`

| Field | Type | Default (sa-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"sa-001"` | Internal ID (used as route param) |
| `name` | string | `"contosowebprod"` | Storage account name |
| `resourceGroup` | string | `"rg-web-prod"` | Owning resource group name |
| `subscriptionId` | string | `"sub-001"` | Owning subscription |
| `location` | string | `"East US"` | Azure region |
| `kind` | string | `"StorageV2"` | Storage kind |
| `performance` | string | `"Standard"` | Performance tier: `"Standard"` or `"Premium"` |
| `replication` | string | `"LRS"` | Replication: `"LRS"`, `"GRS"`, `"ZRS"`, `"RA-GRS"` |
| `accessTier` | string | `"Hot"` | Access tier: `"Hot"` or `"Cool"` |
| `status` | string | `"Available"` | Account status |
| `primaryEndpoint` | string | `"https://contosowebprod.blob.core.windows.net"` | Primary blob endpoint |
| `createdDate` | string (ISO 8601) | `"2024-06-16T12:00:00Z"` | Creation timestamp |
| `tags` | object | `{purpose:"web-assets"}` | Key-value tags |
| `containers` | `Container[]` | *(see below)* | Blob containers within the account |

Default storage accounts: `sa-001` ("contosowebprod"), `sa-002` ("contosodatadev")

### Sub-type: `Container` (nested in StorageAccount)

| Field | Type | Default (container-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"container-001"` | Container ID |
| `name` | string | `"images"` | Container name |
| `publicAccessLevel` | string | `"Blob"` | Access level: `"Blob"` or `"Private"` |
| `leaseState` | string | `"Available"` | Lease state |
| `lastModified` | string (ISO 8601) | `"2024-11-15T08:00:00Z"` | Last modified timestamp |
| `blobCount` | number | `156` | Number of blobs |

Default containers: `container-001` through `container-005` across both storage accounts.

### Sub-type: `VirtualNetwork`

| Field | Type | Default (vnet-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"vnet-001"` | Internal ID |
| `name` | string | `"vnet-web-prod"` | VNet name |
| `resourceGroup` | string | `"rg-web-prod"` | Owning resource group |
| `subscriptionId` | string | `"sub-001"` | Owning subscription |
| `location` | string | `"East US"` | Azure region |
| `addressSpace` | string | `"10.0.0.0/16"` | CIDR address space |
| `status` | string | `"Succeeded"` | Provisioning status |
| `subnets` | `Subnet[]` | *(see below)* | Subnets within the VNet |
| `tags` | object | `{}` | Key-value tags |
| `createdDate` | string (ISO 8601) | `"2024-06-15T10:45:00Z"` | Creation timestamp |

Default VNets: `vnet-001` ("vnet-web-prod"), `vnet-002` ("vnet-data-dev")

### Sub-type: `Subnet` (nested in VirtualNetwork)

| Field | Type | Default (subnet-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"subnet-001"` | Subnet ID |
| `name` | string | `"default"` | Subnet name |
| `addressPrefix` | string | `"10.0.1.0/24"` | Subnet CIDR |
| `connectedDevices` | number | `2` | Number of connected devices |
| `networkSecurityGroup` | string | `"nsg-web-prod"` | Associated NSG name |

Default subnets: `subnet-001` ("default"), `subnet-002` ("management"), `subnet-003` ("db-subnet")

### Sub-type: `NetworkSecurityGroup`

| Field | Type | Default (nsg-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"nsg-001"` | Internal ID (used as route param) |
| `name` | string | `"nsg-web-prod"` | NSG name |
| `resourceGroup` | string | `"rg-web-prod"` | Owning resource group |
| `subscriptionId` | string | `"sub-001"` | Owning subscription |
| `location` | string | `"East US"` | Azure region |
| `inboundRules` | `SecurityRule[]` | *(see below)* | Inbound security rules |
| `outboundRules` | `SecurityRule[]` | *(see below)* | Outbound security rules |
| `tags` | object | `{}` | Key-value tags |
| `createdDate` | string (ISO 8601) | `"2024-06-15T11:00:00Z"` | Creation timestamp |

Default NSGs: `nsg-001` ("nsg-web-prod"), `nsg-002` ("nsg-data-dev"), `nsg-003` ("nsg-management")

### Sub-type: `SecurityRule` (nested in NetworkSecurityGroup)

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `name` | string | `"AllowHTTP"` | Rule name |
| `priority` | number | `100` | Rule priority (lower = higher priority) |
| `direction` | string | `"Inbound"` | `"Inbound"` or `"Outbound"` |
| `access` | string | `"Allow"` | `"Allow"` or `"Deny"` |
| `protocol` | string | `"TCP"` | Protocol: `"TCP"`, `"UDP"`, `"*"` |
| `sourcePortRange` | string | `"*"` | Source port range |
| `destinationPortRange` | string | `"80"` | Destination port range |
| `sourceAddressPrefix` | string | `"*"` | Source address prefix (CIDR or `"*"`) |
| `destinationAddressPrefix` | string | `"*"` | Destination address prefix |
| `description` | string | `"Allow HTTP"` | Rule description |

### Sub-type: `AppService`

| Field | Type | Default (app-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"app-001"` | Internal ID (used as route param) |
| `name` | string | `"contoso-web-app"` | App name |
| `resourceGroup` | string | `"rg-web-prod"` | Owning resource group |
| `subscriptionId` | string | `"sub-001"` | Owning subscription |
| `location` | string | `"East US"` | Azure region |
| `status` | string | `"Running"` | App status |
| `kind` | string | `"app"` | App kind |
| `defaultHostName` | string | `"contoso-web-app.azurewebsites.net"` | Default hostname |
| `appServicePlan` | string | `"asp-web-prod"` | App Service plan name |
| `runtime` | string | `"Node.js 18 LTS"` | Runtime stack |
| `httpsOnly` | boolean | `true` | Whether HTTPS-only is enabled |
| `tags` | object | `{app:"frontend"}` | Key-value tags |
| `createdDate` | string (ISO 8601) | `"2024-07-10T13:00:00Z"` | Creation timestamp |

Default App Services: `app-001` ("contoso-web-app"), `app-002` ("contoso-api")

### Sub-type: `SqlDatabase`

| Field | Type | Default (sqldb-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"sqldb-001"` | Internal ID (used as route param) |
| `name` | string | `"contoso-db"` | Database name |
| `resourceGroup` | string | `"rg-data-dev"` | Owning resource group |
| `subscriptionId` | string | `"sub-001"` | Owning subscription |
| `location` | string | `"West US 2"` | Azure region |
| `serverName` | string | `"contoso-sql-server"` | SQL server name |
| `status` | string | `"Online"` | Database status |
| `pricingTier` | string | `"Standard S0"` | Pricing tier |
| `maxSizeGb` | number | `250` | Max database size in GB |
| `collation` | string | `"SQL_Latin1_General_CP1_CI_AS"` | Database collation |
| `tags` | object | `{environment:"dev"}` | Key-value tags |
| `createdDate` | string (ISO 8601) | `"2024-08-25T12:00:00Z"` | Creation timestamp |

Default SQL databases: `sqldb-001` ("contoso-db")

### Sub-type: `CostManagement`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `currentMonthCost` | number | `487.23` | Current month spend |
| `forecastedCost` | number | `612.50` | Forecasted month-end cost |
| `budgetAmount` | number | `800.00` | Monthly budget amount |
| `currency` | string | `"USD"` | Currency |
| `costByService` | `CostByService[]` | *(6 items)* | Cost breakdown by Azure service |
| `costByResourceGroup` | `CostByResourceGroup[]` | *(3 items)* | Cost breakdown by resource group |
| `costByLocation` | `CostByLocation[]` | *(2 items)* | Cost breakdown by Azure region |
| `dailyCosts` | `DailyCost[]` | *(15 items)* | Daily cost data points |
| `budgets` | `Budget[]` | *(1 item)* | Budget definitions |
| `invoices` | `Invoice[]` | *(3 items)* | Past invoices |

### Sub-type: `CostByService` (nested in CostManagement)

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `service` | string | `"Virtual Machines"` | Service name |
| `cost` | number | `245.80` | Cost amount |
| `percentage` | number | `50.4` | Percentage of total |

### Sub-type: `CostByResourceGroup` (nested in CostManagement)

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `resourceGroup` | string | `"rg-web-prod"` | Resource group name |
| `cost` | number | `340.80` | Cost amount |

### Sub-type: `CostByLocation` (nested in CostManagement)

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `location` | string | `"East US"` | Azure region |
| `cost` | number | `368.80` | Cost amount |

### Sub-type: `DailyCost` (nested in CostManagement)

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `date` | string | `"2024-12-01"` | Date (YYYY-MM-DD) |
| `cost` | number | `16.24` | Daily cost |

### Sub-type: `Budget` (nested in CostManagement)

| Field | Type | Default (budget-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"budget-001"` | Budget ID |
| `name` | string | `"Monthly-Total"` | Budget name |
| `amount` | number | `800` | Budget amount |
| `timeGrain` | string | `"Monthly"` | Time grain |
| `currentSpend` | number | `487.23` | Current spend against budget |
| `status` | string | `"OK"` | Budget status |

### Sub-type: `Invoice` (nested in CostManagement)

| Field | Type | Default (inv-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"inv-001"` | Invoice ID |
| `period` | string | `"November 2024"` | Billing period |
| `amount` | number | `523.45` | Invoice amount |
| `status` | string | `"Paid"` | Payment status |
| `dueDate` | string | `"2024-12-15"` | Due date |

### Sub-type: `ActivityLogEvent`

| Field | Type | Default (event-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"event-001"` | Event ID |
| `timestamp` | string (ISO 8601) | `"2024-12-14T15:30:00Z"` | Event timestamp |
| `operation` | string | `"Microsoft.Compute/virtualMachines/start/action"` | Operation identifier |
| `operationName` | string | `"Start Virtual Machine"` | Human-readable operation name |
| `status` | string | `"Succeeded"` | Status: `"Succeeded"` or `"Failed"` |
| `level` | string | `"Informational"` | Severity: `"Informational"`, `"Warning"`, `"Error"` |
| `resourceGroup` | string | `"rg-web-prod"` | Resource group name |
| `resourceName` | string | `"vm-web-server-01"` | Resource name |
| `resourceType` | string | `"Microsoft.Compute/virtualMachines"` | Azure resource type |
| `initiatedBy` | string | `"alex.johnson@contoso.com"` | Who initiated the action |

Default events: `event-001` through `event-008`

### Sub-type: `Notification`

| Field | Type | Default (notif-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"notif-001"` | Notification ID |
| `title` | string | `"Virtual machine started"` | Notification title |
| `message` | string | `"vm-web-server-01 was started successfully."` | Notification body |
| `level` | string | `"success"` | Level: `"success"`, `"info"`, `"warning"`, `"error"` |
| `timestamp` | string (ISO 8601) | `"2024-12-14T15:30:00Z"` | Notification timestamp |
| `read` | boolean | `false` | Whether notification has been read |
| `resourceName` | string\|null | `"vm-web-server-01"` | Associated resource (null if none) |

Default notifications: `notif-001` through `notif-005` (2 unread, 3 read)

### Sub-type: `Favorite`

| Field | Type | Default (fav-001) | Description |
|-------|------|---------|-------------|
| `id` | string | `"fav-001"` | Favorite ID |
| `name` | string | `"All resources"` | Displayed name in sidebar |
| `icon` | string | `"Grid"` | Icon name (lucide-react component name) |
| `path` | string | `"/all-resources"` | Navigation path |

Default favorites: `fav-001` through `fav-008` (All resources, Resource groups, Virtual machines, Storage accounts, App Services, SQL databases, Subscriptions, Cost Management)

### Sub-type: `ServiceCategory` (in allServicesCategories)

| Field | Type | Description |
|-------|------|-------------|
| `category` | string | Category name (e.g., "Compute", "Networking", "Storage") |
| `services` | `ServiceItem[]` | Services in this category |

### Sub-type: `ServiceItem` (nested in ServiceCategory)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Service display name |
| `icon` | string | Icon name |
| `path` | string | Navigation path |

Categories: Compute (5 services), Networking (5), Storage (2), Databases (4), Web (2), Identity (2), Management + Governance (6), Security (2)

### Sub-type: `RecentResource`

| Field | Type | Default (first entry) | Description |
|-------|------|---------|-------------|
| `name` | string | `"vm-web-server-01"` | Resource name |
| `type` | string | `"Virtual machine"` | Resource type label |
| `resourceGroup` | string\|null | `"rg-web-prod"` | Resource group (null for RGs themselves) |
| `lastViewed` | string (ISO 8601) | `"2024-12-14T15:30:00Z"` | Last viewed timestamp |

Default: 5 recent resources. Automatically updated when visiting detail pages (max 10 entries).

### Sub-type: `PortalSettings`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `theme` | string | `"light"` | UI theme |
| `menuBehavior` | string | `"flyout"` | Sidebar behavior: `"flyout"` or `"docked"` |
| `serviceMenuBehavior` | string | `"collapsed"` | Service menu behavior |
| `startupPage` | string | `"home"` | Startup page |
| `language` | string | `"English"` | Language |
| `regionalFormat` | string | `"English (United States)"` | Regional format |

## Reducer Actions

| Action Type | Payload | Effect |
|-------------|---------|--------|
| `CREATE_RESOURCE_GROUP` | `{name, subscriptionId, location, tags}` | Adds new resource group with auto-generated id and timestamps |
| `DELETE_RESOURCE_GROUP` | `name` (string) | Removes resource group by name |
| `UPDATE_RG_TAGS` | `{name, tags}` | Updates tags on a resource group |
| `CREATE_VM` | `{name, resourceGroup, subscriptionId, location, size, osType, osImage, publicIpAddress, privateIpAddress, virtualNetwork, subnet, networkSecurityGroup, osDiskSizeGb, osDiskType, computerName, adminUsername, tags}` | Adds new VM with status "Running" |
| `START_VM` | `id` (string) | Sets VM status to "Running", powerState to "VM running" |
| `STOP_VM` | `id` (string) | Sets VM status to "Stopped", powerState to "VM deallocated" |
| `RESTART_VM` | `id` (string) | Sets VM status to "Running", powerState to "VM running" |
| `DELETE_VM` | `id` (string) | Removes VM by id |
| `UPDATE_VM_TAGS` | `{id, tags}` | Updates tags on a VM |
| `CREATE_STORAGE_ACCOUNT` | `{name, resourceGroup, subscriptionId, location, performance, replication, accessTier, primaryEndpoint, tags}` | Adds new storage account (kind: StorageV2, status: Available, empty containers) |
| `DELETE_STORAGE_ACCOUNT` | `id` (string) | Removes storage account by id |
| `UPDATE_STORAGE_TAGS` | `{id, tags}` | Updates tags on a storage account |
| `CREATE_CONTAINER` | `{storageAccountId, name, publicAccessLevel}` | Adds container to a storage account |
| `ADD_NSG_RULE` | `{nsgId, rule, direction}` | Adds security rule to NSG (direction: "Inbound" or "Outbound") |
| `DELETE_NSG_RULE` | `{nsgId, ruleName, direction}` | Removes security rule from NSG |
| `DISMISS_NOTIFICATION` | `id` (string) | Removes a notification |
| `DISMISS_ALL_NOTIFICATIONS` | *(none)* | Clears all notifications |
| `ADD_NOTIFICATION` | `Notification` object | Prepends a notification |
| `MARK_NOTIFICATION_READ` | `id` (string) | Marks a notification as read |
| `TOGGLE_FAVORITE` | `{name, icon, path}` | Adds or removes from favorites |
| `UPDATE_SETTINGS` | Partial `PortalSettings` | Merges settings updates |
| `CREATE_BUDGET` | `{name, amount, timeGrain}` | Adds new budget with currentSpend: 0, status: "OK" |
| `UPDATE_RECENT_RESOURCES` | `{name, type, resourceGroup}` | Adds/moves to top of recent resources list |
| `SET_STATE` | Full state object | Replaces entire state (used for session injection) |

## Minimal Inject Example

```json
{
  "action": "set",
  "state": {
    "currentUser": {
      "id": "user-001",
      "displayName": "Alex Johnson",
      "email": "alex.johnson@contoso.com",
      "avatarUrl": null,
      "directoryName": "Contoso",
      "directoryId": "tenant-contoso-001"
    },
    "subscriptions": [
      {
        "id": "sub-001",
        "subscriptionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "displayName": "Pay-As-You-Go",
        "state": "Enabled",
        "tenantId": "tenant-contoso-001",
        "spendingLimit": "Off"
      }
    ],
    "resourceGroups": [
      {
        "id": "rg-001",
        "name": "rg-web-prod",
        "subscriptionId": "sub-001",
        "location": "East US",
        "tags": { "environment": "production" },
        "provisioningState": "Succeeded",
        "createdDate": "2024-06-15T10:30:00Z"
      }
    ],
    "virtualMachines": [
      {
        "id": "vm-001",
        "name": "vm-web-server-01",
        "resourceGroup": "rg-web-prod",
        "subscriptionId": "sub-001",
        "location": "East US",
        "status": "Running",
        "powerState": "VM running",
        "size": "Standard_DS2_v2",
        "osType": "Linux",
        "osImage": "Ubuntu Server 22.04 LTS",
        "publicIpAddress": "52.168.100.45",
        "privateIpAddress": "10.0.1.4",
        "virtualNetwork": "vnet-web-prod",
        "subnet": "default",
        "networkSecurityGroup": "nsg-web-prod",
        "osDiskSizeGb": 30,
        "osDiskType": "Premium SSD",
        "computerName": "vm-web-server-01",
        "adminUsername": "azureuser",
        "tags": { "role": "webserver" },
        "createdDate": "2024-07-01T09:00:00Z"
      }
    ],
    "storageAccounts": [],
    "virtualNetworks": [],
    "networkSecurityGroups": [],
    "appServices": [],
    "sqlDatabases": [],
    "costManagement": {
      "currentMonthCost": 487.23,
      "forecastedCost": 612.50,
      "budgetAmount": 800.00,
      "currency": "USD",
      "costByService": [],
      "costByResourceGroup": [],
      "costByLocation": [],
      "dailyCosts": [],
      "budgets": [],
      "invoices": []
    },
    "activityLog": [],
    "notifications": [],
    "favorites": [
      { "id": "fav-001", "name": "All resources", "icon": "Grid", "path": "/all-resources" },
      { "id": "fav-003", "name": "Virtual machines", "icon": "Monitor", "path": "/virtual-machines" }
    ],
    "allServicesCategories": [],
    "recentResources": [],
    "portalSettings": {
      "theme": "light",
      "menuBehavior": "flyout",
      "serviceMenuBehavior": "collapsed",
      "startupPage": "home",
      "language": "English",
      "regionalFormat": "English (United States)"
    }
  }
}
```

## Observable State Changes (for LLM evaluation)

| User Action | State Field Changed | Details |
|-------------|---------------------|---------|
| Start a virtual machine | `virtualMachines[i].status`, `virtualMachines[i].powerState` | status: "Running", powerState: "VM running" |
| Stop a virtual machine | `virtualMachines[i].status`, `virtualMachines[i].powerState` | status: "Stopped", powerState: "VM deallocated" |
| Restart a virtual machine | `virtualMachines[i].status`, `virtualMachines[i].powerState` | status: "Running", powerState: "VM running" |
| Delete a virtual machine | `virtualMachines` | VM removed from array |
| Create a virtual machine | `virtualMachines` | New VM appended with status "Running" |
| Create a resource group | `resourceGroups` | New resource group appended |
| Delete a resource group | `resourceGroups` | Resource group removed by name |
| Update resource group tags | `resourceGroups[i].tags` | Tags object replaced |
| Create a storage account | `storageAccounts` | New storage account appended |
| Delete a storage account | `storageAccounts` | Storage account removed by id |
| Update storage account tags | `storageAccounts[i].tags` | Tags object replaced |
| Create a blob container | `storageAccounts[i].containers` | New container appended to storage account |
| Add NSG security rule | `networkSecurityGroups[i].inboundRules` or `outboundRules` | New rule appended |
| Delete NSG security rule | `networkSecurityGroups[i].inboundRules` or `outboundRules` | Rule removed by name |
| Dismiss a notification | `notifications` | Notification removed by id |
| Dismiss all notifications | `notifications` | Array cleared to empty |
| Mark notification as read | `notifications[i].read` | Set to `true` |
| Add a notification | `notifications` | New notification prepended |
| Toggle a sidebar favorite | `favorites` | Item added or removed by name |
| Update portal settings | `portalSettings` | Settings fields merged |
| Create a budget | `costManagement.budgets` | New budget appended with currentSpend: 0 |
| Visit resource detail page | `recentResources` | Resource moved to top, list capped at 10 |
| Update VM tags | `virtualMachines[i].tags` | Tags object replaced |

## Default Entity IDs Summary

| Entity Type | IDs | Names |
|-------------|-----|-------|
| User | `user-001` | Alex Johnson |
| Tenant | `tenant-contoso-001` | Contoso |
| Subscription | `sub-001` | Pay-As-You-Go |
| Resource Groups | `rg-001`, `rg-002`, `rg-003` | rg-web-prod, rg-data-dev, rg-networking |
| Virtual Machines | `vm-001`, `vm-002`, `vm-003`, `vm-004` | vm-web-server-01, vm-web-server-02, vm-db-primary, vm-jumpbox |
| Storage Accounts | `sa-001`, `sa-002` | contosowebprod, contosodatadev |
| Containers | `container-001` to `container-005` | images, documents, backups, raw-data, processed |
| Virtual Networks | `vnet-001`, `vnet-002` | vnet-web-prod, vnet-data-dev |
| Subnets | `subnet-001`, `subnet-002`, `subnet-003` | default, management, db-subnet |
| NSGs | `nsg-001`, `nsg-002`, `nsg-003` | nsg-web-prod, nsg-data-dev, nsg-management |
| App Services | `app-001`, `app-002` | contoso-web-app, contoso-api |
| SQL Databases | `sqldb-001` | contoso-db |
| Budgets | `budget-001` | Monthly-Total |
| Invoices | `inv-001`, `inv-002`, `inv-003` | November 2024, October 2024, September 2024 |
| Activity Events | `event-001` to `event-008` | Various operations |
| Notifications | `notif-001` to `notif-005` | Various alerts |
| Favorites | `fav-001` to `fav-008` | All resources, Resource groups, VMs, etc. |
