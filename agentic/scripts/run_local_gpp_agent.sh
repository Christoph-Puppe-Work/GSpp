#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/../gpp_agent"
TF_DIR="$SCRIPT_DIR/../terraform"

cd "$APP_DIR"

export PORT=${PORT:-8000}
export PYTHONPATH=$PYTHONPATH:.
export PYTHONPATH=$PYTHONPATH:$(pwd)/..

# Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example using Terraform outputs..."
    if [ -d "$TF_DIR" ] && terraform -chdir="$TF_DIR" output -json > /dev/null 2>&1; then
        PROJECT_ID=$(terraform -chdir="$TF_DIR" output -raw project_id 2>/dev/null)
        BUCKET=$(terraform -chdir="$TF_DIR" output -raw gpp_artifacts_bucket_name 2>/dev/null || echo "${PROJECT_ID}-artifacts")
        
        sed -e "s/your-project-id/$PROJECT_ID/g" \
            -e "s/your-gcs-bucket-name/$BUCKET/g" \
            .env.example > .env
        echo ".env file generated successfully."
    else
        cp .env.example .env
        echo "Warning: Terraform outputs unavailable. Copied .env.example to .env. Please configure manually."
    fi
fi

set -a
source .env
set +a

echo "Starting gpp_agent locally on port $PORT..."
uv run adk api_server --host 0.0.0.0 --port $PORT
