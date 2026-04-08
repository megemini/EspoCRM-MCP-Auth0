"""Base utilities for MCP tools."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server.fastmcp import Context

from ..auth0.errors import AuthenticationRequired
from ..espocrm import EspoCRMClient

logger = logging.getLogger(__name__)

_espocrm_client: EspoCRMClient | None = None


def get_espocrm_client() -> EspoCRMClient:
    if _espocrm_client is None:
        raise RuntimeError("EspoCRM client not initialized")
    return _espocrm_client


def set_espocrm_client(client: EspoCRMClient) -> None:
    global _espocrm_client
    _espocrm_client = client


def format_entity_list(entities: list[dict[str, Any]], entity_type: str) -> str:
    if not entities:
        return f"No {entity_type} found."

    lines = [f"Found {len(entities)} {entity_type}:"]
    for entity in entities:
        entity_id = entity.get("id", "N/A")
        name = entity.get("name") or entity.get("firstName", "")
        if entity.get("lastName"):
            name = f"{name} {entity.get('lastName')}".strip()
        lines.append(f"  - ID: {entity_id}, Name: {name or 'N/A'}")
    return "\n".join(lines)


def format_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


async def check_fga_dynamic(
    ctx: Context | None,
    object_type: str,
    object_id: str,
    relation: str = "can_read",
) -> None:
    """Runtime FGA permission check for dynamic entity types.

    Use this inside tool functions (not as a decorator) when the entity type
    is determined at runtime from function parameters (e.g., generic_entity tools).
    Silently skips the check if FGA is not configured.
    """
    if ctx is None:
        return
    auth = getattr(ctx.request_context.request.state, "auth", {})
    if not auth:
        raise AuthenticationRequired("Authentication required")

    user_id = auth.get("extra", {}).get("sub")
    if not user_id:
        raise AuthenticationRequired("User ID not found in token")

    try:
        from ..auth0.fga import get_fga_client

        fga_client = get_fga_client()
    except RuntimeError:
        return

    await fga_client.check_permission_or_raise(
        user=user_id,
        object_type=object_type.lower(),
        object_id=str(object_id),
        relation=relation,
    )


def apply_fga(tool_name: str):
    """Apply FGA decorator based on declarative rule from fga_config.

    Returns the original function unchanged if no FGA rule exists for the tool.
    """
    from .fga_config import get_fga_rule

    rule = get_fga_rule(tool_name)
    if not rule:
        return lambda f: f
    from ..auth0.authz import require_fga_permission

    return require_fga_permission(
        object_type=rule.object_type or "",
        object_id_param=rule.object_id_param,
        relation=rule.relation,
    )
