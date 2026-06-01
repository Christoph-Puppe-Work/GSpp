# DESIGN_SPEC.md

## Overview
**gpp-agent** is an AI-supported, graph-based agent system that guides users
through the entire OSCAL process (Open Security Controls Assessment Language)
for **BSI Grundschutz++**. It is implemented as a five-phase, HITL-gated
workflow on the **ADK 2.0 Workflow API** (pre-GA / Beta). The graph
structurally enforces the planning.md gatekeeper rules — most notably that
Phase 5 (Remediation) is reachable from Phase 4 (Audit) **only** through the
`cleared` route on the Phase 4 HITL gate.

## Architecture & Choices

| Area              | Choice                                                                                  |
| ----------------- | ---------------------------------------------------------------------------------------- |
| Agent framework   | **ADK 2.0 Workflow API** (`google-adk>=2.0.0a1`) — pre-GA / Beta. APIs may change before GA. |
| Root agent        | `Workflow(name="gpp_agent", state_schema=WorkflowState, edges=...)` — see [`app/agents/orchestrator.py`](app/agents/orchestrator.py:1). |
| Resumability      | `ResumabilityConfig(is_resumable=True)` on the `App` — see [`app/agent.py`](app/agent.py:1). |
| Storage namespace | `App.name="app"` — must equal the agent directory name because `adk web` / `agents-cli playground` derive the runner `app_name` from the filesystem path; isolate from any leftover ADK 1.x sessions by renaming the agent directory or wiping dev sessions. |
| Deployment target | Vertex AI Agent Runtime (`agent_runtime`).                                              |
| CI/CD runner      | Cloud Build (`cloud_build`).                                                            |
| Session storage   | Agent Platform Sessions (managed automatically by Agent Runtime).                       |
| Models            | `gemini-3.1-pro-preview` (default, override per-phase via `PHASE{1..5}_MODEL` env vars). |

### Workflow graph (verbatim)

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

The graph contains **19 nodes** (`__START__` + classifier + classifier_router
+ five phase agents + twelve gate FunctionNodes). The shape of these nodes
and edges is pinned by the structural tests in
[`tests/integration/test_agent.py`](tests/integration/test_agent.py:1).

### Workflow routing contract

The classifier does not route by natural-language output alone. It uses the
`route_to_phase` tool, which must write the selected route through
`ToolContext.state` so ADK records a state delta. The tool skips summarization
after recording the route so control returns to the Workflow router instead of
giving the classifier another chance to call the routing tool in the same
invocation.

### Per-phase agents

| Phase | LlmAgent                          | Output schema          | MCP tool filter (anwender / backend)                                                                  |
| ----- | --------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------- |
| 1     | `phase1_governance`               | `GovernanceFindings`   | backend: `get_ssp_inventory`, `get_ssp_implementation`, `get_oscal_model_raw`, `list_oscal_models`    |
| 2     | `phase2_mapper`                   | `TailoringReport`      | anwender: `list_zielobjektkategorien`, `controls_for_zielobjekt`, `get_oscal_profile`, `get_control`, `list_groups`, `get_group`<br/>backend: `get_oscal_model_raw`, `get_ssp_inventory` |
| 3     | `phase3_implementation`           | `ImplementationReport` | backend: `get_ssp_implementation`, `get_oscal_model_raw`                                              |
| 4     | `phase4_gatekeeper`               | `GatekeeperVerdict`    | anwender: `verify_oscal_json`, `get_control`, `get_oscal_profile`<br/>backend: `create_oscal_model`, `update_oscal_model`, `get_oscal_model_raw`, `get_assessment_controls`, `get_assessment_subjects`, `get_resolved_profile_catalog` |
| 5     | `phase5_remediation`              | `RemediationPlan`      | backend: `get_assessment_findings`, `get_poam_items`, `update_oscal_model`, `create_oscal_model`      |

All phase agents run in `mode="single_turn"` so they return immediately to
the workflow graph after producing their structured output. Each agent's
output is also written to session state via `output_key="phaseN_result"` so
HITL gates and downstream phases can inspect it.

Tool filters are phase capability boundaries, not loop guards. They should
reflect the process requirements for each phase. Runtime tool loops must be
fixed by inspecting ADK events, FunctionResponses, state deltas, and MCP
auth/session propagation, not by removing required tools from a phase.

### State contract

`WorkflowState` (see [`app/schemas.py`](app/schemas.py:1)) is the
`state_schema` attached to the Workflow:

```python
class WorkflowState(BaseModel):
    current_phase:  Literal["govern","model","track","audit","remediate"] | None
    user_role:      str | None     # ISO, IT-Mgmt, Implementer, Auditor, ...
    iv_id:          str | None     # Informationsverbund identifier
    phase1_result:  GovernanceFindings   | None
    phase2_result:  TailoringReport      | None
    phase3_result:  ImplementationReport | None
    phase4_result:  GatekeeperVerdict    | None
    phase5_result:  RemediationPlan      | None
```

### Resumability

The Workflow is wrapped in
`App(..., resumability_config=ResumabilityConfig(is_resumable=True))`
([`app/agent.py`](app/agent.py:1)). Each completed graph node is checkpointed
so:

- HITL pauses (`RequestInput`) survive client disconnects, server restarts,
  and arbitrarily long human turn-around times.
- Tools may be re-executed at most once on resume — phase 5 explicitly
  de-duplicates POA&M creation by checking `get_poam_items` before
  `update_oscal_model` / `create_oscal_model`.

The workflow is designed for long-running SSP creation and review. Global
step caps are not a primary safety mechanism; HITL gates, resumability,
idempotent tool behavior, and explicit validation boundaries provide control.

### Human-In-The-Loop (HITL) — graph-enforced

Every phase ends in a HITL gate implemented as a `RequestInput` event. Phases
1, 2, 3 and 5 simply require a `continue|stop` acknowledgement and end the
invocation. **Phase 4 is special:** its HITL gate is split into two nodes —

1. `gate_phase4_request` yields `RequestInput(response_schema={cleared|blocked})`.
2. `gate_phase4_decision` reads the user's reply **and** the underlying
   `phase4_result.cleared_for_audit`. It forces `route="blocked"` whenever
   the verdict was not `cleared`, regardless of what the user typed. Only
   `route="cleared"` leads to Phase 5; this is the runtime half of the
   "Phase 4 is the only gate to Phase 5" invariant.

The structural half is enforced by the graph itself: the only edge into
`phase5_remediation` from anywhere downstream of Phase 4 is
`gate_phase4_decision --[cleared]--> phase5_remediation`. There is **no**
direct edge `phase4_gatekeeper → phase5_remediation`.

## Use cases

1. **Phase 1 — Governance:** Validate Segregation of Duties, flag high-impact
   assets that demand a BSI 200-3 overlay.
2. **Phase 2 — System Modelling:** Align Component Definitions with the BSI
   profile; raise a blocker on weakened tailoring (e.g. password length < 12).
3. **Phase 3 — Implementation Status:** Reject `alternative` without
   justification, `planned` without `date-expected`, MUSS `planned` without
   risk acceptance ⇒ "not ready for initial certification".
4. **Phase 4 — Audit Gatekeeper / Audit Assistant:** Run formal SSP pre-check
   (`verify_oscal_json` + profile referencing) and produce per-control
   `satisfied`/`not-satisfied` suggestions with observation text.
5. **Phase 5 — POA&M Remediation:** Convert `not-satisfied` findings to
   POA&M items hard-linked to the violated requirement and asset, with draft
   milestones for user validation.

## Tools required

- **MCP Server `GSpp_MCP` (anwender)** — BSI Grundschutz++ catalogue,
  profiles, controls, OSCAL validation.
- **MCP Server `GS_backend_MCP` (backend)** — Tenant-scoped OSCAL persistence
  (SSP / AP / AR / POA&M reads, mutations).
- **MCP session context** - backend MCP tools require an authenticated session
  user id in `{caller}::iv::{iv_id}` form. Local development fallbacks are
  diagnostic convenience only; they must not be treated as proof that tenant
  isolation is correctly propagated.
- **`verify_oscal_json`** — schema validation; called explicitly by Phase 4.
- **GCS-backed savepoints** — handled by the backend MCP, not by the agent.

## Constraints & safety rules

- **Strict data isolation** — different `iv_id` (tenants) must have isolated
  save directories in GCP Cloud Storage. Enforced by the backend MCP.
- **Local fallback IVs are not a tenant-isolation fix** - they may keep local
  development runs moving, but production correctness requires the MCP session
  context to carry the real IV.
- **Mandatory validation** — Phase 4 always calls `verify_oscal_json` before
  it can set `cleared_for_audit = true`.
- **Graph-enforced HITL** — see the "HITL — graph-enforced" subsection above.
- **No direct schema edits** — agents may not modify the OSCAL schemas
  themselves, only the artefacts they read/write.
- **No model changes without explicit user approval** — the project pins
  `gemini-3.1-pro-preview` for all phase agents.

## Pre-GA risks (ADK 2.0)

ADK 2.0 is pre-GA / Beta. Known risks:

- APIs (`Workflow`, `RequestInput`, `Event.route`) may change before GA.
- Workflow API is **incompatible with Live Streaming**.
- `ResumabilityConfig` is itself flagged `[EXPERIMENTAL]` at runtime.
- Vertex AI Agent Runtime support for ADK 2.0 alpha must be verified during
  the first dev deploy. If it rejects the alpha, fall back to the ADK 1.x
  plan in `todo.md` Appendix.

## Success criteria

1. The Workflow graph has the 19-node, 19-edge shape pinned by
   `tests/integration/test_agent.py`.
2. `gate_phase4_decision` forces `blocked` when
   `phase4_result.cleared_for_audit = false` (regression test:
   `test_gate_phase4_decision_forces_blocked_when_verdict_is_not_cleared`).
3. Each of the five phase prompts produces output that validates against its
   Pydantic `output_schema`.
4. The agent successfully pauses on `RequestInput` and resumes via
   `runner.run_async(invocation_id=...)`.
5. `agents-cli deploy` succeeds against dev Agent Runtime; production deploy
   only after explicit user confirmation per [`AGENTS.md`](AGENTS.md:1) Phase 5.

## Reference samples

- ADK 2.0 graph workflows — [adk.dev/workflows/](https://adk.dev/workflows/)
- HITL with `RequestInput` — [adk.dev/workflows/human-input/](https://adk.dev/workflows/human-input/)
- Resumability — [adk.dev/runtime/resume/](https://adk.dev/runtime/resume/)
