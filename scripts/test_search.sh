#!/bin/bash

# Script to test Snowflake Cortex AI Search independently

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Testing Snowflake Cortex AI Search"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠ Warning: .env file not found"
    echo "Please create .env file with Snowflake configuration"
    echo ""
fi

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Optional: Set stage path
if [ -z "$SNOWFLAKE_STAGE_PATH" ]; then
    echo "ℹ Using default stage path: @my_stage"
    echo "Set SNOWFLAKE_STAGE_PATH environment variable to use a different stage"
    echo ""
fi

# Run the test
cd "$PROJECT_ROOT"
python tests/snowflake/test_search.py

