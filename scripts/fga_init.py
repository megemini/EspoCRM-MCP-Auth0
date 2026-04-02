#!/usr/bin/env python3
"""FGA initialization script to set up authorization model and initial tuples."""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openfga_sdk import (
    ClientConfiguration,
    OpenFgaClient,
)
from openfga_sdk.client.models import ClientTuple, ClientWriteRequest
from openfga_sdk.credentials import Credentials, CredentialConfiguration


async def create_authorization_model(fga_client: OpenFgaClient) -> str:
    """Create the EspoCRM authorization model using DSL."""
    
    print("Creating authorization model...")
    
    # Use the write_authorization_model method with DSL
    # This is the recommended way to create models
    # In FGA 1.1, we need to specify metadata for relations
    try:
        response = await fga_client.write_authorization_model({
            "schema_version": "1.1",
            "type_definitions": [
            {
                "type": "user"
            },
            {
                "type": "team",
                "relations": {
                    "member": {
                        "union": {
                            "child": [
                                {"this": {}},
                                {"computedUserset": {"relation": "manager"}},
                            ]
                        }
                    },
                    "manager": {"this": {}},
                },
                "metadata": {
                    "relations": {
                        "member": {
                            "directly_related_user_types": [{"type": "user"}]
                        },
                        "manager": {
                            "directly_related_user_types": [{"type": "user"}]
                        }
                    }
                }
            },
            {
                "type": "contact",
                "relations": {
                    "owner": {"this": {}},
                    "assigned": {"this": {}},
                    "team": {"this": {}},
                    "can_read": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {"computedUserset": {"relation": "assigned"}},
                                {
                                    "tupleToUserset": {
                                        "computedUserset": {"relation": "member"},
                                        "tupleset": {"relation": "team"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_update": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {"computedUserset": {"relation": "assigned"}},
                            ]
                        }
                    },
                },
                "metadata": {
                    "relations": {
                        "owner": {
                            "directly_related_user_types": [{"type": "user"}]
                        },
                        "assigned": {
                            "directly_related_user_types": [{"type": "user"}]
                        },
                        "team": {
                            "directly_related_user_types": [{"type": "team"}]
                        }
                    }
                }
            },
            {
                "type": "account",
                "relations": {
                    "owner": {"this": {}},
                    "assigned": {"this": {}},
                    "team": {"this": {}},
                    "can_read": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {"computedUserset": {"relation": "assigned"}},
                                {
                                    "tupleToUserset": {
                                        "computedUserset": {"relation": "member"},
                                        "tupleset": {"relation": "team"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_update": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {"computedUserset": {"relation": "assigned"}},
                            ]
                        }
                    },
                },
                "metadata": {
                    "relations": {
                        "owner": {
                            "directly_related_user_types": [{"type": "user"}]
                        },
                        "assigned": {
                            "directly_related_user_types": [{"type": "user"}]
                        },
                        "team": {
                            "directly_related_user_types": [{"type": "team"}]
                        }
                    }
                }
            },
            {
                "type": "lead",
                "relations": {
                    "owner": {"this": {}},
                    "assigned": {"this": {}},
                    "team": {"this": {}},
                    "can_read": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {"computedUserset": {"relation": "assigned"}},
                                {
                                    "tupleToUserset": {
                                        "computedUserset": {"relation": "member"},
                                        "tupleset": {"relation": "team"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_update": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {"computedUserset": {"relation": "assigned"}},
                            ]
                        }
                    },
                },
                "metadata": {
                    "relations": {
                        "owner": {
                            "directly_related_user_types": [{"type": "user"}]
                        },
                        "assigned": {
                            "directly_related_user_types": [{"type": "user"}]
                        },
                        "team": {
                            "directly_related_user_types": [{"type": "team"}]
                        }
                    }
                }
            },
        ]
    })
    
        model_id = response.authorization_model_id
        print(f"✓ Authorization model created: {model_id}")
        return model_id
    except Exception as e:
        print(f"✗ Failed to create authorization model: {e}")
        raise


async def write_sample_tuples(fga_client: OpenFgaClient, model_id: str) -> None:
    """Write sample authorization tuples for testing."""
    
    print("Writing sample authorization tuples...")
    
    # Sample tuples - adjust these based on your EspoCRM data
    sample_tuples = [
        # Team structure
        {"user": "user:admin", "relation": "manager", "object": "team:sales"},
        {"user": "user:manager1", "relation": "manager", "object": "team:sales"},
        {"user": "user:sales1", "relation": "member", "object": "team:sales"},
        {"user": "user:sales2", "relation": "member", "object": "team:sales"},
        
        # Sample account ownership
        {"user": "user:admin", "relation": "owner", "object": "account:account1"},
        {"user": "user:manager1", "relation": "assigned", "object": "account:account2"},
        {"user": "team:sales", "relation": "team", "object": "account:account2"},
        
        # Sample contact ownership
        {"user": "user:sales1", "relation": "owner", "object": "contact:contact1"},
        {"user": "user:sales1", "relation": "assigned", "object": "contact:contact2"},
        {"user": "team:sales", "relation": "team", "object": "contact:contact2"},
        
        # Sample lead ownership
        {"user": "user:sales2", "relation": "owner", "object": "lead:lead1"},
        {"user": "team:sales", "relation": "team", "object": "lead:lead1"},
    ]
    
    # Convert to ClientTuple objects
    tuples = [
        ClientTuple(
            user=t["user"],
            relation=t["relation"],
            object=t["object"],
        )
        for t in sample_tuples
    ]
    
    # Write tuples with error handling for duplicates
    request = ClientWriteRequest(writes=tuples)
    try:
        await fga_client.write(request, {"authorization_model_id": model_id})
        print(f"✓ Sample tuples written: {len(sample_tuples)} tuples")
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg or "already existed" in error_msg:
            print(f"⚠ Sample tuples already exist, skipping...")
            print(f"  (This is normal if you run the script multiple times)")
        else:
            # Re-raise if it's a different error
            raise


async def main():
    """Main initialization function."""
    # Load environment variables
    load_dotenv()
    
    # Get FGA configuration
    api_url = os.getenv("FGA_API_URL", "https://api.us1.fga.dev")
    store_id = os.getenv("FGA_STORE_ID")
    client_id = os.getenv("FGA_CLIENT_ID")
    client_secret = os.getenv("FGA_CLIENT_SECRET")
    api_issuer = os.getenv("FGA_API_ISSUER", "auth.fga.dev")
    api_audience = os.getenv("FGA_API_AUDIENCE", f"{api_url}/")
    
    if not all([store_id, client_id, client_secret]):
        print("Error: Missing FGA configuration. Please set:")
        print("  - FGA_STORE_ID")
        print("  - FGA_CLIENT_ID")
        print("  - FGA_CLIENT_SECRET")
        sys.exit(1)
    
    print("Initializing FGA for EspoCRM...")
    print(f"API URL: {api_url}")
    print(f"Store ID: {store_id}")
    
    # Create credentials following official SDK pattern
    credentials = Credentials(
        method="client_credentials",
        configuration=CredentialConfiguration(
            api_issuer=api_issuer,
            api_audience=api_audience,
            client_id=client_id,
            client_secret=client_secret,
        )
    )
    
    # Create FGA client configuration
    configuration = ClientConfiguration(
        api_url=api_url,
        store_id=store_id,
        credentials=credentials,
    )
    
    # Use context manager for proper resource management
    async with OpenFgaClient(configuration) as fga_client:
        try:
            # Create authorization model
            model_id = await create_authorization_model(fga_client)
            
            # Write sample tuples
            await write_sample_tuples(fga_client, model_id)
            
            print("\n✓ FGA initialization complete!")
            print(f"\nAdd this to your .env file:")
            print(f"FGA_AUTHORIZATION_MODEL_ID={model_id}")
            
        except Exception as e:
            print(f"\n✗ Error during initialization: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
