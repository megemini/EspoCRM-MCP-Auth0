"""Authorization decorators for MCP tools."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any

from mcp.server.fastmcp import Context

from . import Auth0Mcp
from .errors import AuthenticationRequired, InsufficientPermission, InsufficientScope

# Collect required scopes from all decorated functions
_scopes_required: set[str] = set()


def require_scopes(required_scopes: Iterable[str]):
    """
    Decorator that requires scopes on MCP tools.

    Example:
      @mcp.tool(...)
      @require_scopes(["tool:greet", "tool:whoami"])
      async def my_tool(name: str, ctx: Context) -> str:
        return f"Hello {name}!"
    """
    required_scopes_list = list(required_scopes)

    # Collect scopes when decorator is applied
    _scopes_required.update(required_scopes_list)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # ctx is passed in either kw or positional
            ctx: Context | None = (
                kwargs.get("ctx") if isinstance(kwargs.get("ctx"), Context) else None
            ) or next((arg for arg in args if isinstance(arg, Context)), None)
            if ctx is None:
                raise TypeError("ctx: Context is required")

            auth = getattr(ctx.request_context.request.state, "auth", {})
            if not auth:
                raise AuthenticationRequired("Authentication required")

            user_scopes = set(auth.get("scopes", []))
            missing_scopes = [s for s in required_scopes_list if s not in user_scopes]
            if missing_scopes:
                raise InsufficientScope(f"Missing required scopes: {missing_scopes}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def register_required_scopes(auth0_mcp: Auth0Mcp) -> None:
    """Register all scopes that were collected from @require_scopes decorators."""
    if _scopes_required:
        auth0_mcp.register_scopes(list(_scopes_required))
        _scopes_required.clear()


def require_fga_permission(
    object_type: str,
    object_id_param: str = "entity_id",
    relation: str = "can_read",
):
    """
    Decorator that requires FGA permission check.

    This decorator checks fine-grained authorization using FGA before allowing
    the tool to execute. It should be used alongside @require_scopes for
    defense-in-depth security.

    Args:
        object_type: The type of object (e.g., 'contact', 'account', 'lead')
        object_id_param: The parameter name containing the object ID
        relation: The relation to check (e.g., 'can_read', 'can_update', 'can_delete')

    Example:
        @mcp.tool(...)
        @require_scopes(["espocrm:contacts:read"])
        @require_fga_permission(object_type="contact", object_id_param="contact_id", relation="can_read")
        async def get_contact(contact_id: str, ctx: Context) -> str:
            return "Contact data"
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get context
            ctx: Context | None = (
                kwargs.get("ctx") if isinstance(kwargs.get("ctx"), Context) else None
            ) or next((arg for arg in args if isinstance(arg, Context)), None)
            if ctx is None:
                raise TypeError("ctx: Context is required")

            # Get user ID from auth context
            auth = getattr(ctx.request_context.request.state, "auth", {})
            if not auth:
                raise AuthenticationRequired("Authentication required")

            user_id = auth.get("extra", {}).get("sub")
            if not user_id:
                raise AuthenticationRequired("User ID not found in token")

            # Get object ID from parameters
            object_id = kwargs.get(object_id_param)
            if not object_id:
                # Try to find in positional args by inspecting function signature
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if object_id_param in params:
                    idx = params.index(object_id_param)
                    if idx < len(args):
                        object_id = args[idx]

            if not object_id:
                raise ValueError(f"Object ID parameter '{object_id_param}' not found")

            # Check FGA permission
            from .fga import get_fga_client

            fga_client = get_fga_client()
            await fga_client.check_permission_or_raise(
                user=user_id,
                object_type=object_type,
                object_id=str(object_id),
                relation=relation,
            )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_fga_permission_batch(
    object_type: str,
    object_ids_param: str = "entity_ids",
    relation: str = "can_read",
):
    """
    Decorator that requires FGA permission check for batch operations.

    This checks that the user has permission on ALL objects in the batch.

    Args:
        object_type: The type of object
        object_ids_param: The parameter name containing the list of object IDs
        relation: The relation to check

    Example:
        @mcp.tool(...)
        @require_scopes(["espocrm:contacts:read"])
        @require_fga_permission_batch(object_type="contact", object_ids_param="contact_ids")
        async def get_contacts(contact_ids: list[str], ctx: Context) -> str:
            return "Contacts data"
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get context
            ctx: Context | None = (
                kwargs.get("ctx") if isinstance(kwargs.get("ctx"), Context) else None
            ) or next((arg for arg in args if isinstance(arg, Context)), None)
            if ctx is None:
                raise TypeError("ctx: Context is required")

            # Get user ID from auth context
            auth = getattr(ctx.request_context.request.state, "auth", {})
            if not auth:
                raise AuthenticationRequired("Authentication required")

            user_id = auth.get("extra", {}).get("sub")
            if not user_id:
                raise AuthenticationRequired("User ID not found in token")

            # Get object IDs from parameters
            object_ids = kwargs.get(object_ids_param)
            if not object_ids:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if object_ids_param in params:
                    idx = params.index(object_ids_param)
                    if idx < len(args):
                        object_ids = args[idx]

            if not object_ids:
                raise ValueError(f"Object IDs parameter '{object_ids_param}' not found")

            # Check FGA permission for all objects
            from .fga import get_fga_client

            fga_client = get_fga_client()

            for object_id in object_ids:
                await fga_client.check_permission_or_raise(
                    user=user_id,
                    object_type=object_type,
                    object_id=str(object_id),
                    relation=relation,
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
