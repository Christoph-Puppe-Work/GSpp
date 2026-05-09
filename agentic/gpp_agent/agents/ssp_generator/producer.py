import os
from google.adk.agents import LlmAgent
from services.mcp_client_service import McpClientService

def get_producer() -> LlmAgent:
    mcp_service = McpClientService()
    anwender_tools = mcp_service.get_anwender_toolset(allow=[...])
    backend_tools = mcp_service.get_backend_toolset(allow=[...])

    bsi_researcher = LlmAgent(
        name="bsi_researcher",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        instruction="You are a BSI security catalog specialist. Retrieve requirements and controls.",
        tools=[anwender_tools],
    )

    oscal_writer = LlmAgent(
        name="oscal_writer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        instruction="You are an OSCAL standard specialist. Update OSCAL JSON models securely.",
        tools=[backend_tools],
    )

    sub_agents = [bsi_researcher, oscal_writer]

    # data_parser nur wenn echter Sandbox-Resource konfiguriert ist
    sandbox_resource = os.environ.get("SANDBOX_RESOURCE_NAME")
    if sandbox_resource and not sandbox_resource.startswith("projects/local-dev"):
        from google.adk.code_executors import AgentEngineSandboxCodeExecutor
        data_parser = LlmAgent(
            name="data_parser",
            model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
            code_executor=AgentEngineSandboxCodeExecutor(sandbox_resource_name=sandbox_resource),
            instruction="""You are a data analysis specialist. You write and execute python code
            in a sandbox to parse uploaded asset inventories (e.g. CSVs) and return structured data.""",
        )
        sub_agents.append(data_parser)

    return LlmAgent(
        name="ssp_producer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        sub_agents=sub_agents,
        instruction="""You coordinate the SSP production process.
        1. Use data_parser to extract structured info from user uploads (if available).
        2. Use bsi_researcher to query BSI catalogs for relevant controls.
        3. Use oscal_writer to compile everything into the OSCAL SSP artifact.
        """,
    )