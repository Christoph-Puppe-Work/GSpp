"""Phase 4 — Audit Gatekeeper / Audit Assistant Inspector (LlmAgent factory).

Inspector half of the inspector/judge split (architecture.md §4): keeps the
MCP tools, writes free-text notes to ``state["phase4_notes"]``; the judge
converts them into ``GatekeeperVerdict``.
"""

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.models import producer_model
from app.prompts import load_prompt

_ANWENDER_TOOLS = [
    "verify_oscal_json",
    "get_control",
    "get_oscal_profile",
]
_BACKEND_TOOLS = [
    "create_oscal_model",
    "update_oscal_model",
    "get_oscal_model_raw",
    "get_assessment_controls",
    "get_assessment_subjects",
    "get_resolved_profile_catalog",
]


def get_gatekeeper_agent(mcp: McpClientService | None = None) -> LlmAgent:
    """Return the Phase 4 (Gatekeeper / Audit-Assist) inspector LlmAgent.

    Tools: anwender (`verify_oscal_json`, `get_control`, `get_oscal_profile`)
    + backend (assessment plan / results, raw OSCAL, profile-resolution).
    Notes are written to `state["phase4_notes"]`.

    The graph wiring guarantees that Phase 5 is reached **only** when the
    Phase 4 judge emits `cleared_for_audit = true` and the user's HITL
    response is `cleared`.
    """
    mcp = mcp or McpClientService()
    anwender = mcp.get_anwender_toolset(allow=_ANWENDER_TOOLS)
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase4_gatekeeper")

    return LlmAgent(
        name="phase4_gatekeeper",
        model=producer_model(4),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[anwender, backend],
        output_key="phase4_notes",
        description=(
            "Phase 4 inspector — formal SSP pre-check (Phase A) and "
            "audit-assist suggestions (Phase B). Sole gate into Phase 5."
        ),
    )
