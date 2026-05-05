#!/bin/bash
# Test all MCP tools via Streamable-HTTP transport (POST /mcp)
# Captures Mcp-Session-Id from initialize and passes it to all subsequent calls.

BASE_URL=${1:-"http://localhost:8080"}
MCP_URL="${BASE_URL%/}/mcp"
ACCEPT="Accept: application/json, text/event-stream"
CONTENT="Content-Type: application/json"
SESSION_ID=""

echo "--- COMPREHENSIVE MCP TEST (Streamable-HTTP) ---"
echo "Endpoint: $MCP_URL"
echo ""

# 1. Initialize — capture session ID from response header
echo "=== initialize ==="
INIT_RESPONSE=$(curl -s -i -X POST "$MCP_URL" \
  -H "$CONTENT" \
  -H "$ACCEPT" \
  -d '{
    "jsonrpc": "2.0",
    "id": "init-1",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }')

# Extract session ID from Mcp-Session-Id header (case-insensitive)
SESSION_ID=$(echo "$INIT_RESPONSE" | grep -i "mcp-session-id" | sed 's/.*: //;s/\r//')

if [ -z "$SESSION_ID" ]; then
    echo "ERROR: No Mcp-Session-Id returned by server."
    echo "$INIT_RESPONSE"
    exit 1
fi

# Print the JSON body from the init response
echo "$INIT_RESPONSE" | sed -n '/^{/,$p' | python3 -m json.tool 2>/dev/null
echo "Session ID: $SESSION_ID"
echo ""

# Helper: send a JSON-RPC request with session header, pretty-print response
# Handles both plain JSON and SSE-framed (data: ...) responses.
send_request() {
    local label=$1
    local body=$2
    echo "=== $label ==="
    RESPONSE=$(curl -s -X POST "$MCP_URL" \
      -H "$CONTENT" \
      -H "$ACCEPT" \
      -H "Mcp-Session-Id: $SESSION_ID" \
      -d "$body")

    # Try plain JSON first; if that fails, extract from SSE "data:" lines
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "$RESPONSE" | grep "^data: " | sed 's/^data: //' | while read -r line; do
            echo "$line" | python3 -m json.tool 2>/dev/null || echo "$line"
        done
    fi
    echo ""
}

# 2. Send initialized notification
echo "=== notifications/initialized ==="
curl -s -X POST "$MCP_URL" \
  -H "$CONTENT" \
  -H "$ACCEPT" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc": "2.0", "method": "notifications/initialized"}' > /dev/null
echo "(notification sent)"
echo ""

# 3. List available tools
send_request "tools/list" '{
  "jsonrpc": "2.0",
  "id": "list-tools",
  "method": "tools/list",
  "params": {}
}'

# 4. Call list_groups
send_request "list_groups" '{
  "jsonrpc": "2.0",
  "id": "call-list-groups",
  "method": "tools/call",
  "params": {"name": "list_groups", "arguments": {}}
}'

# 5. Call get_control with a sample ID
send_request "get_control (BER.1.1)" '{
  "jsonrpc": "2.0",
  "id": "call-get-control",
  "method": "tools/call",
  "params": {"name": "get_control", "arguments": {"control_id": "BER.1.1"}}
}'

# 6. Call search_controls
send_request "search_controls (Netzwerk)" '{
  "jsonrpc": "2.0",
  "id": "call-search",
  "method": "tools/call",
  "params": {"name": "search_controls", "arguments": {"query": "Netzwerk"}}
}'

# 7. Call verify_oscal_json with an intentionally invalid document
send_request "verify_oscal_json (invalid assessment-plan)" '{
  "jsonrpc": "2.0",
  "id": "call-verify-json",
  "method": "tools/call",
  "params": {"name": "verify_oscal_json", "arguments": {"json_content": "{\"assessment-plan\": {}}"}}
}'

echo "--- TEST COMPLETE ---"
