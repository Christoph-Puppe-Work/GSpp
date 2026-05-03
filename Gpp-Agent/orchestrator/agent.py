import re
from typing import Optional
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import ToolContext

from agents.cis_oscal.workflow import get_workflow as get_cis_oscal_workflow
from agents.vendor_evidence.workflow import get_workflow as get_vendor_evidence_workflow
from agents.policy_generator.workflow import get_workflow as get_policy_generator_workflow

def set_informationsverbund(iv_id: str, tool_context: ToolContext) -> str:
    """
    Sets the Informationsverbund-ID for the current session.
    Validates the ID format: iv-[a-z0-9-]{3,40}
    """
    if not re.match(r"^iv-[a-z0-9-]{3,40}$", iv_id):
        return f"Error: Invalid IV-ID format. Must match iv-[a-z0-9-]{{3,40}}. Got: {iv_id}"

    tool_context.state["informationsverbund_id"] = iv_id
    # We also update the user_id in the session to encode the iv_id for services
    current_user_id = tool_context.user_id.split("::iv::")[0]
    return f"Informationsverbund set to {iv_id}"

async def root_agent() -> LlmAgent:
    return LlmAgent(
        name="root_orchestrator",
        model="gemini-2.0-flash",
        instruction="""You are the Root Orchestrator for Grundschutz++.
        Your first task is to ensure an 'informationsverbund_id' is set in the state.
        If it's not set, ask the user for it and use the 'set_informationsverbund' tool.
        Once set, delegate the user's request to the appropriate sub-agent:
        - cis_oscal_workflow: for CIS to OSCAL mapping
        - vendor_evidence_workflow: for extracting evidence from vendor docs
        - policy_generator_workflow: for generating security policies
        """,
        tools=[set_informationsverbund],
        sub_agents=[
            await get_cis_oscal_workflow(),
            await get_vendor_evidence_workflow(),
            await get_policy_generator_workflow()
        ]
    )
