"""Lead management tools."""

from __future__ import annotations

from datetime import datetime, timedelta

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import apply_fga, format_entity_list, get_espocrm_client


def register_lead_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="create_lead",
        title="Create Lead",
        description="Create a new lead in EspoCRM",
    )
    @require_scopes(["espocrm:leads:write"])
    async def create_lead(
        first_name: str,
        last_name: str,
        source: str,
        email_address: str | None = None,
        phone_number: str | None = None,
        account_name: str | None = None,
        website: str | None = None,
        status: str = "New",
        industry: str | None = None,
        assigned_user_id: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data = {
            "firstName": first_name,
            "lastName": last_name,
            "source": source,
            "status": status,
        }
        if email_address:
            data["emailAddress"] = email_address
        if phone_number:
            data["phoneNumber"] = phone_number
        if account_name:
            data["accountName"] = account_name
        if website:
            data["website"] = website
        if industry:
            data["industry"] = industry
        if assigned_user_id:
            data["assignedUserId"] = assigned_user_id
        if description:
            data["description"] = description

        result = await client.post("Lead", data)
        return f"Successfully created lead: {first_name} {last_name} (ID: {result.get('id')})"

    @mcp.tool(
        name="search_leads",
        title="Search Leads",
        description="Search for leads in EspoCRM",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:leads:read"])
    async def search_leads(
        name: str | None = None,
        status: str | None = None,
        source: str | None = None,
        email_address: str | None = None,
        account_name: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        where = []
        if name:
            where.append(
                WhereClause(
                    type="or",
                    value=[
                        {"type": "contains", "attribute": "firstName", "value": name},
                        {"type": "contains", "attribute": "lastName", "value": name},
                    ],
                )
            )
        if status:
            where.append(WhereClause(type="equals", attribute="status", value=status))
        if source:
            where.append(WhereClause(type="equals", attribute="source", value=source))
        if email_address:
            where.append(
                WhereClause(
                    type="equals", attribute="emailAddress", value=email_address
                )
            )
        if account_name:
            where.append(
                WhereClause(
                    type="contains", attribute="accountName", value=account_name
                )
            )

        response = await client.search(
            "Lead",
            where=where if where else None,
            select=["id", "firstName", "lastName", "status", "source", "accountName"],
            max_size=limit,
            offset=offset,
            order_by="lastName",
        )

        return format_entity_list(response.list or [], "leads")

    @mcp.tool(
        name="update_lead",
        title="Update Lead",
        description="Update an existing lead in EspoCRM",
    )
    @require_scopes(["espocrm:leads:write"])
    @apply_fga("update_lead")
    async def update_lead(
        lead_id: str,
        first_name: str | None = None,
        last_name: str | None = None,
        email_address: str | None = None,
        phone_number: str | None = None,
        account_name: str | None = None,
        status: str | None = None,
        source: str | None = None,
        assigned_user_id: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data = {}
        if first_name is not None:
            data["firstName"] = first_name
        if last_name is not None:
            data["lastName"] = last_name
        if email_address is not None:
            data["emailAddress"] = email_address
        if phone_number is not None:
            data["phoneNumber"] = phone_number
        if account_name is not None:
            data["accountName"] = account_name
        if status is not None:
            data["status"] = status
        if source is not None:
            data["source"] = source
        if assigned_user_id is not None:
            data["assignedUserId"] = assigned_user_id
        if description is not None:
            data["description"] = description

        await client.put("Lead", lead_id, data)
        return f"Successfully updated lead with ID: {lead_id}"

    @mcp.tool(
        name="convert_lead",
        title="Convert Lead",
        description="Convert a lead to contact, account, and optionally opportunity",
    )
    @require_scopes(
        ["espocrm:leads:write", "espocrm:contacts:write", "espocrm:accounts:write"]
    )
    @apply_fga("convert_lead")
    async def convert_lead(
        lead_id: str,
        create_contact: bool = True,
        create_account: bool = True,
        create_opportunity: bool = False,
        opportunity_name: str | None = None,
        opportunity_amount: float | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        lead = await client.get_by_id("Lead", lead_id)
        results = []

        account_id = None
        if create_account and lead.get("accountName"):
            account_data = {
                "name": lead.get("accountName"),
                "website": lead.get("website"),
                "industry": lead.get("industry"),
                "assignedUserId": lead.get("assignedUserId"),
            }
            account = await client.post("Account", account_data)
            account_id = account.get("id")
            results.append(
                f"Created account: {lead.get('accountName')} (ID: {account_id})"
            )

        contact_id = None
        if create_contact:
            contact_data = {
                "firstName": lead.get("firstName"),
                "lastName": lead.get("lastName"),
                "emailAddress": lead.get("emailAddress"),
                "phoneNumber": lead.get("phoneNumber"),
                "accountId": account_id,
                "assignedUserId": lead.get("assignedUserId"),
                "description": lead.get("description"),
            }
            contact = await client.post("Contact", contact_data)
            contact_id = contact.get("id")
            results.append(
                f"Created contact: {lead.get('firstName')} {lead.get('lastName')} (ID: {contact_id})"
            )

        if create_opportunity and account_id and opportunity_name:
            opp_data = {
                "name": opportunity_name,
                "accountId": account_id,
                "stage": "Prospecting",
                "amount": opportunity_amount,
                "closeDate": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "assignedUserId": lead.get("assignedUserId"),
            }
            opportunity = await client.post("Opportunity", opp_data)
            results.append(
                f"Created opportunity: {opportunity_name} (ID: {opportunity.get('id')})"
            )

        await client.put("Lead", lead_id, {"status": "Converted"})
        results.append(f"Lead {lead_id} marked as Converted")

        return f"Successfully converted lead {lead_id}:\n" + "\n".join(results)

    @mcp.tool(
        name="assign_lead",
        title="Assign Lead",
        description="Assign or reassign a lead to a specific user",
    )
    @require_scopes(["espocrm:leads:write"])
    @apply_fga("assign_lead")
    async def assign_lead(
        lead_id: str,
        assigned_user_id: str,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await client.put("Lead", lead_id, {"assignedUserId": assigned_user_id})
        return f"Successfully assigned lead {lead_id} to user {assigned_user_id}"
