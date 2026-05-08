#!/bin/bash
# Test the gpp_agent (ADK API Server) locally or deployed.

BASE_URL=${1:-"http://127.0.0.1:8000"}
TOKEN=${2:-""}

# Example of how to use this script with gcloud:
# ./scripts/test_gpp_agent.sh https://gpp_agent-xxx.run.app $(gcloud auth print-identity-token)

APP_NAME="gpp_agent"
USER_ID="test_user"
SESSION_ID="test_session_$(date +%s)"

echo "--- Testing gpp_agent ---"
echo "Target URL: $BASE_URL"
if [ -n "$TOKEN" ]; then
  echo "Using provided Bearer token for authentication."
  AUTH_HEADER="Authorization: Bearer $TOKEN"
else
  AUTH_HEADER="X-No-Auth: true" # Dummy header
fi
echo ""

# Helper function to make requests
make_request() {
  local method=$1
  local path=$2
  local data=$3
  
  if [ -n "$data" ]; then
    RESPONSE=$(curl -s -X "$method" "$BASE_URL$path" \
      -H "Content-Type: application/json" \
      -H "$AUTH_HEADER" \
      -d "$data")
  else
    RESPONSE=$(curl -s -X "$method" "$BASE_URL$path" \
      -H "$AUTH_HEADER")
  fi

  if [ -z "$RESPONSE" ]; then
     echo "Error: Empty response. Is the server running at $BASE_URL?"
  else
     echo "$RESPONSE" | python3 -m json.tool || echo "$RESPONSE"
  fi
}

# 1. List Apps (ADK Endpoint)
echo "=== 1. List Apps (/list-apps) ==="
make_request "GET" "/list-apps"
echo -e "\n"

# 2. CopilotKit Info Endpoint (often exposed by ADK)
echo "=== 2. CopilotKit Info (/copilotkit/info) ==="
make_request "GET" "/copilotkit/info"
echo -e "\n"

# 3. Send a Query to ADK /run
echo "=== 3. Send a Query (/run) ==="
PAYLOAD="{
  \"appName\": \"$APP_NAME\",
  \"userId\": \"$USER_ID\",
  \"sessionId\": \"$SESSION_ID\",
  \"newMessage\": {
    \"role\": \"user\",
    \"parts\": [
      { \"text\": \"Hallo, kannst du ein neues SSP für das System 'WebShop' anlegen?\" }
    ]
  }
}"
make_request "POST" "/run" "$PAYLOAD"
echo -e "\n"

echo "--- TEST COMPLETE ---"

# 4. CopilotKit POST Endpoint
echo "=== 4. CopilotKit Endpoint (/copilotkit) ==="
# Provide a typical CopilotKit payload (simplified)
PAYLOAD_CK="{
  \"messages\": [
    { \"role\": \"user\", \"content\": \"Hallo von CopilotKit Endpoint Test!\" }
  ]
}"
make_request "POST" "/copilotkit" "$PAYLOAD_CK"
echo -e "\n"
