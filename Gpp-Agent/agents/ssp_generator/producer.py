import os
from google.adk.agents import LlmAgent
from shared.prompts import load_prompt
from services.mcp_client_service import McpClientService

async def get_producer() -> LlmAgent:
    mcp_service = McpClientService()
    toolset = mcp_service.get_bsi_gpp_toolset(allow=[
        "list_groups", "get_group", "list_controls", "get_control",
        "get_control_raw", "search_controls", "list_zielobjektkategorien",
        "controls_for_zielobjekt", "get_oscal_profile"
    ])

    return LlmAgent(
        name="ssp_producer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        instructions=load_prompt("ssp_generator/producer"),
        tools=toolset,
    )
