#!/bin/bash

echo "🎥 Starting Complete Video Transcription System"
echo "==============================================="
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed"
    exit 1
fi

echo "✅ All dependencies found"
echo ""

# Install Python dependencies if needed
if [ ! -f "venv/bin/activate" ]; then
    echo "📦 Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "📦 Activating Python virtual environment..."
    source venv/bin/activate
fi

# Install Node.js dependencies if needed
if [ ! -d "web-ui/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd web-ui
    npm install
    cd ..
fi

echo ""
echo "🚀 Starting both API server and Web UI..."
echo ""
echo "API Server: http://localhost:8000"
echo "Web UI: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Start both servers in parallel
python3 start_api.py &
API_PID=$!

cd web-ui
npm run dev &
WEB_PID=$!

# Wait for both processes and clean up on exit
trap "echo ''; echo '🛑 Stopping servers...'; kill $API_PID $WEB_PID 2>/dev/null; exit" INT TERM

wait
