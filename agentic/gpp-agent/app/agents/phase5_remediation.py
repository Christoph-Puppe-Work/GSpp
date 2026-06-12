"""Phase 5 — Remediation / POA&M Inspector (LlmAgent factory).

Inspector half of the inspector/judge split (architecture.md §4): keeps the
MCP tools, writes free-text notes to ``state["phase5_notes"]``; the judge
converts them into ``RemediationPlan``.
"""

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.models import producer_model
from app.prompts import load_prompt

_BACKEND_TOOLS = [
    "get_assessment_findings",
    "get_poam_items",
    "update_oscal_model",
    "create_oscal_model",
]


def get_remediation_agent(mcp: McpClientService | None = None) -> LlmAgent:
    """Return the Phase 5 (Remediation / POA&M) inspector LlmAgent.

    Tools: backend MCP only — read findings, read existing POA&Ms, mutate
    OSCAL models. Notes are written to `state["phase5_notes"]`.

    Reachable from the graph in two ways:
      1. classifier → "remediate" → here (user explicitly asks for POA&M),
      2. classifier → "audit" → Phase 4 → judge → gate(`cleared`) → here.
    """
    mcp = mcp or McpClientService()
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase5_remediation")

    return LlmAgent(
        name="phase5_remediation",
        model=producer_model(5),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[backend],
        output_key="phase5_notes",
        description=(
            "Phase 5 inspector — auto-creates POA&M items from `not-satisfied` "
            "findings; drafts milestones; asks user to validate responsibilities."
        ),
    )
