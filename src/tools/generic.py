"""Generic entity CRUD tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from .base import check_fga_dynamic, format_entity_list, format_json, get_espocrm_client


def register_generic_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="create_entity",
        title="Create Entity",
        description="Create a record for any entity type in EspoCRM",
    )
    @require_scopes(["espocrm:entities:write"])
    async def create_entity(
        entity_type: str,
        data: dict[str, Any],
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        result = await client.post(entity_type, data)
        return f"Successfully created {entity_type} record with ID: {result.get('id')}"

    @mcp.tool(
        name="search_entity",
        title="Search Entity",
        description="Search for records of any entity type in EspoCRM",
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
        from ..espocrm import WhereClause

        client = get_espocrm_client()

        where = []
        if filters:
            for key, value in filters.items():
                where.append(WhereClause(type="equals", attribute=key, value=value))

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
        description="Get a specific entity record by ID and type",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:entities:read"])
    async def get_entity(
        entity_type: str,
        entity_id: str,
        select: list[str] | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await check_fga_dynamic(ctx, entity_type, entity_id, "can_read")
        entity = await client.get_by_id(entity_type, entity_id, select=select)
        return format_json(entity)

    @mcp.tool(
        name="update_entity",
        title="Update Entity",
        description="Update any entity record by ID",
    )
    @require_scopes(["espocrm:entities:write"])
    async def update_entity(
        entity_type: str,
        entity_id: str,
        data: dict[str, Any],
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await check_fga_dynamic(ctx, entity_type, entity_id, "can_update")
        await client.put(entity_type, entity_id, data)
        return f"Successfully updated {entity_type} record with ID: {entity_id}"

    @mcp.tool(
        name="delete_entity",
        title="Delete Entity",
        description="Delete any entity record by ID",
    )
    @require_scopes(["espocrm:entities:delete"])
    async def delete_entity(
        entity_type: str,
        entity_id: str,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await check_fga_dynamic(ctx, entity_type, entity_id, "can_delete")
        await client.delete(entity_type, entity_id)
        return f"Successfully deleted {entity_type} record with ID: {entity_id}"
