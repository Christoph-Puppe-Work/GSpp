"""Phase 5 — Remediation / POA&M agent (LlmAgent factory)."""

import os

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.prompts import load_prompt
from app.schemas import RemediationPlan

_DEFAULT_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-pro-preview")

_BACKEND_TOOLS = [
    "get_assessment_findings",
    "get_poam_items",
    "update_oscal_model",
    "create_oscal_model",
]


def get_remediation_agent(mcp: McpClientService | None = None) -> LlmAgent:
    """Return the Phase 5 (Remediation / POA&M) LlmAgent.

    Tools: backend MCP only — read findings, read existing POA&Ms, mutate
    OSCAL models. Output is written to `state["phase5_result"]`.

    Reachable from the graph in two ways:
      1. classifier → "remediate" → here (user explicitly asks for POA&M),
      2. classifier → "audit" → Phase 4 → gate(`cleared`) → here.
    """
    mcp = mcp or McpClientService()
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase5_remediation")

    return LlmAgent(
        name="phase5_remediation",
        model=os.environ.get("PHASE5_MODEL", _DEFAULT_MODEL),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[backend],
        output_schema=RemediationPlan,
        output_key="phase5_result",
        description=(
            "Phase 5 — auto-creates POA&M items from `not-satisfied` findings; "
            "drafts milestones; asks user to validate responsibilities."
        ),
    )
