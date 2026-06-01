"""Phase classifier — picks one of govern|model|track|audit|remediate.

This LLM node sits at the top of the workflow graph and writes its routing
decision into workflow state via the `route_to_phase` tool.
"""

import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

from app.prompts import load_prompt
from app.schemas import ClassifierOutput

# All agents default to the same model as the legacy orchestrator. Override
# per-agent via env var if needed.
_DEFAULT_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-pro-preview")


def route_to_phase(route: str, rationale: str, tool_context: ToolContext) -> str:
    """Use this tool when the user has clearly indicated they want to proceed with a specific phase: govern, model, track, audit, remediate.
    
    Args:
        route: The chosen phase (govern, model, track, audit, remediate).
        rationale: Why this phase was chosen.
    """
    tool_context.state["classifier_route"] = {"route": route, "rationale": rationale}
    tool_context.actions.skip_summarization = True
    return f"Routing decision made: {route}. The system will now transition to this phase."


def get_classifier_agent() -> LlmAgent:
    """Return the classifier LlmAgent.

    Single-turn workflow agent that talks to the user and uses the `route_to_phase`
    tool when ready. The router function in the Workflow graph reads
    `state["classifier_route"]` and emits an Event with the corresponding `route` value.
    """
    identity = load_prompt("identity")
    classifier_prompt = load_prompt("classifier")
    
    tool = FunctionTool(func=route_to_phase)

    return LlmAgent(
        name="classifier",
        model=os.environ.get("CLASSIFIER_MODEL", _DEFAULT_MODEL),
        mode="single_turn",
        instruction=f"{identity}\n\n---\n\n{classifier_prompt}\n\n",
        tools=[tool],
        description=(
            "Reads the user's message, talks to the user and picks exactly one of the five "
            "Grundschutz++ workflow phases."
        ),
    )
