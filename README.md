# EspoCRM MCP Server with Auth0 Authentication

A Model Context Protocol (MCP) server for EspoCRM with Auth0 authentication and authorization.

## Overview

This project provides an MCP server that integrates with EspoCRM, allowing AI assistants and other MCP clients to interact with EspoCRM data through a standardized interface. The server includes:

- **Auth0 Authentication**: Secure token-based authentication using Auth0
- **Scope-based Authorization**: Coarse-grained access control using OAuth scopes
- **FGA Fine-Grained Authorization** (Optional): Entity-level, relationship-based access control using OpenFGA
- **EspoCRM Integration**: Full API client for EspoCRM with support for both API key and HMAC authentication
- **Basic MCP Tools**: Essential tools for managing contacts, accounts, leads, and other entities

## Features

### Implemented Tools

1. **Health Check**
   - `health_check`: Verify EspoCRM connection status

2. **Contact Management**
   - `create_contact`: Create new contacts
   - `search_contacts`: Search contacts with filters
   - `get_contact`: Get detailed contact information

3. **Account Management**
   - `create_account`: Create new accounts/companies
   - `search_accounts`: Search accounts with filters

4. **Lead Management**
   - `create_lead`: Create new leads
   - `search_leads`: Search leads with filters

5. **Generic Entity Operations**
   - `search_entity`: Search any entity type
   - `get_entity`: Get any entity by ID

### Authentication & Authorization

All tools (except `health_check`) require valid Auth0 authentication with appropriate scopes:
- `espocrm:contacts:read` / `espocrm:contacts:write`
- `espocrm:accounts:read` / `espocrm:accounts:write`
- `espocrm:leads:read` / `espocrm:leads:write`
- `espocrm:entities:read`

#### Fine-Grained Authorization (FGA)

When FGA is enabled, additional entity-level permission checks are performed:

- **Contact Access**: 
  - Owner: Full access (read, update, delete)
  - Assigned user: Read and update access
  - Team member: Read access
  - Manager of assigned user: Full access

- **Account Access**:
  - Owner: Full access
  - Assigned user: Read and update access
  - Team member: Read access

- **Lead Access**:
  - Owner: Full access
  - Assigned user: Read and update access
  - Team member: Read access

FGA provides defense-in-depth security by combining scope-based (coarse-grained) and entity-level (fine-grained) authorization.

## Key Advantages

This architecture provides significant advantages over traditional API key-based approaches for multi-user and enterprise scenarios.

### Centralized Identity Management

**Auth0 Integration Benefits:**
- **Single Sign-On (SSO)**: Users can access multiple applications with one login
- **Social Login**: Support for Google, GitHub, Microsoft, and other identity providers
- **Multi-Factor Authentication (MFA)**: Built-in support for enhanced security
- **Password Policies**: Centralized password management and policies
- **User Lifecycle**: Automated provisioning and deprovisioning workflows

### Enterprise-Grade Authorization

**Multi-Layer Security Model:**

```
Request → Auth0 Token Validation → Scope Check → FGA Check → EspoCRM API
         (Authentication)         (Coarse-grained) (Fine-grained)
```

1. **Layer 1 - OAuth Scopes** (API-level authorization):
   - `espocrm:contacts:read` - Can user read contacts?
   - `espocrm:contacts:write` - Can user create/update contacts?

2. **Layer 2 - FGA** (Entity-level authorization):
   - Can user Alice read Contact #123?
   - Can user Bob update Lead #456?
   - Permissions computed dynamically based on relationships

**Fine-Grained Access Control:**
- Entity-level permissions (not just entity type level)
- Relationship-based access (owner, assigned user, team member)
- Hierarchical permissions (managers inherit team members' permissions)
- Dynamic authorization rules without code changes

### Deployment Architecture Benefits

**Traditional API Key Approach:**
```
User A ──> Server Instance A ──> EspoCRM (API Key A)
User B ──> Server Instance B ──> EspoCRM (API Key B)
User C ──> Server Instance C ──> EspoCRM (API Key C)

Problems:
❌ Each user needs independent deployment
❌ Resource waste (multiple server instances)
❌ Scattered configuration, hard to manage
❌ No centralized monitoring or auditing
```

**This Project (Auth0 + FGA):**
```
                    ┌─────────────────┐
User A ──> Auth0 ───>│                 │
User B ──> Auth0 ───>│  MCP Server     ├──> EspoCRM (Service Account)
User C ──> Auth0 ───>│  (Single Instance)│
                    └─────────────────┘

Advantages:
✅ Single deployment, centralized management
✅ Resource efficient (one instance serves all users)
✅ Unified monitoring and auditing
✅ Users don't manage API keys
```

### Security Enhancements

**Token-Based Security:**
- Short-lived access tokens (automatic expiration)
- Refresh token rotation
- Token revocation capabilities
- No API keys exposed to end users

**Service Account Pattern:**
- Single service account connects to EspoCRM
- User permissions enforced at MCP Server layer
- API key never exposed to users
- Easier to rotate and manage credentials

**Compliance Ready:**
- Centralized audit logs in Auth0
- Session management and tracking
- Support for compliance requirements (SOC2, GDPR, HIPAA)

### Use Cases

**Ideal For:**

1. **Multi-Application Environments**
   - Multiple apps accessing same EspoCRM data
   - Need SSO across web, mobile, and API clients
   - Example: Sales portal, customer portal, admin dashboard

2. **Complex Organizational Structures**
   - Matrix organizations (users in multiple teams)
   - Hierarchical permissions (managers → teams → entities)
   - Cross-departmental access rules
   - Example: Regional managers access their region's data

3. **External User Access**
   - Customer portal with self-service access
   - Partner integration with limited permissions
   - Contractor access with temporary permissions
   - Example: Customers view only their account data

4. **Regulatory Compliance**
   - HIPAA (healthcare data access control)
   - GDPR (data privacy and access rights)
   - SOX (financial data segregation)
   - Example: Healthcare CRM with patient data access logging

5. **Dynamic Permission Requirements**
   - Frequently changing permission rules
   - Complex business logic for access control
   - Need to modify permissions without code deployment
   - Example: Project-based access, seasonal permissions

### Comparison Summary

| Feature | Traditional API Key Approach | This Project (Auth0 + FGA) |
|---------|------------------------------|----------------------------|
| **Deployment** | Per-user independent deployment | Single deployment, multi-user |
| **Authentication** | EspoCRM API Key per user | Auth0 OAuth Token |
| **Authorization** | EspoCRM RBAC only | OAuth Scopes + FGA |
| **Identity Management** | EspoCRM users | Auth0 centralized |
| **API Key Security** | Exposed to users | Service account (hidden) |
| **Permission Granularity** | Role-based | Entity-level + relationships |
| **SSO Support** | No | Yes |
| **External Users** | Not supported | Fully supported |
| **Compliance** | Manual | Built-in |
| **Maintenance** | High (distributed) | Low (centralized) |
| **Cost** | Lower initial | Higher initial, lower long-term |

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Auth0 account with configured API
- EspoCRM instance with API access

### Setup

1. **Clone the repository**
   ```bash
   cd EspoCRM-MCP-Auth0
   ```

2. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Linux/macOS:
   source venv/bin/activate

   # On Windows:
   # venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration:
   ```env
   # Auth0 Configuration
   AUTH0_DOMAIN=your-tenant.us.auth0.com
   AUTH0_AUDIENCE=https://your-api-identifier
   MCP_SERVER_URL=http://localhost:3001

   # EspoCRM Configuration
   ESPOCRM_URL=https://your-espocrm-instance.com
   ESPOCRM_API_KEY=your-api-key
   ESPOCRM_SECRET_KEY=your-secret-key-for-hmac
   ESPOCRM_AUTH_METHOD=apikey

   # Server Configuration
   PORT=3001
   DEBUG=true
   CORS_ORIGINS=*

   # FGA Configuration (Optional - for fine-grained authorization)
   FGA_ENABLED=false
   FGA_API_URL=https://api.us1.fga.dev
   FGA_API_ISSUER=auth.fga.dev
   FGA_API_AUDIENCE=https://api.us1.fga.dev/
   FGA_STORE_ID=your-fga-store-id
   FGA_CLIENT_ID=your-fga-client-id
   FGA_CLIENT_SECRET=your-fga-client-secret
   FGA_AUTHORIZATION_MODEL_ID=your-authorization-model-id
   ```

5. **(Optional) Initialize FGA**
   
   If you want to use fine-grained authorization:
   
   ```bash
   # First, configure FGA credentials in .env
   # Then run the initialization script
   python scripts/fga_init.py
   ```
   
   This will create the authorization model and sample data. Add the returned model ID to your `.env` file.

6. **Run the server**
   ```bash
   python -m src.server
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn src.server:app --port 3001
   ```

## Configuration

### Auth0 Setup

1. Create an API in your Auth0 dashboard
2. Set the API identifier as `AUTH0_AUDIENCE`
3. Configure scopes for the API:
   - `espocrm:contacts:read`
   - `espocrm:contacts:write`
   - `espocrm:accounts:read`
   - `espocrm:accounts:write`
   - `espocrm:leads:read`
   - `espocrm:leads:write`
   - `espocrm:entities:read`

### EspoCRM Setup

1. **API Key Authentication** (simpler):
   - Generate an API key in EspoCRM
   - Set `ESPOCRM_AUTH_METHOD=apikey`
   - Set `ESPOCRM_API_KEY` to your API key

2. **HMAC Authentication** (more secure):
   - Generate an API key and secret key in EspoCRM
   - Set `ESPOCRM_AUTH_METHOD=hmac`
   - Set both `ESPOCRM_API_KEY` and `ESPOCRM_SECRET_KEY`

### FGA Setup (Optional)

Fine-Grained Authorization provides entity-level access control. To enable FGA:

1. **Create FGA Account**:
   - Sign up at [Okta FGA](https://fga.dev) or use [OpenFGA](https://openfga.dev)
   - Create a new store
   - Generate client credentials

2. **Configure FGA**:
   - Set `FGA_ENABLED=true` in your `.env` file
   - Add your FGA credentials:
     - `FGA_API_URL`: FGA API endpoint (e.g., `https://api.us1.fga.dev`)
     - `FGA_STORE_ID`: Your FGA store ID
     - `FGA_CLIENT_ID`: Your FGA client ID
     - `FGA_CLIENT_SECRET`: Your FGA client secret
     - `FGA_API_ISSUER`: (Optional) Default is `auth.fga.dev`
     - `FGA_API_AUDIENCE`: (Optional) Default is derived from API URL

3. **Initialize Authorization Model**:
   ```bash
   python scripts/fga_init.py
   ```
   
   This creates the authorization model for EspoCRM entities and writes sample tuples. The script will output the authorization model ID - add this to your `.env` file as `FGA_AUTHORIZATION_MODEL_ID`.

4. **How It Works**:
   - FGA checks are performed automatically when tools are called
   - Both scope and FGA checks are applied (defense-in-depth)
   - If FGA is not configured, only scope-based authorization is used
   - The initialization script can be run multiple times safely (handles duplicates)

For detailed FGA documentation, see [FGA_INTEGRATION.md](FGA_INTEGRATION.md).

## API Reference

### MCP Tools

#### Health Check
```python
health_check() -> str
```
Returns the connection status and EspoCRM version information.

#### Create Contact
```python
create_contact(
    first_name: str,
    last_name: str,
    email_address: str | None = None,
    phone_number: str | None = None,
    account_id: str | None = None,
    title: str | None = None,
    description: str | None = None
) -> str
```

#### Search Contacts
```python
search_contacts(
    search_term: str | None = None,
    email_address: str | None = None,
    limit: int = 20,
    offset: int = 0
) -> str
```

#### Get Contact
```python
get_contact(contact_id: str) -> str
```

#### Create Account
```python
create_account(
    name: str,
    account_type: str | None = None,
    industry: str | None = None,
    website: str | None = None,
    email_address: str | None = None,
    phone_number: str | None = None,
    description: str | None = None
) -> str
```

#### Search Accounts
```python
search_accounts(
    name: str | None = None,
    account_type: str | None = None,
    industry: str | None = None,
    limit: int = 20,
    offset: int = 0
) -> str
```

#### Create Lead
```python
create_lead(
    first_name: str,
    last_name: str,
    source: str,
    email_address: str | None = None,
    phone_number: str | None = None,
    account_name: str | None = None,
    status: str = "New",
    description: str | None = None
) -> str
```

#### Search Leads
```python
search_leads(
    name: str | None = None,
    status: str | None = None,
    source: str | None = None,
    limit: int = 20,
    offset: int = 0
) -> str
```

#### Search Entity (Generic)
```python
search_entity(
    entity_type: str,
    filters: dict[str, Any] | None = None,
    select: list[str] | None = None,
    limit: int = 20,
    offset: int = 0
) -> str
```

#### Get Entity (Generic)
```python
get_entity(
    entity_type: str,
    entity_id: str,
    select: list[str] | None = None
) -> str
```

## Architecture

```
src/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── server.py                # Main server application
├── tools.py                 # MCP tool definitions
├── auth0/                   # Auth0 integration
│   ├── __init__.py          # Auth0 MCP wrapper
│   ├── authz.py             # Authorization decorators (scopes + FGA)
│   ├── errors.py            # Error classes
│   ├── fga.py               # FGA client wrapper
│   └── middleware.py        # Authentication middleware
└── espocrm/                 # EspoCRM client
    ├── __init__.py          # Client exports
    ├── client.py            # API client implementation
    └── types.py             # Type definitions

scripts/
└── fga_init.py              # FGA initialization script

schema.fga                    # FGA authorization model definition
```

## Development

### Running in Development Mode

Make sure your virtual environment is activated:

```bash
# On Linux/macOS:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

Then run the server:

```bash
python -m src.server
```

### Code Formatting

```bash
ruff format src/
```

### Linting

```bash
ruff check src/
```

## Future Enhancements

Future versions may include:

- Additional entity types (Opportunities, Meetings, Tasks, etc.)
- Update and delete operations
- Relationship management tools
- Bulk operations
- Advanced search with complex filters
- Webhook support for real-time updates
- Caching for improved performance
- FGA tuple synchronization with EspoCRM data changes
- Admin UI for managing FGA permissions

## Documentation

- [FGA Integration Guide](FGA_INTEGRATION.md) - Detailed FGA setup and usage
- [FGA Implementation Summary](FGA_IMPLEMENTATION_SUMMARY.md) - Technical implementation details

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit pull requests or open issues for any improvements or bug fixes.
