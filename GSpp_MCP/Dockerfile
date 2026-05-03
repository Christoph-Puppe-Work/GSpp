FROM python:3.12-slim

WORKDIR /app

# Install dependencies and project
COPY pyproject.toml .
COPY GSpp_MCP/ ./GSpp_MCP/
RUN pip install --no-cache-dir .

# Create and switch to non-root user
RUN useradd -m appuser
USER appuser

# Set environment variables
ENV CATALOG_PATH=/app/GSpp_MCP/data/Grundschutz++-catalog.json
ENV MAPPING_PATH=/app/GSpp_MCP/data/zielobjekt_controls.json
ENV PYTHONPATH=/app

# Expose port for Cloud Run
EXPOSE 8080

# Start the MCP server
CMD ["python", "-m", "GSpp_MCP.server.main"]
