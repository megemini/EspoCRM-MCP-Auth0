"""Team and role management tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import format_entity_list, get_espocrm_client


def register_team_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="add_user_to_team",
        title="Add User to Team",
        description="Add a user to a team",
    )
    @require_scopes(["espocrm:teams:write"])
    async def add_user_to_team(
        user_id: str,
        team_id: str,
        position: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await client.link_records("Team", team_id, "users", [user_id])
        extra = f" with position: {position}" if position else ""
        return f"Successfully added user {user_id} to team {team_id}{extra}"

    @mcp.tool(
        name="remove_user_from_team",
        title="Remove User from Team",
        description="Remove a user from a team",
    )
    @require_scopes(["espocrm:teams:write"])
    async def remove_user_from_team(
        user_id: str,
        team_id: str,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await client.unlink_records("Team", team_id, "users", [user_id])
        return f"Successfully removed user {user_id} from team {team_id}"

    @mcp.tool(
        name="assign_role_to_user",
        title="Assign Role to User",
        description="Assign a role to a user",
    )
    @require_scopes(["espocrm:users:write"])
    async def assign_role_to_user(
        user_id: str,
        role_id: str,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await client.put("User", user_id, {"rolesIds": [role_id]})
        return f"Successfully assigned role {role_id} to user {user_id}"

    @mcp.tool(
        name="get_user_teams",
        title="Get User Teams",
        description="Get all teams that a user belongs to",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:teams:read"])
    async def get_user_teams(user_id: str, ctx: Context | None = None) -> str:
        client = get_espocrm_client()
        teams = await client.get_related("User", user_id, "teams")

        if not teams or not teams.list:
            return f"User {user_id} is not a member of any teams."

        return format_entity_list(teams.list, "teams")

    @mcp.tool(
        name="get_team_members",
        title="Get Team Members",
        description="Get all members of a team",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:teams:read"])
    async def get_team_members(
        team_id: str,
        limit: int = 50,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        users = await client.get_related(
            "Team", team_id, "users", params={"maxSize": limit, "offset": offset}
        )

        if not users or not users.list:
            return f"Team {team_id} has no members."

        return format_entity_list(users.list, "members")

    @mcp.tool(
        name="search_teams",
        title="Search Teams",
        description="Search for teams in the system",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:teams:read"])
    async def search_teams(
        name: str | None = None,
        description: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        where = []
        if name:
            where.append(WhereClause(type="contains", attribute="name", value=name))
        if description:
            where.append(
                WhereClause(type="contains", attribute="description", value=description)
            )

        response = await client.search(
            "Team",
            where=where if where else None,
            select=["id", "name", "description"],
            max_size=limit,
            offset=offset,
            order_by="name",
        )

        return format_entity_list(response.list or [], "teams")

    @mcp.tool(
        name="get_user_permissions",
        title="Get User Permissions",
        description="Get effective permissions for a user based on roles and teams",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:users:read"])
    async def get_user_permissions(user_id: str, ctx: Context | None = None) -> str:
        client = get_espocrm_client()
        user = await client.get_by_id("User", user_id)

        return (
            f"User Permissions for {user.get('userName', user_id)}:\n"
            f"User Type: {user.get('type', 'Unknown')}\n"
            f"Active: {'Yes' if user.get('isActive', False) is not False else 'No'}\n\n"
            f"Note: Detailed permission breakdown requires custom EspoCRM API integration."
        )
