#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTIC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$AGENTIC_DIR/.venv"

export CATALOG_PATH="data/Grundschutz++-catalog.json"
export MAPPING_PATH="data/zielobjekt_controls.json"
export PORT=${PORT:-8080}

# ─── Central venv ───────────────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up central venv in agentic/ (first run)..."
    uv sync --project "$AGENTIC_DIR"
fi
if [ "${VIRTUAL_ENV:-}" != "$VENV_DIR" ]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
fi

# ─── Start ──────────────────────────────────────────────────────────────────────
echo "Starting GSpp-MCP server locally on port $PORT..."
cd "$AGENTIC_DIR/GSpp_MCP"
exec python -m GSpp_MCP.server.main
