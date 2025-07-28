#!/bin/bash

# Development script for Raimy Cooking Assistant

set -e

echo "🚀 Starting Raimy Cooking Assistant in development mode..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOF
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# LiveKit (optional)
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
EOF
    echo "📝 Please update .env with your actual API keys"
fi

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping development servers..."
    kill $SERVER_PID $CLIENT_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start FastAPI server
echo "🔧 Starting FastAPI server..."
cd server
python api.py &
SERVER_PID=$!
cd ..

# Wait a moment for server to start
sleep 3

# Start Next.js client
echo "🎨 Starting Next.js client..."
cd client
npm run dev &
CLIENT_PID=$!
cd ..

echo "✅ Development servers started!"
echo "📱 FastAPI: http://localhost:8000"
echo "🌐 Next.js: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for background processes
wait 