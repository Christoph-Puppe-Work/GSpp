"""Phase 2 — Component Mapping Agent (LlmAgent factory)."""

import os

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.prompts import load_prompt
from app.schemas import TailoringReport

_DEFAULT_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-pro-preview")

_ANWENDER_TOOLS = [
    "list_zielobjektkategorien",
    "controls_for_zielobjekt",
    "get_oscal_profile",
    "get_control",
    "list_groups",
    "get_group",
]
_BACKEND_TOOLS = [
    "get_oscal_model_raw",
    "get_ssp_inventory",
]


def get_mapper_agent(mcp: McpClientService | None = None) -> LlmAgent:
    """Return the Phase 2 (Component-Mapping) LlmAgent.

    Tools: anwender (GSpp catalogue / profile / controls) + backend
    (read-only OSCAL inspection). Output is written to
    `state["phase2_result"]`.
    """
    mcp = mcp or McpClientService()
    anwender = mcp.get_anwender_toolset(allow=_ANWENDER_TOOLS)
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase2_mapper")

    return LlmAgent(
        name="phase2_mapper",
        model=os.environ.get("PHASE2_MODEL", _DEFAULT_MODEL),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[anwender, backend],
        output_schema=TailoringReport,
        output_key="phase2_result",
        description=(
            "Phase 2 — aligns the user's Component Definition with the BSI "
            "profile, detects tailoring blockers and POA&M gaps."
        ),
    )
