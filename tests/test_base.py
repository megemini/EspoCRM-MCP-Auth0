"""Tests for base utilities in src/tools/base.py."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from src.auth0.errors import AuthenticationRequired
from src.tools.base import (
    apply_fga,
    check_fga_dynamic,
    format_entity_list,
    format_json,
    get_espocrm_client,
    set_espocrm_client,
)


@pytest.fixture(autouse=True)
def _patch_context_for_base(monkeypatch):
    """Patch Context class in base module so MockContext passes isinstance checks."""
    import src.tools.base as base_module
    from tests.conftest import MockContext

    monkeypatch.setattr(base_module, "Context", MockContext)


class TestFormatEntityList:
    def test_empty_list(self):
        result = format_entity_list([], "contacts")
        assert result == "No contacts found."

    def test_single_entity(self):
        entities = [{"id": "c1", "name": "Alice"}]
        result = format_entity_list(entities, "contacts")
        assert "Found 1 contacts" in result
        assert "ID: c1" in result
        assert "Alice" in result

    def test_multiple_entities(self):
        entities = [
            {"id": "c1", "name": "Alice"},
            {"id": "c2", "name": "Bob"},
            {"id": "c3", "name": "Charlie"},
        ]
        result = format_entity_list(entities, "contacts")
        assert "Found 3 contacts" in result

    def test_contact_with_first_last_name(self):
        entities = [{"id": "c1", "firstName": "John", "lastName": "Doe"}]
        result = format_entity_list(entities, "contacts")
        assert "John Doe" in result

    def test_missing_name_shows_na(self):
        entities = [{"id": "c1"}]
        result = format_entity_list(entities, "contacts")
        assert "N/A" in result


class TestFormatJson:
    def test_dict_formatting(self):
        data = {"key": "value", "nested": {"a": 1}}
        result = format_json(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_non_ascii_preserved(self):
        data = {"name": "Test User"}
        result = format_json(data)
        assert "Test User" in result


class TestEspoCRMClientSingleton:
    def test_get_before_set_raises(self, monkeypatch):

        monkeypatch.setattr("src.tools.base._espocrm_client", None)
        with pytest.raises(RuntimeError, match="not initialized"):
            get_espocrm_client()

    def test_set_and_get(self, mock_espocrm_client):
        set_espocrm_client(mock_espocrm_client)
        assert get_espocrm_client() is mock_espocrm_client


class TestCheckFgaDynamic:
    async def test_none_ctx_skips(self):
        await check_fga_dynamic(None, "contact", "c1")

    async def test_no_auth_raises(self, mock_ctx_no_auth):
        with pytest.raises(AuthenticationRequired):
            await check_fga_dynamic(mock_ctx_no_auth, "contact", "c1")

    async def test_no_user_id_raises(self):
        from tests.conftest import MockContext

        ctx = MockContext(auth={"scopes": ["read"], "extra": {}})
        with pytest.raises(AuthenticationRequired, match="User ID not found"):
            await check_fga_dynamic(ctx, "contact", "c1")

    async def test_fga_not_configured_skips(self, mock_ctx):
        with patch(
            "src.auth0.fga.get_fga_client", side_effect=RuntimeError("not init")
        ):
            await check_fga_dynamic(mock_ctx, "contact", "c1")


class TestApplyFga:
    def test_returns_identity_for_unknown_tool(self):
        decorator = apply_fga("nonexistent_tool")

        def func():
            return "ok"

        assert decorator(func) is func

    def test_returns_decorator_for_known_tool(self):
        decorator = apply_fga("get_contact")

        def func():
            return "ok"

        wrapped = decorator(func)
        assert wrapped is not func
        assert callable(wrapped)

    def test_get_entity_rule_exists(self):
        from src.tools.fga_config import get_fga_rule

        rule = get_fga_rule("get_entity")
        assert rule is not None
        assert rule.object_id_param == "entity_id"
        assert rule.relation == "can_read"

    def test_delete_entity_rule_has_can_delete(self):
        from src.tools.fga_config import get_fga_rule

        rule = get_fga_rule("delete_entity")
        assert rule.relation == "can_delete"
