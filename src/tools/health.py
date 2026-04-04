"""Health check tool."""

from __future__ import annotations

import json

from ..auth0 import Auth0Mcp
from .base import get_espocrm_client


def register_health_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="health_check",
        title="Health Check",
        description="Check EspoCRM connection and API status",
        annotations={"readOnlyHint": True},
    )
    async def health_check() -> str:
        client = get_espocrm_client()
        result = await client.test_connection()

        if result.get("success"):
            return json.dumps(
                {
                    "status": "healthy",
                    "user": result.get("user", {}).get("userName", "Unknown"),
                    "version": result.get("version", "Unknown"),
                },
                indent=2,
            )
        else:
            return json.dumps(
                {"status": "unhealthy", "error": result.get("error", "Unknown error")},
                indent=2,
            )
