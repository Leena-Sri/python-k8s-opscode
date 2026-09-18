#!/bin/bash

# Run local development script for Opscode Platform
# This script starts the application with Docker Compose dependencies

set -e

echo "Starting Opscode Platform locally..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start Docker Compose services
echo "Starting Docker Compose services..."
docker-compose up -d postgres redis prometheus grafana

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://opscode:opscode@localhost:5432/opscode"
export REDIS_URL="redis://localhost:6379/0"
export ENVIRONMENT="development"
export REMEDIATION_DRY_RUN="true"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting Opscode application..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "Opscode Platform is running!"
echo "API: http://localhost:8000"
echo "Dashboard: Open dashboard/index.html in your browser"
echo "Grafana: http://localhost:3000 (admin/admin)"
echo "Prometheus: http://localhost:9090"
