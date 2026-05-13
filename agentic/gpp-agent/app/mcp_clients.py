import os
import google.auth
import google.auth.transport.requests
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams


def _id_token_for(audience_url: str) -> str | None:
    """Holt Identity-Token für einen Cloud-Run-Audience.
    Gibt None zurück bei localhost (kein Auth nötig) oder wenn ADC fehlt."""
    if audience_url.startswith("http://localhost") or audience_url.startswith("http://127."):
        return None
    try:
        from google.auth import compute_engine, default
        from google.oauth2 import id_token
        request = google.auth.transport.requests.Request()
        return id_token.fetch_id_token(request, audience_url)
    except Exception:
        return None


class McpClientService:
    def __init__(self, anwender_url: str | None = None, backend_url: str | None = None):
        self.anwender_url = anwender_url or os.environ["ANWENDER_MCP_URL"]
        self.backend_url  = backend_url  or os.environ["BACKEND_MCP_URL"]

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
            connection_params=StreamableHTTPConnectionParams(url=url),
            tool_filter=allow,
            header_provider=header_provider,
        )

    def get_anwender_toolset(self, allow=None):
        return self._toolset(self.anwender_url, allow)

    def get_backend_toolset(self, allow=None):
        return self._toolset(self.backend_url, allow)
