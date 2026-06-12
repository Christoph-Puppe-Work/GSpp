"""Phase 2 — Component Mapping Inspector (LlmAgent factory).

Inspector half of the inspector/judge split (architecture.md §4): keeps the
MCP tools, writes free-text notes to ``state["phase2_notes"]``; the judge
converts them into ``TailoringReport``.
"""

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.models import producer_model
from app.prompts import load_prompt

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
    """Return the Phase 2 (Component-Mapping) inspector LlmAgent.

    Tools: anwender (GSpp catalogue / profile / controls) + backend
    (read-only OSCAL inspection). Notes are written to
    `state["phase2_notes"]`.
    """
    mcp = mcp or McpClientService()
    anwender = mcp.get_anwender_toolset(allow=_ANWENDER_TOOLS)
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase2_mapper")

    return LlmAgent(
        name="phase2_mapper",
        model=producer_model(2),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[anwender, backend],
        output_key="phase2_notes",
        description=(
            "Phase 2 inspector — aligns the user's Component Definition with "
            "the BSI profile, detects tailoring blockers and POA&M gaps."
        ),
    )
