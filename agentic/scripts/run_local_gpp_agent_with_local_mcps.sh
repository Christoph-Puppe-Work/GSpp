#!/bin/bash
# run_local_gpp-agent_with_local_mcps.sh
#
# Variante zum Inner-Dev-Loop, wenn du gleichzeitig an MCP-Tools entwickelst.
# Startet beide MCP-Server als Hintergrundprozesse und räumt sie beim
# Beenden automatisch auf — alles in einem Terminal.
#
# Überschreibt die MCP-URLs aus .env zur Laufzeit auf localhost — die .env
# selbst bleibt unangetastet, damit du jederzeit zum Cloud-Run-Setup
# (run_local_gpp-agent.sh) zurückwechseln kannst.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTIC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$AGENTIC_DIR/gpp-agent"
TF_DIR="$AGENTIC_DIR/terraform"
VENV_DIR="$AGENTIC_DIR/.venv"

export PORT="${PORT:-8000}"

# Ports überschreibbar, falls dein lokales MCP-Setup andere benutzt
ANWENDER_PORT="${ANWENDER_PORT:-8080}"
BACKEND_PORT="${BACKEND_PORT:-8081}"
GPP_BACKEND_DEV_IV_ID="${GPP_BACKEND_DEV_IV_ID:-local-dev}"

# ─── Central venv ───────────────────────────────────────────────────────────────
echo "Syncing central venv in agentic/..."
uv sync --all-packages --project "$AGENTIC_DIR"

if [ "${VIRTUAL_ENV:-}" != "$VENV_DIR" ]; then
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
fi

cd "$APP_DIR"

# ─── .env erzeugen, falls noch keine existiert ─────────────────────────────────
if [ ! -f .env ]; then
    echo "Generating .env from Terraform outputs..."
    TF_OUTPUTS=$(terraform -chdir="$TF_DIR" output -json 2>/dev/null || echo "{}")
    if ! [ -d "$TF_DIR" ] || [ "$TF_OUTPUTS" = "{}" ]; then
        echo "WARNING: Terraform-Outputs nicht verfügbar. Bitte manuell eingeben:"
        read -rp "Enter Project ID: " PROJECT_ID
        read -rp "Enter Region (e.g., europe-west1): " LOCATION
        read -rp "Enter GCS Bucket name: " BUCKET
        for var in PROJECT_ID LOCATION BUCKET; do
            if [ -z "${!var}" ]; then
                echo "ERROR: $var darf nicht leer sein."
                exit 1
            fi
        done
    else
        PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
        LOCATION=$(terraform -chdir="$TF_DIR" output -raw region)
        BUCKET=$(terraform -chdir="$TF_DIR" output -raw oscal_storage_bucket)
    fi
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
GPP_BACKEND_ALLOW_DEV_IV_FALLBACK=1 \
GPP_BACKEND_DEV_IV_ID="$GPP_BACKEND_DEV_IV_ID" \
PORT="$BACKEND_PORT" \
python -m GS_backend_MCP.myserver.main --transport sse --port "$BACKEND_PORT" &
MCP_PIDS+=($!)

# Warten bis beide MCP-Server erreichbar sind
echo "Waiting for MCP servers to become ready..."
MAX_WAIT=30

wait_for_port() {
    local label="$1"
    local host="$2"
    local port="$3"
    local elapsed=0

    while ! (echo > "/dev/tcp/$host/$port") >/dev/null 2>&1; do
        sleep 1
        elapsed=$((elapsed + 1))
        if [ "$elapsed" -ge "$MAX_WAIT" ]; then
            echo "ERROR: $label nicht erreichbar nach ${MAX_WAIT}s"
            exit 1
        fi
    done
    echo "  $label ok"
}

for port in "$ANWENDER_PORT" "$BACKEND_PORT"; do
    wait_for_port "http://localhost:$port" "127.0.0.1" "$port"
done

# Stale .adk-DBs aufräumen
find "$AGENTIC_DIR" -type d -name ".adk" -not -path "*/.venv/*" -exec rm -rf {} + 2>/dev/null || true

# ─── Start ─────────────────────────────────────────────────────────────────────
cd "$APP_DIR"
cat <<EOF

Starting gpp-agent on port $PORT (LOCAL MCPs)
  Anwender-MCP:  $ANWENDER_MCP_URL
  Backend-MCP:   $BACKEND_MCP_URL
  Backend IV:    $GPP_BACKEND_DEV_IV_ID (local dev fallback)
  agents_dir   : $APP_DIR
Dev-UI: http://localhost:$PORT/dev-ui/

EOF

export GOOGLE_ADK_LOG_LEVEL=DEBUG
export LOG_LEVEL=DEBUG

# kein exec — damit der EXIT-Trap die MCP-Prozesse aufräumen kann
agents-cli playground --host 0.0.0.0 --port "$PORT"
