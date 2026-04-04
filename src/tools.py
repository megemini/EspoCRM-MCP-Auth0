"""MCP tools for EspoCRM operations."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from mcp.server.fastmcp import Context

from .auth0 import Auth0Mcp
from .auth0.authz import (
    register_required_scopes,
    require_fga_permission,
    require_scopes,
)
from .espocrm import EspoCRMClient, WhereClause

logger = logging.getLogger(__name__)

# Global EspoCRM client instance
_espocrm_client: Optional[EspoCRMClient] = None


def get_espocrm_client() -> EspoCRMClient:
    """Get the EspoCRM client instance."""
    if _espocrm_client is None:
        raise RuntimeError("EspoCRM client not initialized")
    return _espocrm_client


def set_espocrm_client(client: EspoCRMClient) -> None:
    """Set the EspoCRM client instance."""
    global _espocrm_client
    _espocrm_client = client


def format_entity_list(entities: list[dict[str, Any]], entity_type: str) -> str:
    """Format a list of entities for display."""
    if not entities:
        return f"No {entity_type} found."

    lines = [f"Found {len(entities)} {entity_type}:"]
    for entity in entities:
        entity_id = entity.get("id", "N/A")
        name = entity.get("name") or entity.get("firstName", "")
        if entity.get("lastName"):
            name = f"{name} {entity.get('lastName')}".strip()
        lines.append(f"  - ID: {entity_id}, Name: {name or 'N/A'}")
    return "\n".join(lines)


def register_tools(auth0_mcp: Auth0Mcp) -> None:
    """
    Register all EspoCRM tools with the MCP server.
    """
    mcp = auth0_mcp.mcp

    # Health check tool (no auth required)
    @mcp.tool(
        name="health_check",
        title="Health Check",
        description="Check EspoCRM connection and API status",
        annotations={"readOnlyHint": True},
    )
    async def health_check() -> str:
        """Check EspoCRM connection and API status."""
        client = get_espocrm_client()
        result = await client.test_connection()

        if result.get("success"):
            return json.dumps(
                {
                    "status": "healthy",
                    "user": result.get("user", {}).get("userName", "Unknown"),
                    "version": result.get("version", "Unknown"),
                },
                indent=2,
            )
        else:
            return json.dumps(
                {"status": "unhealthy", "error": result.get("error", "Unknown error")},
                indent=2,
            )

    # Contact tools
    @mcp.tool(
        name="create_contact",
        title="Create Contact",
        description="Create a new contact in EspoCRM",
    )
    @require_scopes(["espocrm:contacts:write"])
    async def create_contact(
        first_name: str,
        last_name: str,
        email_address: str | None = None,
        phone_number: str | None = None,
        account_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Create a new contact in EspoCRM."""
        client = get_espocrm_client()

        data = {
            "firstName": first_name,
            "lastName": last_name,
        }
        if email_address:
            data["emailAddress"] = email_address
        if phone_number:
            data["phoneNumber"] = phone_number
        if account_id:
            data["accountId"] = account_id
        if title:
            data["title"] = title
        if description:
            data["description"] = description

        result = await client.post("Contact", data)
        return f"Successfully created contact: {first_name} {last_name} (ID: {result.get('id')})"

    @mcp.tool(
        name="search_contacts",
        title="Search Contacts",
        description="Search for contacts in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:contacts:read"])
    async def search_contacts(
        search_term: str | None = None,
        email_address: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        """Search for contacts in EspoCRM."""
        client = get_espocrm_client()

        where = []
        if search_term:
            where.append(
                WhereClause(
                    type="or",
                    value=[
                        {
                            "type": "contains",
                            "attribute": "firstName",
                            "value": search_term,
                        },
                        {
                            "type": "contains",
                            "attribute": "lastName",
                            "value": search_term,
                        },
                        {
                            "type": "contains",
                            "attribute": "emailAddress",
                            "value": search_term,
                        },
                    ],
                )
            )
        if email_address:
            where.append(
                WhereClause(
                    type="equals", attribute="emailAddress", value=email_address
                )
            )

        response = await client.search(
            "Contact",
            where=where if where else None,
            select=[
                "id",
                "firstName",
                "lastName",
                "emailAddress",
                "phoneNumber",
                "accountName",
            ],
            max_size=limit,
            offset=offset,
            order_by="lastName",
        )

        return format_entity_list(response.list or [], "contacts")

    @mcp.tool(
        name="get_contact",
        title="Get Contact",
        description="Get detailed information about a specific contact",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:contacts:read"])
    @require_fga_permission(
        object_type="contact", object_id_param="contact_id", relation="can_read"
    )
    async def get_contact(contact_id: str, ctx: Context | None = None) -> str:
        """Get detailed information about a specific contact."""
        client = get_espocrm_client()
        contact = await client.get_by_id("Contact", contact_id)
        return json.dumps(contact, indent=2)

    # Account tools
    @mcp.tool(
        name="create_account",
        title="Create Account",
        description="Create a new account/company in EspoCRM",
    )
    @require_scopes(["espocrm:accounts:write"])
    async def create_account(
        name: str,
        account_type: str | None = None,
        industry: str | None = None,
        website: str | None = None,
        email_address: str | None = None,
        phone_number: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Create a new account/company in EspoCRM."""
        client = get_espocrm_client()

        data = {"name": name}
        if account_type:
            data["type"] = account_type
        if industry:
            data["industry"] = industry
        if website:
            data["website"] = website
        if email_address:
            data["emailAddress"] = email_address
        if phone_number:
            data["phoneNumber"] = phone_number
        if description:
            data["description"] = description

        result = await client.post("Account", data)
        return f"Successfully created account: {name} (ID: {result.get('id')})"

    @mcp.tool(
        name="search_accounts",
        title="Search Accounts",
        description="Search for accounts/companies in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:accounts:read"])
    async def search_accounts(
        name: str | None = None,
        account_type: str | None = None,
        industry: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        """Search for accounts/companies in EspoCRM."""
        client = get_espocrm_client()

        where = []
        if name:
            where.append(WhereClause(type="contains", attribute="name", value=name))
        if account_type:
            where.append(
                WhereClause(type="equals", attribute="type", value=account_type)
            )
        if industry:
            where.append(
                WhereClause(type="contains", attribute="industry", value=industry)
            )

        response = await client.search(
            "Account",
            where=where if where else None,
            select=["id", "name", "type", "industry", "website", "emailAddress"],
            max_size=limit,
            offset=offset,
            order_by="name",
        )

        return format_entity_list(response.list or [], "accounts")

    # Lead tools
    @mcp.tool(
        name="create_lead",
        title="Create Lead",
        description="Create a new lead in EspoCRM",
    )
    @require_scopes(["espocrm:leads:write"])
    async def create_lead(
        first_name: str,
        last_name: str,
        source: str,
        email_address: str | None = None,
        phone_number: str | None = None,
        account_name: str | None = None,
        status: str = "New",
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Create a new lead in EspoCRM."""
        client = get_espocrm_client()

        data = {
            "firstName": first_name,
            "lastName": last_name,
            "source": source,
            "status": status,
        }
        if email_address:
            data["emailAddress"] = email_address
        if phone_number:
            data["phoneNumber"] = phone_number
        if account_name:
            data["accountName"] = account_name
        if description:
            data["description"] = description

        result = await client.post("Lead", data)
        return f"Successfully created lead: {first_name} {last_name} (ID: {result.get('id')})"

    @mcp.tool(
        name="search_leads",
        title="Search Leads",
        description="Search for leads in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:leads:read"])
    async def search_leads(
        name: str | None = None,
        status: str | None = None,
        source: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        """Search for leads in EspoCRM."""
        client = get_espocrm_client()

        where = []
        if name:
            where.append(
                WhereClause(
                    type="or",
                    value=[
                        {"type": "contains", "attribute": "firstName", "value": name},
                        {"type": "contains", "attribute": "lastName", "value": name},
                    ],
                )
            )
        if status:
            where.append(WhereClause(type="equals", attribute="status", value=status))
        if source:
            where.append(WhereClause(type="equals", attribute="source", value=source))

        response = await client.search(
            "Lead",
            where=where if where else None,
            select=["id", "firstName", "lastName", "status", "source", "accountName"],
            max_size=limit,
            offset=offset,
            order_by="lastName",
        )

        return format_entity_list(response.list or [], "leads")

    # Generic entity tools
    @mcp.tool(
        name="search_entity",
        title="Search Entity",
        description="Search any entity type in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:entities:read"])
    async def search_entity(
        entity_type: str,
        filters: dict[str, Any] | None = None,
        select: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        """Search any entity type in EspoCRM."""
        client = get_espocrm_client()

        where = []
        if filters:
            for key, value in filters.items():
                where.append(WhereClause(type="contains", attribute=key, value=value))

        response = await client.search(
            entity_type,
            where=where if where else None,
            select=select,
            max_size=limit,
            offset=offset,
        )

        return format_entity_list(response.list or [], entity_type)

    @mcp.tool(
        name="get_entity",
        title="Get Entity",
        description="Get a specific entity by ID",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:entities:read"])
    @require_fga_permission(
        object_type="entity", object_id_param="entity_id", relation="can_read"
    )
    async def get_entity(
        entity_type: str,
        entity_id: str,
        select: list[str] | None = None,
        ctx: Context | None = None,
    ) -> str:
        """Get a specific entity by ID."""
        client = get_espocrm_client()
        entity = await client.get_by_id(entity_type, entity_id, select)
        return json.dumps(entity, indent=2)

    # Register all scopes used by tools
    register_required_scopes(auth0_mcp)
