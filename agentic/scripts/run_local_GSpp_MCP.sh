#!/bin/bash
cd "$(dirname "$0")/../GSpp_MCP"
export CATALOG_PATH="data/Grundschutz++-catalog.json"
export MAPPING_PATH="data/zielobjekt_controls.json"
export PORT=${PORT:-8080}
export PYTHONPATH=$PYTHONPATH:.
# Add parent directory so that GSpp_MCP is found as a package if we are in the repo root
export PYTHONPATH=$PYTHONPATH:$(pwd)/..

echo "Starting GSpp-MCP server locally on port $PORT..."
python3 -m GSpp_MCP.server.main
