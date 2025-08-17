#!/bin/bash

# Video Transcription System Installation Script

echo "🎥 Video Transcription System Installation"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✓ Python $python_version is compatible"
else
    echo "✗ Python 3.8+ required, found $python_version"
    exit 1
fi

# Check for FFmpeg
echo "Checking for FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg is installed"
else
    echo "⚠️  FFmpeg not found. Please install it:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu: sudo apt install ffmpeg"
    echo "   Windows: Download from https://ffmpeg.org/"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if pip3 install -r requirements.txt; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Create configuration file
echo "Setting up configuration..."
if [ ! -f ".env" ]; then
    cp config.example.env .env
    echo "✓ Created .env configuration file"
    echo "  Edit .env to customize settings"
else
    echo "✓ Configuration file already exists"
fi

# Run initial setup
echo "Running initial setup..."
python3 main.py setup

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env to customize settings (optional)"
echo "2. Add a YouTube channel: python3 main.py add-channel <URL>"
echo "3. Start monitoring: python3 main.py start-monitoring"
echo ""
echo "For help: python3 main.py --help"
