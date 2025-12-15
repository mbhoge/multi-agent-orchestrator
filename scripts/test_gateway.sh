#!/bin/bash

# Script to test Snowflake Cortex AI Agent Gateway

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Testing Snowflake Cortex AI Agent Gateway"
echo "=========================================="
echo ""

# Check if gateway is running
GATEWAY_URL="http://localhost:8002"
if ! curl -s "$GATEWAY_URL/health" > /dev/null 2>&1; then
    echo "⚠ Gateway is not running!"
    echo ""
    echo "Please start the gateway first:"
    echo "  Option 1: python -m snowflake_cortex.gateway.api"
    echo "  Option 2: uvicorn snowflake_cortex.gateway.api:app --host 0.0.0.0 --port 8002"
    echo ""
    read -p "Do you want to start it now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting gateway in background..."
        cd "$PROJECT_ROOT"
        if [ -d "$PROJECT_ROOT/venv" ]; then
            source "$PROJECT_ROOT/venv/bin/activate"
        fi
        python -m snowflake_cortex.gateway.api &
        GATEWAY_PID=$!
        echo "Gateway started with PID: $GATEWAY_PID"
        echo "Waiting for gateway to be ready..."
        sleep 5
        echo ""
    else
        echo "Please start the gateway manually and run this script again"
        exit 1
    fi
fi

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Run the test
cd "$PROJECT_ROOT"
python tests/snowflake/test_gateway.py

# Cleanup if we started the gateway
if [ ! -z "$GATEWAY_PID" ]; then
    echo ""
    echo "Stopping gateway (PID: $GATEWAY_PID)..."
    kill $GATEWAY_PID 2>/dev/null || true
fi

