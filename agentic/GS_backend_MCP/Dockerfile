# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app

COPY GS_backend_MCP/pyproject.toml ./
# We don't have a lock file yet, so we just sync dependencies
RUN uv sync --no-dev

# CRITICAL: Local schemas must be physically copied for Zero-Trust validation
COPY GS_backend_MCP/schemas/ ./GS_backend_MCP/schemas/
COPY GS_backend_MCP/myserver/ ./GS_backend_MCP/myserver/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
EXPOSE 8080

CMD ["uv", "run", "python", "-m", "GS_backend_MCP.myserver.main"]
