"""Tools package - MCP tools for EspoCRM operations."""

from ..auth0 import Auth0Mcp
from ..auth0.authz import register_required_scopes
from .base import get_espocrm_client
from .base import set_espocrm_client as _set_client

__all__ = ["register_tools", "set_espocrm_client", "get_espocrm_client"]


def set_espocrm_client(client) -> None:
    _set_client(client)


def register_tools(auth0_mcp: Auth0Mcp) -> None:
    mcp = auth0_mcp.mcp

    from . import health

    health.register_health_tools(mcp)

    from . import contacts

    contacts.register_contact_tools(mcp)

    from . import accounts

    accounts.register_account_tools(mcp)

    from . import leads

    leads.register_lead_tools(mcp)

    from . import opportunities

    opportunities.register_opportunity_tools(mcp)

    from . import meetings

    meetings.register_meeting_tools(mcp)

    from . import tasks

    tasks.register_task_tools(mcp)

    from . import users

    users.register_user_tools(mcp)

    from . import teams

    teams.register_team_tools(mcp)

    from . import calls

    calls.register_call_tools(mcp)

    from . import cases

    cases.register_case_tools(mcp)

    from . import notes

    notes.register_note_tools(mcp)

    from . import generic

    generic.register_generic_tools(mcp)

    from . import relationships

    relationships.register_relationship_tools(mcp)

    register_required_scopes(auth0_mcp)
