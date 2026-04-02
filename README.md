# EspoCRM MCP Server with Auth0 Authentication

A Model Context Protocol (MCP) server for EspoCRM with Auth0 authentication and authorization.

## Overview

This project provides an MCP server that integrates with EspoCRM, allowing AI assistants and other MCP clients to interact with EspoCRM data through a standardized interface. The server includes:

- **Auth0 Authentication**: Secure token-based authentication using Auth0
- **Scope-based Authorization**: Fine-grained access control using OAuth scopes
- **EspoCRM Integration**: Full API client for EspoCRM with support for both API key and HMAC authentication
- **Basic MCP Tools**: Essential tools for managing contacts, accounts, leads, and other entities

## Features

### Implemented Tools (First Version)

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
   ```

5. **Run the server**
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
│   ├── authz.py             # Authorization decorators
│   ├── errors.py            # Error classes
│   └── middleware.py        # Authentication middleware
└── espocrm/                 # EspoCRM client
    ├── __init__.py          # Client exports
    ├── client.py            # API client implementation
    └── types.py             # Type definitions
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

This is the first version with basic functionality. Future versions may include:

- Additional entity types (Opportunities, Meetings, Tasks, etc.)
- Update and delete operations
- Relationship management tools
- Bulk operations
- Advanced search with complex filters
- Webhook support for real-time updates
- Caching for improved performance

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit pull requests or open issues for any improvements or bug fixes.
