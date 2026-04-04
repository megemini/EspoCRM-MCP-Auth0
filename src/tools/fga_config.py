"""FGA permission configuration for MCP tools.

This module provides a declarative configuration for FGA (Fine-Grained Authorization)
permissions across all MCP tools. Since this project uses a service account to access
EspoCRM, FGA is the primary mechanism for per-entity access control.

Design Principles:
- Service Account Architecture: EspoCRM sees only the service account, not end users.
  FGA enforces per-user entity-level permissions at the MCP layer.
- Defense in Depth: Scope checks (coarse-grained) + FGA checks (fine-grained).
- Explicit Allow List: Only tools listed here get FGA protection; search/list operations
  are intentionally excluded (service account returns all matching data, which is
  documented as a known limitation).

FGA Relations (must match the authorization model defined in fga_init.py):
- can_read: View entity details
- can_update: Modify entity fields
- can_delete: Remove entity
- can_assign: Change ownership/assignment
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FGARule:
    """Defines an FGA permission rule for a tool."""

    object_type: str
    object_id_param: str
    relation: str = "can_read"


TOOL_FGA_RULES: dict[str, FGARule] = {
    "get_contact": FGARule(
        object_type="contact",
        object_id_param="contact_id",
        relation="can_read",
    ),
    "get_meeting": FGARule(
        object_type="meeting",
        object_id_param="meeting_id",
        relation="can_read",
    ),
    "get_task": FGARule(
        object_type="task",
        object_id_param="task_id",
        relation="can_read",
    ),
    "get_entity": FGARule(
        object_type=None,
        object_id_param="entity_id",
        relation="can_read",
    ),
    "update_account": FGARule(
        object_type="account",
        object_id_param="account_id",
        relation="can_update",
    ),
    "update_lead": FGARule(
        object_type="lead",
        object_id_param="lead_id",
        relation="can_update",
    ),
    "update_meeting": FGARule(
        object_type="meeting",
        object_id_param="meeting_id",
        relation="can_update",
    ),
    "update_task": FGARule(
        object_type="task",
        object_id_param="task_id",
        relation="can_update",
    ),
    "update_case": FGARule(
        object_type="case",
        object_id_param="case_id",
        relation="can_update",
    ),
    "update_entity": FGARule(
        object_type=None,
        object_id_param="entity_id",
        relation="can_update",
    ),
    "delete_entity": FGARule(
        object_type=None,
        object_id_param="entity_id",
        relation="can_delete",
    ),
    "assign_lead": FGARule(
        object_type="lead",
        object_id_param="lead_id",
        relation="can_assign",
    ),
    "assign_task": FGARule(
        object_type="task",
        object_id_param="task_id",
        relation="can_assign",
    ),
    "convert_lead": FGARule(
        object_type="lead",
        object_id_param="lead_id",
        relation="can_update",
    ),
    "link_entities": FGARule(
        object_type=None,
        object_id_param="entity_id",
        relation="can_update",
    ),
    "unlink_entities": FGARule(
        object_type=None,
        object_id_param="entity_id",
        relation="can_update",
    ),
}


def get_fga_rule(tool_name: str) -> FGARule | None:
    """Get the FGA rule for a tool, if one exists."""
    return TOOL_FGA_RULES.get(tool_name)


def list_fga_protected_tools() -> dict[str, FGARule]:
    """List all tools that have FGA protection configured."""
    return dict(TOOL_FGA_RULES)
