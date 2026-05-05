#!/bin/bash
# Test all MCP tools via Streamable-HTTP transport (POST /mcp)

BASE_URL=${1:-"http://localhost:8080"}
MCP_URL="${BASE_URL%/}/mcp"

echo "--- COMPREHENSIVE MCP TEST (Streamable-HTTP) ---"
echo "Endpoint: $MCP_URL"
echo ""

# Helper: send a JSON-RPC request and pretty-print the response
send_request() {
    local label=$1
    local body=$2
    echo "=== $label ==="
    curl -s -X POST "$MCP_URL" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json" \
      -d "$body" | python3 -m json.tool 2>/dev/null || echo "(no JSON response)"
    echo ""
}

# 1. Initialize session
send_request "initialize" '{
  "jsonrpc": "2.0",
  "id": "init-1",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "test-client", "version": "1.0.0"}
  }
}'

# 2. Send initialized notification (no id, no response expected)
echo "=== notifications/initialized ==="
curl -s -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
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
