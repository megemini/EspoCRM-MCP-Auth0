"""Shared test fixtures."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


class MockContext:
    """Mock MCP Context object for testing."""

    def __init__(self, auth: dict[str, Any] | None = None):
        self.request_context = MagicMock()
        self.request_context.request = MagicMock()
        self.request_context.request.state = MagicMock()
        self.request_context.request.state.auth = auth or {}


@pytest.fixture
def mock_ctx() -> MockContext:
    """Return a mock Context with default authenticated user."""
    return MockContext(
        auth={
            "scopes": [
                "espocrm:contacts:read",
                "espocrm:contacts:write",
                "espocrm:accounts:read",
                "espocrm:accounts:write",
                "espocrm:leads:read",
                "espocrm:leads:write",
                "espocrm:entities:read",
                "espocrm:entities:write",
            ],
            "extra": {"sub": "user-123"},
        }
    )


@pytest.fixture
def mock_ctx_no_auth() -> MockContext:
    """Return a mock Context without authentication."""
    return MockContext(auth=None)


@pytest.fixture
def mock_espocrm_client():
    """Return a mock EspoCRM client."""
    client = MagicMock()
    client.post = AsyncMock(return_value={"id": "new-entity-id"})
    client.get_by_id = AsyncMock(
        side_effect=lambda entity_type, entity_id, **kw: (
            {
                "id": entity_id,
                "firstName": "John",
                "lastName": "Doe",
                "emailAddress": "john@example.com",
            }
            if entity_type == "Contact"
            else {"id": entity_id, "name": f"{entity_type}-{entity_id}"}
        )
    )
    client.search = AsyncMock(
        return_value=MagicMock(list=[{"id": "c1", "name": "Test Contact"}])
    )
    client.put = AsyncMock(return_value={"id": "contact-1", "name": "Updated"})
    client.delete = AsyncMock(return_value=True)
    client.link_records = AsyncMock(return_value=True)
    client.unlink_records = AsyncMock(return_value=True)
    client.get_related = AsyncMock(
        return_value=MagicMock(list=[{"id": "r1", "name": "Related"}])
    )
    client.test_connection = AsyncMock(
        return_value={
            "success": True,
            "user": {"userName": "admin"},
            "version": "9.0.0",
        }
    )
    return client


@pytest.fixture(autouse=True)
def _setup_espocrm_client(mock_espocrm_client):
    """Auto-setup the global EspoCRM client before each test."""
    from src.tools.base import set_espocrm_client

    original = None
    try:
        from src.tools.base import get_espocrm_client

        original = get_espocrm_client()
    except RuntimeError:
        pass

    set_espocrm_client(mock_espocrm_client)

    yield

    if original is not None:
        set_espocrm_client(original)


@pytest.fixture
def mock_fga_client():
    """Return a mock FGA client."""
    client = MagicMock()
    client.check_permission = AsyncMock(return_value=True)
    client.check_permission_or_raise = AsyncMock(return_value=None)
    client.write_tuple = AsyncMock(return_value=None)
    client.write_tuples = AsyncMock(return_value=None)
    client.delete_tuple = AsyncMock(return_value=None)
    client.close = AsyncMock(return_value=None)
    return client
