#!/bin/bash
set -e

# Navigate to the GS_backend_MCP directory
cd "$(dirname "$0")/../GS_backend_MCP"

echo "Fetching variables from Terraform..."
TF_DIR="$(dirname "$0")/../terraform"
PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
REGION=$(terraform -chdir="$TF_DIR" output -raw region)
BUCKET_NAME=$(terraform -chdir="$TF_DIR" output -raw oscal_storage_bucket)
REPO="agentic-repo"
SERVICE_NAME="gpp-backend-mcp"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_NAME}:latest"

echo "=== Building $SERVICE_NAME ==="
gcloud builds submit --project $PROJECT_ID --config cloudbuild.yaml --substitutions=_TAG=$IMAGE_TAG .

echo "=== Deploying $SERVICE_NAME to Cloud Run ==="
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_TAG \
  --region $REGION \
  --project $PROJECT_ID \
  --set-env-vars "BUCKET_NAME=${BUCKET_NAME},PROJECT_ID=${PROJECT_ID}"
