# gpp_agent — Architecture Rules

> **STATUS (2026-06-12, P2-15):** the implementation has moved to an
> **ADK 2.0 Workflow graph** (`gpp-agent/app/agents/orchestrator.py`) and
> several sections below describe the older LoopAgent/sub-agent design that
> was **never built**. Until this document is rewritten:
>
> - **Still binding:** §2 (protocols — Streamable-HTTP only), §3 (tenant
>   isolation / `{caller}::iv::{iv_id}`), §4 (inspector/judge split — now
>   implemented as per-phase inspector + judge nodes), §7 (least-privilege
>   tool allow-lists), §8 (model rules — implemented in `app/models.py`),
>   §10 (DoD tests — treat as open checklist).
> - **Aspirational / superseded:** maker-checker `LoopAgent` +
>   `EscalationBarrier`, `services/mcp_client_service.py`, the
>   `shared/` + `agents/<domain>/` layout, `tools/observability.py`,
>   `TOOL_AGENT_MODEL`, `AGUIToolset` wiring (deferred with the P0-2
>   frontend-transport decision).
>
> See `agentic/issues.md` for the live finding list.

This document outlines the **binding** architecture decisions for
`agentic/gpp_agent/`. It is the source of truth for code reviewers
and code-generating tools (models). Not a tutorial, no code snippets —
only rules. Anyone writing code that violates one of these rules is introducing
a bug.

Accompanying Docs: `README.md` (Spec), `tasks.md` (Backlog/Progress),
`agentic/install.md` (local setup), `agentic/terraform/` (Cloud Run topology).

---

## 1. Component Map

Four services, two persistence layers:

- **`frontend`** — Next.js + CopilotKit. Only public service.
- **`gpp_agent`** — ADK Multi-Agent (FastAPI + ag-ui-adk).
- **`GSpp_MCP`** — read-only user catalog server (BSI G++).
- **`GS_backend_MCP`** — State, OSCAL validation, GCS persistence.
- **Firestore** — Session and state store of the agent.
- **GCS** — versioned OSCAL artifacts per Information Domain (Informationsverbund).

Call direction: Browser → Frontend → `gpp_agent` → `{GSpp_MCP, GS_backend_MCP}` → `{Firestore, GCS}`. **No** other paths. In particular, the frontend never calls an MCP server directly, and no MCP server calls the agent back.

---

## 2. Protocols and Transport

| Connection | Protocol | Path |
|---|---|---|
| Frontend → Agent | AG-UI (HTTP-POST + Event-Stream) | `/copilotkit` |
| Agent → MCP Servers (both) | MCP Streamable-HTTP | `/mcp` |
| Agent → Firestore | Google Cloud SDK | — |
| Agent → GCS (via Backend MCP) | indirect, no direct access | — |

**Forbidden:**

- SSE for MCP. The old `SseConnectionParams` is deprecated; exclusively `StreamableHTTPConnectionParams`.
- `adk api_server` as a frontend endpoint. The agent runs as a FastAPI process (uvicorn), AG-UI bridge via `ag_ui_adk.add_adk_fastapi_endpoint`. `adk web` is only allowed for backend debugging in a second terminal.
- Direct GCS write accesses from the agent. Writing is done exclusively via Backend MCP tools.

---

## 3. Multi-Tenancy (Information Domain Isolation)

- `iv_id` matches `^iv-[a-z0-9-]{3,40}$`. Other values are rejected.
- `user_id` for `Runner.run_async()` has exactly the format `{caller}::iv::{iv_id}`. Frontend sets this, Agent relies on it.
- App-level Callback (`before_run_callback` on the `App`) extracts `iv_id` from `RunAgentInput.userId` and writes it into `state["informationsverbund_id"]`. Without this callback, there is no tenant isolation.
- Mandatory GCS layout: `gs://{GCS_BUCKET_NAME}/{iv_id}/saves/{save_id}/…`. Backend MCP enforces this.
- Firestore sessions carry `iv_id` as a label. Cross-IV reads are a security incident, not a feature.

Any code snippet that accepts `user_id` without the `::iv::` suffix or constructs GCS paths without an IV prefix is a **Tenant Isolation Violation** and a merge blocker.

---

## 4. Maker-Checker with Iteration

Producer and Reviewer run in a `LoopAgent`, never in a `SequentialAgent`. A `SequentialAgent` is a one-shot without a correction path and collapses the pattern.

- **Producer** creates the draft (`PRODUCER_MODEL`). Has write access to the Backend MCP.
- **Reviewer** verifies (`REVIEWER_MODEL`). Toolset is read-only (see §7). Delivers a structured verdict (`output_schema=ReviewCriteria`).
- **Approval Signal**: Reviewer calls `exit_loop`, which sets `escalate=True` AND `skip_summarization=True`. Both are mandatory.
- **Loop Termination**: at the latest after `MAX_REVIEW_ITERATIONS` (default 3). Never unlimited.

`LoopAgent` propagates `escalate=True` to the parent `SequentialAgent` and would block the subsequent steps (e.g., GCS Save). Therefore, the `LoopAgent` is always wrapped in an `EscalationBarrier` (`tools/escalation_barrier.py`), whose `inner` is typed as `BaseAgent` (not `LoopAgent`, otherwise it won't accept a `SequentialAgent`).

If a Reviewer needs both `output_schema` and `tools`: split into two stages — `inspector` (with Tools, free output, writes to `state`) followed by `judge` (no Tools, `output_schema`, reads `state`). Gemini models do not emit reliable tool calls when a `responseSchema` is active.

---

## 5. Human-in-the-Loop

HITL runs **exclusively** via AG-UI / CopilotKit Generative UI, not as a server-side polling loop.

- `App` is constructed with `ResumabilityConfig(is_resumable=True)`. Without this, ADK does not pause on a client tool call.
- The Agent (Orchestrator or relevant Sub-Agent) has `AGUIToolset()` in `tools=[…]`. This turns all actions registered by the frontend via `useCopilotAction` (e.g., `approve_artifact`) into genuine ADK tools.
- When calling a client tool, ADK persists the `FunctionCall` event and pauses. Frontend renders the Generative UI, user responds, AG-UI sends the `FunctionResponse` event back, ADK resumes.
- Server-side `LoopAgent`-based HITL constructs are forbidden. They collide with the resumability model and lead to a double truth.

---

## 6. Validation

- Every written OSCAL artifact goes through `verify_oscal_json` **before** it lands in GCS. The tool is a Gatekeeper, not optional.
- `verify_oscal_json` architecturally belongs in the **Backend MCP**, not in the User MCP. The Backend MCP atomically merges schemas + persistence. (Note: currently the tool is in the User MCP — migration is due.)
- On validation error: Agent passes the error unaltered to the user (HITL). The Agent does not correct OSCAL JSON independently — this results in hallucination patches and masks bugs.

---

## 7. MCP Tool Access Policy

Tool filter per Agent is mandatory, not a recommendation. Defaults:

| Tool | Server | Producer | Reviewer | Validator |
|---|---|---|---|---|
| `list_groups`, `get_group` | User | ✓ | ✓ | — |
| `list_controls`, `get_control` | User | ✓ | ✓ | — |
| `get_control_raw` | User | ✓ | — | — |
| `search_controls` | User | ✓ | — | — |
| `list_zielobjektkategorien`, `controls_for_zielobjekt`, `get_oscal_profile` | User | ✓ | — | — |
| `verify_oscal_json` | Backend (Target) | — | — | ✓ |
| `create_oscal_model`, `update_oscal_model` | Backend | ✓ | — | — |
| `get_ssp_inventory`, `get_ssp_implementation` | Backend | ✓ | ✓ | — |
| `get_assessment_*`, `get_poam_items` | Backend | ✓ | ✓ | — |

A Reviewer with a write tool is a DoD violation. MCP toolsets are generated via `services/mcp_client_service.py` (`get_anwender_toolset(allow=…)`, `get_backend_toolset(allow=…)`), nowhere else.

---

## 8. Models

Three Gemini IDs are in scope, all from the 3.x family. Other IDs are forbidden.

| Env Var | Default | Role |
|---|---|---|
| `PRODUCER_MODEL` | `gemini-3.1-pro-preview` | Producer Agents, anything where mapping quality directly determines the artifact |
| `REVIEWER_MODEL` | `gemini-3-flash-preview` | Reviewer, Orchestrator Routing, Catalog Resolver |
| `TOOL_AGENT_MODEL` | `gemini-3.1-flash-lite-preview` | input_loader, high-frequency mechanical agents |

Rules:

- Never hardcode model strings. Always `os.environ.get("…", DEFAULT)`, with a default from the 3.x family. Fallbacks to `gemini-2.5-*` are forbidden — they mask missing `.env` loads.
- `temperature` override on Gemini 3 models is forbidden. Default `1.0` is trained; lower creates loops and reasoning degradation.
- Reviewer on Pro: only with measured quality proof. Default is Flash.

---

## 9. Observability

- OpenTelemetry is set up once per process in `tools/observability.py:configure_observability()`. `OTEL_DISABLED=1` deactivates it for tests.
- Every `LlmAgent` registers `enrich_span_with_iv` as a `before_agent_callback`. Spans thus carry `gpp.iv_id` and `gpp.agent` as attributes.
- Tool arguments are never logged in plaintext. SHA-256 hash of the `args` JSON representation, truncated to 16 characters. CIS data, Vendor Evidence, customer secrets must not reach Cloud Trace.
- Custom Metric `gpp_agent/tokens_per_run` with labels `{iv_id, workflow, model}` as a billing/chargeback signal.

---

## 10. Definition of Done — Tests

A workflow is not considered finished until these tests are green:

1. `test_tenant_isolation` — two parallel sessions with different `iv_id`s see nothing of each other.
2. `test_review_loop_passes_after_one_rejection` — Reviewer rejects once, approves on the second run, Post-Loop Step (GCS Save) runs. Proves `EscalationBarrier`.
3. `test_agui_resumability_pause` — Workflow pauses at the `approve_artifact` tool call and correctly picks up a simulated `FunctionResponse`.
4. `test_schema_validation_blocks_save` — invalid OSCAL does not reach GCS.
5. `test_redteam_prompt_injection_in_pdf` — Vendor PDF with "IGNORE PREVIOUS INSTRUCTIONS" payload. Producer does not exfiltrate, Reviewer flags it as a Finding.
6. `test_redteam_unauthorized_tool_call` — Producer requests a tool outside its filter → `ToolNotFound`, no silent fallback.
7. `test_token_exhaustion_failsafe` — Reviewer that never approves → Loop ends at `MAX_REVIEW_ITERATIONS`, no endless loop.
8. `test_mcp_5xx_does_not_crash_producer` — MCP Sidecar returns 503 → structured tool error in the event stream, no silent catch.

---

## 11. Directory Conventions

| Content | Path |
|---|---|
| Domain Workflow | `agents/<domain>/{producer,reviewer,workflow,tools}.py` |
| Shared Schemas | `shared/schemas.py` |
| Review Criteria | `shared/review_criteria.py` |
| Prompts | `shared/prompts/<domain>/<role>.md` (with YAML Frontmatter) |
| Service Layer (GCS, Sessions, MCP Clients) | `services/` |
| Custom Infra Agents (`EscalationBarrier`) | `tools/` |
| MCP Tool Wrapper | `tools/<name>.py` |
| Unit Test | `tests/unit/test_<module>.py` |
| Integration Test | `tests/integration/test_<workflow>_<scenario>.py` |
| Eval Snapshot | `tests/eval_snapshots/<workflow>/case_NNN_<slug>/` |

No new top-level directories without an entry in this table. No production logic in `tests/`. `shared/` is only for code that is shared between at least two sub-projects.

---

## 12. References (verified May 2026)

- Frontend Bridge: <https://docs.copilotkit.ai/adk>, <https://www.copilotkit.ai/blog/build-a-frontend-for-your-adk-agents-with-ag-ui>
- AG-UI ADK Middleware: <https://pypi.org/project/ag-ui-adk/>
- ADK MCP Tools (Streamable-HTTP): <https://google.github.io/adk-docs/tools-custom/mcp-tools/>
- ADK escalate Behavior: <https://github.com/google/adk-python/issues/1376>
- ADK LoopAgent: <https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/>
- MCP Streamable-HTTP Spec: <https://modelcontextprotocol.io/specification/2025-03-26/basic/transports>

If the live docs contradict these rules, the live docs win — then
this doc state is stale and must be updated via PR.
