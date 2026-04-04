"""Account management tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import format_entity_list, get_espocrm_client


def register_account_tools(mcp: Auth0Mcp.mcp_class) -> None:

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
