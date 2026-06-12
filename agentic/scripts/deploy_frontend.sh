#!/bin/bash
set -e

# ─── DEFERRED (P0-2) ──────────────────────────────────────────────────────────
# The frontend↔agent transport is not decided yet: Terraform wires the Agent
# Engine :query URL into the frontend, while this script assumes a Cloud Run
# FastAPI agent exposing /copilotkit (and reads a Terraform output
# `gpp_agent_url` that does not exist). Until the P0-2 architecture decision
# (Option A: Cloud Run + ag-ui-adk vs. Option B: Agent Engine bridge) lands,
# deploying the frontend is pointless — the playground is the UI.
echo "ERROR: frontend deployment is deferred pending the P0-2 transport decision (see agentic/issues.md)." >&2
exit 1

# Resolve paths BEFORE cd — $0 is relative and breaks after chdir.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TF_DIR="$SCRIPT_DIR/../terraform"

# Navigate to the frontend directory
cd "$SCRIPT_DIR/../frontend"

echo "Fetching variables from Terraform..."
PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
REGION=$(terraform -chdir="$TF_DIR" output -raw region)
AGENT_URL=$(terraform -chdir="$TF_DIR" output -raw gpp_agent_url)
REPO="agentic-repo"
SERVICE_NAME="gpp-frontend"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_NAME}:latest"

echo "=== Building $SERVICE_NAME ==="
gcloud builds submit --project $PROJECT_ID --tag $IMAGE_TAG .

echo "=== Deploying $SERVICE_NAME to Cloud Run ==="
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_TAG \
  --region $REGION \
  --project $PROJECT_ID \
  --set-env-vars "AGENT_URL=${AGENT_URL}/copilotkit"
