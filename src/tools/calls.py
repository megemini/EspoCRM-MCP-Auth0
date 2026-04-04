"""Call (phone call logging) tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import format_entity_list, get_espocrm_client


def register_call_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="create_call",
        title="Create Call",
        description="Log a phone call in EspoCRM",
    )
    @require_scopes(["espocrm:calls:write"])
    async def create_call(
        name: str,
        direction: str = "Outbound",
        status: str = "Held",
        duration: int | None = None,
        parent_type: str | None = None,
        parent_id: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data: dict[str, Any] = {
            "name": name,
            "direction": direction,
            "status": status,
        }
        if duration is not None:
            data["duration"] = duration
        if parent_type:
            data["parentType"] = parent_type
        if parent_id:
            data["parentId"] = parent_id
        if description:
            data["description"] = description

        result = await client.post("Call", data)
        return (
            f"Successfully logged call: {name} ({direction}) (ID: {result.get('id')})"
        )

    @mcp.tool(
        name="search_calls",
        title="Search Calls",
        description="Search for logged calls in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:calls:read"])
    async def search_calls(
        date_from: str | None = None,
        date_to: str | None = None,
        direction: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        where = []
        if date_from:
            where.append(
                WhereClause(
                    type="greaterThanOrEquals",
                    attribute="dateStart",
                    value=f"{date_from} 00:00:00",
                )
            )
        if date_to:
            where.append(
                WhereClause(
                    type="lessThanOrEquals",
                    attribute="dateStart",
                    value=f"{date_to} 23:59:59",
                )
            )
        if direction:
            where.append(
                WhereClause(type="equals", attribute="direction", value=direction)
            )
        if status:
            where.append(WhereClause(type="equals", attribute="status", value=status))

        response = await client.search(
            "Call",
            where=where if where else None,
            select=[
                "id",
                "name",
                "direction",
                "status",
                "duration",
                "dateStart",
                "parentType",
                "parentName",
            ],
            max_size=limit,
            offset=offset,
            order_by="dateStart",
        )

        return format_entity_list(response.list or [], "calls")
