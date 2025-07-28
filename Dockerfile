# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Copy requirements first for better caching
COPY server/requirements.txt ./server/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy server code
COPY server/ ./server/

# Copy client code
COPY client/ ./client/

# Install client dependencies
WORKDIR /app/client
RUN npm ci --only=production

# Build the client
RUN npm run build

# Switch back to app directory
WORKDIR /app

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Starting Raimy Cooking Assistant..."\n\
cd /app/server\n\
python api.py &\n\
SERVER_PID=$!\n\
\n\
# Wait for server to start\n\
sleep 5\n\
\n\
# Keep container running\n\
wait $SERVER_PID\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 8000 3000

# Set environment variables
ENV PYTHONPATH=/app/server
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["/app/start.sh"] 