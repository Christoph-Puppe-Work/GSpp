#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTIC_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$AGENTIC_DIR/gpp_agent"
TF_DIR="$AGENTIC_DIR/terraform"
VENV_DIR="$AGENTIC_DIR/.venv"

export PORT="${PORT:-8000}"

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

# ─── .env aus Terraform-Outputs erzeugen ──────────────────────────────────────
if [ ! -f .env ]; then
    echo "Generating .env from Terraform outputs..."

    if ! [ -d "$TF_DIR" ] || ! terraform -chdir="$TF_DIR" output -json > /dev/null 2>&1; then
        echo "ERROR: Terraform-Outputs nicht verfügbar in $TF_DIR"
        echo "       Run: terraform -chdir=$TF_DIR init && terraform -chdir=$TF_DIR apply"
        exit 1
    fi

    PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
    LOCATION=$(terraform -chdir="$TF_DIR" output -raw region)
    BUCKET=$(terraform -chdir="$TF_DIR" output -raw oscal_storage_bucket)
    GSPP_MCP_URL=$(terraform -chdir="$TF_DIR" output -raw gspp_mcp_url)
    BACKEND_MCP_URL=$(terraform -chdir="$TF_DIR" output -raw backend_mcp_url)

    sed -e "s|your-project-id|$PROJECT_ID|g" \
        -e "s|your-gcs-bucket-name|$BUCKET|g" \
        -e "s|your-location|$LOCATION|g" \
        -e "s|http://localhost:8080|$GSPP_MCP_URL|g" \
        -e "s|http://localhost:8081|$BACKEND_MCP_URL|g" \
        .env.example > .env

    echo ".env generated:"
    echo "  project=$PROJECT_ID  location=$LOCATION  bucket=$BUCKET"
    echo "  anwender_mcp=$GSPP_MCP_URL  backend_mcp=$BACKEND_MCP_URL"
fi

set -a; source .env; set +a

# ─── Pflichtvariablen prüfen ───────────────────────────────────────────────────
required_vars=(GOOGLE_CLOUD_PROJECT GOOGLE_CLOUD_LOCATION ANWENDER_MCP_URL BACKEND_MCP_URL)
for v in "${required_vars[@]}"; do
    if [ -z "${!v:-}" ]; then
        echo "ERROR: $v fehlt in .env. Vergleiche mit .env.example, lösche .env und re-run."
        exit 1
    fi
done

# ─── Sanity-Checks ─────────────────────────────────────────────────────────────
echo "Sanity checks..."

if ! gcloud auth application-default print-access-token > /dev/null 2>&1; then
    echo "ERROR: kein ADC-Token. Run: gcloud auth application-default login"
    exit 1
fi
echo "  ADC ok"

if ! gcloud services list --enabled --project="$GOOGLE_CLOUD_PROJECT" \
        --filter="config.name:aiplatform.googleapis.com" --format="value(config.name)" \
        2>/dev/null | grep -q aiplatform; then
    echo "ERROR: aiplatform.googleapis.com nicht aktiviert in $GOOGLE_CLOUD_PROJECT"
    echo "       Run: gcloud services enable aiplatform.googleapis.com --project=$GOOGLE_CLOUD_PROJECT"
    exit 1
fi
echo "  Vertex AI API enabled"

for url in "${ANWENDER_MCP_URL:-}" "${BACKEND_MCP_URL:-}"; do
    [ -z "$url" ] && continue
    if ! curl -s -o /dev/null --max-time 5 -L -k "$url/mcp" 2>/dev/null; then
        echo "  WARNING: $url nicht erreichbar"
    fi
done

# Stale .adk-DBs aufräumen
find "$AGENTIC_DIR" -type d -name ".adk" -not -path "*/.venv/*" -exec rm -rf {} + 2>/dev/null || true

# ─── Start ─────────────────────────────────────────────────────────────────────
cd "$AGENTIC_DIR"
echo ""
echo "Starting gpp_agent on port $PORT"
echo "Dev-UI: http://localhost:$PORT/dev-ui/"
echo "  agents_dir = $AGENTIC_DIR"
echo "  [DEBUG] The following directories will be detected as apps by ADK:"
ls -1d */ | sed 's/\/$//' | awk '{print "    - " $0}'
echo ""
exec adk web --host 0.0.0.0 --port "$PORT" .
