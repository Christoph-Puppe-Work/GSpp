"""Phase 3 — Implementation Validator (LlmAgent factory)."""

import os

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.prompts import load_prompt
from app.schemas import ImplementationReport

_DEFAULT_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-pro-preview")

_BACKEND_TOOLS = [
    "get_ssp_implementation",
    "get_oscal_model_raw",
]


def get_implementation_agent(mcp: McpClientService | None = None) -> LlmAgent:
    """Return the Phase 3 (Implementation Status) LlmAgent.

    Tools: backend MCP only — the SSP `implemented-requirement` block and
    raw OSCAL access. Output is written to `state["phase3_result"]`.
    """
    mcp = mcp or McpClientService()
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase3_implementation")

    return LlmAgent(
        name="phase3_implementation",
        model=os.environ.get("PHASE3_MODEL", _DEFAULT_MODEL),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[backend],
        output_schema=ImplementationReport,
        output_key="phase3_result",
        description=(
            "Phase 3 — semantic validation of SSP implementation statuses; "
            "flags unjustified `alternative` and `planned`-without-date entries."
        ),
    )
