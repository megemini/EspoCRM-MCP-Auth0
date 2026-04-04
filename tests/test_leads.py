"""Tests for lead tools."""

from __future__ import annotations


class TestCreateLead:
    async def test_create_lead(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.post(
            "Lead",
            {
                "firstName": "Prospect",
                "lastName": "User",
                "status": "New",
                "stage": "Qualified",
            },
        )
        assert result.get("id") == "new-entity-id"


class TestSearchLeads:
    async def test_search_leads(self):
        from src.espocrm import WhereClause
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        where = [WhereClause(type="equals", attribute="status", value="New")]
        response = await client.search(
            "Lead",
            where=where,
            select=["id", "firstName", "lastName", "status"],
            max_size=20,
            offset=0,
            order_by="createdAt",
        )
        assert response.list is not None


class TestConvertLead:
    async def test_convert_lead(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.post(
            "Lead/lead-1/action/convertLead",
            {
                "opportunityName": "Converted Opp",
                "amount": 10000.0,
                "closeDate": "2025-06-01",
                "stage": "Prospecting",
            },
        )
        assert result is not None


class TestAssignLead:
    async def test_assign_lead(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        await client.put("Lead", "lead-1", {"assignedUserId": "user-456"})
