"""Meeting management tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import apply_fga, format_entity_list, format_json, get_espocrm_client


def register_meeting_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="create_meeting",
        title="Create Meeting",
        description="Create a new meeting in EspoCRM",
    )
    @require_scopes(["espocrm:meetings:write"])
    async def create_meeting(
        name: str,
        date_start: str,
        date_end: str,
        location: str | None = None,
        description: str | None = None,
        status: str = "Planned",
        parent_type: str | None = None,
        parent_id: str | None = None,
        contacts_ids: list[str] | None = None,
        users_ids: list[str] | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data = {
            "name": name,
            "dateStart": date_start,
            "dateEnd": date_end,
            "status": status,
        }
        if location:
            data["location"] = location
        if description:
            data["description"] = description
        if parent_type:
            data["parentType"] = parent_type
        if parent_id:
            data["parentId"] = parent_id

        result = await client.post("Meeting", data)
        meeting_id = result.get("id")

        if contacts_ids:
            await client.link_records("Meeting", meeting_id, "contacts", contacts_ids)
        if users_ids:
            await client.link_records("Meeting", meeting_id, "users", users_ids)

        return f"Successfully created meeting: {name} ({status}) (ID: {meeting_id})"

    @mcp.tool(
        name="search_meetings",
        title="Search Meetings",
        description="Search for meetings in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:meetings:read"])
    async def search_meetings(
        name: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        assigned_user_name: str | None = None,
        location: str | None = None,
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
        if assigned_user_name:
            where.append(
                WhereClause(
                    type="contains",
                    attribute="assignedUserName",
                    value=assigned_user_name,
                )
            )
        if location:
            where.append(
                WhereClause(type="contains", attribute="location", value=location)
            )

        response = await client.search(
            "Meeting",
            where=where if where else None,
            select=[
                "id",
                "name",
                "status",
                "dateStart",
                "dateEnd",
                "location",
                "assignedUserName",
            ],
            max_size=limit,
            offset=offset,
            order_by="dateStart",
        )

        return format_entity_list(response.list or [], "meetings")

    @mcp.tool(
        name="get_meeting",
        title="Get Meeting",
        description="Get detailed information about a specific meeting",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:meetings:read"])
    @apply_fga("get_meeting")
    async def get_meeting(meeting_id: str, ctx: Context | None = None) -> str:
        client = get_espocrm_client()
        meeting = await client.get_by_id("Meeting", meeting_id)
        return format_json(meeting)

    @mcp.tool(
        name="update_meeting",
        title="Update Meeting",
        description="Update an existing meeting in EspoCRM",
    )
    @require_scopes(["espocrm:meetings:write"])
    @apply_fga("update_meeting")
    async def update_meeting(
        meeting_id: str,
        name: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        location: str | None = None,
        description: str | None = None,
        status: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data = {}
        if name is not None:
            data["name"] = name
        if date_start is not None:
            data["dateStart"] = date_start
        if date_end is not None:
            data["dateEnd"] = date_end
        if location is not None:
            data["location"] = location
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status

        await client.put("Meeting", meeting_id, data)
        return f"Successfully updated meeting with ID: {meeting_id}"
