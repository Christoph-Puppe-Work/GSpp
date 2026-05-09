# Gpp-Agent Implementation Plan

This document outlines the steps required to port the old `gpp_agent_OLD` workflow into the new ADK-based `gpp-agent` project, integrating the MCP servers and implementing the required Maker-Checker and HITL mechanisms.

## Phase 1: Preparation & Configuration
- [ ] Add `mcp` package to `gpp-agent/pyproject.toml` and lock dependencies.
- [ ] Migrate `gpp_agent_OLD/shared/prompts` to `gpp-agent/app/prompts` to retain LLM instructions.
- [ ] Migrate `gpp_agent_OLD/shared/schemas.py` to `gpp-agent/app/schemas.py`.

## Phase 2: MCP Tool Integration
- [ ] Create `gpp-agent/app/mcp_clients.py` module.
- [ ] Implement `get_anwender_toolset` to connect to `GSpp_MCP` (provides BSI catalog and `verify_oscal_json`).
- [ ] Implement `get_backend_toolset` to connect to `GS_backend_MCP` (provides GCP state management and OSCAL model mutations).
- [ ] Configure `StdioConnectionParams` vs `SseConnectionParams` based on environment variable flags.

## Phase 3: Sub-Agent Implementation
- [ ] Implement `gpp-agent/app/agents/producer.py`. Create `bsi_researcher` and `oscal_writer` sub-agents (or one combined `ssp_producer` agent). Equip them with the necessary MCP toolsets and the instruction to *always* use `verify_oscal_json` before writing to `GS_backend_MCP`.
- [ ] Implement `gpp-agent/app/agents/reviewer.py`. Create the `ssp_reviewer` agent. Equip it with read-only MCP tools to verify the backend state against BSI criteria.

## Phase 4: Workflow Orchestration & HITL
- [ ] Implement `gpp-agent/app/agents/ssp_generator_workflow.py`. Combine Producer and Reviewer into a `SequentialAgent` or `LoopAgent` to establish the Maker-Checker cycle.
- [ ] Enforce Human-In-The-Loop (HITL). Identify critical tool executions (e.g., `update_oscal_model` for finalization) and add `require_confirmation=True` or implement a dedicated confirmation tool/callback.
- [ ] Implement `gpp-agent/app/agents/orchestrator.py`. Define the `root_agent` that routes user intents (Modelling, SSP-Filling, Audit, POA&M) to the respective workflows.

## Phase 5: App Wiring
- [ ] Update `gpp-agent/app/agent.py` to remove the dummy agents (`get_weather`, etc.).
- [ ] Import and expose the `root_agent` from the orchestrator in `App(name="app", root_agent=root_agent)`.

## Phase 6: Testing & Validation
- [ ] Run `agents-cli playground` to test the prompt interactions.
- [ ] Manually verify that `verify_oscal_json` prevents schema violations and that GCP writes work correctly.
- [ ] Confirm HITL interrupts work properly in the workflow.