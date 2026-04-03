"""Main server application for EspoCRM MCP Server with Auth0 authentication."""
from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncIterator

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route

from .auth0 import Auth0Mcp
from .auth0.fga import FGAClient, set_fga_client
from .auth0.oauth import OAuthManager
from .config import get_config
from .espocrm import EspoCRMClient
from .tools import register_tools, set_espocrm_client

config = get_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Auth0 MCP
auth0_mcp = Auth0Mcp(
    name="EspoCRM MCP Server",
    audience=config.auth0_audience,
    domain=config.auth0_domain,
    mcp_server_url=config.mcp_server_url
)

# Initialize EspoCRM client
espocrm_client = EspoCRMClient(config.espocrm)
set_espocrm_client(espocrm_client)

# Initialize FGA client (if configured)
fga_client = None
if config.fga and config.fga.enabled:
    try:
        fga_client = FGAClient(
            api_url=config.fga.api_url,
            store_id=config.fga.store_id,
            client_id=config.fga.client_id,
            client_secret=config.fga.client_secret,
            authorization_model_id=config.fga.authorization_model_id,
            api_issuer=config.fga.api_issuer,
            api_audience=config.fga.api_audience,
        )
        set_fga_client(fga_client)
        logger.info("FGA client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize FGA client: {e}")
        logger.warning("Continuing without FGA - using scope-based authorization only")

# Initialize OAuth manager (if configured)
oauth_manager = None
if config.oauth and config.oauth.enabled:
    try:
        oauth_manager = OAuthManager(
            auth0_domain=config.auth0_domain,
            auth0_client_id=config.oauth.client_id,
            auth0_client_secret=config.oauth.client_secret,
            auth0_audience=config.auth0_audience,
            mcp_server_url=config.mcp_server_url,
            secret_key=config.oauth.secret_key,
        )
        logger.info("OAuth manager initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize OAuth manager: {e}")
        logger.warning("Continuing without OAuth - manual token required")

# Register MCP tools
register_tools(auth0_mcp)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """Application lifespan context manager."""
    async with contextlib.AsyncExitStack() as stack:
        # Start MCP session manager
        await stack.enter_async_context(auth0_mcp.mcp.session_manager.run())
        logger.info("EspoCRM MCP Server started successfully")
        logger.info(f"EspoCRM URL: {config.espocrm.url}")
        logger.info(f"Auth Method: {config.espocrm.auth_method}")
        if fga_client:
            logger.info("FGA: Enabled")
        else:
            logger.info("FGA: Disabled (using scope-based authorization)")
        if oauth_manager:
            logger.info("OAuth: Enabled (dynamic token acquisition via Auth0 Universal Login)")
        else:
            logger.info("OAuth: Disabled (manual token required)")
        yield
        # Cleanup
        await espocrm_client.close()
        if fga_client:
            await fga_client.close()
        logger.info("EspoCRM MCP Server shut down")


# Build routes
routes = [
    # Discovery metadata route (specific path, won't shadow /mcp)
    Mount("/.well-known", app=auth0_mcp.well_known_app()),
]

# Add OAuth routes if enabled
if oauth_manager:
    routes.extend([
        Route("/auth/login", endpoint=oauth_manager.login, methods=["GET"]),
        Route("/auth/callback", endpoint=oauth_manager.callback, methods=["GET"]),
        Route("/auth/token", endpoint=oauth_manager.get_token, methods=["GET"]),
        Route("/auth/logout", endpoint=oauth_manager.logout, methods=["GET"]),
    ])

# Add main MCP app route
routes.append(
    Mount(
        "/",
        app=auth0_mcp.mcp.streamable_http_app(),
        middleware=auth0_mcp.auth_middleware()
    )
)

# Create Starlette application
starlette_app = Starlette(
    debug=config.debug,
    routes=routes,
    lifespan=lifespan,
    exception_handlers=auth0_mcp.exception_handlers(),
)

# Wrap ASGI application with CORS middleware
app = CORSMiddleware(
    starlette_app,
    allow_origins=config.cors_origins,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],  # MCP streamable HTTP methods
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Mcp-Session-Id",
        "Mcp-Protocol-Version",
        "Last-Event-Id",
    ],
    expose_headers=["Mcp-Session-Id"],
)


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on port {config.port}")
    uvicorn.run(app, port=config.port)
