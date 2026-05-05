---
name: gpp-agent-coding
description: "Build, extend or debug the Gpp-Agent — the ADK-based multi-agent system for Grundschutz++ workflows that lives under Gpp-Agent/ in the GSpp monorepo. Use this skill whenever code changes touch any Python file under Gpp-Agent/ (orchestrator, agents/cis_oscal, agents/vendor_evidence, services, tools, shared, tests). Covers the verified May-2026 dependency stack (google-adk 1.32.0, mcp 1.27.0, pydantic 2.13.3), the canonical Producer/Reviewer/exit_loop pattern with the LoopAgent-escalate workaround that the naive SequentialAgent layout silently breaks on, the Informationsverbund multi-tenancy convention encoded in user_id, the BSI G++ MCPToolset factory for stdio and Streamable-HTTP, native OpenTelemetry instrumentation via the otel-gcp extra, current Gemini 3.1 Pro / Gemini 3 Flash / Gemini 3.1 Flash-Lite model assignment per agent role, and the red-team and tenant-isolation test classes that are non-negotiable Definition-of-Done items. Read this BEFORE writing or modifying any Gpp-Agent code."
---

# Gpp-Agent — Coding Skill

A working manual for writing, extending and reviewing code in `Gpp-Agent/`, the
ADK-based multi-agent system that ports the One-Page-App workflows server-side
with peer-review quality control and per-Informationsverbund GCS persistence.

This skill is opinionated. It assumes the README under `Gpp-Agent/README.md` is
the spec and this document is the implementation manual. **Read the README first.**
Verzeichnisstruktur, Tenancy-Modell und DoD-Liste werden hier nicht wiederholt.

---

## When to use

- Any code change under `Gpp-Agent/`
- Adding a new domain workflow following the cis_oscal / vendor_evidence template
- Diagnosing why a LoopAgent doesn't terminate or why the post-loop step never runs
- Wiring a new MCP tool from `../GSpp_MCP` into the Producer
- Fixing IV-namespacing or session-service issues
- Adding observability hooks or red-team test cases
- Pinning or upgrading dependencies — read § Dependencies first

Do **not** use this skill for changes outside `Gpp-Agent/` (use the appropriate
sibling README/skill), or for high-level architecture decisions (those live in
the README and require Christoph's sign-off).

---

## Dependencies — verified May 2026

Stack is pinned. Do **not** loosen unless you also verify the ADK override
points listed in § ADK gotchas.

| Package | Version | Why pinned |
|---|---|---|
| `google-adk` | `==1.32.0` | latest stable on PyPI (May 1, 2026); native OpenTelemetry agentic metrics landed here |
| `google-cloud-storage` | `==3.10.1` | GCS client; ADK transitive but explicit pin keeps Dockerfile reproducible |
| `pydantic` | `==2.13.3` | output schemas + review criteria |
| `mcp` | `==1.27.0` | MCP client; matches Streamable-HTTP transport on `../GSpp_MCP` |
| `python-dotenv` | `==1.2.2` | local `.env` loading |
| Python | `>=3.10` | ADK requirement; Dockerfile uses 3.11-slim |

Optional ADK extras you may need:

```toml
google-adk[otel-gcp]==1.32.0     # if you instrument with Cloud Trace (recommended for prod)
google-adk[eval]==1.32.0         # for tests/eval_snapshots/ rubric eval
google-adk[a2a]==1.32.0          # only if you ever do agent-to-agent across services
```

Before any version bump:
1. Read [google/adk-python releases](https://github.com/google/adk-python/releases)
2. Grep for `_get_blob_name`, `_get_blob_prefix`, `escalate`, `MCPToolset`,
   `StdioServerParameters`, `SseServerParams` in the ADK source — those are
   our coupling points.
3. Run `pytest tests/unit/test_artifact_service.py tests/unit/test_session_service.py`.

---

## Model assignment — verified May 2026

Three Gemini IDs are in scope. Do not invent others.

| ID | Use for | Notes |
|---|---|---|
| `gemini-3.1-pro-preview` | Producer in CIS→OSCAL, Producer in Vendor Evidence — anything where mapping or extraction quality directly determines artifact correctness | 1M context, 64k output, `thinking_level: high` default. Most expensive ($2/$12 per 1M tok). |
| `gemini-3-flash-preview` | Reviewer in all workflows, Orchestrator routing, catalog_resolver | "Pro-level intelligence at Flash speed" per Google's April 2026 release. Cheaper, faster, free tier on the API. Set `thinking_level: medium` for review tasks. |
| `gemini-3.1-flash-lite-preview` | input_loader, artifact_writer, simple checker agents that just read state and call one tool | Cheapest ($0.25/$1.50). Use for high-frequency / mechanical agents. |

**Don't:**
- Use `gemini-3-pro-preview` — that was retired March 26, 2026.
- Default everything to Pro "to be safe". A Reviewer on Pro is 4–10x more
  expensive than on Flash for marginal quality gain — confirmed in the CLEAR
  cost-aware-evaluation literature and in our own sub-agent traces.
- Use `temperature` overrides on Gemini 3 models. Default `1.0` is what the
  family is trained for; lowering it causes loops and degraded reasoning.

**Configurable via env** (see `.env.example`):

```bash
ORCHESTRATOR_MODEL=gemini-3-flash-preview
PRODUCER_MODEL=gemini-3.1-pro-preview
REVIEWER_MODEL=gemini-3-flash-preview
TOOL_AGENT_MODEL=gemini-3.1-flash-lite-preview
```

Read these in code, never hardcode model strings.

```python
import os
PRODUCER_MODEL = os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview")
```

---

## ADK gotchas you will hit

### 🔥 The `escalate` propagation trap (read this first)

When an agent inside a `LoopAgent` sets `tool_context.actions.escalate = True`,
the signal terminates the loop. **It also propagates upward and halts the
parent `SequentialAgent`.** This is documented behavior — see
[google/adk-python#1376](https://github.com/google/adk-python/issues/1376).

The README's diagram shows:

```
SequentialAgent("cis_oscal_workflow")
 ├── input_loader
 ├── LoopAgent("review_loop", [producer, reviewer])
 └── artifact_writer       ← NEVER RUNS with naive implementation
```

If you implement that literally, the `artifact_writer` is unreachable. Same
for any sibling step after the loop. You will notice this in integration
tests as "the loop completes, but my GCS bucket is empty". Don't.

**Canonical workaround — use `EscalationBarrier`:**

```python
# tools/escalation_barrier.py
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event


class EscalationBarrier(BaseAgent):
    """
    Wraps a LoopAgent so escalate=True terminates the loop but does NOT
    propagate up to halt the parent SequentialAgent.

    Without this, any step that follows the LoopAgent in a SequentialAgent
    is unreachable. See https://github.com/google/adk-python/issues/1376.
    """

    inner: LoopAgent

    def __init__(self, *, name: str, inner: LoopAgent, **kwargs):
        super().__init__(name=name, sub_agents=[inner], **kwargs)
        self.inner = inner

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        async for event in self.inner.run_async(ctx):
            # Strip escalate from events leaving this barrier so the parent
            # SequentialAgent continues with the next sub-agent.
            if event.actions and event.actions.escalate:
                event.actions.escalate = False
            yield event
```

**Workflow assembly with the barrier:**

```python
review_loop = LoopAgent(
    name="cis_oscal_review_loop",
    sub_agents=[producer, reviewer],
    max_iterations=int(os.environ.get("MAX_REVIEW_ITERATIONS", "3")),
)

cis_oscal_workflow = SequentialAgent(
    name="cis_oscal_workflow",
    sub_agents=[
        input_loader,
        EscalationBarrier(name="cis_oscal_review_barrier", inner=review_loop),
        artifact_writer,
    ],
)
```

This is the canonical pattern for **every** domain workflow in this repo.
There is no exception. If you see a `LoopAgent` inside a `SequentialAgent`
without an `EscalationBarrier`, that is a bug.

### Reviewer must signal both `escalate` AND `skip_summarization`

The latest ADK Loop docs require both:

```python
# tools/exit_loop.py
from google.adk.tools.tool_context import ToolContext


def exit_loop(reason: str, tool_context: ToolContext) -> dict:
    """Signal that the reviewed artifact is approved and the loop can exit.

    Args:
        reason: short human-readable approval rationale, written to the
                review log for audit purposes.
    """
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True   # avoids extra LLM call
    return {"status": "approved", "reason": reason}
```

Without `skip_summarization=True` the model fires an extra summarization
call after the tool returns — wasted tokens, slower loop exit. The current
exit_loop in the repo lacks this; fix it.

### Per-agent MCP tool filtering

Don't pass the full BSI G++ MCP toolset to every sub-agent. Reviewer needs
read-only tools; Producer needs lookup tools; nobody needs the stub
`apply_profile` until it's implemented.

```python
from google.adk.tools.mcp_tool import MCPToolset


def get_bsi_gpp_toolset(*, allow: list[str] | None = None) -> MCPToolset:
    """
    Factory. `allow` filters tool names; None means all.

    Reviewer:  allow=["catalog_info", "get_control", "get_parameter",
                       "find_referencing_controls"]
    Producer:  allow=None   (all)
    """
    ts = MCPToolset(connection_params=_connection_params())
    if allow is not None:
        ts.tool_filter = lambda t: t.name in set(allow)
    return ts
```

Tool-filtering is the cheapest lever to reduce both cost and prompt-injection
surface. Use it.

### `mcp` client gracefully handles transport crashes — don't catch broadly

ADK 1.32.0 includes the `mcp: gracefully handle tool execution errors and
transport crashes` fix. Producer code should let MCP errors surface as
tool errors — the framework retries and the model sees a structured error.
Don't wrap MCP calls in `try: except Exception:` and swallow.

---

## The canonical Producer / Reviewer pattern

Every domain workflow follows the same template. Copy it, change names,
don't reinvent.

```python
# agents/<domain>/producer.py
import os
from google.adk.agents import LlmAgent
from gs_pp_shared import load_prompt          # see § Prompts
from gs_pp_shared.schemas import OscalComponentDefinition
from tools.bsi_gpp_mcp import get_bsi_gpp_toolset


async def get_producer() -> LlmAgent:
    mcp = get_bsi_gpp_toolset()                # full toolset for producer
    return LlmAgent(
        name="cis_oscal_producer",
        model=os.environ.get("PRODUCER_MODEL", "gemini-3.1-pro-preview"),
        instruction=load_prompt("cis_oscal/producer"),
        tools=await mcp.get_tools(),
        output_schema=OscalComponentDefinition,   # Pydantic structured output
        output_key="draft_artifact",              # writes to state["draft_artifact"]
    )
```

```python
# agents/<domain>/reviewer.py
import os
from google.adk.agents import LlmAgent
from gs_pp_shared import load_prompt
from gs_pp_shared.review_criteria import CisOscalReviewCriteria
from tools.bsi_gpp_mcp import get_bsi_gpp_toolset
from tools.exit_loop import exit_loop


REVIEWER_READ_ONLY_MCP_TOOLS = [
    "catalog_info", "get_control", "get_parameter",
    "find_referencing_controls", "list_groups", "list_controls",
]


async def get_reviewer() -> LlmAgent:
    mcp = get_bsi_gpp_toolset(allow=REVIEWER_READ_ONLY_MCP_TOOLS)
    return LlmAgent(
        name="cis_oscal_reviewer",
        model=os.environ.get("REVIEWER_MODEL", "gemini-3-flash-preview"),
        instruction=load_prompt("cis_oscal/reviewer"),
        tools=[*await mcp.get_tools(), exit_loop],
        output_schema=CisOscalReviewCriteria,
        output_key="review_feedback",
    )
```

```python
# agents/<domain>/workflow.py
import os
from google.adk.agents import LoopAgent, SequentialAgent
from tools.escalation_barrier import EscalationBarrier
from .producer import get_producer
from .reviewer import get_reviewer
from .tools import get_input_loader, get_artifact_writer


async def get_cis_oscal_workflow() -> SequentialAgent:
    review_loop = LoopAgent(
        name="cis_oscal_review_loop",
        sub_agents=[await get_producer(), await get_reviewer()],
        max_iterations=int(os.environ.get("MAX_REVIEW_ITERATIONS", "3")),
    )
    return SequentialAgent(
        name="cis_oscal_workflow",
        sub_agents=[
            await get_input_loader(),
            EscalationBarrier(
                name="cis_oscal_review_barrier",
                inner=review_loop,
            ),
            await get_artifact_writer(),
        ],
    )
```

### Why structured output, not free text

`output_schema=OscalComponentDefinition` makes the Producer return Pydantic-validated
JSON. Two payoffs:
1. The Reviewer reads typed state, not strings. Saves tokens and prevents
   "is this approved?" / "I think so" hallucinations.
2. The Reviewer's own approval is also typed (`CisOscalReviewCriteria`),
   which is what the Pydantic-checklist trick from the README's § 7 buys you.

Both schemas live in `shared/schemas.py` and `shared/review_criteria.py`.

---

## Multi-Tenancy / IV-namespacing

Already implemented in `services/artifact_service.py` and
`services/session_service.py`. **Don't reimplement.** Just know:

- `user_id` passed to `Runner.run()` MUST be of form `{caller}::iv::{iv_id}`
- IV pattern: `^iv-[a-z0-9-]{3,40}$`
- `iv_id` is extracted by `_extract_iv_id()` and used as GCS key prefix
- The `default-iv` fallback is a TEST-ONLY escape hatch — your tests must
  never rely on it, and it must be removed before prod (see DoD in README)

When you start a session from the orchestrator:

```python
from google.adk.runners import Runner
from services.artifact_service import InformationsverbundGcsArtifactService
from services.session_service import InformationsverbundGcsSessionService

artifact_service = InformationsverbundGcsArtifactService(
    bucket_name=os.environ["GCS_BUCKET_NAME"],
)
session_service = InformationsverbundGcsSessionService(
    bucket_name=os.environ["GCS_BUCKET_NAME"],
)

runner = Runner(
    agent=root_orchestrator,
    app_name="grundschutz_pp_agents",
    artifact_service=artifact_service,
    session_service=session_service,
)

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

Anything that bypasses `user_id`-encoding (e.g. calling
`artifact_service.save_artifact(...)` directly with a hardcoded user_id) is a
**tenant-isolation violation** and will fail the red-team tests.

---

## Prompts — `shared/prompts/{domain}/{role}.md`

The README's DoD says move prompts out of code. Do that. Loader:

```python
# shared/__init__.py
from pathlib import Path
import re
import yaml

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(prompt_id: str) -> str:
    """
    Load a prompt by id like 'cis_oscal/producer'. Strips YAML frontmatter
    and returns the body. Frontmatter is read for validation but not
    returned to the LLM.
    """
    path = _PROMPTS_DIR / f"{prompt_id}.md"
    text = path.read_text(encoding="utf-8")

    # Strip YAML frontmatter
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m:
        return text
    frontmatter = yaml.safe_load(m.group(1))
    body = m.group(2)

    # Validate referenced output_schema actually exists
    if "output_schema" in frontmatter:
        _assert_schema_exists(frontmatter["output_schema"])
    return body
```

Frontmatter convention:

```markdown
---
id: cis_oscal/producer
version: 1.0
model_hint: gemini-3.1-pro-preview
output_schema: OscalComponentDefinition
---

You are a security architect specialized in mapping CIS Benchmarks to OSCAL...
```

When you change a prompt, bump `version` in frontmatter and update the
corresponding `tests/eval_snapshots/{workflow}/` set in the same PR.

---

## Observability — native OpenTelemetry (ADK 1.32.0+)

ADK 1.32.0 has **native OpenTelemetry agentic metrics**. You don't need
manual span creation. Configure once at startup:

```python
# tools/observability.py
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter


def configure_observability() -> None:
    """Call once at process startup, before any agent runs."""
    if os.environ.get("OTEL_DISABLED") == "1":
        return  # tests can disable

    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(
            CloudTraceSpanExporter(
                project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
            )
        )
    )
    trace.set_tracer_provider(provider)
```

Then enrich spans with our IV / session context via ADK callbacks:

```python
from google.adk.agents.callback_context import CallbackContext
from opentelemetry import trace


def enrich_span_with_iv(callback_context: CallbackContext) -> None:
    """before_agent_callback: tag the current span with iv_id for filtering."""
    iv_id = callback_context.state.get("informationsverbund_id", "unknown")
    span = trace.get_current_span()
    span.set_attribute("gpp.iv_id", iv_id)
    span.set_attribute("gpp.agent", callback_context.agent_name)
```

Attach `enrich_span_with_iv` as `before_agent_callback` on every LlmAgent
in the system. This gives Cloud Trace per-IV filtering for free.

**Never log tool args in plaintext** — they may contain CIS data, vendor
evidence, customer secrets. Log a SHA-256 of the args dict instead:

```python
import hashlib, json
args_hash = hashlib.sha256(
    json.dumps(args, sort_keys=True).encode()
).hexdigest()[:16]
```

The README's § 11.5 spans table is the contract.

---

## Cost metric — `gpp_agent/tokens_per_run`

Aggregate token usage per session and emit a Cloud Monitoring custom metric.
ADK fires `after_agent_callback` with a `LlmResponse` that has token counts.

```python
from google.cloud import monitoring_v3


def emit_token_metric(callback_context, llm_response):
    iv_id = callback_context.state.get("informationsverbund_id", "unknown")
    workflow = callback_context.state.get("active_workflow", "unknown")
    # ... write a TimeSeries with labels {iv_id, workflow, model}
    # See https://cloud.google.com/monitoring/custom-metrics/creating-metrics
```

This is also the IV-billing signal if Christoph ever wants to chargeback.

---

## Testing patterns

### Unit tests

`pytest` against modules in isolation. No GCS, no network. Mock
`MCPToolset.get_tools()` to return a fake tool list with deterministic
responses. Pydantic schemas are testable with synthetic dicts.

### Integration tests — three flavors

1. **Mock-MCP integration**: Producer/Reviewer talk to an in-process fake
   MCP server. Loop runs end-to-end. No real Vertex calls (use ADK's
   `BaseLlmConnection` mocking or `pytest-vcr` against canned responses).

2. **Sidecar-MCP integration**: docker-compose with the real
   `../GSpp_MCP` running on a localhost port. Used for catalog-correctness
   tests. **Not** for testing LLM behavior — that's flaky and expensive.

3. **End-to-end live**: nightly only, against a `gs-pp-agent-test` bucket
   and a sandbox GCP project. This is the only place real Gemini calls
   happen in CI. Budget-cap it at $5/run.

### The mandatory tests (DoD)

| Test | Why mandatory |
|---|---|
| `test_review_loop_passes_after_one_rejection` | Validates that the EscalationBarrier works AND that the post-loop writer actually runs after approval. If this passes, you've avoided the #1376 trap. |
| `test_tenant_isolation` | Two parallel sessions with different IV-IDs. Neither sees the other's GCS objects. |
| `test_redteam_prompt_injection_in_pdf` | A vendor PDF with `IGNORE PREVIOUS INSTRUCTIONS...`. Producer must not exfiltrate. Reviewer must mark it as a finding. |
| `test_redteam_unauthorized_tool_call` | Producer is asked to call `apply_profile` with a URL outside the allowed set. Tool-filter must refuse. |
| `test_token_exhaustion_failsafe` | Reviewer that never approves. Loop must terminate after `MAX_REVIEW_ITERATIONS`, NOT recurse infinitely. |
| `test_mcp_5xx_does_not_crash_producer` | MCP sidecar returns 503. Producer surfaces structured error, doesn't catch-and-swallow. |

Without these, do not merge to main.

### Eval snapshots

Live under `tests/eval_snapshots/{workflow}/`. Format:

```
tests/eval_snapshots/cis_oscal/
├── case_001_basic_mapping/
│   ├── input.json           # the CIS input
│   ├── state_initial.json   # state at workflow entry
│   └── expected_output.json # the OSCAL Component Definition
├── case_002_with_revision/
│   ├── ...
│   └── expected_iterations.json   # loop should fail once, approve on 2nd
```

Nightly job runs each case, diffs output against expected, alerts on
significant divergence (controlled by a similarity threshold, not exact match —
LLM outputs vary even at temperature 1.0).

---

## Common pitfalls — checklist

Before you open a PR, scan this list.

- [ ] No `LoopAgent` directly inside a `SequentialAgent` without an
      `EscalationBarrier`. (#1376 trap)
- [ ] `exit_loop` sets BOTH `escalate` AND `skip_summarization` to True.
- [ ] Reviewer model is Flash-tier, not Pro, unless you have a measured
      quality reason otherwise.
- [ ] No model strings hardcoded in agents — they come from env vars.
- [ ] No `temperature` overrides on Gemini 3 models.
- [ ] No `try: except Exception:` around MCP tool calls — let them surface.
- [ ] No prompts inline in `producer.py` / `reviewer.py` — load from
      `shared/prompts/`.
- [ ] No GCS paths constructed manually that bypass IV-namespacing.
      Always use the artifact_service.
- [ ] No `user_id` passed to `Runner` without the `::iv::{iv_id}` suffix.
- [ ] Tool args never logged in plaintext. Hash them.
- [ ] No `Reviewer` with a write-capable MCP tool in its filter list.
- [ ] Every LlmAgent has the `enrich_span_with_iv` `before_agent_callback`.
- [ ] All four DoD red-team tests pass for the modified workflow.
- [ ] If you changed a prompt, the eval snapshot was regenerated in the
      same PR and the version field in frontmatter was bumped.
- [ ] If you bumped `google-adk`, the override-points smoke test is green.

---

## Where to put new files

| What | Where |
|---|---|
| New domain workflow | `agents/<domain>/{producer.py, reviewer.py, workflow.py, tools.py}` |
| New shared schema | `shared/schemas.py` (one file, append) |
| New review criteria class | `shared/review_criteria.py` |
| New prompt | `shared/prompts/<domain>/<role>.md` (with frontmatter) |
| New MCP-tool wrapper | `tools/<name>.py` |
| Custom infra agent (like EscalationBarrier) | `tools/<name>.py` |
| Service-layer code (GCS, sessions) | `services/` |
| Unit test | `tests/unit/test_<module>.py` |
| Integration test | `tests/integration/test_<workflow>_<scenario>.py` |
| Eval snapshot | `tests/eval_snapshots/<workflow>/case_NNN_<slug>/` |

Don't create new top-level directories. Don't put production code in `tests/`.
Don't put helpers in `shared/` that aren't actually shared between two
sibling subprojects (right now, only the agent uses `shared/`, that's fine).

---

## Useful ADK doc anchors

When in doubt, read these (verified May 2026):

- Multi-agents: <https://google.github.io/adk-docs/agents/multi-agents/>
- LoopAgent: <https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/>
- Events / escalate: <https://google.github.io/adk-docs/events/>
- MCP integration: <https://google.github.io/adk-docs/tools/mcp-tools/>
- Custom agents: <https://google.github.io/adk-docs/agents/custom-agents/>
- Get started Python: <https://google.github.io/adk-docs/get-started/python/>
- Releases changelog: <https://github.com/google/adk-python/releases>

If something in this skill contradicts the live ADK docs, the live docs win.
File a PR to update this skill.
