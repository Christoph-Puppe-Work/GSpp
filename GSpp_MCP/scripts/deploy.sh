#!/bin/bash
PROJECT_ID="agentic-tryouts-495214"
REGION="europe-west3"
REPO="mcp-server-repo"
IMAGE_NAME="gs-plus-plus-mcp"
TAG="latest"
FULL_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:${TAG}"

echo "Building and pushing image: $FULL_IMAGE_NAME"
gcloud builds submit --tag "$FULL_IMAGE_NAME" .

echo "Deploying to Cloud Run..."
gcloud run deploy "$IMAGE_NAME" \
  --image "$FULL_IMAGE_NAME" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "CATALOG_PATH=/app/GSpp_MCP/data/Grundschutz++-catalog.json,MAPPING_PATH=/app/GSpp_MCP/data/zielobjekt_controls.json"
