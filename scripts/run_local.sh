#!/bin/bash

# Script to run the multi-agent orchestrator locally with Docker Compose

set -e

echo "Starting multi-agent orchestrator services locally..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please update .env with your configuration before continuing"
        exit 1
    else
        echo "Error: .env.example not found"
        exit 1
    fi
fi

# Build and start services
echo "Building and starting Docker containers..."
docker-compose up --build -d

echo ""
echo "Services started!"
echo ""
echo "Service endpoints:"
echo "  - AWS Agent Core API: http://localhost:8000"
echo "  - LangGraph Supervisor: http://localhost:8001"
echo "  - Snowflake Cortex Agent: http://localhost:8002"
echo "  - Langfuse: http://localhost:3000"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"

