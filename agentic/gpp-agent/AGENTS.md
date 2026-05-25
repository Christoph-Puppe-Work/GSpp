# Coding Agent Guide

## Prerequisites

Install the CLI (one-time):
```bash
uv tool install google-agents-cli
```

---

## Development Phases

### Phase 1: Understand Requirements
Before writing any code, understand the project's requirements, constraints, and success criteria.

### Phase 2: Build and Implement
Implement agent logic in `app/`. Use `agents-cli playground` for interactive testing. Iterate based on user feedback.

### Phase 3: The Evaluation Loop (Main Iteration Phase)
Start with 1-2 eval cases, run `agents-cli eval run`, iterate. Expect 5-10+ iterations. See the **Evaluation Guide** for metrics, evalset schema, LLM-as-judge config, and common gotchas.

### Phase 4: Pre-Deployment Tests
Run `uv run pytest tests/unit tests/integration`. Fix issues until all tests pass.

### Phase 5: Deploy to Dev
**Requires explicit human approval.** Run `agents-cli deploy` only after user confirms. See the **Deployment Guide** for details.

### Phase 6: Production Deployment
Ask the user: Option A (simple single-project) or Option B (full CI/CD pipeline with `agents-cli infra cicd`).

## Development Commands

| Command | Purpose |
|---------|---------|
| `agents-cli playground` | Interactive local testing |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |
| `agents-cli eval run` | Run evaluation against evalsets |
| `agents-cli lint` | Check code quality |
| `agents-cli infra single-project` | Set up project infrastructure (Terraform) |
| `agents-cli deploy` | Deploy to dev |
| `agents-cli scaffold enhance` | Add deployment target or CI/CD to project |
| `agents-cli scaffold upgrade` | Upgrade project to latest version |

## Helper Scripts
For convenience, we use helper scripts located in the root `scripts/` directory:
- `scripts/run_local_gpp_agent_with_local_mcps.sh`: Use this script for local testing. It sets up the environment and runs `agents-cli playground` internally to start the agent locally with local MCP servers.
- `scripts/run_local_gpp_agent.sh`: Starts the agent locally reading from Terraform (for testing without local MCP overrides).
- `scripts/deploy_gpp_agent.sh`: Gathers infrastructure variables from Terraform and issues `agents-cli deploy`.

---

## ADK Workflow Lessons

- **Workflow LlmAgents should use `mode="single_turn"`** unless there is a proven reason otherwise. `chat` mode inside a Workflow graph can keep control inside the agent and prevent the next graph node or router from running cleanly.
- **State-changing tools must write through `ToolContext.state`**, not `tool_context.session.state`. ADK turns `ToolContext.state[...]` writes into tracked state deltas that downstream Workflow nodes can read reliably.
- **Routing/control-flow tools should set `tool_context.actions.skip_summarization = True`** after recording their state. Otherwise ADK may feed the FunctionResponse back into the LLM for summarization, and the model can call the same routing tool again before the Workflow router gets control.
- **Do not fix ADK/MCP tool loops by shrinking tool filters or capping `max_steps` first.** Capture the ADK event trace, tool call arguments, FunctionResponse content, state deltas, and MCP session/auth context before changing phase capabilities.
- **MCP tenant/session context is part of the runtime contract.** Backend MCP expects a session user id in `{caller}::iv::{iv_id}` form. Local fallback IVs are diagnostic/dev-only convenience, not proof that tenant isolation is correctly propagated.
- **`App.name` must match the agent directory name for local ADK runners.** For this project that means `App(name="app", ...)`; use storage/session cleanup or directory isolation instead of renaming `App.name`.

---

## Operational Guidelines for Coding Agents

- **Code preservation**: Only modify code directly targeted by the user's request. Preserve all surrounding code, config values (e.g., `model`), comments, and formatting.
- **NEVER change the model** unless explicitly asked.
- **Model 404 errors**: Fix `GOOGLE_CLOUD_LOCATION` (e.g., `global` instead of `europe-west3`), not the model name.
- **ADK tool imports**: Import the tool instance, not the module: `from google.adk.tools.load_web_page import load_web_page`
- **Run Python with `.venv`**: Always source `(GIT_ROOT)/agentic/.venv/bin/activate` because it is the one shared environment for all tools. Do not use `uv run` if it isolates dependencies away from the shared `.venv`.
- **Stop on repeated errors**: If the same error appears 3+ times, fix the root cause instead of retrying.
- **Terraform conflicts** (Error 409): Use `terraform import` instead of retrying creation.
