#!/bin/bash
set -e

# Resolve paths BEFORE cd — $0 is relative and breaks after chdir.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TF_DIR="$SCRIPT_DIR/../terraform"

# Navigate to the GSpp_MCP directory
cd "$SCRIPT_DIR/../GSpp_MCP"

echo "Fetching variables from Terraform..."
PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
REGION=$(terraform -chdir="$TF_DIR" output -raw region)
REPO="agentic-repo"
SERVICE_NAME="gs-plus-plus-mcp"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_NAME}:latest"

echo "=== Building $SERVICE_NAME ==="
gcloud builds submit --project $PROJECT_ID --tag $IMAGE_TAG .

echo "=== Rolling new revision of $SERVICE_NAME ==="
# Terraform owns service config (env vars, scaling, IAM) — P2-23. This script
# only builds/pushes the image and rolls a new revision; never pass
# --set-env-vars here or the next `terraform apply` will fight the change.
gcloud run services update $SERVICE_NAME \
  --image $IMAGE_TAG \
  --region $REGION \
  --project $PROJECT_ID
