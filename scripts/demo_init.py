#!/usr/bin/env python3
"""
Demo initialization script.

Creates sample data in EspoCRM and writes matching FGA tuples
so that the demo user has proper permissions for testing.

Usage:
    python scripts/demo_init.py <auth0_user_sub>

Example:
    python scripts/demo_init.py "auth0|6abc123def456"

The auth0_user_sub is the 'sub' claim from your Auth0 user's access token.
You can find it in Auth0 Dashboard → User Management → Users → user_id.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from src.config import EspoCRMConfig
from src.espocrm import EspoCRMClient


async def create_entity(
    client: EspoCRMClient, entity_type: str, data: dict, label: str
) -> dict:
    """Create an entity, handling duplicates gracefully."""
    try:
        result = await client.post(entity_type, data)
        print(f"  ✓ {entity_type} '{label}': {result['id']}")
        return result
    except Exception as e:
        print(f"  ✗ {entity_type} '{label}' failed: {e}")
        raise


async def create_espocrm_data(client: EspoCRMClient) -> dict[str, str]:
    """Create sample entities in EspoCRM and return their IDs."""
    ids = {}

    # Create accounts
    account1 = await create_entity(
        client,
        "Account",
        {
            "name": "Demo Corp",
            "type": "Customer",
            "industry": "Technology",
            "website": "https://demo-corp.example.com",
            "emailAddress": "info@demo-corp.example.com",
        },
        "Demo Corp",
    )
    ids["account1"] = account1["id"]

    account2 = await create_entity(
        client,
        "Account",
        {
            "name": "Acme Inc",
            "type": "Partner",
            "industry": "Consulting",
            "website": "https://acme.example.com",
        },
        "Acme Inc",
    )
    ids["account2"] = account2["id"]

    # Create contacts
    contact1 = await create_entity(
        client,
        "Contact",
        {
            "firstName": "Alice",
            "lastName": "Johnson",
            "emailAddress": "alice@demo-corp.example.com",
            "phoneNumber": "+1-555-0101",
            "accountId": ids["account1"],
            "title": "CTO",
        },
        "Alice Johnson",
    )
    ids["contact1"] = contact1["id"]

    contact2 = await create_entity(
        client,
        "Contact",
        {
            "firstName": "Bob",
            "lastName": "Smith",
            "emailAddress": "bob@acme.example.com",
            "phoneNumber": "+1-555-0102",
            "accountId": ids["account2"],
            "title": "Sales Manager",
        },
        "Bob Smith",
    )
    ids["contact2"] = contact2["id"]

    # Create leads
    lead1 = await create_entity(
        client,
        "Lead",
        {
            "firstName": "Charlie",
            "lastName": "Brown",
            "emailAddress": "charlie@startup.example.com",
            "status": "New",
            "accountName": "Startup Labs",
        },
        "Charlie Brown",
    )
    ids["lead1"] = lead1["id"]

    return ids


async def write_fga_tuples(user_sub: str, entity_ids: dict[str, str]) -> None:
    """Write FGA tuples matching the created EspoCRM entities."""
    from openfga_sdk import ClientConfiguration, OpenFgaClient
    from openfga_sdk.client.models import ClientTuple, ClientWriteRequest
    from openfga_sdk.credentials import CredentialConfiguration, Credentials

    api_url = os.getenv("FGA_API_URL", "https://api.us1.fga.dev")
    store_id = os.getenv("FGA_STORE_ID")
    client_id = os.getenv("FGA_CLIENT_ID")
    client_secret = os.getenv("FGA_CLIENT_SECRET")
    model_id = os.getenv("FGA_AUTHORIZATION_MODEL_ID")
    api_issuer = os.getenv("FGA_API_ISSUER", "auth.fga.dev")
    api_audience = os.getenv("FGA_API_AUDIENCE", f"{api_url}/")

    if not all([store_id, client_id, client_secret]):
        print("\n⚠ FGA not configured, skipping FGA tuple creation.")
        print("  Set FGA_STORE_ID, FGA_CLIENT_ID, FGA_CLIENT_SECRET to enable.")
        return

    credentials = Credentials(
        method="client_credentials",
        configuration=CredentialConfiguration(
            api_issuer=api_issuer,
            api_audience=api_audience,
            client_id=client_id,
            client_secret=client_secret,
        ),
    )

    configuration = ClientConfiguration(
        api_url=api_url,
        store_id=store_id,
        credentials=credentials,
    )

    # Grant the demo user owner permission on all created entities
    tuples = [
        ClientTuple(
            user=f"user:{user_sub}",
            relation="owner",
            object=f"account:{entity_ids['account1']}",
        ),
        ClientTuple(
            user=f"user:{user_sub}",
            relation="owner",
            object=f"account:{entity_ids['account2']}",
        ),
        ClientTuple(
            user=f"user:{user_sub}",
            relation="owner",
            object=f"contact:{entity_ids['contact1']}",
        ),
        ClientTuple(
            user=f"user:{user_sub}",
            relation="owner",
            object=f"contact:{entity_ids['contact2']}",
        ),
        ClientTuple(
            user=f"user:{user_sub}",
            relation="owner",
            object=f"lead:{entity_ids['lead1']}",
        ),
    ]

    async with OpenFgaClient(configuration) as fga_client:
        options = {}
        if model_id:
            options["authorization_model_id"] = model_id

        request = ClientWriteRequest(writes=tuples)
        try:
            await fga_client.write(request, options)
            print(f"  ✓ FGA tuples written: {len(tuples)} tuples for user:{user_sub}")
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg or "already existed" in error_msg:
                print("  ⚠ FGA tuples already exist, skipping.")
            else:
                raise


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/demo_init.py <auth0_user_sub>")
        print('Example: python scripts/demo_init.py "auth0|6abc123def456"')
        print("\nFind your user_id in Auth0 Dashboard → User Management → Users")
        sys.exit(1)

    user_sub = sys.argv[1]

    load_dotenv()

    espocrm_url = os.getenv("ESPOCRM_URL")
    espocrm_api_key = os.getenv("ESPOCRM_API_KEY")
    if not espocrm_url or not espocrm_api_key:
        print("Error: ESPOCRM_URL and ESPOCRM_API_KEY must be set in .env")
        sys.exit(1)

    espocrm_config = EspoCRMConfig(
        url=espocrm_url,
        api_key=espocrm_api_key,
        secret_key=os.getenv("ESPOCRM_SECRET_KEY"),
        auth_method=os.getenv("ESPOCRM_AUTH_METHOD", "apikey"),
    )

    print(f"Demo initialization for user: {user_sub}")
    print(f"EspoCRM: {espocrm_url}")
    print()

    client = EspoCRMClient(espocrm_config)
    try:
        # Step 1: Create EspoCRM entities
        print("Step 1: Creating EspoCRM entities...")
        entity_ids = await create_espocrm_data(client)

        # Step 2: Write FGA tuples with real IDs
        print("\nStep 2: Writing FGA tuples...")
        await write_fga_tuples(user_sub, entity_ids)

        print("\n✓ Demo initialization complete!")
        print("\nCreated entities:")
        for key, eid in entity_ids.items():
            print(f"  {key}: {eid}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
