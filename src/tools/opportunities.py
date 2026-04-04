"""Opportunity management tools."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import format_entity_list, get_espocrm_client


def register_opportunity_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="create_opportunity",
        title="Create Opportunity",
        description="Create a new sales opportunity in EspoCRM",
    )
    @require_scopes(["espocrm:opportunities:write"])
    async def create_opportunity(
        name: str,
        account_id: str,
        stage: str,
        amount: float | None = None,
        close_date: str | None = None,
        probability: int | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data: dict[str, Any] = {
            "name": name,
            "accountId": account_id,
            "stage": stage,
        }
        if close_date:
            data["closeDate"] = close_date
        else:
            data["closeDate"] = (datetime.now() + timedelta(days=90)).strftime(
                "%Y-%m-%d"
            )
        if amount is not None:
            data["amount"] = amount
        if probability is not None:
            data["probability"] = probability
        if description:
            data["description"] = description

        result = await client.post("Opportunity", data)
        return f"Successfully created opportunity: {name} ({stage}) (ID: {result.get('id')})"

    @mcp.tool(
        name="search_opportunities",
        title="Search Opportunities",
        description="Search for sales opportunities in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:opportunities:read"])
    async def search_opportunities(
        name: str | None = None,
        account_name: str | None = None,
        stage: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        where = []
        if name:
            where.append(WhereClause(type="contains", attribute="name", value=name))
        if account_name:
            where.append(
                WhereClause(
                    type="contains", attribute="accountName", value=account_name
                )
            )
        if stage:
            where.append(WhereClause(type="equals", attribute="stage", value=stage))
        if min_amount is not None:
            where.append(
                WhereClause(
                    type="greaterThanOrEquals", attribute="amount", value=min_amount
                )
            )
        if max_amount is not None:
            where.append(
                WhereClause(
                    type="lessThanOrEquals", attribute="amount", value=max_amount
                )
            )

        response = await client.search(
            "Opportunity",
            where=where if where else None,
            select=[
                "id",
                "name",
                "stage",
                "amount",
                "closeDate",
                "probability",
                "accountName",
            ],
            max_size=limit,
            offset=offset,
            order_by="createdAt",
        )

        return format_entity_list(response.list or [], "opportunities")
