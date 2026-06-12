"""Central model selection for all gpp-agent LLM nodes (architecture.md §8).

Role-based defaults:

- **Flash** (`gemini-3-flash-preview`) — classifier and the schema-bound
  judges: cheap, fast, no tool calls, structured output only.
- **3.1 Pro** (`gemini-3.1-pro-preview`) — the tool-using phase inspectors
  (producers) that must reason over OSCAL documents.

Override order (first set wins):

1. ``PHASE<n>_MODEL`` / ``PHASE<n>_JUDGE_MODEL`` / ``CLASSIFIER_MODEL`` —
   per-node override.
2. ``PRODUCER_MODEL`` / ``REVIEWER_MODEL`` / ``ORCHESTRATOR_MODEL`` —
   per-role override.
3. Hard-coded role default.

Env vars are read at factory-call time (not import time) so tests and
deployments can override them without re-importing the app.

NOTE: Gemini 3 preview models require the ``global`` Vertex endpoint —
`app/agent.py` forces ``GOOGLE_CLOUD_LOCATION=global`` at import time.
"""

import os

FLASH_DEFAULT = "gemini-3-flash-preview"
PRO_DEFAULT = "gemini-3.1-pro-preview"


def _first_env(*names: str, default: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


def classifier_model() -> str:
    """Model for the routing classifier — Flash by default."""
    return _first_env("CLASSIFIER_MODEL", "ORCHESTRATOR_MODEL", default=FLASH_DEFAULT)


def producer_model(phase: int) -> str:
    """Model for the tool-using phase inspector — 3.1 Pro by default."""
    return _first_env(f"PHASE{phase}_MODEL", "PRODUCER_MODEL", default=PRO_DEFAULT)


def judge_model(phase: int) -> str:
    """Model for the schema-bound phase judge — Flash by default."""
    return _first_env(
        f"PHASE{phase}_JUDGE_MODEL", "REVIEWER_MODEL", default=FLASH_DEFAULT
    )
