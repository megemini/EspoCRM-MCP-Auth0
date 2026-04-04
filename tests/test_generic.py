"""Tests for generic entity tools and relationship tools."""

from __future__ import annotations


class TestCreateEntity:
    async def test_create_generic_entity(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.post("CustomEntity", {"name": "Test", "value": 42})
        assert result.get("id") == "new-entity-id"


class TestSearchEntity:
    async def test_search_entity_with_filters(self):
        from src.espocrm import WhereClause
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        where = [
            WhereClause(type="equals", attribute="status", value="Active"),
            WhereClause(type="contains", attribute="name", value="test"),
        ]
        response = await client.search(
            "CustomEntity",
            where=where,
            select=["id", "name"],
            max_size=20,
            offset=0,
        )
        assert response.list is not None


class TestGetEntity:
    async def test_get_entity_by_id(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        entity = await client.get_by_id("CustomEntity", "entity-1")
        assert entity["id"] == "entity-1"


class TestUpdateEntity:
    async def test_update_generic_entity(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        await client.put("CustomEntity", "entity-1", {"name": "Updated"})


class TestDeleteEntity:
    async def test_delete_generic_entity(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        deleted = await client.delete("CustomEntity", "entity-1")
        assert deleted is True


class TestLinkEntities:
    async def test_link_entities(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        await client.link_records("Contact", "c1", "accounts", ["a1", "a2"])


class TestUnlinkEntities:
    async def test_unlink_entities(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        await client.unlink_records("Contact", "c1", "accounts", ["a1"])


class TestGetEntityRelationships:
    async def test_get_related_entities(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.get_related(
            "Contact",
            "c1",
            "accounts",
            params={"maxSize": 20, "offset": 0},
        )
        assert result.list is not None
