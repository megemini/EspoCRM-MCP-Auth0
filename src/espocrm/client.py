"""EspoCRM API client with authentication support."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from typing import Any, Literal

import httpx

from ..config import EspoCRMConfig
from .types import EspoCRMResponse, WhereClause

logger = logging.getLogger(__name__)


class EspoCRMError(Exception):
    """Base exception for EspoCRM errors."""

    pass


class EspoCRMClient:
    """
    Client for interacting with EspoCRM API.

    Supports both API key and HMAC authentication methods.
    """

    def __init__(self, config: EspoCRMConfig):
        """Initialize the EspoCRM client."""
        self.config = config
        self.base_url = f"{config.url.rstrip('/')}/api/v1"
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def _build_auth_headers(
        self, method: str, uri: str, body: str = ""
    ) -> dict[str, str]:
        """Build authentication headers for the request."""
        headers = {}

        if self.config.auth_method == "apikey":
            headers["X-Api-Key"] = self.config.api_key
        elif self.config.auth_method == "hmac" and self.config.secret_key:
            string_to_sign = f"{method} /{uri}{body}"
            signature = hmac.new(
                self.config.secret_key.encode(), string_to_sign.encode(), hashlib.sha256
            ).hexdigest()
            auth_string = f"{self.config.api_key}:{signature}"
            headers["X-Hmac-Authorization"] = base64.b64encode(
                auth_string.encode()
            ).decode()

        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to EspoCRM API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        body = json.dumps(data) if data else ""

        headers = self._build_auth_headers(method, endpoint, body)

        try:
            response = await self.client.request(
                method, url, content=body, params=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise EspoCRMError(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise EspoCRMError(f"Request failed: {str(e)}")

    async def get(
        self, entity: str, params: dict[str, Any] | None = None
    ) -> EspoCRMResponse:
        """Get a list of entities."""
        data = await self._request("GET", entity, params=params)
        return EspoCRMResponse(**data)

    async def get_by_id(
        self, entity: str, entity_id: str, select: list[str] | None = None
    ) -> dict[str, Any]:
        """Get a specific entity by ID."""
        params = {}
        if select:
            params["select"] = ",".join(select)
        return await self._request("GET", f"{entity}/{entity_id}", params=params)

    async def post(self, entity: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new entity."""
        result = await self._request("POST", entity, data=data)
        logger.info(f"Created {entity} with ID: {result.get('id')}")
        return result

    async def put(
        self, entity: str, entity_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an entity."""
        result = await self._request("PUT", f"{entity}/{entity_id}", data=data)
        logger.info(f"Updated {entity} with ID: {entity_id}")
        return result

    async def delete(self, entity: str, entity_id: str) -> bool:
        """Delete an entity."""
        await self._request("DELETE", f"{entity}/{entity_id}")
        logger.info(f"Deleted {entity} with ID: {entity_id}")
        return True

    async def search(
        self,
        entity: str,
        where: list[WhereClause] | None = None,
        select: list[str] | None = None,
        order_by: str | None = None,
        order: Literal["asc", "desc"] = "asc",
        max_size: int = 20,
        offset: int = 0,
    ) -> EspoCRMResponse:
        """Search for entities with filters."""
        params: dict[str, Any] = {
            "maxSize": max_size,
            "offset": offset,
        }

        if where:
            params["where"] = json.dumps([w.model_dump() for w in where])
        if select:
            params["select"] = ",".join(select)
        if order_by:
            params["orderBy"] = order_by
            params["order"] = order

        return await self.get(entity, params=params)

    async def link_records(
        self, entity: str, entity_id: str, link: str, foreign_ids: list[str]
    ) -> bool:
        """Link records to an entity."""
        for foreign_id in foreign_ids:
            await self._request(
                "POST", f"{entity}/{entity_id}/{link}", data={"id": foreign_id}
            )
        logger.info(f"Linked {entity}/{entity_id} to {link}: {foreign_ids}")
        return True

    async def unlink_records(
        self, entity: str, entity_id: str, link: str, foreign_ids: list[str]
    ) -> bool:
        """Unlink records from an entity."""
        for foreign_id in foreign_ids:
            await self._request(
                "DELETE", f"{entity}/{entity_id}/{link}", data={"id": foreign_id}
            )
        logger.info(f"Unlinked {entity}/{entity_id} from {link}: {foreign_ids}")
        return True

    async def test_connection(self) -> dict[str, Any]:
        """Test the connection to EspoCRM."""
        try:
            data = await self._request("GET", "App/user")
            return {
                "success": True,
                "user": data.get("user"),
                "version": data.get("settings", {}).get("version", "Unknown"),
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_related(
        self,
        entity: str,
        entity_id: str,
        link: str,
        params: dict[str, Any] | None = None,
    ) -> EspoCRMResponse:
        """Get related entities for a given entity link."""
        data = await self._request(
            "GET",
            f"{entity}/{entity_id}/{link}",
            params=params,
        )
        return EspoCRMResponse(**data)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
