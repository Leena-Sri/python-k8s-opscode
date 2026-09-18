#!/bin/bash

# Setup script for Opscode Platform
# This script sets up the development environment

set -e

echo "Setting up Opscode Platform..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
pip install ruff black mypy pytest pytest-asyncio pytest-cov pytest-mock

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the application, run:"
echo "  make run"
echo ""
echo "To start with Docker Compose, run:"
echo "  make docker-up"
