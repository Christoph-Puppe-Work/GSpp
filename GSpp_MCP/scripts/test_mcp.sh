#!/bin/bash

# Usage: ./scripts/test_mcp.sh [BASE_URL]
# Example Local:  ./scripts/test_mcp.sh http://localhost:8080
# Example Remote: ./scripts/test_mcp.sh https://gs-plus-plus-mcp-12345.a.run.app

BASE_URL=${1:-"http://localhost:8080"}

# FastMCP streamable-http transport usually mounts at /mcp
TARGET_URL="${BASE_URL%/}/sse"
TARGET_URL="${BASE_URL%/}/mcp/sse"

echo "--- MCP TEST TOOL (Streamable HTTP) ---"

# 1. Initialize session by requesting the SSE stream
echo "Step 1: Initializing session via SSE..."
# We use a 2-second timeout because the SSE stream is persistent
INIT_RESPONSE=$(curl -s -m 5 -X GET -H "Accept: text/event-stream" "$TARGET_URL")

# Extract the endpoint (which includes the sessionId) from the SSE data: line
SESSION_PATH=$(echo "$INIT_RESPONSE" | grep -m 1 "data: " | sed 's/data: //')

if [ -z "$SESSION_PATH" ]; then
    echo "Error: Could not retrieve sessionId from $TARGET_URL"
    echo "Response received: $INIT_RESPONSE"
    exit 1
fi

# Construct the final URL (handling both relative and absolute paths)
if [[ "$SESSION_PATH" == http* ]]; then
    POST_URL="$SESSION_PATH"
else
    POST_URL="${BASE_URL%/}${SESSION_PATH}"
fi

echo "Step 2: Sending request to $POST_URL"
curl -i -X POST "$POST_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "tools/list",
    "params": {}
  }'