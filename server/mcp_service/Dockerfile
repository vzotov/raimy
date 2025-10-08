FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server.py .

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose MCP server port (HTTP with Streamable HTTP transport)
EXPOSE 8002

# Health check for MCP server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/ || exit 1

# Run the MCP server with HTTP transport
CMD ["python", "server.py"]
