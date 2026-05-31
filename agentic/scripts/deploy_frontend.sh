#!/bin/bash
set -e

# Navigate to the frontend directory
cd "$(dirname "$0")/../frontend"

echo "Fetching variables from Terraform..."
TF_DIR="$(dirname "$0")/../terraform"
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
