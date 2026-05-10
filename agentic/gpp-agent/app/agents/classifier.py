"""Phase classifier — picks one of govern|model|track|audit|remediate.

This is a tool-less LLM node sitting at the top of the workflow graph.
It runs in `single_turn` mode (workflow graph requirement) and writes its
decision to `state["classifier_route"]` via `output_key`.
"""

import os

from google.adk.agents import LlmAgent

from app.prompts import load_prompt
from app.schemas import ClassifierOutput

# All agents default to the same model as the legacy orchestrator. Override
# per-agent via env var if needed.
_DEFAULT_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-pro-preview")


def get_classifier_agent() -> LlmAgent:
    """Return the classifier LlmAgent.

    No tools — pure prompt + structured output. The router function in the
    Workflow graph reads `state["classifier_route"]` and emits an Event with
    the corresponding `route` value.
    """
    identity = load_prompt("identity")
    classifier_prompt = load_prompt("classifier")

    return LlmAgent(
        name="classifier",
        model=os.environ.get("CLASSIFIER_MODEL", _DEFAULT_MODEL),
        mode="task",
        instruction=f"{identity}\n\n---\n\n{classifier_prompt}\n\n",
        output_schema=ClassifierOutput,
        output_key="classifier_route",
        description=(
            "Reads the user's message and picks exactly one of the five "
            "Grundschutz++ workflow phases."
        ),
    )
