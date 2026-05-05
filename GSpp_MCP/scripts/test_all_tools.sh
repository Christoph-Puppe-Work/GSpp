#!/bin/bash

BASE_URL=${1:-"http://localhost:8080"}
TARGET_URL="${BASE_URL%/}/mcp/sse"
SSE_LOG="sse_output.log"

echo "--- COMPREHENSIVE MCP TEST ---"
rm -f "$SSE_LOG"

# 1. Start SSE connection in background
echo "Step 1: Opening SSE connection..."
curl -N -s -H "Accept: text/event-stream" "$TARGET_URL" > "$SSE_LOG" &
SSE_PID=$!

# Wait for the endpoint to appear in the log
echo "Waiting for session initialization..."
for i in {1..10}; do
    if grep -q "data: /mcp/messages" "$SSE_LOG"; then
        break
    fi
    sleep 1
done

INIT_RESPONSE=$(cat "$SSE_LOG")
SESSION_PATH=$(echo "$INIT_RESPONSE" | grep -m 1 "data: " | sed 's/data: //;s/\r//')

if [ -z "$SESSION_PATH" ]; then
    echo "Error: Could not retrieve sessionId"
    cat "$SSE_LOG"
    kill $SSE_PID
    exit 1
fi

if [[ "$SESSION_PATH" == http* ]]; then
    POST_URL="$SESSION_PATH"
else
    POST_URL="${BASE_URL%/}${SESSION_PATH}"
fi

echo "Session initialized. POST URL: $POST_URL"

# Function to send a request
send_request() {
    local method=$1
    local params=$2
    local id=$3
    echo "Calling $method ($id)..."
    curl -s -X POST "$POST_URL" \
      -H "Content-Type: application/json" \
      -d "{\"jsonrpc\": \"2.0\", \"id\": \"$id\", \"method\": \"$method\", \"params\": $params}" > /dev/null
}

# 2. Initialization Sequence
send_request "initialize" "{\"protocolVersion\": \"2024-11-05\", \"capabilities\": {}, \"clientInfo\": {\"name\": \"test-client\", \"version\": \"1.0.0\"}}" "init-1"
sleep 1
# Notifications don't have an ID
echo "Sending notifications/initialized..."
curl -s -X POST "$POST_URL" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\": \"2.0\", \"method\": \"notifications/initialized\"}" > /dev/null
sleep 1

# 3. Call various tools
send_request "tools/list" "{}" "list-tools"
sleep 1
send_request "tools/call" "{\"name\": \"list_groups\", \"arguments\": {}}" "call-list-groups"
sleep 2

# 4. Shutdown SSE and show results
kill $SSE_PID
echo -e "\n--- Captured Responses ---"
grep "data: " "$SSE_LOG" | sed 's/data: //' | grep "jsonrpc" | while read -r line; do
    echo "$line" | python3 -m json.tool || echo "$line"
done
