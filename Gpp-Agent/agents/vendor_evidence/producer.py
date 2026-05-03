from google.adk.agents.llm_agent import LlmAgent
from tools.bsi_gpp_mcp import get_bsi_gpp_toolset

async def get_producer() -> LlmAgent:
    mcp_toolset = get_bsi_gpp_toolset()
    tools = await mcp_toolset.get_tools()
    return LlmAgent(
        name="vendor_evidence_producer",
        model="gemini-2.0-flash",
        instruction="""Extract Evidence-Statements from vendor documents and map them to G++ requirements.
        Use MCP tools to lookup G++ requirements.
        Output should include evidence and mapping.""",
        tools=tools
    )
