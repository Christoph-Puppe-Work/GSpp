import os
from google.adk.tools.mcp_tool import MCPToolset

class McpClientService:
    def __init__(self, server_url: str | None = None):
        self.server_url = server_url or os.environ.get("MCP_SERVER_URL", "http://localhost:8080")

    def get_bsi_gpp_toolset(self, allow: list[str] | None = None) -> MCPToolset:
        # Note: In a real scenario, we'd need to handle connection params correctly for the transport
        # FastMCP often uses SSE/HTTP or stdio.
        # Assuming HTTP transport for now as hinted in the skill.
        connection_params = {
            "url": f"{self.server_url}/sse", # Common FastMCP endpoint
        }
        ts = MCPToolset(connection_params=connection_params)
        if allow is not None:
            ts.tool_filter = lambda t: t.name in set(allow)
        return ts
