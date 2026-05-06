---
name: mcp-cloud-run-python-stateful
description: Build Python MCP (Model Context Protocol) servers deployed to GCP Cloud Run using the official `mcp` SDK with FastMCP and Streamable HTTP. Use this skill whenever building or modifying the G++ OSCAL Context Management MCP Server. This server acts as a stateful proxy, enforcing Zero-Trust local JSON schema validation and In-Memory transactions against GCP buckets. Cloud Run is the assumed production target.
---

# MCP Server in Python on GCP Cloud Run (Stateful Context Proxy)

This skill captures the architectural decisions and coding patterns for shipping the production Python MCP server for G++ on Cloud Run. Read it end-to-end before writing or modifying any MCP server code. Skipping these patterns produces silent failures, corrupt GCP savepoints, or deploy timeouts.

**Fundamental Workflow Rules:**
1. **use Skill**: `GS_backend_MCP/mcp_backend_MCP_skill_jules.md`
2. **Always start by reading `GS_backend_MCP/tasks.md`** to understand the current progress and pending items.
3. **Always end by updating `GS_backend_MCP/tasks.md`** to reflect the work done.
4. **New Skill entries:** Update `GS_backend_MCP/mcp_backend_MCP_skill_jules.md` if new learning makes you deviate from this skill.

## Verified Stack (May 2026)

- Python 3.11+ (`python:3.13-slim` for the container image).
- `mcp >= 1.27.0` — the **official Anthropic Python SDK** (`from mcp.server.fastmcp import FastMCP`).
- `pydantic >= 2.x` and `jsonschema>=4.21.0` (for local validation).
- `uv` for dependency resolution and image builds.
- Google Cloud Run with Streamable HTTP transport.

## Multi-Tenancy & Context Extraction (CRITICAL)

The server handles multiple independent "Informationsverbünde" (IVs). Tenant isolation is paramount.
- `user_id` passed to the server via the MCP client MUST be of form `{caller}::iv::{iv_id}`.
- **Implementation Rule:** Tools cannot rely on the client passing `iv_id` as a normal argument. The server MUST extract it from the FastMCP `Context`.
```python
from mcp.server.fastmcp import Context

def get_iv_id(ctx: Context) -> str:
    """Extracts IV-ID from the authenticated session context."""
    user_id = ctx.request_context.session.user_id # Format: caller::iv::iv-12345
    if not user_id or "::iv::" not in user_id:
        raise ValueError("Tenant isolation violation: Missing or malformed iv_id in context.")
    return user_id.split("::iv::")[1]
```

## The 8 Hardcoded OSCAL Models (No Flexibility Policy)

The server must strictly reject any operations on models outside of the core 8. Implement this as an Enum and use it for type hinting in all tools.

```python
from enum import Enum

class OscalModel(str, Enum):
    ASSESSMENT_PLAN = "assessment-plan"
    ASSESSMENT_RESULTS = "assessment-results"
    CATALOG = "catalog"
    COMPONENT = "component"
    MAPPING = "mapping"
    POAM = "poam"
    PROFILE = "profile"
    SSP = "ssp"
```

## Architectural Decisions

| Decision | Value | Why |
|---|---|---|
| Transport | `streamable-http` | Required for remote servers on Cloud Run. |
| Bind host | `0.0.0.0` | Cloud Run requires this. `127.0.0.1` causes deploy timeouts. |
| Port | `int(os.getenv("PORT", "8080"))` | Cloud Run injects `PORT`. Hard-coding breaks deployments. |
| Validation | Local `jsonschema` | **Zero-Trust.** The 8 schemas must be loaded from local disk at startup. |
| Auth | IAM + `roles/run.invoker` | Public MCP servers are an exfiltration risk. |
| Caching | In-Memory (Module Level) | Schemas and Resolved Catalogs are cached in RAM upon first load to prevent disk I/O bottlenecks on every request. |

## Canonical Server Skeleton (Maker-Checker Transaction Loop)

Do NOT build a generic read/write server. Implement strict extractors and the In-Memory transaction loop.

```python
import logging
import os
import json
import jsonschema
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from enum import Enum

# Domain imports
from myserver.gcp import storage
from myserver.extractors import ssp_extractor

# --- Logging & Config -----------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GppContextMCP")
PORT = int(os.getenv("PORT", "8080"))

# --- Schema Pre-Loading (Performance) -------------------------------------
# Load schemas into RAM at process start, not during tool execution.
SCHEMA_CACHE = {}
def load_schemas():
    for model in OscalModel:
        path = f"/app/schemas/oscal_{model.value}_schema.json"
        with open(path, 'r') as f:
            SCHEMA_CACHE[model] = json.load(f)

logger.info("Pre-loading 8 OSCAL schemas...")
load_schemas()

# --- FastMCP setup --------------------------------------------------------
mcp = FastMCP("GppContextMCP", host="0.0.0.0", port=PORT)

# --- Tool Registration ----------------------------------------------------

@mcp.tool()
def get_ssp_implementation(status: str, ctx: Context) -> List[Dict]:
    """Extracts controls matching a specific implementation status."""
    iv_id = get_iv_id(ctx)
    ssp_data = storage.read_oscal_model(iv_id, OscalModel.SSP)
    return ssp_extractor.filter_implemented_requirements(ssp_data, status)

@mcp.tool()
def update_oscal_model(model_enum: OscalModel, payload: Dict[str, Any], ctx: Context) -> Dict[str, str]:
    """
    Maker-Checker Loop: Applies patch in RAM, validates locally, commits to GCP.
    """
    iv_id = get_iv_id(ctx)
    
    # 1. Read master document
    master_doc = storage.read_oscal_model(iv_id, model_enum)
    
    # 2. Patch in RAM (Draft)
    draft_doc = storage.apply_patch(master_doc, payload)
    
    # 3. Local Air-Gapped Validation
    schema = SCHEMA_CACHE[model_enum]
    try:
        jsonschema.validate(instance=draft_doc, schema=schema)
    except jsonschema.ValidationError as e:
        # DO NOT CATCH AND SILENCE. The LLM must see this exact error string to fix it.
        raise RuntimeError(f"Maker-Checker Validation Failed for {model_enum.value}: {e.message} at path {e.json_path}")
    
    # 4. Commit to GCP
    new_version = storage.commit_savepoint(iv_id, model_enum, draft_doc)
    return {"status": "success", "new_version": new_version}

# --- Entry point ----------------------------------------------------------
if __name__ == "__main__":
    logger.info(f"Starting GppContextMCP on port {PORT}")
    mcp.run(transport="streamable-http")
```

## pyproject.toml & Dockerfile (uv-based)

```toml
[project]
name = "gpp-context-mcp"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.27.0",
    "jsonschema>=4.21.0",
    "google-cloud-storage>=2.16.0",
    "jsonpatch>=1.33"
]
```

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

# CRITICAL: Local schemas must be physically copied for Zero-Trust validation
COPY schemas/ ./schemas/
COPY myserver/ ./myserver/

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["uv", "run", "python", "-m", "myserver.main"]
```

## Common Pitfalls (STRICT ATTENTION)

- **Silence is Deadly:** If `jsonschema.validate()` fails, do NOT return a string like `{"error": "bad schema"}`. Raise a Python Exception. FastMCP translates Python exceptions into standard MCP error envelopes, which triggers the Agent's internal retry/correction logic.
- **Reference Resolution via Internet:** Ensure `jsonschema` does not attempt to resolve `$ref` URLs by downloading files from the internet. All `$ref`s in the OSCAL schemas must resolve to the local files in `/app/schemas/`.
- **`host="127.0.0.1"`:** Works locally, fails on Cloud Run (timeout on readiness probe). Always use `0.0.0.0`.
- **Direct streamable-http hangs:** Testing against the Cloud Run URL directly hangs. Use the `gcloud run services proxy` tunnel.

## Tool Design Checklist

- [ ] Does the tool extract `iv_id` safely via `Context`?
- [ ] Do read tools return isolated fragments, preventing "Lost-in-the-Middle"?
- [ ] Do write tools use `OscalModel` Enum to prevent arbitrary file modifications?
- [ ] Are all schemas pre-loaded in memory at process start to prevent disk latency?
- [ ] Is `jsonschema.ValidationError` actively raised to utilize the Agent's Maker-Checker workflow?
