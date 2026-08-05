import logging
import os
import time

import google.auth.transport.requests
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

logger = logging.getLogger("gpp_agent.mcp_clients")

# Generous connect timeout: the MCP Cloud Run services may cold-start
# (observed ~7 s); the ADK default of 5 s loses that race.
_MCP_TIMEOUT_S = float(os.environ.get("MCP_CONNECT_TIMEOUT_S", "30"))
_MCP_SSE_READ_TIMEOUT_S = float(os.environ.get("MCP_SSE_READ_TIMEOUT_S", "300"))

# Refresh ID tokens 5 minutes before their (1 h) expiry.
_TOKEN_TTL_S = 55 * 60
_token_cache: dict[str, tuple[str, float]] = {}


def _id_token_for(audience_url: str) -> str | None:
    """Return a cached Google identity token for a Cloud Run audience.

    Returns None for localhost targets (no auth needed). For remote targets a
    failure to obtain a token is logged at ERROR — an unauthenticated request
    to a private Cloud Run service yields an opaque 401/403 that is easily
    misread as "MCP server down".
    """
    if audience_url.startswith("http://localhost") or audience_url.startswith("http://127."):
        return None

    cached = _token_cache.get(audience_url)
    if cached and cached[1] > time.monotonic():
        return cached[0]

    try:
        from google.oauth2 import id_token

        request = google.auth.transport.requests.Request()
        token = id_token.fetch_id_token(request, audience_url)
        _token_cache[audience_url] = (token, time.monotonic() + _TOKEN_TTL_S)
        return token
    except Exception:
        logger.exception(
            "Failed to fetch identity token for MCP audience %s — the request "
            "will go out UNAUTHENTICATED and a private Cloud Run service will "
            "reject it.",
            audience_url,
        )
        return None


class McpClientService:
    def __init__(self, anwender_url: str | None = None, backend_url: str | None = None):
        self.anwender_url = anwender_url or os.environ.get("ANWENDER_MCP_URL", "http://localhost:8080")
        self.backend_url  = backend_url  or os.environ.get("BACKEND_MCP_URL", "http://localhost:8081")

    def _toolset(self, base_url: str, allow: list[str] | None) -> McpToolset:
        url = f"{base_url}/mcp"

        def header_provider(readonly_context) -> dict[str, str]:
            headers = {}
            token = _id_token_for(base_url)
            if token:
                headers["Authorization"] = f"Bearer {token}"

            # Propagate ADK user session context for backend tenant isolation
            if readonly_context and hasattr(readonly_context, "session") and readonly_context.session:
                user_id = getattr(readonly_context.session, "user_id", None)
                if user_id:
                    # HTTP headers should be robust against casing
                    headers["X-Gpp-User-Id"] = user_id

            return headers

        return McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=url,
                timeout=_MCP_TIMEOUT_S,
                sse_read_timeout=_MCP_SSE_READ_TIMEOUT_S,
            ),
            tool_filter=allow,
            header_provider=header_provider,
        )

    def get_anwender_toolset(self, allow=None):
        return self._toolset(self.anwender_url, allow)

    def get_backend_toolset(self, allow=None):
        return self._toolset(self.backend_url, allow)
