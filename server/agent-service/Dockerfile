FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY server/agent-service/requirements.txt ./server/agent-service/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r server/agent-service/requirements.txt

# Copy entire server directory structure (needed for shared modules)
COPY server/ ./server/

# Set PYTHONPATH to include both server directory (for shared modules like core/, app/)
# and agent-service directory (for local modules like agents/, config.py, mcp/)
ENV PYTHONPATH=/app/server:/app/server/agent-service

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application from agent-service directory
WORKDIR /app/server/agent-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]
