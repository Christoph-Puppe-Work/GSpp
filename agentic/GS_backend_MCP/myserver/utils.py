import logging
import os
from mcp.server.fastmcp import Context

logger = logging.getLogger("GppContextMCP.utils")

def get_iv_id(ctx: Context) -> str:
    """
    Extracts IV-ID from the authenticated session context.
    Expected format: caller::iv::iv-12345
    """
    user_id = None

    try:
        # 1. Check HTTP headers explicitly propagated by ADK's dynamic header provider.
        if hasattr(ctx, "request_context") and hasattr(ctx.request_context, "meta") and isinstance(ctx.request_context.meta, dict):
            headers = ctx.request_context.meta.get("headers", {})
            # ASGI/FastAPI typically lowercases headers
            user_id = headers.get("x-gpp-user-id")

        # 2. Check the FastMCP session object (legacy / standard way)
        if not user_id and hasattr(ctx, "request_context") and hasattr(ctx.request_context, "session"):
            user_id = getattr(ctx.request_context.session, "user_id", None)

        if not user_id or "::iv::" not in user_id:
            fallback_iv_id = _get_dev_fallback_iv_id()
            if fallback_iv_id:
                logger.warning(
                    "Using local development IV fallback %r for malformed "
                    "user_id %r. Disable GPP_BACKEND_ALLOW_DEV_IV_FALLBACK "
                    "outside local development.",
                    fallback_iv_id,
                    user_id,
                )
                return fallback_iv_id
            logger.error(f"Tenant isolation violation: Missing or malformed user_id in context: {user_id}")
            raise ValueError("Tenant isolation violation: Missing or malformed iv_id in context.")

        iv_id = user_id.split("::iv::")[1]
        return iv_id
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Could not find session info in context: {e}")
        fallback_iv_id = _get_dev_fallback_iv_id()
        if fallback_iv_id:
            logger.warning(
                "Using local development IV fallback %r because MCP session "
                "context is unavailable.",
                fallback_iv_id,
            )
            return fallback_iv_id
        raise ValueError("Authentication context missing.")


def _get_dev_fallback_iv_id() -> str | None:
    """Return a local-dev tenant fallback only when explicitly enabled."""
    allow = os.getenv("GPP_BACKEND_ALLOW_DEV_IV_FALLBACK", "").lower()
    if allow not in {"1", "true", "yes"}:
        return None

    iv_id = os.getenv("GPP_BACKEND_DEV_IV_ID", "").strip()
    return iv_id or None
