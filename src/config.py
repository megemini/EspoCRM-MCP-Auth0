"""Configuration management for EspoCRM MCP Server."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal, Optional, List

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
class Config:
    """Application configuration."""
    auth0_domain: str
    auth0_audience: str
    mcp_server_url: str
    espocrm: EspoCRMConfig
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

        espocrm_config = EspoCRMConfig(
            url=espocrm_url,
            api_key=espocrm_api_key,
            secret_key=os.getenv("ESPOCRM_SECRET_KEY"),
            auth_method=os.getenv("ESPOCRM_AUTH_METHOD", "apikey"),
            timeout=int(os.getenv("ESPOCRM_TIMEOUT", "30")),
        )

        return cls(
            auth0_domain=auth0_domain,
            auth0_audience=auth0_audience,
            mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:3001"),
            espocrm=espocrm_config,
            port=int(os.getenv("PORT", "3001")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        )


def get_config() -> Config:
    """Get application configuration."""
    load_dotenv()
    return Config.from_env()
