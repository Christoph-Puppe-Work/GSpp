#!/bin/bash
# run_local_gpp_agent_with_local_mcps.sh
#
# Variante zum Inner-Dev-Loop, wenn du gleichzeitig an MCP-Tools entwickelst.
# Startet beide MCP-Server als Hintergrundprozesse und räumt sie beim
# Beenden automatisch auf — alles in einem Terminal.
#
# Überschreibt die MCP-URLs aus .env zur Laufzeit auf localhost — die .env
# selbst bleibt unangetastet, damit du jederzeit zum Cloud-Run-Setup
# (run_local_gpp_agent.sh) zurückwechseln kannst.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTIC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$AGENTIC_DIR/gpp_agent"
TF_DIR="$AGENTIC_DIR/terraform"
VENV_DIR="$AGENTIC_DIR/.venv"

export PORT="${PORT:-8000}"

# Ports überschreibbar, falls dein lokales MCP-Setup andere benutzt
ANWENDER_PORT="${ANWENDER_PORT:-8080}"
BACKEND_PORT="${BACKEND_PORT:-8081}"

# ─── Central venv ───────────────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up central venv in agentic/ (first run)..."
    uv sync --all-packages --project "$AGENTIC_DIR"
fi
if [ "${VIRTUAL_ENV:-}" != "$VENV_DIR" ]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
fi

cd "$APP_DIR"

# ─── .env erzeugen, falls noch keine existiert ─────────────────────────────────
if [ ! -f .env ]; then
    echo "Generating .env from Terraform outputs..."
    if ! [ -d "$TF_DIR" ] || ! terraform -chdir="$TF_DIR" output -json > /dev/null 2>&1; then
        echo "ERROR: Terraform-Outputs nicht verfügbar. Run terraform apply oder erstelle .env manuell."
        exit 1
    fi
    PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
    LOCATION=$(terraform -chdir="$TF_DIR" output -raw region)
    BUCKET=$(terraform -chdir="$TF_DIR" output -raw oscal_storage_bucket)
    sed -e "s|your-project-id|$PROJECT_ID|g" \
        -e "s|your-gcs-bucket-name|$BUCKET|g" \
        -e "s|your-location|$LOCATION|g" \
        .env.example > .env
    echo ".env generated."
fi

set -a; source .env; set +a

# ─── MCP-URLs auf localhost überschreiben ──────────────────────────────────────
export ANWENDER_MCP_URL="http://localhost:$ANWENDER_PORT"
export BACKEND_MCP_URL="http://localhost:$BACKEND_PORT"

# ─── Sanity-Checks ─────────────────────────────────────────────────────────────
echo "Sanity checks (local-MCP mode)..."

if ! gcloud auth application-default print-access-token > /dev/null 2>&1; then
    echo "ERROR: kein ADC-Token. Run: gcloud auth application-default login"
    exit 1
fi
echo "  ADC ok"

if ! gcloud services list --enabled --project="$GOOGLE_CLOUD_PROJECT" \
        --filter="config.name:aiplatform.googleapis.com" --format="value(config.name)" \
        2>/dev/null | grep -q aiplatform; then
    echo "ERROR: aiplatform.googleapis.com nicht aktiviert in $GOOGLE_CLOUD_PROJECT"
    exit 1
fi
echo "  Vertex AI API enabled"

cd "$AGENTIC_DIR"

# ─── MCP-Server als Hintergrundprozesse starten ──────────────────────────────
MCP_PIDS=()

cleanup() {
    echo ""
    echo "Stopping MCP servers..."
    for pid in "${MCP_PIDS[@]}"; do
        kill "$pid" 2>/dev/null && wait "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT INT TERM

echo "Starting GSpp-MCP on port $ANWENDER_PORT..."
CATALOG_PATH="GSpp_MCP/data/Grundschutz++-catalog.json" \
MAPPING_PATH="GSpp_MCP/data/zielobjekt_controls.json" \
PORT="$ANWENDER_PORT" \
python -m GSpp_MCP.server.main &
MCP_PIDS+=($!)

echo "Starting GS_backend_MCP on port $BACKEND_PORT..."
PORT="$BACKEND_PORT" \
python -m myserver.main --transport sse --port "$BACKEND_PORT" &
MCP_PIDS+=($!)

# Warten bis beide MCP-Server erreichbar sind
echo "Waiting for MCP servers to become ready..."
MAX_WAIT=30
for url in "$ANWENDER_MCP_URL" "$BACKEND_MCP_URL"; do
    elapsed=0
    while ! curl -s -o /dev/null --max-time 2 "$url/mcp" 2>/dev/null; do
        sleep 1
        elapsed=$((elapsed + 1))
        if [ "$elapsed" -ge "$MAX_WAIT" ]; then
            echo "ERROR: $url nicht erreichbar nach ${MAX_WAIT}s"
            exit 1
        fi
    done
    echo "  $url ok"
done

# Stale .adk-DBs aufräumen
find "$AGENTIC_DIR" -type d -name ".adk" -not -path "*/.venv/*" -exec rm -rf {} + 2>/dev/null || true

# ─── Start ─────────────────────────────────────────────────────────────────────
cat <<EOF

Starting gpp_agent on port $PORT (LOCAL MCPs)
  Anwender-MCP:  $ANWENDER_MCP_URL
  Backend-MCP:   $BACKEND_MCP_URL
  agents_dir   : $AGENTIC_DIR
Dev-UI: http://localhost:$PORT/dev-ui/

EOF

export GOOGLE_ADK_LOG_LEVEL=DEBUG
export LOG_LEVEL=DEBUG

# kein exec — damit der EXIT-Trap die MCP-Prozesse aufräumen kann
adk web --host 0.0.0.0 --port "$PORT" .
