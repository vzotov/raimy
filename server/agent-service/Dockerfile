FROM python:3.11-slim

WORKDIR /app/server/agent-service

# Install system dependencies including curl for health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire server directory structure (needed for shared modules)
COPY ../.. /app/server

# Set PYTHONPATH to include server directory
ENV PYTHONPATH=/app/server

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application from agent-service directory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]
