from google.adk.agents.llm_agent import LlmAgent
from tools.bsi_gpp_mcp import get_bsi_gpp_toolset

async def get_producer(domain: str) -> LlmAgent:
    mcp_toolset = get_bsi_gpp_toolset()
    tools = await mcp_toolset.get_tools()
    return LlmAgent(
        name=f"policy_producer_{domain}",
        model="gemini-2.0-flash",
        instruction=f"Generate a security policy for the domain: {domain} based on G++ requirements.",
        tools=tools
    )
