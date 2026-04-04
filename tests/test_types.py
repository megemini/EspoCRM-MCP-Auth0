"""Tests for EspoCRM types and error classes."""

from __future__ import annotations

import pytest

from src.auth0.errors import (
    AuthenticationRequired,
    InsufficientPermission,
    InsufficientScope,
    MalformedAuthorizationRequest,
)
from src.espocrm.types import EspoCRMResponse, WhereClause


class TestWhereClause:
    def test_valid_equals_clause(self):
        clause = WhereClause(type="equals", attribute="name", value="test")
        assert clause.type == "equals"
        assert clause.attribute == "name"
        assert clause.value == "test"

    def test_valid_contains_clause(self):
        clause = WhereClause(type="contains", attribute="email", value="john")
        assert clause.value == "john"

    def test_or_clause_with_nested_values(self):
        clause = WhereClause(
            type="or",
            value=[
                {"type": "contains", "attribute": "firstName", "value": "John"},
                {"type": "contains", "attribute": "lastName", "value": "Doe"},
            ],
        )
        assert len(clause.value) == 2

    def test_invalid_type_raises(self):
        with pytest.raises(Exception):
            WhereClause(type="invalid_type", attribute="x", value="y")

    def test_all_valid_types(self):
        valid_types = [
            "equals",
            "notEquals",
            "greaterThan",
            "lessThan",
            "greaterThanOrEquals",
            "lessThanOrEquals",
            "contains",
            "notContains",
            "startsWith",
            "endsWith",
            "in",
            "notIn",
            "isTrue",
            "isFalse",
            "isNull",
            "isNotNull",
            "or",
            "and",
        ]
        for t in valid_types:
            clause = WhereClause(type=t, attribute="field")
            assert clause.type == t


class TestEspoCRMResponse:
    def test_empty_response(self):
        resp = EspoCRMResponse()
        assert resp.total is None
        assert resp.list is None

    def test_full_response(self):
        resp = EspoCRMResponse(total=10, list=[{"id": "1"}])
        assert resp.total == 10
        assert len(resp.list) == 1


class TestAuthenticationRequired:
    def test_default_message(self):
        err = AuthenticationRequired()
        assert err.status_code == 401
        assert err.error_code == "invalid_token"
        assert str(err) == "Authentication required"

    def test_custom_message(self):
        err = AuthenticationRequired("Token expired")
        assert str(err) == "Token expired"


class TestInsufficientScope:
    def test_default_message(self):
        err = InsufficientScope()
        assert err.status_code == 403
        assert err.error_code == "insufficient_scope"

    def test_custom_message(self):
        err = InsufficientScope("Missing: contacts:write")
        assert "contacts:write" in str(err)


class TestInsufficientPermission:
    def test_default_message(self):
        err = InsufficientPermission()
        assert err.status_code == 403
        assert err.error_code == "insufficient_permission"

    def test_custom_message(self):
        err = InsufficientPermission("Cannot delete contact c1")
        assert "contact" in str(err)


class TestMalformedAuthorizationRequest:
    def test_default_message(self):
        err = MalformedAuthorizationRequest()
        assert err.status_code == 400
        assert err.error_code == "invalid_request"
