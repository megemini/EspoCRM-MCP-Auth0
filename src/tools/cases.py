"""Case (support ticket) tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import apply_fga, format_entity_list, get_espocrm_client


def register_case_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="create_case",
        title="Create Case",
        description="Create a support case/ticket in EspoCRM",
    )
    @require_scopes(["espocrm:cases:write"])
    async def create_case(
        name: str,
        case_type: str | None = None,
        priority: str = "Normal",
        status: str = "New",
        account_id: str | None = None,
        contact_id: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data = {"name": name, "priority": priority, "status": status}
        if case_type:
            data["type"] = case_type
        if account_id:
            data["accountId"] = account_id
        if contact_id:
            data["contactId"] = contact_id
        if description:
            data["description"] = description

        result = await client.post("Case", data)
        return (
            f"Successfully created case: {name} ({priority}) (ID: {result.get('id')})"
        )

    @mcp.tool(
        name="search_cases",
        title="Search Cases",
        description="Search for support cases in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:cases:read"])
    async def search_cases(
        name: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        case_type: str | None = None,
        account_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        where = []
        if name:
            where.append(WhereClause(type="contains", attribute="name", value=name))
        if status:
            where.append(WhereClause(type="equals", attribute="status", value=status))
        if priority:
            where.append(
                WhereClause(type="equals", attribute="priority", value=priority)
            )
        if case_type:
            where.append(WhereClause(type="equals", attribute="type", value=case_type))
        if account_id:
            where.append(
                WhereClause(type="equals", attribute="accountId", value=account_id)
            )

        response = await client.search(
            "Case",
            where=where if where else None,
            select=[
                "id",
                "name",
                "status",
                "priority",
                "type",
                "accountName",
                "contactName",
            ],
            max_size=limit,
            offset=offset,
            order_by="createdAt",
        )

        return format_entity_list(response.list or [], "cases")

    @mcp.tool(
        name="update_case",
        title="Update Case",
        description="Update an existing support case",
    )
    @require_scopes(["espocrm:cases:write"])
    @apply_fga("update_case")
    async def update_case(
        case_id: str,
        name: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        description: str | None = None,
        resolution: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data = {}
        if name is not None:
            data["name"] = name
        if status is not None:
            data["status"] = status
        if priority is not None:
            data["priority"] = priority
        if description is not None:
            data["description"] = description
        if resolution is not None:
            data["resolution"] = resolution

        await client.put("Case", case_id, data)
        return f"Successfully updated case with ID: {case_id}"
