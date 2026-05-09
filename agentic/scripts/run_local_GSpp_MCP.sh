#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTIC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$AGENTIC_DIR/.venv"

export CATALOG_PATH="GSpp_MCP/data/Grundschutz++-catalog.json"
export MAPPING_PATH="GSpp_MCP/data/zielobjekt_controls.json"
export PORT=${PORT:-8080}

# ─── Central venv ───────────────────────────────────────────────────────────────
echo "Syncing central venv in agentic/..."
uv sync --all-packages --project "$AGENTIC_DIR"

if [ "${VIRTUAL_ENV:-}" != "$VENV_DIR" ]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
fi

# ─── Start ──────────────────────────────────────────────────────────────────────
echo "Starting GSpp-MCP server locally on port $PORT..."
cd "$AGENTIC_DIR"
exec python -m GSpp_MCP.server.main
