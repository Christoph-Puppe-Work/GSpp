"""Phase 1 - Governance Validator (LlmAgent factory)."""

import os
from typing import Any

from google.adk.agents import LlmAgent

from app.mcp_clients import McpClientService
from app.prompts import load_prompt
from app.schemas import GovernanceFindings

_DEFAULT_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-pro-preview")
_PHASE1_TOOL_CALL_COUNT_KEY = "temp:phase1_backend_tool_calls"

# Strict tool filter: Phase 1 gets one raw SSP read. Alternative discovery
# tools made the model retry sideways after auth or tenant-context failures.
_BACKEND_TOOLS = ["get_oscal_model_raw"]


def _block_phase1_tool_retry(
    tool: Any,
    args: dict[str, Any],
    tool_context: Any,
) -> dict[str, str] | None:
    """Allow one backend read attempt, then return a synthetic tool failure.

    The prompt tells the model to stop after one failed read; this callback is
    the runtime guard that prevents another MCP call if the model tries anyway.
    """
    state = getattr(tool_context, "state", None)
    if state is None:
        return None

    try:
        tool_call_count = int(state.get(_PHASE1_TOOL_CALL_COUNT_KEY, 0) or 0)
    except (TypeError, ValueError):
        tool_call_count = 0

    if tool_call_count >= 1:
        return {
            "error": "phase1_tool_retry_blocked",
            "summary": (
                "Phase 1 already used its single backend read attempt. "
                "Return GovernanceFindings now with empty finding lists, "
                "requires_overlay=false, and a concise error summary."
            ),
        }

    state[_PHASE1_TOOL_CALL_COUNT_KEY] = tool_call_count + 1
    return None


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
            "Phase 1 - validates Segregation of Duties on `parties` and flags "
            "high-impact assets that demand a BSI 200-3 overlay."
        ),
        before_tool_callback=_block_phase1_tool_retry,
    )
