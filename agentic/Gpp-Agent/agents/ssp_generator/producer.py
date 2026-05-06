import os
from google.adk.agents import LlmAgent
from shared.prompts import load_prompt
from services.mcp_client_service import McpClientService
from tools.temp_file_service import read_temp_file

async def get_producer() -> LlmAgent:
    mcp_service = McpClientService()

    # Anwenderkatalog Tools (Read-Only Info)
    anwender_tools = mcp_service.get_anwender_toolset(allow=[
        "list_groups", "get_group", "list_controls", "get_control",
        "get_control_raw", "search_controls", "list_zielobjektkategorien",
        "controls_for_zielobjekt", "get_oscal_profile"
    ])

    # Backend MCP Tools (Artifact Management)
    backend_tools = mcp_service.get_backend_toolset(allow=[
        "create_oscal_model", "update_oscal_model", "get_ssp_inventory",
        "get_ssp_implementation", "get_assessment_subjects",
        "get_assessment_controls", "get_assessment_findings", "get_poam_items"
    ])

    tools = list(anwender_tools) + list(backend_tools)

    agent = LlmAgent(
        name="ssp_producer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        instructions=load_prompt("ssp_generator/producer"),
        tools=tools,
    )

    # Add local temp file reader for handling uploads
    @agent.tool
    def read_uploaded_file(filepath: str) -> str:
        """Reads a temporary uploaded file (e.g., CSV, text) for parsing and deletes it immediately."""
        try:
            content = read_temp_file(filepath)
            return content
        finally:
            from tools.temp_file_service import delete_temp_file
            delete_temp_file(filepath)

    return agent
