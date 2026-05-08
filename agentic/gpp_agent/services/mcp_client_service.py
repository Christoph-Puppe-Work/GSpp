import os
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

class McpClientService:
    def __init__(
        self,
        anwender_url: str | None = None,
        backend_url: str | None = None
    ):
        self.anwender_url = anwender_url or os.environ.get("ANWENDER_MCP_URL", "http://localhost:8080")
        self.backend_url = backend_url or os.environ.get("BACKEND_MCP_URL", "http://localhost:8081")

    def get_anwender_toolset(self, allow: list[str] | None = None) -> McpToolset:
        return McpToolset(
            connection_params=SseConnectionParams(url=f"{self.anwender_url}/sse"),
            tool_filter=allow,
        )

    def get_backend_toolset(self, allow: list[str] | None = None) -> McpToolset:
        return McpToolset(
            connection_params=SseConnectionParams(url=f"{self.backend_url}/sse"),
            tool_filter=allow,
        )
