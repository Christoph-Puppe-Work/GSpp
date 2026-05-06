import os
from google.adk.agents import LlmAgent
from shared.prompts import load_prompt
from shared.schemas import ReviewCriteria
from services.mcp_client_service import McpClientService
from tools.exit_loop import exit_loop

async def get_reviewer() -> LlmAgent:
    mcp_service = McpClientService()
    # Reviewer has read-only tools
    toolset = mcp_service.get_bsi_gpp_toolset(allow=[
        "list_groups", "get_group", "list_controls", "get_control"
    ])

    agent = LlmAgent(
        name="ssp_reviewer",
        model=os.environ.get("REVIEWER_MODEL", "gemini-3-flash-preview"),
        instructions=load_prompt("ssp_generator/reviewer"),
        tools=toolset,
        response_format=ReviewCriteria,
    )

    @agent.tool
    def approve_artifact(reason: str, tool_context) -> dict:
        """Call this to approve the artifact and exit the review loop."""
        return exit_loop(reason, tool_context)

    return agent
