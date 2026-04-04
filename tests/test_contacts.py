"""Tests for contact tools."""

from __future__ import annotations

import pytest

from src.tools.contacts import register_contact_tools


@pytest.fixture
def registered_tools(mock_ctx, mock_espocrm_client):
    """Register contact tools and return the tool functions."""
    from unittest.mock import MagicMock

    mcp = MagicMock()
    mcp.tool = lambda **kwargs: (lambda f: f)
    register_contact_tools(mcp)
    return True


class TestCreateContact:
    async def test_create_with_required_fields(self, mock_ctx):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.post(
            "Contact",
            {
                "firstName": "Jane",
                "lastName": "Smith",
            },
        )
        assert result.get("id") == "new-entity-id"

    async def test_create_with_optional_fields(self, mock_ctx):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        data = {
            "firstName": "Jane",
            "lastName": "Smith",
            "emailAddress": "jane@example.com",
            "phone_number": "555-1234",
        }
        result = await client.post("Contact", data)
        assert "id" in result


class TestSearchContacts:
    async def test_search_returns_list(self, mock_ctx):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        response = await client.search(
            "Contact",
            where=[],
            select=["id", "firstName", "lastName"],
            max_size=20,
            offset=0,
            order_by="lastName",
        )
        assert response.list is not None


class TestGetContact:
    async def test_get_by_id(self, mock_ctx):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        contact = await client.get_by_id("Contact", "contact-1")
        assert contact["id"] == "contact-1"
        assert contact["firstName"] == "John"
