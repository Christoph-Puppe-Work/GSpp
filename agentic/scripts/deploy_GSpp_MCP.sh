#!/bin/bash
set -e

# Navigate to the GSpp_MCP directory
cd "$(dirname "$0")/../GSpp_MCP"

echo "Fetching variables from Terraform..."
TF_DIR="$(dirname "$0")/../terraform"
PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
REGION=$(terraform -chdir="$TF_DIR" output -raw region)
REPO="agentic-repo"
SERVICE_NAME="gs-plus-plus-mcp"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_NAME}:latest"

echo "=== Building $SERVICE_NAME ==="
gcloud builds submit --project $PROJECT_ID --tag $IMAGE_TAG .

echo "=== Deploying $SERVICE_NAME to Cloud Run ==="
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_TAG \
  --region $REGION \
  --project $PROJECT_ID \
  --set-env-vars "CATALOG_PATH=/app/GSpp_MCP/data/Grundschutz++-catalog.json,MAPPING_PATH=/app/GSpp_MCP/data/zielobjekt_controls.json"
