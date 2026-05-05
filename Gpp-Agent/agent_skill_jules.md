---
name: gpp-agent-coding
description: "Build, extend or debug the Gpp-Agent. Use this skill whenever code changes touch any Python file under Gpp-Agent/. Covers the verified May-2026 dependency stack, the canonical Maker-Checker (Producer/Reviewer) pattern with HITL, the Informationsverbund (IV) multi-tenancy convention, GCP versioned savepoints, the GSpp_MCP toolset factory, native OpenTelemetry instrumentation, and current Gemini model assignments. Read this BEFORE writing or modifying any Gpp-Agent code."
---

# Gpp-Agent — Coding Skill

A working manual for writing, extending, and reviewing code in `Gpp-Agent/`, the multi-agent system designed to guide users through the OSCAL process (BSI Grundschutz++) with peer-review quality control, Human-in-the-Loop (HITL) interventions, and per-Informationsverbund GCP persistence.

This skill assumes the `README.md` and `todo.md` in `Gpp-Agent/` are the absolute spec. **Read the README and TODO first.** 

---

## When to use

- Any code change under `Gpp-Agent/`
- Adding a new domain workflow following the 4 phases (SSP-Generator, SSP-Ausfüllen, AP/AR, POA&M).
- Implementing Maker-Checker loops (Producer/Reviewer).
- Adding HITL (Human-in-the-Loop) pause logic.
- Wiring a new MCP tool from `../GSpp_MCP` into an agent.
- Fixing IV-namespacing or GCP savepoint logic.
- Adding observability hooks or test cases.

---

## Dependencies & Framework

If building on ADK or a similar agent framework, respect these pinned rules.

| Package | Version | Why pinned |
|---|---|---|
| `google-adk` | `==1.32.0` | Recommended agent framework; native OpenTelemetry metrics. |
| `google-cloud-storage` | `==3.10.1` | GCS client; mandatory for IV namespacing and Savepoints. |
| `pydantic` | `==2.13.3` | Output schemas + review criteria. |
| `mcp` | `==1.27.0` | MCP client to connect to `../GSpp_MCP`. |

---

## Model Assignment

Three Gemini IDs are in scope. **Do not invent others.**

| ID | Use for | Notes |
|---|---|---|
| `gemini-3.1-pro-preview` | **Producer Agents**: SSP generation, complex mapping, risk analysis. | 1M context. Use when output quality directly determines artifact correctness. |
| `gemini-3-flash-preview` | **Reviewer Agents** & **Orchestrator**: Routing, Maker-Checker validation against schemas. | Fast, cheaper. Perfect for validation and routing tasks. |
| `gemini-3.1-flash-lite-preview` | **Utility Agents**: Input loading, GCS writing, HITL controllers. | Use for high-frequency / mechanical tasks. |

**Configurable via env** (see `.env`):
```bash
ORCHESTRATOR_MODEL=gemini-3-flash-preview
PRODUCER_MODEL=gemini-3.1-pro-preview
REVIEWER_MODEL=gemini-3-flash-preview
UTILITY_MODEL=gemini-3.1-flash-lite-preview
```
*Never hardcode model strings in Python files.*

---

## The Canonical Producer / Reviewer (Maker-Checker) Pattern

Every workflow phase (SSP-Generator, SSP-Ausfüllen, etc.) follows the same Peer-Review template.

### 1. Producer
Generates the draft artifact (e.g., OSCAL JSON) using `PRODUCER_MODEL`.
- **Must** use strict Pydantic `output_schema` to ensure JSON validity before GCP saving.
- Has access to broad MCP lookup tools.

### 2. Reviewer
Validates the Producer's draft against schemas and the MCP catalog.
- Uses `REVIEWER_MODEL`.
- **Must** use a structured `ReviewCriteria` schema to return its verdict.
- Has read-only MCP tools (tool filtering is mandatory).

### 3. Human-in-the-Loop (HITL)
After the Reviewer approves, the workflow **must pause** and await user confirmation or edits before the final artifact is pushed to the GCS Savepoint.

```python
# Example: agents/ssp_generator/workflow.py (Pseudo-ADK)
from google.adk.agents import LoopAgent, SequentialAgent
from tools.escalation_barrier import EscalationBarrier

async def get_ssp_generator_workflow() -> SequentialAgent:
    review_loop = LoopAgent(
        name="ssp_review_loop",
        sub_agents=[await get_producer(), await get_reviewer()],
        max_iterations=3,
    )
    return SequentialAgent(
        name="ssp_generator_workflow",
        sub_agents=[
            await get_input_loader(),
            EscalationBarrier(name="review_barrier", inner=review_loop),
            await get_hitl_controller(), # Prompts user for approval
            await get_gcs_writer(),      # Saves to GCP Bucket
        ],
    )
```

*(Note: The `EscalationBarrier` prevents a `LoopAgent`'s internal `escalate=True` from prematurely halting the entire parent `SequentialAgent`. This ADK gotcha is critical.)*

---

## Multi-Tenancy & GCP Savepoints

The `README.md` strictly mandates isolation per `Informationsverbund` (IV) and versioned saves.

- **GCS Layout**: `gs://{GCS_BUCKET_NAME}/{iv_id}/saves/{save_id}/`
- All GCS interactions must be routed through a dedicated `GcsStorageService` that strictly enforces the `{iv_id}` prefix.
- **Never bypass this service.** Writing files locally or outside the `{iv_id}` namespace is a critical failure.

---

## MCP Tool Filtering

Do not pass the full `GSpp_MCP` toolset to every agent.
- **Reviewer**: Read-only tools (`catalog_info`, `get_control`, etc.).
- **Producer**: Lookup and generation tools.

```python
def get_bsi_gpp_toolset(*, allow: list[str] | None = None):
    # Filter tools based on the 'allow' list to reduce context and prompt-injection surface
    ...
```

---

## Prompts — `shared/prompts/{domain}/{role}.md`

Prompts belong in Markdown files, NOT inline in Python.

Use YAML frontmatter to track prompt versions and required schemas:
```markdown
---
id: ssp_generator/producer
version: 1.0
model_hint: gemini-3.1-pro-preview
output_schema: OscalSspDefinition
---
You are a security architect specialized in BSI Grundschutz++...
```

---

## Testing & DoD (Definition of Done)

Before opening a PR, ensure the following test cases pass:

1. **Tenant Isolation**: Two parallel IV sessions must not see each other's GCS objects.
2. **Review Loop Completion**: A test where the Reviewer rejects the first draft and approves the second, proving the EscalationBarrier works.
3. **HITL Interruption**: A test verifying the workflow successfully pauses and waits for external user input before hitting the GCS writer.
4. **Schema Validation**: A test proving malformed OSCAL JSON is rejected before GCS save.
5. **Red-Team Prompt Injection**: A user upload (e.g., Asset list) containing malicious instructions. The Reviewer must catch it, or the Producer must ignore it.

---

## Where to put new files

| What | Where |
|---|---|
| Domain workflow logic | `agents/<phase>/{producer.py, reviewer.py, workflow.py}` (e.g., `agents/ssp_generator/`) |
| Shared OSCAL Schemas | `schemas/oscal.py` |
| Review criteria | `schemas/review.py` |
| Prompts | `shared/prompts/<phase>/<role>.md` |
| Infra/Services (GCS, MCP) | `services/` |
| Tools (HITL, EscBarrier) | `tools/` |
| Tests | `tests/unit/` or `tests/integration/` |

**Rule of thumb:** Do not create top-level directories outside of `agents/`, `tools/`, `services/`, `schemas/`, `shared/`, and `tests/`.
