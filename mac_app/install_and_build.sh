#!/bin/bash
#
# Dakota Content Generator - Mac App Build Script
# This script installs dependencies and builds the Mac app
#

set -e

echo "🚀 Dakota Content Generator - Mac App Builder"
echo "==========================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS"
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "   Install it with: brew install python3"
    exit 1
fi

# Get API keys from user
echo "📝 Please provide your API keys (they will be embedded in the app):"
echo ""

read -p "OpenAI API Key (sk-...): " OPENAI_KEY
read -p "Vector Store ID (vs_...): " VECTOR_STORE_ID  
read -p "Serper API Key: " SERPER_KEY

# Validate keys
if [[ -z "$OPENAI_KEY" || -z "$VECTOR_STORE_ID" || -z "$SERPER_KEY" ]]; then
    echo "❌ All API keys are required"
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Setting up build environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r ../requirements.txt

# Build the app
echo ""
echo "🔨 Building Mac app..."
python3 build_mac_app.py \
    --openai-key "$OPENAI_KEY" \
    --vector-store-id "$VECTOR_STORE_ID" \
    --serper-key "$SERPER_KEY" \
    --dmg

# Deactivate virtual environment
deactivate

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Your app is ready at: dist/Dakota Content Generator.app"
echo "💿 DMG installer at: dist/Dakota-Content-Generator.dmg"
echo ""
echo "To install:"
echo "1. Open the DMG file"
echo "2. Drag 'Dakota Content Generator' to your Applications folder"
echo "3. Launch from Applications"
echo ""
echo "Note: You may need to right-click and select 'Open' the first time"
echo "      due to macOS security settings."