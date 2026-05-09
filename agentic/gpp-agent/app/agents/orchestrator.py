import os
from google.adk.agents import Agent
from app.agents.ssp_generator_workflow import get_ssp_generator_workflow

def get_orchestrator() -> Agent:
    ssp_generator_loop = get_ssp_generator_workflow()

    return Agent(
        name="gpp_agent",
        model=os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-pro-preview"),
        instruction="""You are the gpp_agent Orchestrator.
Your job is to route user requests to the appropriate sub-agent or workflow.
The system supports:
1. SSP-Generator (Modelling, Asset integration, Risk Analysis)
2. SSP-Filling (Implementation status)
3. Assessment Plan & Results (Audit)
4. POA&M-Generator (Remediation)

Identify the user intent and delegate to the correct sub-agent.
CRITICAL HITL: Before finalizing any major step or initiating a major state transition 
(like finishing the SSP modelling), you must pause and request explicit user confirmation.
""",
        sub_agents=[ssp_generator_loop],
        description="Main entrypoint agent that coordinates across sub-workflows."
    )
