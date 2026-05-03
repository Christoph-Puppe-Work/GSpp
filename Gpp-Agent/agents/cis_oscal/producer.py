from google.adk.agents.llm_agent import LlmAgent
from tools.bsi_gpp_mcp import get_bsi_gpp_toolset

async def get_producer() -> LlmAgent:
    mcp_toolset = get_bsi_gpp_toolset()
    tools = await mcp_toolset.get_tools()

    return LlmAgent(
        name="cis_oscal_producer",
        model="gemini-2.0-flash",
        instruction="""You are a CIS to OSCAL Mapper.
        Your task is to take CIS benchmarks/recommendations and map them to BSI Grundschutz++ components.
        Use the MCP tools to lookup G++ controls.
        Produce a valid OSCAL 1.1.2 Component Definition.
        Store your result in the state under 'draft_artifact'.""",
        tools=tools
    )
