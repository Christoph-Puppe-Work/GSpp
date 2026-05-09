#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTIC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$AGENTIC_DIR/GS_backend_MCP"
VENV_DIR="$AGENTIC_DIR/.venv"

export PORT=${PORT:-8081}

# ─── Central venv ───────────────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up central venv in agentic/ (first run)..."
    uv sync --all-packages --project "$AGENTIC_DIR"
fi
if [ "${VIRTUAL_ENV:-}" != "$VENV_DIR" ]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
fi

# ─── Start ──────────────────────────────────────────────────────────────────────
echo "Starting GS_backend_MCP server locally on port $PORT..."
# cd into the package dir so that the uninstalled `myserver` package is on sys.path
cd "$APP_DIR"
exec python -m myserver.main --transport sse --port "$PORT"
