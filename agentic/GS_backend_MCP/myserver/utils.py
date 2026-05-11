import logging
import os
from mcp.server.fastmcp import Context

logger = logging.getLogger("GppContextMCP.utils")
_warned_dev_fallbacks: set[tuple[str, str, str | None]] = set()


def _warn_dev_fallback_once(
    reason: str,
    fallback_iv_id: str,
    user_id: str | None = None,
) -> None:
    """Log the explicit local-dev fallback once per reason/fallback/user."""
    key = (reason, fallback_iv_id, user_id)
    if key in _warned_dev_fallbacks:
        return

    _warned_dev_fallbacks.add(key)
    if user_id is None:
        logger.warning(
            "Using local development IV fallback %r because %s. Disable "
            "GPP_BACKEND_ALLOW_DEV_IV_FALLBACK outside local development.",
            fallback_iv_id,
            reason,
        )
        return

    logger.warning(
        "Using local development IV fallback %r for %s user_id %r. Disable "
        "GPP_BACKEND_ALLOW_DEV_IV_FALLBACK outside local development.",
        fallback_iv_id,
        reason,
        user_id,
    )


def get_iv_id(ctx: Context) -> str:
    """
    Extracts IV-ID from the authenticated session context.
    Expected format: caller::iv::iv-12345
    """
    # In newer mcp SDK, access might differ, but based on skill:
    # ctx.request_context.session.user_id
    try:
        user_id = ctx.request_context.session.user_id
        if not user_id or "::iv::" not in user_id:
            fallback_iv_id = _get_dev_fallback_iv_id()
            if fallback_iv_id:
                _warn_dev_fallback_once("malformed", fallback_iv_id, user_id)
                return fallback_iv_id
            logger.error(
                "Tenant isolation violation: Missing or malformed user_id "
                "in context: %r",
                user_id,
            )
            raise ValueError(
                "Tenant isolation violation: Missing or malformed iv_id in context."
            )

        iv_id = user_id.split("::iv::")[1]
        return iv_id
    except AttributeError:
        fallback_iv_id = _get_dev_fallback_iv_id()
        if fallback_iv_id:
            _warn_dev_fallback_once(
                "MCP session context is unavailable",
                fallback_iv_id,
            )
            return fallback_iv_id
        logger.error("Could not find session info in context")
        raise ValueError("Authentication context missing.")


def _get_dev_fallback_iv_id() -> str | None:
    """Return a local-dev tenant fallback only when explicitly enabled."""
    allow = os.getenv("GPP_BACKEND_ALLOW_DEV_IV_FALLBACK", "").lower()
    if allow not in {"1", "true", "yes"}:
        return None

    iv_id = os.getenv("GPP_BACKEND_DEV_IV_ID", "").strip()
    return iv_id or None
