"""Pydantic schemas used as `output_schema` on phase LlmAgents and as
`state_schema` on the top-level Workflow.

These models implement the structural contract from `planning.md`.
Every phase agent emits exactly one of these structured payloads via its
`output_schema`, and the Workflow accumulates them into the WorkflowState.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

PhaseRoute = Literal["govern", "model", "track", "audit", "remediate"]


class ClassifierOutput(BaseModel):
    """Output of the classifier agent — picks exactly one phase route."""

    route: PhaseRoute = Field(
        description=(
            "Which phase the user wants to drive. "
            "govern=Phase 1 governance/SoD, model=Phase 2 component mapping, "
            "track=Phase 3 implementation status, audit=Phase 4 audit gatekeeping, "
            "remediate=Phase 5 POA&M remediation."
        )
    )
    rationale: str = Field(
        description="Short justification (one sentence) of why this route was chosen."
    )


# ---------------------------------------------------------------------------
# Phase 1 — Governance
# ---------------------------------------------------------------------------


class GovernanceFindings(BaseModel):
    """Phase 1 result — governance and segregation-of-duties validation."""

    sod_violations: list[str] = Field(
        default_factory=list,
        description=(
            "Free-text violations of Segregation of Duties found in `parties` "
            "(e.g. 'ISO and IT-Mgmt share UUID xyz')."
        ),
    )
    high_impact_assets: list[str] = Field(
        default_factory=list,
        description="UUIDs (or names) of assets whose `security-impact-level` is High.",
    )
    requires_overlay: bool = Field(
        description=(
            "True if any high-impact asset triggers the BSI 200-3 overlay-import demand."
        )
    )
    summary: str = Field(description="Short user-facing summary of governance findings.")


# ---------------------------------------------------------------------------
# Phase 2 — System Modelling / Component Mapping
# ---------------------------------------------------------------------------


class TailoringBlocker(BaseModel):
    """A single tailoring constraint violation (blocker)."""

    control_id: str = Field(description="OSCAL control identifier, e.g. 'BER.1.A2'.")
    parameter: str = Field(description="Parameter name (e.g. 'pwd_min_length').")
    actual: str = Field(description="Value the user set.")
    required: str = Field(description="Profile-mandated minimum / constraint.")
    explanation: str = Field(
        description="Why this weakening makes the system non-certifiable."
    )


class TailoringReport(BaseModel):
    """Phase 2 result — Component Definition vs. profile alignment."""

    blockers: list[TailoringBlocker] = Field(
        default_factory=list,
        description="Tailoring values that fall below profile constraints.",
    )
    gaps_for_poam: list[str] = Field(
        default_factory=list,
        description=(
            "Control IDs not covered by the chosen Component Definition; "
            "must become POA&M items."
        ),
    )
    summary: str = Field(description="Short user-facing summary.")


# ---------------------------------------------------------------------------
# Phase 3 — Implementation status tracking
# ---------------------------------------------------------------------------


class ImplementationReport(BaseModel):
    """Phase 3 result — semantic validation of implementation statuses."""

    unjustified_alternatives: list[str] = Field(
        default_factory=list,
        description=(
            "Control IDs marked `alternative` whose justification field is empty "
            "or insufficient."
        ),
    )
    planned_without_date: list[str] = Field(
        default_factory=list,
        description="Control IDs marked `planned` without a `date-expected`.",
    )
    not_certifiable: bool = Field(
        description=(
            "True if any MUSS requirement is `planned` without authorized "
            "residual-risk acceptance — meaning the SSP is NOT ready for "
            "initial certification."
        )
    )
    summary: str = Field(description="Short user-facing summary.")


# ---------------------------------------------------------------------------
# Phase 4 — Gatekeeper / Audit Assistant
# ---------------------------------------------------------------------------


class FindingSuggestion(BaseModel):
    """Phase 4 audit-assist suggestion for one control."""

    control_id: str = Field(description="OSCAL control identifier.")
    suggested_status: Literal["satisfied", "not-satisfied", "other"] = Field(
        description="Proposed assessment result status."
    )
    observation: str = Field(
        description="Concrete observation text justifying the suggested status."
    )


class GatekeeperVerdict(BaseModel):
    """Phase 4 result — formal pre-check + audit-assist suggestions."""

    phase: Literal["pre_check", "audit_assist"] = Field(
        description=(
            "pre_check = before the AP is created; audit_assist = the auditor "
            "is currently evaluating controls."
        )
    )
    cleared_for_audit: bool = Field(
        description=(
            "True ONLY if schema validation passes AND no MUSS requirement is "
            "'planned'/'partial' without authorised risk acceptance. "
            "This is the hard gate into Phase 5."
        )
    )
    schema_errors: list[str] = Field(
        default_factory=list,
        description="Output of `verify_oscal_json` — empty when SSP is schema-valid.",
    )
    findings_suggestion: list[FindingSuggestion] = Field(
        default_factory=list,
        description="Audit-assist suggestions (only populated when phase='audit_assist').",
    )
    summary: str = Field(description="Short user-facing summary.")


# ---------------------------------------------------------------------------
# Phase 5 — Remediation / POA&M
# ---------------------------------------------------------------------------


class PoamItem(BaseModel):
    """A single POA&M entry that the agent created."""

    poam_id: str = Field(description="Generated POA&M item UUID.")
    finding_uuid: str = Field(
        description="UUID of the originating Assessment Result finding."
    )
    requirement_uuid: str = Field(
        description="UUID of the violated security requirement / control."
    )
    asset_uuid: str = Field(description="UUID of the affected asset (Zielobjekt).")
    description: str = Field(description="Short description of the deficiency.")
    proposed_milestones: list[str] = Field(
        default_factory=list,
        description="Draft milestones the user is asked to validate.",
    )


class RemediationPlan(BaseModel):
    """Phase 5 result — POA&M generation."""

    created_poam_items: list[PoamItem] = Field(
        default_factory=list,
        description="POA&M entries the agent created from `not-satisfied` findings.",
    )
    pending_user_input: list[str] = Field(
        default_factory=list,
        description=(
            "Free-text questions the user must answer to validate "
            "responsibilities / deadlines."
        ),
    )
    summary: str = Field(description="Short user-facing summary.")


# ---------------------------------------------------------------------------
# Workflow-level state contract
# ---------------------------------------------------------------------------


class WorkflowState(BaseModel):
    """Top-level Workflow `state_schema` — accumulates results across phases.

    All `phaseN_result` fields are Optional because in any single invocation
    only one phase runs (the classifier picks exactly one route). The state is
    persisted across invocations when `ResumabilityConfig(is_resumable=True)`
    is set, so previous-phase results remain visible to later phases (e.g.
    Phase 5 can inspect Phase 4's verdict).
    """

    current_phase: Optional[PhaseRoute] = Field(
        default=None,
        description="The route picked by the classifier in the current invocation.",
    )
    classifier_route: Optional[ClassifierOutput] = Field(
        default=None,
        description="The raw structural output from the classifier agent.",
    )
    user_role: Optional[str] = Field(
        default=None,
        description=(
            "Self-declared role of the human user (CISO, ISO, IT-Mgmt, "
            "Implementer, Auditor, ...). Set by the agent during the first turn."
        ),
    )
    iv_id: Optional[str] = Field(
        default=None,
        description="Informationsverbund (system boundary) identifier under work.",
    )

    phase1_result: Optional[GovernanceFindings] = None
    phase2_result: Optional[TailoringReport] = None
    phase3_result: Optional[ImplementationReport] = None
    phase4_result: Optional[GatekeeperVerdict] = None
    phase5_result: Optional[RemediationPlan] = None
