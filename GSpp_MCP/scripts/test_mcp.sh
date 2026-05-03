#!/bin/bash

# Usage: ./scripts/test_mcp.sh [BASE_URL]
# Example Local:  ./scripts/test_mcp.sh http://localhost:8080
# Example Remote: ./scripts/test_mcp.sh https://gs-plus-plus-mcp-12345.a.run.app

BASE_URL=${1:-"http://localhost:8080"}

# FastMCP streamable-http transport usually mounts at /mcp
TARGET_URL="${BASE_URL%/}/mcp"

echo "--- MCP TEST TOOL ---"
echo "Target: $TARGET_URL"

HEADERS=(
  -H "Content-Type: application/json"
  -H "Accept: application/json, text/event-stream"
)

curl -i -X POST "$TARGET_URL" \
  "${HEADERS[@]}" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "tools/list",
    "params": {}
  }'