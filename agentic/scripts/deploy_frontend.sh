#!/bin/bash
set -e

# Navigate to the frontend directory
cd "$(dirname "$0")/../frontend"

echo "Fetching variables from Terraform..."
PROJECT_ID=$(terraform -chdir="$(dirname "$0")/../terraform" output -raw project_id)
REGION=$(terraform -chdir="$(dirname "$0")/../terraform" output -raw region)
REPO="agentic-repo"
SERVICE_NAME="gpp-frontend"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${SERVICE_NAME}:latest"

echo "=== Building $SERVICE_NAME ==="
gcloud builds submit --project $PROJECT_ID --tag $IMAGE_TAG .

echo "=== Deploying $SERVICE_NAME to Cloud Run ==="
gcloud run deploy $SERVICE_NAME --image $IMAGE_TAG --region $REGION --project $PROJECT_ID
