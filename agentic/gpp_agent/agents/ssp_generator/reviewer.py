import os
from google.adk.agents import LlmAgent
from shared.prompts import load_prompt
from shared.schemas import ReviewCriteria
from services.mcp_client_service import McpClientService

async def get_reviewer() -> LlmAgent:
    mcp_service = McpClientService()

    # Reviewer has read-only tools to verify content
    anwender_tools = mcp_service.get_anwender_toolset(allow=[
        "list_groups", "get_group", "list_controls", "get_control"
    ])

    # Reviewer also needs to check the state in the backend
    backend_tools = mcp_service.get_backend_toolset(allow=[
        "get_ssp_inventory", "get_ssp_implementation"
    ])

    tools = list(anwender_tools) + list(backend_tools)

    agent = LlmAgent(
        name="ssp_reviewer",
        model=os.environ.get("REVIEWER_MODEL", "gemini-3-flash-preview"),
        instructions=load_prompt("ssp_generator/reviewer"),
        tools=tools,
        response_format=ReviewCriteria,
    )

    return agent
