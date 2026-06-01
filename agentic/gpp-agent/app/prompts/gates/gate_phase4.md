---
id: gates/gate_phase4
purpose: HITL gate after Phase 4 — Audit pre-check / audit assist
response_schema: cleared|blocked
---

# HITL — Phase 4 Audit-Gatekeeper gate

Phase 4 produced this gatekeeper verdict:

- **Sub-phase:** {phase}
- **Cleared for audit:** {cleared_for_audit}
- **Schema errors:** {schema_errors_count}
- **Audit-assist suggestions:** {findings_suggestion_count}

Summary: {summary}

This is the **only path** into Phase 5 (Remediation). The graph routes
deterministically: `cleared` → Phase 5; `blocked` → end of workflow.

Reply with `cleared` to authorise moving to Phase 5 (Remediation), or
`blocked` to refuse clearance.

> **Note.** A reply of `cleared` is honoured only if Phase 4 itself reported
> `cleared_for_audit = true`. The gate node enforces this rule — if the
> verdict was `false`, the answer is forced to `blocked` regardless of your
> input.
