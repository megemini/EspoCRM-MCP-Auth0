"""Configuration management for EspoCRM MCP Server."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Literal, Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class EspoCRMConfig:
    """EspoCRM connection configuration."""

    url: str
    api_key: str
    secret_key: Optional[str] = None
    auth_method: Literal["apikey", "hmac"] = "apikey"
    timeout: int = 30


@dataclass(frozen=True)
class FGAConfig:
    """FGA (Fine-Grained Authorization) configuration."""

    api_url: str
    store_id: str
    client_id: str
    client_secret: str
    authorization_model_id: Optional[str] = None
    api_issuer: str = "auth.fga.dev"
    api_audience: Optional[str] = None
    enabled: bool = True


@dataclass(frozen=True)
class OAuthConfig:
    """OAuth configuration for dynamic token acquisition via Auth0 Universal Login."""

    client_id: str
    client_secret: str
    secret_key: str
    scopes: List[str] = field(
        default_factory=lambda: [
            "openid",
            "profile",
            "email",
            "espocrm:contacts:read",
            "espocrm:contacts:write",
            "espocrm:accounts:read",
            "espocrm:accounts:write",
            "espocrm:leads:read",
            "espocrm:leads:write",
            "espocrm:opportunities:read",
            "espocrm:opportunities:write",
            "espocrm:meetings:read",
            "espocrm:meetings:write",
            "espocrm:tasks:read",
            "espocrm:tasks:write",
            "espocrm:calls:read",
            "espocrm:calls:write",
            "espocrm:cases:read",
            "espocrm:cases:write",
            "espocrm:notes:read",
            "espocrm:notes:write",
            "espocrm:users:read",
            "espocrm:teams:read",
            "espocrm:teams:write",
            "espocrm:entities:read",
            "espocrm:entities:write",
        ]
    )
    enabled: bool = True


@dataclass(frozen=True)
class Config:
    """Application configuration."""

    auth0_domain: str
    auth0_audience: str
    mcp_server_url: str
    espocrm: EspoCRMConfig
    fga: Optional[FGAConfig] = None
    oauth: Optional[OAuthConfig] = None
    port: int = 3001
    debug: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables."""
        auth0_domain = os.getenv("AUTH0_DOMAIN")
        if not auth0_domain:
            raise ValueError("AUTH0_DOMAIN environment variable is required")

        auth0_audience = os.getenv("AUTH0_AUDIENCE")
        if not auth0_audience:
            raise ValueError("AUTH0_AUDIENCE environment variable is required")

        espocrm_url = os.getenv("ESPOCRM_URL")
        if not espocrm_url:
            raise ValueError("ESPOCRM_URL environment variable is required")

        espocrm_api_key = os.getenv("ESPOCRM_API_KEY")
        if not espocrm_api_key:
            raise ValueError("ESPOCRM_API_KEY environment variable is required")

        auth_method = os.getenv("ESPOCRM_AUTH_METHOD", "apikey")
        if auth_method not in ("apikey", "hmac"):
            raise ValueError(
                f"Invalid ESPOCRM_AUTH_METHOD: {auth_method}. Must be 'apikey' or 'hmac'"
            )

        espocrm_config = EspoCRMConfig(
            url=espocrm_url,
            api_key=espocrm_api_key,
            secret_key=os.getenv("ESPOCRM_SECRET_KEY"),
            auth_method=auth_method,  # type: ignore[arg-type]
            timeout=int(os.getenv("ESPOCRM_TIMEOUT", "30")),
        )

        # Load FGA configuration (optional)
        fga_config = None
        fga_enabled = os.getenv("FGA_ENABLED", "false").lower() == "true"

        if fga_enabled:
            fga_api_url = os.getenv("FGA_API_URL")
            fga_store_id = os.getenv("FGA_STORE_ID")
            fga_client_id = os.getenv("FGA_CLIENT_ID")
            fga_client_secret = os.getenv("FGA_CLIENT_SECRET")

            if not all([fga_api_url, fga_store_id, fga_client_id, fga_client_secret]):
                raise ValueError(
                    "FGA is enabled but missing required configuration. "
                    "Please set FGA_API_URL, FGA_STORE_ID, FGA_CLIENT_ID, and FGA_CLIENT_SECRET"
                )

            fga_config = FGAConfig(
                api_url=fga_api_url,
                store_id=fga_store_id,
                client_id=fga_client_id,
                client_secret=fga_client_secret,
                authorization_model_id=os.getenv("FGA_AUTHORIZATION_MODEL_ID"),
                api_issuer=os.getenv("FGA_API_ISSUER", "auth.fga.dev"),
                api_audience=os.getenv("FGA_API_AUDIENCE"),
                enabled=True,
            )

        # Load OAuth configuration (optional - for dynamic token acquisition)
        oauth_config = None
        oauth_enabled = os.getenv("OAUTH_ENABLED", "false").lower() == "true"

        if oauth_enabled:
            oauth_client_id = os.getenv("OAUTH_CLIENT_ID")
            oauth_client_secret = os.getenv("OAUTH_CLIENT_SECRET")
            oauth_secret_key = os.getenv("OAUTH_SECRET_KEY")

            if not all([oauth_client_id, oauth_client_secret, oauth_secret_key]):
                raise ValueError(
                    "OAuth is enabled but missing required configuration. "
                    "Please set OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, and OAUTH_SECRET_KEY"
                )

            oauth_config = OAuthConfig(
                client_id=oauth_client_id,
                client_secret=oauth_client_secret,
                secret_key=oauth_secret_key,
                enabled=True,
            )

        return cls(
            auth0_domain=auth0_domain,
            auth0_audience=auth0_audience,
            mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:3001"),
            espocrm=espocrm_config,
            fga=fga_config,
            oauth=oauth_config,
            port=int(os.getenv("PORT", "3001")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        )


def get_config() -> Config:
    """Get application configuration."""
    load_dotenv()
    return Config.from_env()
