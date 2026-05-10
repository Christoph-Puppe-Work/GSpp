import os
from google.adk.agents import Agent
from app.prompts import load_prompt
from app.schemas import ReviewCriteria
from app.mcp_clients import McpClientService

def get_reviewer() -> Agent:
    mcp_service = McpClientService()
    identity_prompt = load_prompt("identity")
    reviewer_prompt = load_prompt("ssp_generator/reviewer")

    # Reviewer has read-only tools to verify content
    anwender_tools = mcp_service.get_anwender_toolset(allow=[
        "list_groups", "get_group", "list_controls", "get_control"
    ])

    # Reviewer also needs to check the state in the backend
    backend_tools = mcp_service.get_backend_toolset(allow=[
        "get_ssp_inventory", "get_ssp_implementation", "get_oscal_model_raw"
    ])

    agent = Agent(
        name="ssp_reviewer",
        model=os.environ.get("REVIEWER_MODEL", "gemini-2.5-flash"),
        instruction=f"{identity_prompt}\n\n{reviewer_prompt}",
        tools=[anwender_tools, backend_tools],
        output_schema=ReviewCriteria,
        output_key="review_feedback",
        description="Reviews the generated SSP using read-only MCP tools and provides structured feedback.",
    )

    return agent
