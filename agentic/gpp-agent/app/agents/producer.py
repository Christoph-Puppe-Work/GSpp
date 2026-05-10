import os
from google.adk.agents import Agent
from app.mcp_clients import McpClientService
from app.prompts import load_prompt

def get_producer() -> Agent:
    mcp_service = McpClientService()
    identity_prompt = load_prompt("identity")
    producer_prompt = load_prompt("ssp_generator/producer")
    
    # Anwender tools (BSI catalog and verify_oscal_json)
    anwender_tools = mcp_service.get_anwender_toolset(allow=None)
    
    # Backend tools (GCP State Manager)
    backend_tools = mcp_service.get_backend_toolset(allow=None)

    bsi_researcher = Agent(
        name="bsi_researcher",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        instruction=f"{identity_prompt}\n\nYou are a BSI security catalog specialist. Retrieve requirements and controls.",
        tools=[anwender_tools],
        description="Delegated to for querying BSI catalogs for relevant controls.",
    )

    oscal_writer = Agent(
        name="oscal_writer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        instruction=f"{identity_prompt}\n\n,{producer_prompt}",
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
            instruction=f"{identity_prompt}\n\nYou are a data analysis specialist. You write and execute python code\n            in a sandbox to parse uploaded asset inventories (e.g. CSVs) and return structured data.",
            description="Delegated to for extracting structured info from user uploads via code execution.",
        )
        sub_agents.append(data_parser)

    return Agent(
        name="ssp_producer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        sub_agents=sub_agents,
        instruction=f"{identity_prompt}\n\n{producer_prompt}",
        description="Main producer agent for generating SSP and interacting with catalogs.",
    )
