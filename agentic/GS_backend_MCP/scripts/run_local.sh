#!/bin/bash
export PORT=${PORT:-8081}
export PYTHONPATH=$PYTHONPATH:.
# Add parent directory so that GS_backend_MCP is found as a package if we are in the repo root
export PYTHONPATH=$PYTHONPATH:$(pwd)/..

echo "Starting GS_backend_MCP server locally on port $PORT..."
python3 -m myserver.main --transport sse --port $PORT
