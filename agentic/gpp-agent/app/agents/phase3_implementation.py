"""Phase 3 — Implementation Inspector (LlmAgent factory).

Inspector half of the inspector/judge split (architecture.md §4): keeps the
MCP tools, writes free-text notes to ``state["phase3_notes"]``; the judge
converts them into ``ImplementationReport``.
"""

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.models import producer_model
from app.prompts import load_prompt

_BACKEND_TOOLS = [
    "get_ssp_implementation",
    "get_oscal_model_raw",
]


def get_implementation_agent(mcp: McpClientService | None = None) -> LlmAgent:
    """Return the Phase 3 (Implementation Status) inspector LlmAgent.

    Tools: backend MCP only — the SSP `implemented-requirement` block and
    raw OSCAL access. Notes are written to `state["phase3_notes"]`.
    """
    mcp = mcp or McpClientService()
    backend = mcp.get_backend_toolset(allow=_BACKEND_TOOLS)

    identity = load_prompt("identity")
    phase_prompt = load_prompt("phase3_implementation")

    return LlmAgent(
        name="phase3_implementation",
        model=producer_model(3),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{phase_prompt}",
        tools=[backend],
        output_key="phase3_notes",
        description=(
            "Phase 3 inspector — semantic validation of SSP implementation "
            "statuses; flags unjustified `alternative` and "
            "`planned`-without-date entries."
        ),
    )
