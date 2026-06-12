"""Phase 1 — Governance Inspector (LlmAgent factory).

Inspector half of the inspector/judge split (architecture.md §4): this agent
keeps the MCP tools and writes free-text notes to ``state["phase1_notes"]``;
the schema-bound judge (`app.agents.judges`) converts them into
``GovernanceFindings``.
"""

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.models import producer_model
from app.prompts import load_prompt

# OSCAL inspection tools plus the write tools needed to bootstrap a
# schema-valid skeleton SSP when none exists yet (P0-4 — "lege ein SSP an"
# routes here).
_BACKEND_TOOLS = [
    "get_ssp_inventory",
    "get_ssp_implementation",
    "get_oscal_model_raw",
    "list_oscal_models",
    "create_oscal_model",
    "update_oscal_model",
]


def get_governance_agent(mcp: McpClientService | None = None) -> LlmAgent:
    """Return the Phase 1 (Governance) inspector LlmAgent.

    Tools: backend MCP only (no anwender / GSpp catalogue calls in this
    phase). Notes are written to `state["phase1_notes"]`.
    """
    mcp = mcp or McpClientService()
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase1_governance")

    return LlmAgent(
        name="phase1_governance",
        model=producer_model(1),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[backend],
        output_key="phase1_notes",
        description=(
            "Phase 1 inspector — validates Segregation of Duties on `parties`, "
            "flags high-impact assets that demand a BSI 200-3 overlay, and "
            "bootstraps a skeleton SSP when none exists."
        ),
    )
