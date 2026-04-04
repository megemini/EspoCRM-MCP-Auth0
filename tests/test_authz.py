"""Tests for src/auth0/authz.py decorators."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.auth0.authz import require_fga_permission, require_scopes
from src.auth0.errors import AuthenticationRequired, InsufficientScope


@pytest.fixture(autouse=True)
def _patch_context_for_authz(monkeypatch):
    """Patch Context class in authz module so MockContext passes isinstance checks."""
    import src.auth0.authz as authz_module
    from tests.conftest import MockContext

    monkeypatch.setattr(authz_module, "Context", MockContext)


class TestRequireScopes:
    def _make_tool(self, scopes):
        @require_scopes(scopes)
        async def my_tool(ctx=None, name="test"):
            return f"Hello {name}"

        return my_tool

    async def test_all_scopes_present(self, mock_ctx):
        tool = self._make_tool(["espocrm:contacts:read"])
        result = await tool(ctx=mock_ctx, name="World")
        assert result == "Hello World"

    async def test_missing_scope_raises(self):
        from tests.conftest import MockContext

        ctx = MockContext(
            auth={
                "scopes": ["espocrm:contacts:read"],
                "extra": {"sub": "u1"},
            }
        )
        tool = self._make_tool(["espocrm:contacts:write"])
        with pytest.raises(InsufficientScope) as exc_info:
            await tool(ctx=ctx)
        assert "espocrm:contacts:write" in str(exc_info.value)

    async def test_no_auth_raises(self, mock_ctx_no_auth):
        tool = self._make_tool(["espocrm:contacts:read"])
        with pytest.raises(AuthenticationRequired):
            await tool(ctx=mock_ctx_no_auth)

    async def test_no_ctx_raises(self):
        tool = self._make_tool(["espocrm:contacts:read"])
        with pytest.raises(TypeError, match="ctx"):
            await tool()

    async def test_multiple_scopes(self, mock_ctx):
        tool = self._make_tool(
            [
                "espocrm:contacts:read",
                "espocrm:accounts:read",
            ]
        )
        result = await tool(ctx=mock_ctx)
        assert result == "Hello test"


class TestRequireFgaPermission:
    def _make_fga_tool(self, **kwargs):
        defaults = {
            "object_type": "contact",
            "object_id_param": "contact_id",
            "relation": "can_read",
        }
        defaults.update(kwargs)

        @require_fga_permission(**defaults)
        async def my_tool(contact_id, ctx=None):
            return f"Got contact {contact_id}"

        return my_tool

    async def test_no_ctx_raises(self):
        tool = self._make_fga_tool()
        with pytest.raises(TypeError, match="ctx"):
            await tool("c1")

    async def test_no_auth_raises(self, mock_ctx_no_auth):
        tool = self._make_fga_tool()
        with pytest.raises(AuthenticationRequired):
            await tool("c1", ctx=mock_ctx_no_auth)

    async def test_no_user_id_raises(self):
        from tests.conftest import MockContext

        ctx = MockContext(auth={"scopes": ["read"], "extra": {}})
        tool = self._make_fga_tool()
        with pytest.raises(AuthenticationRequired, match="User ID not found"):
            await tool("c1", ctx=ctx)

    async def test_fga_not_configured_skips(self, mock_ctx):
        tool = self._make_fga_tool()
        with patch(
            "src.auth0.fga.get_fga_client", side_effect=RuntimeError("not init")
        ):
            result = await tool("c1", ctx=mock_ctx)
            assert result == "Got contact c1"

    async def test_fga_check_passes(self, mock_ctx, mock_fga_client):
        tool = self._make_fga_tool()
        with patch("src.auth0.fga.get_fga_client", return_value=mock_fga_client):
            result = await tool("c1", ctx=mock_ctx)
            assert result == "Got contact c1"
            mock_fga_client.check_permission_or_raise.assert_awaited_once_with(
                user="user-123",
                object_type="contact",
                object_id="c1",
                relation="can_read",
            )

    async def test_missing_object_id_raises(self, mock_ctx):
        def _dummy(**kwargs):
            return "ok"

        tool = require_fga_permission(
            object_type="contact", object_id_param="nonexistent_param"
        )(_dummy)
        with pytest.raises(ValueError, match="nonexistent_param"):
            await tool(ctx=mock_ctx)
