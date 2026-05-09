import os
from google.adk.agents import Agent
from app.mcp_clients import McpClientService

def get_producer() -> Agent:
    mcp_service = McpClientService()
    
    # Anwender tools (BSI catalog and verify_oscal_json)
    anwender_tools = mcp_service.get_anwender_toolset(allow=None)
    
    # Backend tools (GCP State Manager)
    backend_tools = mcp_service.get_backend_toolset(allow=None)

    bsi_researcher = Agent(
        name="bsi_researcher",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        instruction="You are a BSI security catalog specialist. Retrieve requirements and controls.",
        tools=[anwender_tools],
        description="Delegated to for querying BSI catalogs for relevant controls.",
    )

    oscal_writer = Agent(
        name="oscal_writer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        instruction="""You are an OSCAL standard specialist. Update OSCAL JSON models securely.
        CRITICAL: Before writing any OSCAL models using the backend tools, you MUST validate your JSON payload using the `verify_oscal_json` tool from the Anwender tools.
        """,
        tools=[backend_tools, anwender_tools],
        description="Delegated to for compiling and writing the OSCAL SSP artifact.",
    )

    sub_agents = [bsi_researcher, oscal_writer]

    # data_parser nur wenn echter Sandbox-Resource konfiguriert ist
    sandbox_resource = os.environ.get("SANDBOX_RESOURCE_NAME")
    if sandbox_resource and not sandbox_resource.startswith("projects/local-dev"):
        from google.adk.code_executors import VertexAiCodeExecutor
        data_parser = Agent(
            name="data_parser",
            model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
            code_executor=VertexAiCodeExecutor(sandbox_resource_name=sandbox_resource),
            instruction="""You are a data analysis specialist. You write and execute python code
            in a sandbox to parse uploaded asset inventories (e.g. CSVs) and return structured data.""",
            description="Delegated to for extracting structured info from user uploads via code execution.",
        )
        sub_agents.append(data_parser)

    return Agent(
        name="ssp_producer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        sub_agents=sub_agents,
        instruction="""You coordinate the SSP production process.
        1. Use data_parser to extract structured info from user uploads (if available).
        2. Use bsi_researcher to query BSI catalogs for relevant controls.
        3. Use oscal_writer to compile everything into the OSCAL SSP artifact.
        """,
        description="Main producer agent for generating SSP and interacting with catalogs.",
    )
