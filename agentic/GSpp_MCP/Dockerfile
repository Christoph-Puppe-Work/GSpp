FROM python:3.12-slim

WORKDIR /app

# Install dependencies and project
COPY pyproject.toml .
# Copy all local files into a subdirectory named GSpp_MCP
COPY . ./GSpp_MCP/
RUN pip install --no-cache-dir ./GSpp_MCP/

# Create and switch to non-root user
RUN useradd -m appuser
USER appuser

# Set environment variables
ENV CATALOG_PATH=/app/GSpp_MCP/data/Grundschutz++-catalog.json
ENV MAPPING_PATH=/app/GSpp_MCP/data/zielobjekt_controls.json
ENV OSCAL_SCHEMAS_DIR=/app/GSpp_MCP/OSCAL_schemas
ENV PYTHONPATH=/app

# Expose port for Cloud Run
EXPOSE 8080

# Start the MCP server
CMD ["python", "-m", "GSpp_MCP.server.main"]
