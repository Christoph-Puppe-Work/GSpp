import os
from typing import Optional, List, Union, Any
from google.adk.tools.mcp_tool import (
    McpToolset,
    StdioConnectionParams,
    SseConnectionParams,
)
from mcp.client.stdio import StdioServerParameters

def get_bsi_gpp_toolset(tool_filter: Optional[Union[List[str], Any]] = None) -> McpToolset:
    """
    Factory for the BSI G++ MCP toolset. Reads mode from environment variables.
    """
    mode = os.environ.get("BSI_GPP_MCP_MODE", "stdio")

    if mode == "stdio":
        command = os.environ.get("BSI_GPP_MCP_COMMAND", "python")
        args = os.environ.get("BSI_GPP_MCP_ARGS", "-m bsi_gpp_mcp_server").split()
        return McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=command,
                    args=args,
                )
            ),
            tool_filter=tool_filter
        )
    elif mode == "sse":
        url = os.environ.get("BSI_GPP_MCP_URL")
        if not url:
            raise ValueError("BSI_GPP_MCP_URL is required for SSE mode")
        return McpToolset(
            connection_params=SseConnectionParams(
                url=url,
            ),
            tool_filter=tool_filter
        )
    else:
        raise ValueError(f"Unknown BSI_GPP_MCP_MODE: {mode}")
