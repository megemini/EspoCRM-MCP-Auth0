"""FGA (Fine-Grained Authorization) client wrapper."""

from __future__ import annotations

import logging

from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.client.models import (
    ClientCheckRequest,
    ClientTuple,
    ClientWriteRequest,
)
from openfga_sdk.credentials import CredentialConfiguration, Credentials

from .errors import InsufficientPermission

logger = logging.getLogger(__name__)


class FGAClient:
    """Wrapper for OpenFGA client with EspoCRM-specific operations."""

    def __init__(
        self,
        api_url: str,
        store_id: str,
        client_id: str,
        client_secret: str,
        authorization_model_id: str | None = None,
        api_issuer: str = "auth.fga.dev",
        api_audience: str | None = None,
    ):
        """
        Initialize FGA client.

        Args:
            api_url: FGA API URL (e.g., https://api.us1.fga.dev)
            store_id: FGA store ID
            client_id: FGA client ID
            client_secret: FGA client secret
            authorization_model_id: Optional authorization model ID
            api_issuer: FGA API issuer (default: auth.fga.dev)
            api_audience: FGA API audience (default: derived from api_url)
        """
        # Derive api_audience from api_url if not provided
        if api_audience is None:
            api_audience = f"{api_url}/"

        # Create credentials configuration following official SDK pattern
        credentials = Credentials(
            method="client_credentials",
            configuration=CredentialConfiguration(
                api_issuer=api_issuer,
                api_audience=api_audience,
                client_id=client_id,
                client_secret=client_secret,
            ),
        )

        self.configuration = ClientConfiguration(
            api_url=api_url,
            store_id=store_id,
            credentials=credentials,
        )
        self.client = OpenFgaClient(self.configuration)
        self.authorization_model_id = authorization_model_id
        logger.info(f"FGA client initialized for store: {store_id}")

    async def check_permission(
        self,
        user: str,
        object_type: str,
        object_id: str,
        relation: str,
    ) -> bool:
        """
        Check if user has permission on object.

        Args:
            user: User ID (without 'user:' prefix)
            object_type: Object type (e.g., 'contact', 'account')
            object_id: Object ID
            relation: Relation to check (e.g., 'can_read', 'can_update')

        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Create check request following official SDK pattern
            body = ClientCheckRequest(
                user=f"user:{user}",
                relation=relation,
                object=f"{object_type}:{object_id}",
            )

            # Check with optional authorization model ID
            options = {}
            if self.authorization_model_id:
                options["authorization_model_id"] = self.authorization_model_id

            response = await self.client.check(body, options)

            allowed = response.allowed if response else False
            logger.debug(
                f"FGA check: user:{user} {relation} {object_type}:{object_id} = {allowed}"
            )
            return allowed

        except Exception as e:
            logger.error(f"FGA check failed: {e}")
            return False

    async def check_permission_or_raise(
        self,
        user: str,
        object_type: str,
        object_id: str,
        relation: str,
    ) -> None:
        """
        Check permission and raise exception if not allowed.

        Args:
            user: User ID
            object_type: Object type
            object_id: Object ID
            relation: Relation to check

        Raises:
            InsufficientPermission: If user doesn't have permission
        """
        if not await self.check_permission(user, object_type, object_id, relation):
            raise InsufficientPermission(
                f"User {user} does not have {relation} permission on {object_type}:{object_id}"
            )

    async def write_tuple(
        self,
        user: str,
        relation: str,
        object_type: str,
        object_id: str,
    ) -> None:
        """
        Write a single authorization tuple.

        Args:
            user: User ID (with or without 'user:' prefix)
            relation: Relation name
            object_type: Object type
            object_id: Object ID
        """
        if not user.startswith("user:"):
            user = f"user:{user}"

        tuple_data = ClientTuple(
            user=user,
            relation=relation,
            object=f"{object_type}:{object_id}",
        )

        request = ClientWriteRequest(writes=[tuple_data])
        await self.client.write(
            request, authorization_model_id=self.authorization_model_id
        )
        logger.info(f"FGA tuple written: {user} {relation} {object_type}:{object_id}")

    async def write_tuples(self, tuples: list[dict[str, str]]) -> None:
        """
        Write multiple authorization tuples.

        Args:
            tuples: List of tuple dictionaries with 'user', 'relation', 'object_type', 'object_id'
        """
        tuple_list = []
        for t in tuples:
            user = t["user"]
            if not user.startswith("user:") and not user.startswith("team:"):
                user = f"user:{user}"

            tuple_list.append(
                ClientTuple(
                    user=user,
                    relation=t["relation"],
                    object=f"{t['object_type']}:{t['object_id']}",
                )
            )

        request = ClientWriteRequest(writes=tuple_list)
        await self.client.write(
            request, authorization_model_id=self.authorization_model_id
        )
        logger.info(f"FGA tuples written: {len(tuples)} tuples")

    async def delete_tuple(
        self,
        user: str,
        relation: str,
        object_type: str,
        object_id: str,
    ) -> None:
        """
        Delete a single authorization tuple.

        Args:
            user: User ID
            relation: Relation name
            object_type: Object type
            object_id: Object ID
        """
        if not user.startswith("user:"):
            user = f"user:{user}"

        tuple_data = ClientTuple(
            user=user,
            relation=relation,
            object=f"{object_type}:{object_id}",
        )

        request = ClientWriteRequest(deletes=[tuple_data])
        await self.client.write(
            request, authorization_model_id=self.authorization_model_id
        )
        logger.info(f"FGA tuple deleted: {user} {relation} {object_type}:{object_id}")

    async def sync_entity_permissions(
        self,
        entity_type: str,
        entity_id: str,
        owner: str | None = None,
        assigned_user: str | None = None,
        team_id: str | None = None,
        account_id: str | None = None,
    ) -> None:
        """
        Sync permissions for an EspoCRM entity.

        Args:
            entity_type: Entity type (e.g., 'contact', 'account')
            entity_id: Entity ID
            owner: Owner user ID
            assigned_user: Assigned user ID
            team_id: Team ID
            account_id: Related account ID (for contacts/opportunities)
        """
        tuples = []

        # Add owner relationship
        if owner:
            tuples.append(
                {
                    "user": owner,
                    "relation": "owner",
                    "object_type": entity_type,
                    "object_id": entity_id,
                }
            )

        # Add assigned user relationship
        if assigned_user:
            tuples.append(
                {
                    "user": assigned_user,
                    "relation": "assigned",
                    "object_type": entity_type,
                    "object_id": entity_id,
                }
            )

        # Add team relationship
        if team_id:
            tuples.append(
                {
                    "user": f"team:{team_id}",
                    "relation": "team",
                    "object_type": entity_type,
                    "object_id": entity_id,
                }
            )

        # Add account relationship (for contacts/opportunities)
        if account_id and entity_type in ["contact", "opportunity"]:
            tuples.append(
                {
                    "user": f"account:{account_id}",
                    "relation": "account",
                    "object_type": entity_type,
                    "object_id": entity_id,
                }
            )

        if tuples:
            await self.write_tuples(tuples)

    async def close(self) -> None:
        """Close the FGA client connection."""
        await self.client.close()
        logger.info("FGA client closed")


# Global FGA client instance
_fga_client: FGAClient | None = None


def get_fga_client() -> FGAClient:
    """Get the global FGA client instance."""
    if _fga_client is None:
        raise RuntimeError("FGA client not initialized")
    return _fga_client


def set_fga_client(client: FGAClient) -> None:
    """Set the global FGA client instance."""
    global _fga_client
    _fga_client = client
