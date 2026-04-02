"""Main server application for EspoCRM MCP Server with Auth0 authentication."""
from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncIterator

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount

from .auth0 import Auth0Mcp
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
        yield
        # Cleanup
        await espocrm_client.close()
        logger.info("EspoCRM MCP Server shut down")


# Create Starlette application
starlette_app = Starlette(
    debug=config.debug,
    routes=[
        # Add discovery metadata route
        Mount("/", app=auth0_mcp.auth_metadata_router()),

        # Main MCP app route with authentication middleware
        Mount(
            "/",
            app=auth0_mcp.mcp.streamable_http_app(),
            middleware=auth0_mcp.auth_middleware()
        ),
    ],
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
