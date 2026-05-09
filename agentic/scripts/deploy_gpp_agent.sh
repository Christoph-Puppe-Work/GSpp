#!/bin/bash
set -e

# Navigate to the agent directory
cd "$(dirname "$0")/../gpp_agent"

echo "Fetching variables from Terraform..."
TF_DIR="$(dirname "$0")/../terraform"
PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
REGION=$(terraform -chdir="$TF_DIR" output -raw region)
ANWENDER_MCP_URL=$(terraform -chdir="$TF_DIR" output -raw gspp_mcp_url)
BACKEND_MCP_URL=$(terraform -chdir="$TF_DIR" output -raw backend_mcp_url)
REPO="agentic-repo"
SERVICE_NAME="gpp-agent"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_NAME}:latest"

echo "=== Building $SERVICE_NAME ==="
gcloud builds submit --project $PROJECT_ID --tag $IMAGE_TAG .

echo "=== Deploying $SERVICE_NAME to Cloud Run ==="
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_TAG \
  --region $REGION \
  --project $PROJECT_ID \
  --min-instances 1 \
  --set-env-vars "ANWENDER_MCP_URL=${ANWENDER_MCP_URL},BACKEND_MCP_URL=${BACKEND_MCP_URL},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
