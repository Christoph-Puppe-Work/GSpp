#!/bin/bash
# run_local_gpp_agent_with_local_mcps.sh
#
# Variante zum Inner-Dev-Loop, wenn du gleichzeitig an MCP-Tools entwickelst.
# Erwartet, dass die beiden MCP-Server in separaten Terminals laufen:
#   ./run_local_GSpp_MCP.sh        # Port 8080 (Anwender)
#   ./run_local_GS_backend_MCP.sh  # Port 8081 (Backend)
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
    uv sync --project "$AGENTIC_DIR"
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

mcp_missing=0
for url in "$ANWENDER_MCP_URL" "$BACKEND_MCP_URL"; do
    if ! curl -s -o /dev/null --max-time 2 "$url/mcp" 2>/dev/null; then
        echo "  ERROR: $url nicht erreichbar"
        mcp_missing=1
    else
        echo "  $url ok"
    fi
done
if [ "$mcp_missing" = "1" ]; then
    cat <<EOF

MCP-Server laufen nicht. Starte sie in zwei separaten Terminals:

  Terminal 2:  $SCRIPT_DIR/run_local_GSpp_MCP.sh
  Terminal 3:  $SCRIPT_DIR/run_local_GS_backend_MCP.sh

Wenn deine MCPs auf anderen Ports laufen, überschreib mit
  ANWENDER_PORT=9080 BACKEND_PORT=9081 $0
EOF
    exit 1
fi

# Stale .adk-DBs aufräumen
find "$AGENTIC_DIR" -type d -name ".adk" -not -path "*/.venv/*" -exec rm -rf {} + 2>/dev/null || true

# ─── Start ─────────────────────────────────────────────────────────────────────
cd "$AGENTIC_DIR"
cat <<EOF

Starting gpp_agent on port $PORT (LOCAL MCPs)
  Anwender-MCP:  $ANWENDER_MCP_URL
  Backend-MCP:   $BACKEND_MCP_URL
Dev-UI: http://localhost:$PORT/dev-ui/

EOF

export GOOGLE_ADK_LOG_LEVEL=DEBUG
export LOG_LEVEL=DEBUG

exec adk web --host 0.0.0.0 --port "$PORT" _adk_apps
