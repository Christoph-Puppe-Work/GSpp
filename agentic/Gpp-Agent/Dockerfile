FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies using uv for faster builds
RUN pip install uv
COPY . .
RUN uv pip install --system -e .

EXPOSE 8000

# Start ADK Agent API server (Production)
CMD ["adk", "api", "--host", "0.0.0.0", "--port", "8000"]
