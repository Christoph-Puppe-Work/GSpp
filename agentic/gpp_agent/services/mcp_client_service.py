import os
from google.adk.tools.mcp_tool import MCPToolset

class McpClientService:
    def __init__(
        self,
        anwender_url: str | None = None,
        backend_url: str | None = None
    ):
        self.anwender_url = anwender_url or os.environ.get("ANWENDER_MCP_URL", "http://localhost:8080")
        self.backend_url = backend_url or os.environ.get("BACKEND_MCP_URL", "http://localhost:8081")

    def get_anwender_toolset(self, allow: list[str] | None = None) -> MCPToolset:
        connection_params = {
            "url": f"{self.anwender_url}/sse",
        }
        ts = MCPToolset(connection_params=connection_params)
        if allow is not None:
            ts.tool_filter = lambda t: t.name in set(allow)
        return ts

    def get_backend_toolset(self, allow: list[str] | None = None) -> MCPToolset:
        connection_params = {
            "url": f"{self.backend_url}/sse",
        }
        ts = MCPToolset(connection_params=connection_params)
        if allow is not None:
            ts.tool_filter = lambda t: t.name in set(allow)
        return ts
