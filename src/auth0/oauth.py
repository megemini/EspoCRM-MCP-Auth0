"""OAuth authentication using Auth0 Universal Login Page.

This module provides dynamic token acquisition for MCP clients like CherryStudio,
using Auth0's hosted Universal Login Page for secure authentication.
"""

from __future__ import annotations

import logging
import secrets
import time

from authlib.integrations.starlette_client import OAuth
from itsdangerous import URLSafeTimedSerializer
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class OAuthManager:
    """
    OAuth manager for Auth0 Universal Login Page integration.

    Provides endpoints for:
    - /auth/login: Redirects to Auth0 Universal Login Page
    - /auth/callback: Handles OAuth callback and exchanges code for token
    - /auth/token: Retrieves stored token by session ID
    - /auth/logout: Invalidates session and logs out

    This implementation uses Auth0's hosted login page for maximum security
    and best user experience.
    """

    def __init__(
        self,
        auth0_domain: str,
        auth0_client_id: str,
        auth0_client_secret: str,
        auth0_audience: str,
        mcp_server_url: str,
        secret_key: str,
        scopes: list[str] | None = None,
    ):
        """
        Initialize OAuth manager.

        Args:
            auth0_domain: Auth0 tenant domain (e.g., 'tenant.us.auth0.com')
            auth0_client_id: Auth0 application client ID
            auth0_client_secret: Auth0 application client secret
            auth0_audience: Auth0 API identifier
            mcp_server_url: Base URL of the MCP server
            secret_key: Secret key for session signing
            scopes: OAuth scopes to request (optional)
        """
        self.auth0_domain = auth0_domain
        self.auth0_client_id = auth0_client_id
        self.auth0_client_secret = auth0_client_secret
        self.auth0_audience = auth0_audience
        self.mcp_server_url = mcp_server_url.rstrip("/")
        self.secret_key = secret_key

        # Use provided scopes or default to openid scopes
        self.scopes = scopes or ["openid", "profile", "email"]

        # Initialize OAuth client with Auth0
        self.oauth = OAuth()
        self.oauth.register(
            "auth0",
            client_id=self.auth0_client_id,
            client_secret=self.auth0_client_secret,
            server_metadata_url=f"https://{self.auth0_domain}/.well-known/openid-configuration",
            client_kwargs={
                "scope": " ".join(self.scopes),
            },
        )

        # Session serializer for secure state management
        self.serializer = URLSafeTimedSerializer(secret_key, salt="oauth-session")

        # In-memory token storage (use Redis/database in production)
        self._token_store: dict[str, dict] = {}
        self._state_store: dict[str, float] = {}

        logger.info(f"OAuth manager initialized for Auth0 domain: {auth0_domain}")

    async def login(self, request: Request) -> Response:
        """
        Initiate OAuth login flow using Auth0 Universal Login Page.

        This endpoint redirects the user to Auth0's hosted login page,
        where they can authenticate using any configured method
        (email/password, social login, MFA, etc.).

        Args:
            request: Starlette request object

        Returns:
            RedirectResponse to Auth0 Universal Login Page
        """
        # Generate callback URL
        callback_url = f"{self.mcp_server_url}/auth/callback"

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Store state with timestamp (expires in 10 minutes)
        self._state_store[state] = time.time() + 600

        # Clean up expired states
        self._cleanup_expired_states()

        logger.info(f"Initiating OAuth login, state: {state[:8]}...")

        # Use Auth0's authorize_redirect which will redirect to Universal Login Page
        redirect = await self.oauth.auth0.authorize_redirect(
            request,
            redirect_uri=callback_url,
            state=state,
            audience=self.auth0_audience,
        )

        return redirect

    async def callback(self, request: Request) -> Response:
        """
        Handle OAuth callback from Auth0 Universal Login Page.

        After successful authentication, Auth0 redirects to this endpoint
        with an authorization code. This endpoint exchanges the code
        for an access token and stores it securely.

        Args:
            request: Starlette request object with code and state parameters

        Returns:
            JSONResponse with session_id and token information
        """
        try:
            # Extract state from query parameters
            state = request.query_params.get("state")

            if not state:
                logger.error("OAuth callback missing state parameter")
                return JSONResponse(
                    {
                        "error": "invalid_request",
                        "error_description": "Missing state parameter",
                    },
                    status_code=400,
                )

            # Verify state to prevent CSRF attacks
            if state not in self._state_store:
                logger.error(f"Invalid or expired state: {state[:8]}...")
                return JSONResponse(
                    {
                        "error": "invalid_state",
                        "error_description": "Invalid or expired state parameter",
                    },
                    status_code=400,
                )

            # Check if state has expired
            if time.time() > self._state_store[state]:
                del self._state_store[state]
                logger.error(f"State expired: {state[:8]}...")
                return JSONResponse(
                    {
                        "error": "expired_state",
                        "error_description": "State parameter has expired",
                    },
                    status_code=400,
                )

            # Remove used state
            del self._state_store[state]

            # Exchange authorization code for access token
            callback_url = f"{self.mcp_server_url}/auth/callback"
            token = await self.oauth.auth0.authorize_access_token(
                request, redirect_uri=callback_url
            )

            # Extract token information
            access_token = token.get("access_token")
            if not access_token:
                logger.error("No access token in Auth0 response")
                return JSONResponse(
                    {
                        "error": "no_token",
                        "error_description": "No access token in response",
                    },
                    status_code=500,
                )

            # Generate session ID
            session_id = secrets.token_urlsafe(32)

            # Store token with metadata
            self._token_store[session_id] = {
                "access_token": access_token,
                "token_type": token.get("token_type", "Bearer"),
                "expires_at": time.time() + token.get("expires_in", 3600),
                "scope": token.get("scope", ""),
                "created_at": time.time(),
            }

            logger.info(f"OAuth callback successful, session: {session_id[:8]}...")

            # Return token information to client
            # CherryStudio can use session_id to retrieve token later
            return JSONResponse(
                {
                    "success": True,
                    "session_id": session_id,
                    "access_token": access_token,
                    "token_type": token.get("token_type", "Bearer"),
                    "expires_in": token.get("expires_in", 3600),
                    "scope": token.get("scope", ""),
                }
            )

        except Exception as e:
            logger.error(f"OAuth callback error: {e}", exc_info=True)
            return JSONResponse(
                {
                    "error": "callback_error",
                    "error_description": f"Authentication failed: {str(e)}",
                },
                status_code=500,
            )

    async def get_token(self, request: Request) -> Response:
        """
        Retrieve stored access token by session ID.

        CherryStudio can call this endpoint to get the token
        after the user completes authentication.

        Args:
            request: Starlette request with session_id query parameter

        Returns:
            JSONResponse with token or error
        """
        session_id = request.query_params.get("session_id")

        if not session_id:
            return JSONResponse(
                {
                    "error": "missing_session_id",
                    "error_description": "Session ID not provided",
                },
                status_code=400,
            )

        # Retrieve token from store
        token_data = self._token_store.get(session_id)

        if not token_data:
            logger.warning(f"Invalid session: {session_id[:8]}...")
            return JSONResponse(
                {
                    "error": "invalid_session",
                    "error_description": "Invalid or expired session",
                },
                status_code=404,
            )

        # Check if token has expired
        if time.time() > token_data["expires_at"]:
            del self._token_store[session_id]
            logger.info(f"Token expired for session: {session_id[:8]}...")
            return JSONResponse(
                {
                    "error": "token_expired",
                    "error_description": "Access token has expired",
                },
                status_code=401,
            )

        # Return token information
        return JSONResponse(
            {
                "access_token": token_data["access_token"],
                "token_type": token_data["token_type"],
                "expires_in": int(token_data["expires_at"] - time.time()),
                "scope": token_data["scope"],
            }
        )

    async def logout(self, request: Request) -> Response:
        """
        Logout and invalidate session.

        Args:
            request: Starlette request with session_id query parameter

        Returns:
            JSONResponse confirming logout
        """
        session_id = request.query_params.get("session_id")

        if session_id and session_id in self._token_store:
            del self._token_store[session_id]
            logger.info(f"Session logged out: {session_id[:8]}...")

        return JSONResponse({"success": True, "message": "Logged out successfully"})

    def _cleanup_expired_states(self) -> None:
        """Remove expired state parameters to prevent memory leaks."""
        current_time = time.time()
        expired_states = [
            state
            for state, expiry in self._state_store.items()
            if current_time > expiry
        ]

        for state in expired_states:
            del self._state_store[state]

        if expired_states:
            logger.debug(f"Cleaned up {len(expired_states)} expired states")

    def cleanup_expired_tokens(self) -> None:
        """
        Remove expired tokens from store.

        This should be called periodically (e.g., by a background task)
        to prevent memory leaks.
        """
        current_time = time.time()
        expired_sessions = [
            session_id
            for session_id, token_data in self._token_store.items()
            if current_time > token_data["expires_at"]
        ]

        for session_id in expired_sessions:
            del self._token_store[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired tokens")
