#!/bin/bash
set -e

# Navigate to the agent directory
cd "$(dirname "$0")/../gpp-agent"

echo "Fetching variables from Terraform..."
TF_DIR="$(dirname "$0")/../terraform"
PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
REGION=$(terraform -chdir="$TF_DIR" output -raw region)
ANWENDER_MCP_URL=$(terraform -chdir="$TF_DIR" output -raw gspp_mcp_url)
BACKEND_MCP_URL=$(terraform -chdir="$TF_DIR" output -raw backend_mcp_url)

echo "=== Deploying gpp-agent via agents-cli ==="
agents-cli deploy \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --update-env-vars "ANWENDER_MCP_URL=${ANWENDER_MCP_URL},BACKEND_MCP_URL=${BACKEND_MCP_URL},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --no-confirm-project
