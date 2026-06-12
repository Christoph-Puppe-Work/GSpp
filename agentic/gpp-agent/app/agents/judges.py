"""Schema-bound judge agents — the second half of the inspector/judge split.

architecture.md §4: Gemini models do not emit reliable tool calls while a
`responseSchema` is active, so each phase is split into

- an **inspector** (tools, free-text notes → ``state["phaseN_notes"]``) and
- a **judge** (no tools, ``output_schema``, → ``state["phaseN_result"]``).

The judge instruction reads the notes via ADK 2.0 optional state injection
(``{phaseN_notes?}``) and converts them into the phase's Pydantic schema.
"""

from google.adk.agents import LlmAgent
from pydantic import BaseModel

from app.models import judge_model
from app.prompts import load_prompt
from app.schemas import (
    GatekeeperVerdict,
    GovernanceFindings,
    ImplementationReport,
    RemediationPlan,
    TailoringReport,
)

_JUDGE_SPECS: dict[int, tuple[type[BaseModel], str]] = {
    1: (GovernanceFindings, "governance findings"),
    2: (TailoringReport, "tailoring report"),
    3: (ImplementationReport, "implementation report"),
    4: (GatekeeperVerdict, "gatekeeper verdict"),
    5: (RemediationPlan, "remediation plan"),
}


def get_judge_agent(phase: int) -> LlmAgent:
    """Return the schema-bound judge LlmAgent for the given phase (1–5).

    No tools. Reads ``state["phase{N}_notes"]`` via instruction injection and
    writes the validated schema object to ``state["phase{N}_result"]``.
    """
    schema, label = _JUDGE_SPECS[phase]

    return LlmAgent(
        name=f"phase{phase}_judge",
        model=judge_model(phase),
        mode="single_turn",
        instruction=load_prompt(f"judges/phase{phase}_judge"),
        output_schema=schema,
        output_key=f"phase{phase}_result",
        description=(
            f"Phase {phase} judge — converts the inspector's free-text notes "
            f"into a structured {label} ({schema.__name__})."
        ),
    )
