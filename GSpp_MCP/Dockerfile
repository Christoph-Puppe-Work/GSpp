FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY GSpp_MCP/pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source code and data
COPY GSpp_MCP/server ./GSpp_MCP/server
COPY GSpp_MCP/data ./GSpp_MCP/data

# Set environment variables
ENV CATALOG_PATH=/app/GSpp_MCP/data/Grundschutz++-catalog.json
ENV MAPPING_PATH=/app/GSpp_MCP/data/zielobjekt_controls.json
ENV PYTHONPATH=/app

# Expose port for Cloud Run
EXPOSE 8080

# Start the MCP server
CMD ["python", "-m", "GSpp_MCP.server.main"]
