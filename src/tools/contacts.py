"""Contact management tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import apply_fga, format_entity_list, format_json, get_espocrm_client


def register_contact_tools(mcp: Auth0Mcp.mcp_class) -> None:

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
        department: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
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
        if department:
            data["department"] = department
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
        phone_number: str | None = None,
        account_name: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
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
        if phone_number:
            where.append(
                WhereClause(
                    type="contains", attribute="phoneNumber", value=phone_number
                )
            )
        if account_name:
            where.append(
                WhereClause(
                    type="contains", attribute="accountName", value=account_name
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
    @apply_fga("get_contact")
    async def get_contact(contact_id: str, ctx: Context | None = None) -> str:
        client = get_espocrm_client()
        contact = await client.get_by_id("Contact", contact_id)
        return format_json(contact)
