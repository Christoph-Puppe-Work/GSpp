"""Phase 1 — Governance Validator (LlmAgent factory)."""

import os

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.prompts import load_prompt
from app.schemas import GovernanceFindings

_DEFAULT_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-pro-preview")

# Strict tool filter — only the read-only OSCAL inspection tools needed to
# validate Segregation of Duties and detect high-impact assets.
_BACKEND_TOOLS = [
    "get_ssp_inventory",
    "get_ssp_implementation",
    "get_oscal_model_raw",
    "list_oscal_models",
]


def get_governance_agent(mcp: McpClientService | None = None) -> LlmAgent:
    """Return the Phase 1 (Governance) LlmAgent.

    Tools: backend MCP only (no anwender / GSpp catalogue calls in this
    phase). Output is written to `state["phase1_result"]`.
    """
    mcp = mcp or McpClientService()
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase1_governance")

    return LlmAgent(
        name="phase1_governance",
        model=os.environ.get("PHASE1_MODEL", _DEFAULT_MODEL),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[backend],
        output_schema=GovernanceFindings,
        output_key="phase1_result",
        description=(
            "Phase 1 — validates Segregation of Duties on `parties` and flags "
            "high-impact assets that demand a BSI 200-3 overlay."
        ),
    )
