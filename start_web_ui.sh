#!/bin/bash

echo "🌐 Starting Video Transcription System Web UI"
echo "=============================================="
echo ""

# Check if we're in the right directory
if [ ! -d "web-ui" ]; then
    echo "❌ Error: web-ui directory not found"
    echo "Please run this script from the VideoTranscriptionmodel directory"
    exit 1
fi

# Navigate to web-ui directory
cd web-ui

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "🚀 Starting Next.js development server..."
echo "Web UI will be available at: http://localhost:3000"
echo "Press Ctrl+C to stop"
echo ""

# Start the development server
npm run dev
