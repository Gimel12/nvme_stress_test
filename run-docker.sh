#!/bin/bash

# NVMe Stress Test - Docker Runner Script
# This script handles X11 forwarding and runs the containerized GUI application

echo "========================================="
echo "NVMe Stress Test - Docker Runner"
echo "========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Allow X11 forwarding for GUI
echo "🔧 Setting up X11 forwarding for GUI..."
xhost +local:docker

# Create results directory if it doesn't exist
mkdir -p results

echo "🐳 Building and starting the NVMe Stress Test container..."

# Use docker compose if available, otherwise docker-compose
if docker compose version &> /dev/null; then
    docker compose up --build
else
    docker-compose up --build
fi

echo ""
echo "🧹 Cleaning up X11 permissions..."
xhost -local:docker

echo "✅ Container stopped."
