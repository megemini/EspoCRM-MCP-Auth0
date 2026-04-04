"""Relationship management tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from .base import check_fga_dynamic, format_entity_list, get_espocrm_client


def register_relationship_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="link_entities",
        title="Link Entities",
        description="Create relationships between entities in EspoCRM",
    )
    @require_scopes(["espocrm:entities:write"])
    async def link_entities(
        entity_type: str,
        entity_id: str,
        relationship_name: str,
        related_entity_ids: list[str],
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await check_fga_dynamic(ctx, entity_type, entity_id, "can_write")
        await client.link_records(
            entity_type, entity_id, relationship_name, related_entity_ids
        )
        return (
            f"Successfully linked {len(related_entity_ids)} entities to "
            f"{entity_type} {entity_id} via relationship '{relationship_name}'"
        )

    @mcp.tool(
        name="unlink_entities",
        title="Unlink Entities",
        description="Remove relationships between entities in EspoCRM",
    )
    @require_scopes(["espocrm:entities:write"])
    async def unlink_entities(
        entity_type: str,
        entity_id: str,
        relationship_name: str,
        related_entity_ids: list[str],
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await check_fga_dynamic(ctx, entity_type, entity_id, "can_write")
        await client.unlink_records(
            entity_type, entity_id, relationship_name, related_entity_ids
        )
        return (
            f"Successfully unlinked {len(related_entity_ids)} entities from "
            f"{entity_type} {entity_id} via relationship '{relationship_name}'"
        )

    @mcp.tool(
        name="get_entity_relationships",
        title="Get Entity Relationships",
        description="Get related entities for a specific relationship on an entity",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:entities:read"])
    async def get_entity_relationships(
        entity_type: str,
        entity_id: str,
        link_field: str,
        where: dict | None = None,
        select: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        params: dict = {"maxSize": limit, "offset": offset}
        if select:
            params["select"] = ",".join(select)

        result = await client.get_related(
            entity_type,
            entity_id,
            link_field,
            params=params,
        )

        if not result or not result.list:
            return f"No related entities found for {entity_type} {entity_id} via '{link_field}'."

        return format_entity_list(
            result.list, f"{link_field} of {entity_type} {entity_id}"
        )
