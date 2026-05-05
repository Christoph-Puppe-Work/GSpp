---
name: gpp-agent-coding
description: "Build, extend or debug the Gpp-Agent — the ADK-based multi-agent system for Grundschutz++ workflows that lives under Gpp-Agent/ in the GSpp monorepo. Use this skill whenever code changes touch any Python file under Gpp-Agent/ (orchestrator, agents, services, tools, shared, tests). Covers the dependency stack (parse pyproject.toml dynamically), the canonical Maker-Checker (Producer/Reviewer) pattern with HITL, the Informationsverbund multi-tenancy convention encoded in user_id, the GSpp_MCP toolset factory, native OpenTelemetry instrumentation, current Gemini model assignment per agent role, and the red-team/tenant-isolation test classes that are non-negotiable Definition-of-Done items. Read this BEFORE writing or modifying any Gpp-Agent code."
---

# Gpp-Agent — Coding Skill

A working manual for writing, extending and reviewing code in `Gpp-Agent/`, the
ADK-based multi-agent system that ports the One-Page-App workflows server-side
with peer-review quality control, Human-in-the-Loop (HITL) interventions, and per-Informationsverbund GCS persistence.

This skill is opinionated. It assumes the README under `Gpp-Agent/README.md` is
the spec and this document is the implementation manual. **Read the README first.**
Verzeichnisstruktur, Tenancy-Modell und DoD-Liste werden hier nicht wiederholt.

---

## When to use

- Any code change under `Gpp-Agent/`
- Adding a new domain workflow following the 4 phases (SSP-Generator, SSP-Ausfüllen, AP/AR, POA&M).
- Implementing Maker-Checker loops (Producer/Reviewer) and HITL pause logic.
- Diagnosing why a LoopAgent doesn't terminate or why the post-loop step never runs.
- Wiring a new MCP tool from `../GSpp_MCP` into the an agent.
- Fixing IV-namespacing or session-service issues.
- Adding observability hooks or red-team test cases.

Do **not** use this skill for changes outside `Gpp-Agent/` (use the appropriate
sibling README/skill), or for high-level architecture decisions.

---

## Dependencies & Framework

**Do not rely on hardcoded dates or static versions.** Always parse the repository's dependency manager (`pyproject.toml` or `requirements.txt`) to determine the current execution environment constraints. 

However, maintain strict adherence to these framework components and their architectural purpose:

| Package | Purpose in Architecture |
|---|---|
| `google-adk` | Recommended agent framework. Native OpenTelemetry agentic metrics must be utilized. |
| `google-cloud-storage` | GCS client; mandatory for IV namespacing and versioned GCP Savepoints. |
| `pydantic` | Mandatory for internal agent-to-agent output schemas and review criteria. |
| `mcp` | MCP client to connect to `../GSpp_MCP`. Matches Streamable-HTTP transport. |

Optional ADK extras you may see/need:
`google-adk[otel-gcp]` (Cloud Trace), `google-adk[eval]` (tests), `google-adk[a2a]` (cross-service).

---

## Model assignment

Three Gemini IDs are in scope. Do not invent others. Read these in code, never hardcode model strings.

| ID | Use for | Notes |
|---|---|---|
| `gemini-3.1-pro-preview` | Producer in workflows — anything where mapping or extraction quality directly determines artifact correctness | 1M context, 64k output, `thinking_level: high` default. Most expensive ($2/$12 per 1M tok). |
| `gemini-3-flash-preview` | Reviewer in all workflows, Orchestrator routing, catalog_resolver | "Pro-level intelligence at Flash speed". Cheaper, faster. Set `thinking_level: medium` for review tasks. |
| `gemini-3.1-flash-lite-preview` | input_loader, get_gcs_writer, HITL controllers, simple checker agents that just read state | Cheapest ($0.25/$1.50). Use for high-frequency / mechanical agents. |

**Don't:**
- Default everything to Pro "to be safe". A Reviewer on Pro is 4–10x more expensive than on Flash for marginal quality gain.
- Use `temperature` overrides on Gemini 3 models. Default `1.0` is what the family is trained for; lowering it causes loops and degraded reasoning.

**Configurable via env** (see `.env.example`):
```bash
ORCHESTRATOR_MODEL=gemini-3-flash-preview
PRODUCER_MODEL=gemini-3.1-pro-preview
REVIEWER_MODEL=gemini-3-flash-preview
TOOL_AGENT_MODEL=gemini-3.1-flash-lite-preview
```

---

## The Canonical Maker-Checker Pattern with HITL

Every workflow phase follows a strict automated Peer-Review, followed by a dynamically validated Human-in-the-Loop (HITL) phase. 

### 1. Producer
Generates the draft artifact (e.g., OSCAL JSON) using `PRODUCER_MODEL`.
- **Must** use strict Pydantic `output_schema` to ensure initial structural validity.
- Has access to broad MCP lookup tools.

### 2. Reviewer
Validates the Producer's draft against schemas and the MCP catalog.
- Uses `REVIEWER_MODEL`.
- **Must** use a structured `ReviewCriteria` schema to return its verdict.
- Has read-only MCP tools (tool filtering is mandatory).

### 3. Human-in-the-Loop (HITL) & Final Validation Loop
After the automated Reviewer approves, the workflow **must pause** and await user confirmation or manual edits. Because humans can introduce syntax or schema errors, any manual modification must be routed through the MCP server's `verify_oscal_json` tool before saving.

**The HITL Validation Rules:**
1. If the human edits the JSON, a Validator Agent must invoke the `verify_oscal_json` MCP tool.
2. If the tool reports errors, the agent **must not** attempt to fix the JSON itself. It must present the exact validation errors back to the human for correction.
3. Only when `verify_oscal_json` returns a clean pass does the loop terminate and proceed to the GCS Savepoint.
```python
# agents/<domain>/workflow.py
import os
from google.adk.agents import LoopAgent, SequentialAgent
from tools.escalation_barrier import EscalationBarrier
from .producer import get_producer
from .reviewer import get_reviewer
from .tools import get_input_loader, get_gcs_writer, get_hitl_controller, get_mcp_validator

async def get_cis_oscal_workflow() -> SequentialAgent:
    
    # Automated Maker-Checker
    review_loop = LoopAgent(
        name="review_loop",
        sub_agents=[await get_producer(), await get_reviewer()],
        max_iterations=int(os.environ.get("MAX_REVIEW_ITERATIONS", "3")),
    )
    
    # Human Modification & Deterministic Validation
    hitl_validation_loop = LoopAgent(
        name="hitl_validation_loop",
        sub_agents=[await get_hitl_controller(), await get_mcp_validator()],
        max_iterations=int(os.environ.get("MAX_HITL_ITERATIONS", "5")),
        # Validator agent uses `verify_oscal_json`. 
        # Sets escalate=True ONLY if validation passes.
    )

    return SequentialAgent(
        name="domain_workflow",
        sub_agents=[
            await get_input_loader(),
            EscalationBarrier(name="review_barrier", inner=review_loop),
            EscalationBarrier(name="hitl_barrier", inner=hitl_validation_loop),
            await get_gcs_writer(), # Safe to save; payload is verified
        ],
    )
```

---

## ADK gotchas you will hit (MANDATORY)

### 🔥 The `escalate` propagation trap (read this first)
When an agent inside a `LoopAgent` sets `tool_context.actions.escalate = True`, the signal terminates the loop. **It also propagates upward and halts the parent `SequentialAgent`.** This is documented behavior (google/adk-python#1376).

If you implement a `LoopAgent` inside a `SequentialAgent` without a wrapper, any step that follows the loop (like `get_gcs_writer`) is unreachable. 

**Canonical workaround — use `EscalationBarrier`:**
```python
# tools/escalation_barrier.py
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

class EscalationBarrier(BaseAgent):
    inner: LoopAgent

    def __init__(self, *, name: str, inner: LoopAgent, **kwargs):
        super().__init__(name=name, sub_agents=[inner], **kwargs)
        self.inner = inner

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        async for event in self.inner.run_async(ctx):
            # Strip escalate from events leaving this barrier so the parent
            # SequentialAgent continues with the next sub-agent.
            if event.actions and event.actions.escalate:
                event.actions.escalate = False
            yield event
```

### Reviewer must signal both `escalate` AND `skip_summarization`
```python
# tools/exit_loop.py
from google.adk.tools.tool_context import ToolContext

def exit_loop(reason: str, tool_context: ToolContext) -> dict:
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True   # avoids extra LLM call
    return {"status": "approved", "reason": reason}
```
Without `skip_summarization=True` the model fires an extra summarization call after the tool returns.

### Per-agent MCP tool filtering
Don't pass the full BSI G++ MCP toolset to every sub-agent. 

| Tool | Purpose | Primary User |
| --- | --- | --- |
| `list_groups` | Group hierarchy (IDs, titles, parent_id) | Producer / Reviewer |
| `get_group` | Get specific group metadata | Producer / Reviewer |
| `list_controls` | List all controls (IDs, titles, prose, guidance) | Producer / Reviewer |
| `get_control` | Get specific control details (slimmed down) | Producer / Reviewer |
| `get_control_raw` | Full OSCAL control JSON | Producer |
| `search_controls` | Keyword search using an in-memory index | Producer |
| `list_zielobjektkategorien` | Asset categories defined by the catalog | Producer |
| `controls_for_zielobjekt` | Controls applicable to an asset category | Producer |
| `get_oscal_profile` | Generate an OSCAL profile for a category | Producer |
| `verify_oscal_json` | **Final Gatekeeper:** Verifies JSON against `OSCAL_schemas/` | Validator (in HITL Loop) |
```python
from google.adk.tools.mcp_tool import MCPToolset

def get_bsi_gpp_toolset(*, allow: list[str] | None = None) -> MCPToolset:
    ts = MCPToolset(connection_params=_connection_params())
    if allow is not None:
        ts.tool_filter = lambda t: t.name in set(allow)
    return ts
```

### `mcp` client gracefully handles transport crashes
Producer code should let MCP errors (like 5xx) surface as tool errors — the framework retries and the model sees a structured error. Don't wrap MCP calls in `try: except Exception:` and swallow.

---

## Multi-Tenancy / IV-namespacing

- `user_id` passed to `Runner.run()` MUST be of form `{caller}::iv::{iv_id}`
- IV pattern: `^iv-[a-z0-9-]{3,40}$`
- `iv_id` is extracted by `_extract_iv_id()` and used as GCS key prefix: `gs://{GCS_BUCKET_NAME}/{iv_id}/saves/{save_id}/`
```python
# IMPORTANT: encode IV into user_id
user_id = f"{caller_principal}::iv::{informationsverbund_id}"
session = await session_service.create_session(
    app_name="grundschutz_pp_agents",
    user_id=user_id,
    state={"informationsverbund_id": informationsverbund_id},
)

async for event in runner.run_async(
    user_id=user_id,
    session_id=session.id,
    new_message=...,
):
    ...
```
Anything that bypasses `user_id`-encoding or the dedicated get_gcs_writer is a **tenant-isolation violation**.

---

## Prompts — `shared/prompts/{domain}/{role}.md`

Move prompts out of code. Loader:

```python
# shared/__init__.py
import re, yaml
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(prompt_id: str) -> str:
    path = _PROMPTS_DIR / f"{prompt_id}.md"
    text = path.read_text(encoding="utf-8")

    # Strip YAML frontmatter
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m: return text
    
    frontmatter = yaml.safe_load(m.group(1))
    if "output_schema" in frontmatter:
        _assert_schema_exists(frontmatter["output_schema"])
    return m.group(2)
```

---

## Observability — native OpenTelemetry

Configure once at startup:
```python
# tools/observability.py
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

def configure_observability() -> None:
    if os.environ.get("OTEL_DISABLED") == "1": return
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter(project_id=os.environ["GOOGLE_CLOUD_PROJECT"])))
    trace.set_tracer_provider(provider)
```

Enrich spans with our IV / session context via ADK callbacks:
```python
def enrich_span_with_iv(callback_context: CallbackContext) -> None:
    """before_agent_callback: tag the current span with iv_id for filtering."""
    iv_id = callback_context.state.get("informationsverbund_id", "unknown")
    span = trace.get_current_span()
    span.set_attribute("gpp.iv_id", iv_id)
    span.set_attribute("gpp.agent", callback_context.agent_name)
```
**Never log tool args in plaintext**. Log a SHA-256 of the args dict instead.

## Cost metric — `gpp_agent/tokens_per_run`
```python
def emit_token_metric(callback_context, llm_response):
    iv_id = callback_context.state.get("informationsverbund_id", "unknown")
    workflow = callback_context.state.get("active_workflow", "unknown")
    # write a TimeSeries with labels {iv_id, workflow, model}
```

---

## Testing patterns

### Integration tests — three flavors
1. **Mock-MCP integration**: Producer/Reviewer talk to an in-process fake MCP server. Loop runs end-to-end.
2. **Sidecar-MCP integration**: docker-compose with the real `../GSpp_MCP` running on a localhost port. Used for catalog-correctness tests.
3. **End-to-end live**: nightly only, against a `gs-pp-agent-test` bucket and a sandbox GCP project. Real Gemini calls happen here. Budget-cap it at $5/run.

### The mandatory tests (DoD)
Without these, do not merge to main:
1. `test_tenant_isolation`: Two parallel sessions with different IV-IDs must not see the other's GCS objects.
2. `test_review_loop_passes_after_one_rejection`: Validates the `EscalationBarrier` works AND the post-loop writer runs.
3. `test_hitl_interruption_and_validation`: Verifies the workflow pauses, waits for external input, successfully invokes `verify_oscal_json`, and loops back on JSON errors.
4. `test_schema_validation`: Proves malformed OSCAL JSON is rejected before GCS save.
5. `test_redteam_prompt_injection_in_pdf`: A vendor PDF with `IGNORE PREVIOUS INSTRUCTIONS...`. Producer must ignore, Reviewer must flag.
6. `test_redteam_unauthorized_tool_call`: Producer is asked to call a tool outside its filter. Tool-filter must refuse.
7. `test_token_exhaustion_failsafe`: Reviewer that never approves. Loop must terminate after `MAX_REVIEW_ITERATIONS`.
8. `test_mcp_5xx_does_not_crash_producer`: MCP sidecar returns 503. Producer surfaces structured error.

### Eval snapshots
Nightly job runs each case under `tests/eval_snapshots/{workflow}/`, diffs output against expected, alerts on divergence. Regenerate these if you change prompts.

---

## Common pitfalls — checklist
Before you open a PR, scan this list:
- [ ] Dependencies parsed dynamically, no hardcoded framework versions in code.
- [ ] No `LoopAgent` directly inside a `SequentialAgent` without an `EscalationBarrier`.
- [ ] `exit_loop` sets BOTH `escalate` AND `skip_summarization` to True.
- [ ] HITL loop implemented; `verify_oscal_json` used as final gatekeeper.
- [ ] No model strings hardcoded in agents — they come from env vars.
- [ ] No `try: except Exception:` around MCP tool calls.
- [ ] No prompts inline in python files.
- [ ] GCS paths never bypass `GcsStorageService` / IV-namespacing.
- [ ] `user_id` passed to `Runner` includes the `::iv::{iv_id}` suffix.
- [ ] Tool args never logged in plaintext. Hash them.
- [ ] Reviewer tool-filter is read-only.
- [ ] Every LlmAgent has the `enrich_span_with_iv` callback.
- [ ] All DoD tests pass for the modified workflow.

---

## Where to put new files

| What | Where |
|---|---|
| Domain workflow logic | `agents/<domain>/{producer.py, reviewer.py, workflow.py, tools.py}` |
| Shared schemas | `shared/schemas.py` |
| Review criteria class | `shared/review_criteria.py` |
| Prompts | `shared/prompts/<domain>/<role>.md` (with frontmatter) |
| MCP-tool wrapper | `tools/<name>.py` |
| Custom infra agent (EscalationBarrier) | `tools/<name>.py` |
| Service-layer code (GCS, sessions) | `services/` |
| Unit test | `tests/unit/test_<module>.py` |
| Integration test | `tests/integration/test_<workflow>_<scenario>.py` |
| Eval snapshot | `tests/eval_snapshots/<workflow>/case_NNN_<slug>/` |

## Useful ADK doc anchors
- Multi-agents: <https://google.github.io/adk-docs/agents/multi-agents/>
- LoopAgent: <https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/>
- Events / escalate: <https://google.github.io/adk-docs/events/>
- MCP integration: <https://google.github.io/adk-docs/tools/mcp-tools/>
- Custom agents: <https://google.github.io/adk-docs/agents/custom-agents/>