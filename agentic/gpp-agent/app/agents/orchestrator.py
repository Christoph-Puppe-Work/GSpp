"""ADK 2.0 Workflow graph for the BSI Grundschutz++ five-phase gatekeeper.

Architecture (see [`planning.md`](../../planning.md:1) and
[`todo.md`](../../todo.md:1)):

```
START
  └─ classifier (LlmAgent, output_schema=ClassifierOutput)
       └─ classify_router  (FunctionNode → Event.route)
            ├─ "govern"     → phase1_governance     → gate_phase1   (HITL)
            ├─ "model"      → phase2_mapper         → gate_phase2   (HITL)
            ├─ "track"      → phase3_implementation → gate_phase3   (HITL)
            ├─ "audit"      → phase4_gatekeeper     → gate_phase4_request (HITL)
            │                                         → gate_phase4_decision
            │                                              ├─ "cleared" → phase5_remediation → gate_phase5
            │                                              └─ "blocked" → gate_phase4_blocked (terminal)
            └─ "remediate"  → phase5_remediation    → gate_phase5   (HITL)
```

The graph guarantees that the only path **into** Phase 5 from Phase 4 is the
`cleared` route on `gate_phase4_decision`, and the decision node forces
`blocked` whenever the underlying `phase4_result.cleared_for_audit` is `False`.
"""

from typing import Any

from google.adk import Event, Workflow
from google.adk.events import RequestInput
from google.adk.agents.invocation_context import InvocationContext

from app.agents.classifier import get_classifier_agent
from app.agents.phase1_governance import get_governance_agent
from app.agents.phase2_mapper import get_mapper_agent
from app.agents.phase3_implementation import get_implementation_agent
from app.agents.phase4_gatekeeper import get_gatekeeper_agent
from app.agents.phase5_remediation import get_remediation_agent
from app.mcp_clients import McpClientService
from app.prompts import load_prompt
from app.schemas import (
    ClassifierOutput,
    GatekeeperVerdict,
    GovernanceFindings,
    ImplementationReport,
    RemediationPlan,
    TailoringReport,
    WorkflowState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _coerce_classifier(node_input: Any) -> ClassifierOutput:
    """Accept either a `ClassifierOutput`, a dict, or a JSON string."""
    if isinstance(node_input, ClassifierOutput):
        return node_input
    if isinstance(node_input, dict):
        return ClassifierOutput.model_validate(node_input)
    if isinstance(node_input, str):
        return ClassifierOutput.model_validate_json(node_input)
    raise ValueError(
        f"classify_router received unexpected node_input type: {type(node_input)!r}"
    )


def _coerce_verdict(state_value: Any) -> GatekeeperVerdict | None:
    """Read `phase4_result` from session state — may be a dict after rehydration."""
    if state_value is None:
        return None
    if isinstance(state_value, GatekeeperVerdict):
        return state_value
    if isinstance(state_value, dict):
        try:
            return GatekeeperVerdict.model_validate(state_value)
        except Exception:
            return None
    return None


def _render_gate_message(template_id: str, **fields: Any) -> str:
    """Load a gate prompt template and substitute simple `{key}` fields."""
    tpl = load_prompt(template_id)
    try:
        return tpl.format(**fields)
    except KeyError:
        # Fall back to the raw template if a placeholder is missing — better
        # than crashing the whole workflow.
        return tpl


# ---------------------------------------------------------------------------
# Classifier router
# ---------------------------------------------------------------------------


def classify_router(node_input: Any) -> Event:
    """Read the `ClassifierOutput` from the classifier agent and emit
    `Event(route=...)` so the next graph edge dispatches to the right phase
    agent. Also writes the chosen route into state for downstream gates.
    """
    decision = _coerce_classifier(node_input)
    return Event(
        route=decision.route,
        state={"current_phase": decision.route},
    )


# ---------------------------------------------------------------------------
# HITL gates — Phase 1, 2, 3, 5 follow the same simple pattern:
# Request a continue/stop acknowledgement, then end the invocation.
# ---------------------------------------------------------------------------


async def gate_phase1_request(ctx: InvocationContext) -> Any:
    """Phase 1 HITL gate — yields RequestInput summarising the findings."""
    raw = ctx.session.state.get("phase1_result") or {}
    findings = (
        raw if isinstance(raw, GovernanceFindings)
        else GovernanceFindings.model_validate(raw) if raw else None
    )
    if findings is None:
        message = "Phase 1 produced no findings (the SSP could not be read)."
    else:
        message = _render_gate_message(
            "gates/gate_phase1",
            sod_violations_count=len(findings.sod_violations),
            high_impact_assets_count=len(findings.high_impact_assets),
            requires_overlay=findings.requires_overlay,
            summary=findings.summary,
        )
    yield RequestInput(
        interrupt_id="gate_phase1",
        message=message,
        response_schema={"type": "string", "enum": ["continue", "stop"]},
    )


def gate_phase1_ack(node_input: Any) -> Event:
    """Acknowledge the user's response and end the invocation."""
    decision = str(node_input or "continue").strip().lower()
    return Event(message=f"Phase 1 acknowledged ({decision}).")


async def gate_phase2_request(ctx: InvocationContext) -> Any:
    raw = ctx.session.state.get("phase2_result") or {}
    findings = (
        raw if isinstance(raw, TailoringReport)
        else TailoringReport.model_validate(raw) if raw else None
    )
    if findings is None:
        message = "Phase 2 produced no tailoring report."
    else:
        message = _render_gate_message(
            "gates/gate_phase2",
            blockers_count=len(findings.blockers),
            gaps_count=len(findings.gaps_for_poam),
            summary=findings.summary,
        )
    yield RequestInput(
        interrupt_id="gate_phase2",
        message=message,
        response_schema={"type": "string", "enum": ["continue", "stop"]},
    )


def gate_phase2_ack(node_input: Any) -> Event:
    decision = str(node_input or "continue").strip().lower()
    return Event(message=f"Phase 2 acknowledged ({decision}).")


async def gate_phase3_request(ctx: InvocationContext) -> Any:
    raw = ctx.session.state.get("phase3_result") or {}
    findings = (
        raw if isinstance(raw, ImplementationReport)
        else ImplementationReport.model_validate(raw) if raw else None
    )
    if findings is None:
        message = "Phase 3 produced no implementation report."
    else:
        message = _render_gate_message(
            "gates/gate_phase3",
            unjustified_count=len(findings.unjustified_alternatives),
            planned_no_date_count=len(findings.planned_without_date),
            not_certifiable=findings.not_certifiable,
            summary=findings.summary,
        )
    yield RequestInput(
        interrupt_id="gate_phase3",
        message=message,
        response_schema={"type": "string", "enum": ["continue", "stop"]},
    )


def gate_phase3_ack(node_input: Any) -> Event:
    decision = str(node_input or "continue").strip().lower()
    return Event(message=f"Phase 3 acknowledged ({decision}).")


async def gate_phase5_request(ctx: InvocationContext) -> Any:
    raw = ctx.session.state.get("phase5_result") or {}
    findings = (
        raw if isinstance(raw, RemediationPlan)
        else RemediationPlan.model_validate(raw) if raw else None
    )
    if findings is None:
        message = "Phase 5 produced no remediation plan."
    else:
        message = _render_gate_message(
            "gates/gate_phase5",
            poam_items_count=len(findings.created_poam_items),
            pending_user_input_count=len(findings.pending_user_input),
            summary=findings.summary,
        )
    yield RequestInput(
        interrupt_id="gate_phase5",
        message=message,
        response_schema={"type": "string", "enum": ["continue", "stop"]},
    )


def gate_phase5_ack(node_input: Any) -> Event:
    decision = str(node_input or "continue").strip().lower()
    return Event(message=f"Phase 5 acknowledged ({decision}).")


# ---------------------------------------------------------------------------
# Phase 4 HITL gate — TWO nodes, because we need to route on cleared/blocked.
# ---------------------------------------------------------------------------


async def gate_phase4_request(ctx: InvocationContext) -> Any:
    """Yield the RequestInput for the audit-clearance decision."""
    raw = ctx.session.state.get("phase4_result") or {}
    verdict = _coerce_verdict(raw)
    if verdict is None:
        message = (
            "Phase 4 produced no verdict — refusing audit clearance by default."
        )
    else:
        message = _render_gate_message(
            "gates/gate_phase4",
            phase=verdict.phase,
            cleared_for_audit=verdict.cleared_for_audit,
            schema_errors_count=len(verdict.schema_errors),
            findings_suggestion_count=len(verdict.findings_suggestion),
            summary=verdict.summary,
        )
    yield RequestInput(
        interrupt_id="gate_phase4",
        message=message,
        response_schema={"type": "string", "enum": ["cleared", "blocked"]},
    )


async def gate_phase4_decision(ctx: InvocationContext, node_input: Any) -> Event:
    """Read the user's reply AND the underlying verdict; emit a routed Event.

    Hard rule: even if the user replies `cleared`, we force `blocked` whenever
    `phase4_result.cleared_for_audit` is `False`. The graph guarantees this is
    the only path into Phase 5.
    """
    raw = ctx.session.state.get("phase4_result") or {}
    verdict = _coerce_verdict(raw)

    user_decision = str(node_input or "blocked").strip().lower()
    if user_decision not in {"cleared", "blocked"}:
        user_decision = "blocked"

    if user_decision == "cleared" and (verdict is None or not verdict.cleared_for_audit):
        # Refuse to honour a `cleared` reply when the agent itself said no.
        user_decision = "blocked"

    return Event(
        route=user_decision,
        output=user_decision,
        state={"phase4_decision": user_decision},
        message=(
            f"Phase 4 gate decision: {user_decision}"
            + (
                ""
                if user_decision == "cleared"
                else " — Phase 5 (Remediation) will NOT run."
            )
        ),
    )


def gate_phase4_blocked(node_input: Any = None) -> Event:
    """Terminal node when the gate refuses audit clearance."""
    return Event(
        message=(
            "Audit clearance was refused. The workflow ended without entering "
            "Phase 5 (Remediation). Address the gatekeeper's findings and run "
            "Phase 4 again."
        )
    )


# ---------------------------------------------------------------------------
# Workflow factory
# ---------------------------------------------------------------------------


def get_workflow(mcp: McpClientService | None = None) -> Workflow:
    """Build the gpp-agent five-phase Workflow.

    Args:
        mcp: Optional pre-built MCP client service (useful for tests / local
             dev with explicit URLs). When None, `McpClientService()` reads the
             `ANWENDER_MCP_URL` and `BACKEND_MCP_URL` env vars.
    """
    mcp = mcp or McpClientService()

    classifier = get_classifier_agent()
    p1 = get_governance_agent(mcp)
    p2 = get_mapper_agent(mcp)
    p3 = get_implementation_agent(mcp)
    p4 = get_gatekeeper_agent(mcp)
    p5 = get_remediation_agent(mcp)

    edges = [
        # 1. Entry: classifier picks the route
        ("START", classifier, classify_router),

        # 2. Dispatch to one of five phase agents
        (
            classify_router,
            {
                "govern":    p1,
                "model":     p2,
                "track":     p3,
                "audit":     p4,
                "remediate": p5,
            },
        ),

        # 3. Phase 1 / 2 / 3 / 5 → simple HITL gate (request + ack), then end
        (p1, gate_phase1_request, gate_phase1_ack),
        (p2, gate_phase2_request, gate_phase2_ack),
        (p3, gate_phase3_request, gate_phase3_ack),

        # 4. Phase 4 → request → decision → conditional routing
        (p4, gate_phase4_request, gate_phase4_decision),
        (
            gate_phase4_decision,
            {
                "cleared": p5,                 # ONLY path into P5 from P4
                "blocked": gate_phase4_blocked,
            },
        ),

        # 5. Phase 5 → simple HITL gate, then end
        (p5, gate_phase5_request, gate_phase5_ack),
    ]

    return Workflow(
        name="gpp_agent",
        description=(
            "BSI Grundschutz++ five-phase gatekeeper workflow. The graph "
            "structurally enforces that Phase 5 (Remediation) is reachable "
            "from Phase 4 (Audit) only via the `cleared` HITL gate."
        ),
        state_schema=WorkflowState,
        edges=edges,
    )
