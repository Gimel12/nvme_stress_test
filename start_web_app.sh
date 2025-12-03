#!/bin/bash
# Start NVMe Stress Test Web Application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================"
echo "NVMe Stress Test - Web Application"
echo "======================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d "venv_web" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv_web
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
source venv_web/bin/activate

# Install/upgrade requirements
echo "📦 Installing/updating dependencies..."
pip install -q --upgrade pip
pip install -q -r web_requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✅ Dependencies installed successfully"
echo ""

# Make sure run_single_drive_test.sh is executable
if [ -f "run_single_drive_test.sh" ]; then
    chmod +x run_single_drive_test.sh
fi

# Start the web application
echo "🚀 Starting web application..."
echo ""
python3 web_app.py

# Deactivate virtual environment on exit
deactivate
