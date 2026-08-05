#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTIC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$AGENTIC_DIR/GS_backend_MCP"
VENV_DIR="$AGENTIC_DIR/.venv"

export PORT=${PORT:-8081}

# ─── Central venv ───────────────────────────────────────────────────────────────
echo "Syncing central venv in agentic/..."
uv sync --all-packages --project "$AGENTIC_DIR"

if [ "${VIRTUAL_ENV:-}" != "$VENV_DIR" ]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
fi

# ─── Start ──────────────────────────────────────────────────────────────────────
echo "Starting GS_backend_MCP server locally on port $PORT..."
cd "$AGENTIC_DIR"
exec python -m GS_backend_MCP.myserver.main
