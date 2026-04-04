"""Note tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import format_entity_list, get_espocrm_client


def register_note_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="add_note",
        title="Add Note",
        description="Add a note/comment to any entity in EspoCRM",
    )
    @require_scopes(["espocrm:notes:write"])
    async def add_note(
        parent_type: str,
        parent_id: str,
        post: str,
        attachments: list[dict[str, Any]] | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data: dict[str, Any] = {
            "parentType": parent_type,
            "parentId": parent_id,
            "post": post,
        }
        if attachments:
            data["attachments"] = attachments

        result = await client.post("Note", data)
        return f"Successfully added note to {parent_type} {parent_id} (ID: {result.get('id')})"

    @mcp.tool(
        name="search_notes",
        title="Search Notes",
        description="Search for notes across entities in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:notes:read"])
    async def search_notes(
        parent_type: str | None = None,
        parent_id: str | None = None,
        search_term: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        where = []
        if parent_type:
            where.append(
                WhereClause(type="equals", attribute="parentType", value=parent_type)
            )
        if parent_id:
            where.append(
                WhereClause(type="equals", attribute="parentId", value=parent_id)
            )
        if search_term:
            where.append(
                WhereClause(type="contains", attribute="post", value=search_term)
            )

        response = await client.search(
            "Note",
            where=where if where else None,
            select=[
                "id",
                "post",
                "parentType",
                "parentId",
                "createdAt",
                "createdByName",
            ],
            max_size=limit,
            offset=offset,
            order_by="createdAt",
        )

        return format_entity_list(response.list or [], "notes")
