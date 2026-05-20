#!/bin/bash
# Test all MCP tools via Streamable-HTTP transport (POST /mcp)
# Captures Mcp-Session-Id from initialize and passes it to all subsequent calls.

BASE_URL=${1:-"http://localhost:8080"}
TOKEN=${2:-"YOUR_BEARER_TOKEN"}
MCP_URL="${BASE_URL%/}/mcp"
ACCEPT="Accept: application/json, text/event-stream"
CONTENT="Content-Type: application/json"
AUTH="Authorization: Bearer $TOKEN"
SESSION_ID=""

echo "--- COMPREHENSIVE MCP TEST (Streamable-HTTP) ---"
echo "Endpoint: $MCP_URL"
echo ""

# 1. Initialize — capture session ID from response header
echo "=== initialize ==="
INIT_RESPONSE=$(curl -s -i -X POST "$MCP_URL" \
  -H "$CONTENT" \
  -H "$ACCEPT" \
  -H "$AUTH" \
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
      -H "$AUTH" \
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
  -H "$AUTH" \
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

# 4. Call list_oscal_models
send_request "list_oscal_models" '{
  "jsonrpc": "2.0",
  "id": "call-list-oscal-models",
  "method": "tools/call",
  "params": {"name": "list_oscal_models", "arguments": {}}
}'

# 5. Call get_ssp_inventory
send_request "get_ssp_inventory" '{
  "jsonrpc": "2.0",
  "id": "call-get-ssp-inventory",
  "method": "tools/call",
  "params": {"name": "get_ssp_inventory", "arguments": {}}
}'

# 6. Call get_assessment_subjects
send_request "get_assessment_subjects" '{
  "jsonrpc": "2.0",
  "id": "call-get-assessment-subjects",
  "method": "tools/call",
  "params": {"name": "get_assessment_subjects", "arguments": {}}
}'

# 7. Call get_poam_items
send_request "get_poam_items" '{
  "jsonrpc": "2.0",
  "id": "call-get-poam-items",
  "method": "tools/call",
  "params": {"name": "get_poam_items", "arguments": {}}
}'

# 8. Call create_oscal_model
send_request "create_oscal_model" '{
  "jsonrpc": "2.0",
  "id": "call-create-oscal-model",
  "method": "tools/call",
  "params": {
    "name": "create_oscal_model",
    "arguments": {
      "model_enum": "ssp",
      "initial_payload": {"ssp": {}}
    }
  }
}'

# 9. Call update_oscal_model
send_request "update_oscal_model" '{
  "jsonrpc": "2.0",
  "id": "call-update-oscal-model",
  "method": "tools/call",
  "params": {
    "name": "update_oscal_model",
    "arguments": {
      "model_enum": "ssp",
      "patch_payload": {"ssp": {}}
    }
  }
}'

# 10. Call get_ssp_implementation
send_request "get_ssp_implementation" '{
  "jsonrpc": "2.0",
  "id": "call-get-ssp-implementation",
  "method": "tools/call",
  "params": {
    "name": "get_ssp_implementation",
    "arguments": {
      "status": "implemented"
    }
  }
}'

# 11. Call get_assessment_findings
send_request "get_assessment_findings" '{
  "jsonrpc": "2.0",
  "id": "call-get-assessment-findings",
  "method": "tools/call",
  "params": {
    "name": "get_assessment_findings",
    "arguments": {
      "risk_level": "high"
    }
  }
}'

# 12. Call get_assessment_controls
send_request "get_assessment_controls" '{
  "jsonrpc": "2.0",
  "id": "call-get-assessment-controls",
  "method": "tools/call",
  "params": {
    "name": "get_assessment_controls",
    "arguments": {
      "regex_filter": "AC-1"
    }
  }
}'

# 13. Call get_oscal_model_raw
send_request "get_oscal_model_raw" '{
  "jsonrpc": "2.0",
  "id": "call-get-oscal-model-raw",
  "method": "tools/call",
  "params": {
    "name": "get_oscal_model_raw",
    "arguments": {
      "model_enum": "ssp"
    }
  }
}'

# 14. Call list_oscal_model_versions
send_request "list_oscal_model_versions" '{
  "jsonrpc": "2.0",
  "id": "call-list-oscal-model-versions",
  "method": "tools/call",
  "params": {
    "name": "list_oscal_model_versions",
    "arguments": {
      "model_enum": "ssp"
    }
  }
}'

# 15. Call get_resolved_profile_catalog
send_request "get_resolved_profile_catalog" '{
  "jsonrpc": "2.0",
  "id": "call-get-resolved-profile-catalog",
  "method": "tools/call",
  "params": {
    "name": "get_resolved_profile_catalog",
    "arguments": {
      "profile_id": "profile-123"
    }
  }
}'

echo "--- TEST COMPLETE ---"
