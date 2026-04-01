"""Type definitions for EspoCRM API."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class WhereClause(BaseModel):
    """Represents a where clause for EspoCRM search queries."""
    type: Literal[
        "equals", "notEquals", "greaterThan", "lessThan",
        "greaterThanOrEquals", "lessThanOrEquals", "contains",
        "notContains", "startsWith", "endsWith", "in", "notIn",
        "isTrue", "isFalse", "isNull", "isNotNull", "or", "and"
    ]
    attribute: str | None = None
    value: Any = None


class EspoCRMResponse(BaseModel):
    """Standard EspoCRM API response."""
    total: int | None = None
    list: list[dict[str, Any]] | None = None
