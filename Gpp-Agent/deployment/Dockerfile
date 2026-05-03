FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables (should be overridden in Cloud Run)
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE
ENV BSI_GPP_MCP_MODE=sse

# Entrypoint for ADK
ENTRYPOINT ["adk", "run", "orchestrator.agent:root_agent"]
