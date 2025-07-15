#!/bin/bash

# NVMe Stress Test Tool - Installation Script
# This script installs dependencies and sets up permissions for the NVMe stress test tool

echo "========================================="
echo "NVMe Stress Test Tool - Installation"
echo "========================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Please do not run this script as root. Run it as a regular user."
    echo "   The script will prompt for sudo when needed."
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install packages
install_package() {
    local package=$1
    echo "📦 Installing $package..."
    
    if sudo apt update && sudo apt install -y "$package"; then
        echo "✅ $package installed successfully"
    else
        echo "❌ Failed to install $package"
        exit 1
    fi
}

echo "🔍 Checking system requirements..."

# Check if apt is available (Debian/Ubuntu systems)
if ! command_exists apt; then
    echo "❌ This script is designed for Debian/Ubuntu systems with apt package manager"
    exit 1
fi

echo "📋 Installing required dependencies..."

# Install fio if not present
if ! command_exists fio; then
    install_package "fio"
else
    echo "✅ fio is already installed"
fi

# Install nvme-cli if not present
if ! command_exists nvme; then
    install_package "nvme-cli"
else
    echo "✅ nvme-cli is already installed"
fi

# Install Python3 and tkinter if not present
if ! command_exists python3; then
    install_package "python3"
else
    echo "✅ python3 is already installed"
fi

# Check for tkinter (required for GUI)
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "📦 Installing python3-tkinter for GUI support..."
    install_package "python3-tkinter"
else
    echo "✅ python3-tkinter is already available"
fi

# Install pip if not present
if ! command_exists pip3; then
    install_package "python3-pip"
else
    echo "✅ pip3 is already installed"
fi

# Install Python requirements if requirements.txt exists
if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
    echo "📦 Installing Python dependencies..."
    if pip3 install -r "$SCRIPT_DIR/requirements.txt"; then
        echo "✅ Python dependencies installed successfully"
    else
        echo "⚠️  Some Python dependencies may have failed to install"
        echo "   You can install them manually with: pip3 install -r requirements.txt"
    fi
else
    echo "ℹ️  No requirements.txt found, skipping Python dependencies"
fi

echo "🔧 Setting up file permissions..."

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Make all shell scripts executable
echo "📝 Making shell scripts executable..."
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true

# Verify shell scripts are executable
echo "🔍 Verifying shell script permissions..."
for script in "$SCRIPT_DIR"/*.sh; do
    if [[ -f "$script" ]]; then
        if [[ -x "$script" ]]; then
            echo "✅ $(basename "$script") is executable"
        else
            echo "❌ Failed to make $(basename "$script") executable"
        fi
    fi
done

# Make Python GUI script executable
if [[ -f "$SCRIPT_DIR/nvme_stress_gui.py" ]]; then
    chmod +x "$SCRIPT_DIR/nvme_stress_gui.py"
    echo "✅ nvme_stress_gui.py is executable"
fi

echo ""
echo "========================================="
echo "✅ Installation completed successfully!"
echo "========================================="
echo ""
echo "🚀 You can now use the NVMe stress test tool:"
echo "   • Run GUI: python3 nvme_stress_gui.py"
echo "   • Run CLI tests: ./test_all_drives.sh"
echo "   • Run parallel tests: ./parallel_test_all_drives.sh"
echo ""
echo "📖 For more information, check the README.md file"
echo ""
echo "⚠️  Note: NVMe operations require sudo privileges"
echo "   You will be prompted for your password when running tests"
echo ""
