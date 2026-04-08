"""Type definitions for EspoCRM API."""

from typing import Any, List, Literal, Optional

from pydantic import BaseModel


class WhereClause(BaseModel):
    """Represents a where clause for EspoCRM search queries."""

    type: Literal[
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
    attribute: Optional[str] = None
    value: Any = None


class EspoCRMResponse(BaseModel):
    """Standard EspoCRM API response."""

    total: Optional[int] = None
    list: Optional[List[dict[str, Any]]] = None
