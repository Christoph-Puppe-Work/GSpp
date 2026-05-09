# gpp_agent Dockerfile.
#
# Layout in container:
#   /app/                 ← ADK agents_dir (scanned by `adk api_server`)
#     gpp_agent/          ← the agent package (with `agent.py` exposing
#                           `app: App` for auto-discovery)
#       pyproject.toml
#       agent.py
#       agents/, services/, shared/, tools/
#
# `adk api_server` builds a FastAPI app via
# `google.adk.cli.fast_api.get_fast_api_app(...)` and runs it under uvicorn,
# so this *is* the "uvicorn for prod" entrypoint — no manual uvicorn wrapper
# needed, and the FastAPI/session/artifact/eval/tracing plumbing is wired up
# automatically.
#
# Build context: `gpp_agent/` (set by scripts/deploy_gpp_agent.sh).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir uv

# Install the package + deps (uses gpp_agent/pyproject.toml). Working dir is
# the package root during install, then we move up one level so the agents-dir
# layout (`/app/gpp_agent/agent.py`) is what `adk api_server` actually scans.
WORKDIR /app/gpp_agent
COPY . .
RUN uv pip install --system -e .

WORKDIR /app

EXPOSE 8000

# To enable Firestore-backed sessions, append:
#   --session_service_uri firestore://<project>/<database>
# (requires registering the URI scheme via a `services.py` next to agent.py;
# see google/adk/cli/service_registry.py).
CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8000", "/app"]
