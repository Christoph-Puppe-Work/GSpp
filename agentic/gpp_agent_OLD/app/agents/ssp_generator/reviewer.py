import os
from google.adk.agents import LlmAgent
from shared.prompts import load_prompt
from shared.schemas import ReviewCriteria
from services.mcp_client_service import McpClientService

def get_reviewer() -> LlmAgent:
    mcp_service = McpClientService()

    # Reviewer has read-only tools to verify content
    anwender_tools = mcp_service.get_anwender_toolset(allow=[
        "list_groups", "get_group", "list_controls", "get_control"
    ])

    # Reviewer also needs to check the state in the backend
    backend_tools = mcp_service.get_backend_toolset(allow=[
        "get_ssp_inventory", "get_ssp_implementation"
    ])

    agent = LlmAgent(
        name="ssp_reviewer",
        model=os.environ.get("REVIEWER_MODEL", "gemini-2.5-flash"),
        instruction=load_prompt("ssp_generator/reviewer"),
        tools=[anwender_tools, backend_tools],
        output_schema=ReviewCriteria,
    )

    return agent
