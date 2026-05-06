import logging
from mcp.server.fastmcp import Context

logger = logging.getLogger("GppContextMCP.utils")

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
            logger.error(f"Tenant isolation violation: Missing or malformed user_id in context: {user_id}")
            raise ValueError("Tenant isolation violation: Missing or malformed iv_id in context.")

        iv_id = user_id.split("::iv::")[1]
        return iv_id
    except AttributeError:
        logger.error("Could not find session info in context")
        raise ValueError("Authentication context missing.")
