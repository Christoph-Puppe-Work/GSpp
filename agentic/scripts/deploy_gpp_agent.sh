#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/../terraform"
AGENT_DIR="$SCRIPT_DIR/../gpp-agent"

# Navigate to the agent directory
cd "$AGENT_DIR"

echo "Fetching variables from Terraform..."
PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id)
REGION=$(terraform -chdir="$TF_DIR" output -raw region)
ANWENDER_MCP_URL=$(terraform -chdir="$TF_DIR" output -raw gspp_mcp_url)
BACKEND_MCP_URL=$(terraform -chdir="$TF_DIR" output -raw backend_mcp_url)

echo "=== Deploying gpp-agent via agents-cli ==="
# agents-cli introspects app.agent_runtime_app at deploy time, which
# initialises Vertex AI — that needs a resolvable project even when ADC has
# no default project configured.
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
export GOOGLE_GENAI_USE_VERTEXAI=true
agents-cli deploy \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --update-env-vars "ANWENDER_MCP_URL=${ANWENDER_MCP_URL},BACKEND_MCP_URL=${BACKEND_MCP_URL}" \
  --no-confirm-project
