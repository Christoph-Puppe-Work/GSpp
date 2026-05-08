#!/bin/bash
cd "$(dirname "$0")/../gpp_agent"

export PORT=${PORT:-8000}
export PYTHONPATH=$PYTHONPATH:.
export PYTHONPATH=$PYTHONPATH:$(pwd)/..

# Load env variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "Warning: .env file not found in gpp_agent directory. You might need to copy .env.example to .env and configure it."
fi

echo "Starting gpp_agent locally on port $PORT..."
uv run adk api_server --host 0.0.0.0 --port $PORT
