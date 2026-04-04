"""Tests for account tools."""

from __future__ import annotations


class TestCreateAccount:
    async def test_create_account(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.post(
            "Account",
            {
                "name": "Test Corp",
                "website": "https://test.com",
            },
        )
        assert result.get("id") == "new-entity-id"


class TestSearchAccounts:
    async def test_search_accounts(self):
        from src.espocrm import WhereClause
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        where = [WhereClause(type="contains", attribute="name", value="Test")]
        response = await client.search(
            "Account",
            where=where,
            select=["id", "name"],
            max_size=20,
            offset=0,
            order_by="name",
        )
        assert response.list is not None


class TestUpdateAccount:
    async def test_update_account(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        await client.put("Account", "acc-1", {"name": "Updated Corp"})
