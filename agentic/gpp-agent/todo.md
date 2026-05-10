# Gpp-Agent Implementation Plan

This document outlines the steps to strictly implement the 5-phase BSI Grundschutz++ workflow (from `planning.md`) into the ADK `gpp-agent` architecture. The core foundation (MCP clients, basic LoopAgents) exists, but the precise roles, prompts, and tool wirings for the 5-step Gatekeeper logic are missing.

## Phase 1: Prompts Definition
Create dedicated markdown prompt files in `gpp-agent/app/prompts/` to encapsulate the exact system instructions defined in `planning.md`.
- [ ] Create `phase1_governance.md`: Instructs the Governance Validator to enforce Segregation of Duties (e.g. ISO != IT Management) and check for high `security-impact-level`.
- [ ] Create `phase2_mapper.md`: Instructs the Component Mapping Agent to validate component definitions against BSI profiles and monitor tailoring parameters (e.g. password length).
- [ ] Create `phase3_implementation.md`: Instructs the Implementation Validator. It must enforce that `alternative` status has justification and `planned` has a target date.
- [ ] Create `phase4_gatekeeper.md`: Instructs the Gatekeeper for Audit Readiness. Must mandate `verify_oscal_json` before AP generation and assist with Assessment Results (AR).
- [ ] Create `phase5_remediation.md`: Instructs the Remediation Agent to automatically extract `not-satisfied` findings to the POA&M.

## Phase 2: Agent Modules Creation
Implement the Python definitions for each phase in `gpp-agent/app/agents/`, replacing or refactoring the generic `producer.py`/`reviewer.py` setup. Equip them with the exact MCP tools they need.
- [ ] Implement `phase1_governance.py`: Define `get_governance_agent()`. Equip with `GS_backend_MCP` tools (like `get_ssp_inventory`).
- [ ] Implement `phase2_mapper.py`: Define `get_mapper_agent()`. Equip with `GSpp_MCP` tools (`get_oscal_profile`, `controls_for_zielobjekt`).
- [ ] Implement `phase3_implementation.py`: Define `get_implementation_agent()`. Equip with `GS_backend_MCP` tool `get_ssp_implementation`.
- [ ] Implement `phase4_gatekeeper.py`: Define `get_gatekeeper_agent()`. Equip with `verify_oscal_json` (from `GSpp_MCP`) and `create_oscal_model` (from `GS_backend_MCP`).
- [ ] Implement `phase5_remediation.py`: Define `get_remediation_agent()`. Equip with `get_assessment_findings` and `get_poam_items`.

## Phase 3: Orchestration & HITL Wiring
- [ ] Refactor `gpp-agent/app/agents/orchestrator.py` to import and register the 5 new agents (`phase1_governance`, `phase2_mapper`, etc.) instead of just the generic `ssp_generator_loop`.
- [ ] Update the `root_agent` instruction in `orchestrator.py` to clearly map user intents to the 5 distinct phases.
- [ ] Explicitly encode the Human-In-The-Loop (HITL) gates into the prompt of the orchestrator or sub-agents (e.g. "Do not proceed from Phase 3 to Phase 4 without explicitly asking the user to confirm the SSP is ready for audit").

## Phase 4: Testing & Verification
- [ ] Run `agents-cli playground` locally.
- [ ] Simulate Phase 1: Trigger a Segregation of Duties conflict.
- [ ] Simulate Phase 2: Trigger a Tailoring constraint violation.
- [ ] Simulate Phase 4: Trigger an OSCAL validation error using `verify_oscal_json` to prove the Gatekeeper works.
