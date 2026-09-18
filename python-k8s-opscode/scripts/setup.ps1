# Setup script for Opscode Platform (Windows)
# This script sets up the development environment

Write-Host "Setting up Opscode Platform..." -ForegroundColor Green

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "Python version: $pythonVersion"

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install development dependencies
Write-Host "Installing development dependencies..." -ForegroundColor Yellow
pip install ruff black mypy pytest pytest-asyncio pytest-cov pytest-mock

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment, run:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "To start the application, run:" -ForegroundColor Cyan
Write-Host "  make run"
Write-Host ""
Write-Host "To start with Docker Compose, run:" -ForegroundColor Cyan
Write-Host "  make docker-up"
