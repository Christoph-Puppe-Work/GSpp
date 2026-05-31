"""Phase 4 — Audit Gatekeeper / Audit Assistant (LlmAgent factory)."""

import os

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.prompts import load_prompt
from app.schemas import GatekeeperVerdict

_DEFAULT_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-pro-preview")

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
    """Return the Phase 4 (Gatekeeper / Audit-Assist) LlmAgent.

    Tools: anwender (`verify_oscal_json`, `get_control`, `get_oscal_profile`)
    + backend (assessment plan / results, raw OSCAL, profile-resolution).
    Output is written to `state["phase4_result"]`.

    The graph wiring guarantees that Phase 5 is reached **only** when this
    agent emits `cleared_for_audit = true` and the user's HITL response is
    `cleared`.
    """
    mcp = mcp or McpClientService()
    anwender = mcp.get_anwender_toolset(allow=_ANWENDER_TOOLS)
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase4_gatekeeper")

    return LlmAgent(
        name="phase4_gatekeeper",
        model=os.environ.get("PHASE4_MODEL", _DEFAULT_MODEL),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[anwender, backend],
        output_schema=GatekeeperVerdict,
        output_key="phase4_result",
        description=(
            "Phase 4 — formal SSP pre-check (Phase A) and audit-assist "
            "suggestions (Phase B). Sole gate into Phase 5."
        ),
    )
