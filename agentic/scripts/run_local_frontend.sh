#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"
TF_DIR="$SCRIPT_DIR/../terraform"

cd "$FRONTEND_DIR"

if [ "$1" == "--cloud" ]; then
    echo "Fetching Cloud Run agent URL from Terraform..."
    if [ -d "$TF_DIR" ] && terraform -chdir="$TF_DIR" output -json > /dev/null 2>&1; then
        CLOUD_AGENT_URL=$(terraform -chdir="$TF_DIR" output -raw gpp_agent_url 2>/dev/null)
        if [ -n "$CLOUD_AGENT_URL" ] && [ "$CLOUD_AGENT_URL" != "No outputs found" ]; then
            export AGENT_URL="${CLOUD_AGENT_URL}/copilotkit"
            echo "Connecting to Cloud Run agent at: $AGENT_URL"
        else
            echo "Could not fetch agent URL from Terraform. Make sure it is deployed."
            exit 1
        fi
    else
        echo "Terraform directory not found or terraform failed."
        exit 1
    fi
else
    export AGENT_URL=${AGENT_URL:-"http://127.0.0.1:8000/copilotkit"}
    echo "Connecting to local agent at: $AGENT_URL"
    echo "Use '--cloud' to connect to the deployed Cloud Run agent."
fi

echo "Starting frontend locally on port 3000..."
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

npm run dev
