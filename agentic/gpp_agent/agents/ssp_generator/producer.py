import os
from google.adk.agents import LlmAgent
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from services.mcp_client_service import McpClientService

async def get_producer() -> LlmAgent:
    mcp_service = McpClientService()

    # Pattern 2 & 3: Focused toolsets for specialists
    anwender_tools = mcp_service.get_anwender_toolset(allow=[
        "list_groups", "get_group", "list_controls", "get_control",
        "get_control_raw", "search_controls", "list_zielobjektkategorien",
        "controls_for_zielobjekt", "get_oscal_profile"
    ])

    backend_tools = mcp_service.get_backend_toolset(allow=[
        "create_oscal_model", "update_oscal_model", "get_ssp_inventory",
        "get_ssp_implementation", "get_assessment_subjects",
        "get_assessment_controls", "get_assessment_findings", "get_poam_items"
    ])

    bsi_researcher = LlmAgent(
        name="bsi_researcher",
        model=os.environ.get("PRODUCER_MODEL", "gemini-2.5-pro"),
        instruction="You are a BSI security catalog specialist. Retrieve requirements and controls.",
        tools=anwender_tools,
    )

    oscal_writer = LlmAgent(
        name="oscal_writer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-2.5-pro"),
        instruction="You are an OSCAL standard specialist. Update OSCAL JSON models securely.",
        tools=backend_tools,
    )

    # Pattern 5: Sandboxed Executor (replaces local read_uploaded_file tool)
    data_parser = LlmAgent(
        name="data_parser",
        model=os.environ.get("PRODUCER_MODEL", "gemini-2.5-pro"),
        code_executor=AgentEngineSandboxCodeExecutor(
            sandbox_resource_name=os.environ.get("SANDBOX_RESOURCE_NAME", "projects/local-dev/sandboxes/mock"),
        ),
        instruction="""You are a data analysis specialist. You write and execute python code
        in a sandbox to parse uploaded asset inventories (e.g. CSVs) and return structured data."""
    )

    # Coordinator
    coordinator = LlmAgent(
        name="ssp_producer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-2.5-pro"),
        sub_agents=[bsi_researcher, oscal_writer, data_parser],
        instruction="""You coordinate the SSP production process.
        1. Use data_parser to extract structured info from user uploads.
        2. Use bsi_researcher to query BSI catalogs for relevant controls.
        3. Use oscal_writer to compile everything into the OSCAL SSP artifact.
        """,
    )

    return coordinator
