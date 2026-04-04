"""User management tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import format_entity_list, format_json, get_espocrm_client


def register_user_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="search_users",
        title="Search Users",
        description="Search for users in the EspoCRM system",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:users:read"])
    async def search_users(
        user_name: str | None = None,
        email_address: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_active: bool | None = None,
        user_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        where = []
        if user_name:
            where.append(
                WhereClause(type="contains", attribute="userName", value=user_name)
            )
        if email_address:
            where.append(
                WhereClause(
                    type="equals", attribute="emailAddress", value=email_address
                )
            )
        if first_name:
            where.append(
                WhereClause(type="contains", attribute="firstName", value=first_name)
            )
        if last_name:
            where.append(
                WhereClause(type="contains", attribute="lastName", value=last_name)
            )
        if is_active is not None:
            where.append(
                WhereClause(type="equals", attribute="isActive", value=is_active)
            )
        if user_type:
            where.append(WhereClause(type="equals", attribute="type", value=user_type))

        response = await client.search(
            "User",
            where=where if where else None,
            select=[
                "id",
                "userName",
                "firstName",
                "lastName",
                "emailAddress",
                "type",
                "isActive",
            ],
            max_size=limit,
            offset=offset,
            order_by="userName",
        )

        return format_entity_list(response.list or [], "users")

    @mcp.tool(
        name="get_user_by_email",
        title="Get User by Email",
        description="Find a user by their email address",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:users:read"])
    async def get_user_by_email(email_address: str, ctx: Context | None = None) -> str:
        client = get_espocrm_client()

        response = await client.search(
            "User",
            where=[
                WhereClause(
                    type="equals", attribute="emailAddress", value=email_address
                )
            ],
            max_size=1,
        )

        if not response.list:
            return f"No user found with email: {email_address}"

        return format_json(response.list[0])
