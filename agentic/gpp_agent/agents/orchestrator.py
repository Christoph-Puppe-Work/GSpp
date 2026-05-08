import os
from google.adk.agents import LlmAgent
from .ssp_generator.workflow import get_ssp_generator_workflow

def _extract_iv_id(user_id: str) -> str:
    # user_id pattern: {caller}::iv::{iv_id}
    parts = user_id.split("::iv::")
    if len(parts) == 2:
        return parts[1]
    return "unknown-iv"

async def get_orchestrator() -> LlmAgent:
    ssp_generator = await get_ssp_generator_workflow()

    return LlmAgent(
        name="orchestrator",
        model=os.environ.get("ORCHESTRATOR_MODEL", "gemini-3-flash-preview"),
        instructions="""You are the gpp_agent Orchestrator.
Your job is to route user requests to the appropriate sub-agent or workflow.
The system supports:
1. SSP-Generator (Modelling, Asset integration, Risk Analysis)
2. SSP-Filling (Implementation status)
3. Assessment Plan & Results (Audit)
4. POA&M-Generator (Remediation)

Identify the user intent and delegate to the correct sub-agent.
""",
        sub_agents=[ssp_generator],
    )
