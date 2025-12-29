#!/bin/bash
# Build Lambda deployment packages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAMBDA_DEPLOY_DIR="$PROJECT_ROOT/lambda_deployments"
LAMBDA_LAYER_DIR="$PROJECT_ROOT/lambda_layer"

echo "Building Lambda deployment packages..."

# Create directories
mkdir -p "$LAMBDA_DEPLOY_DIR"
mkdir -p "$LAMBDA_LAYER_DIR/python"

# Clean previous builds
rm -rf "$LAMBDA_DEPLOY_DIR"/*.zip
rm -rf "$LAMBDA_LAYER_DIR"/python/*

# Install dependencies to layer
echo "Installing dependencies to Lambda layer..."
pip install -r "$PROJECT_ROOT/requirements.txt" -t "$LAMBDA_LAYER_DIR/python/" --upgrade

# Create Lambda layer zip
echo "Creating Lambda layer zip..."
cd "$LAMBDA_LAYER_DIR"
zip -r "$PROJECT_ROOT/lambda_layer.zip" python/ -q
cd "$PROJECT_ROOT"

# Build individual Lambda function packages
build_lambda_function() {
    local handler_name=$1
    local handler_path=$2
    
    echo "Building $handler_name..."
    
    # Create temporary directory
    local temp_dir=$(mktemp -d)
    
    # Copy project code
    cp -r "$PROJECT_ROOT/aws_agent_core" "$temp_dir/"
    cp -r "$PROJECT_ROOT/shared" "$temp_dir/"
    cp -r "$PROJECT_ROOT/langfuse" "$temp_dir/"
    cp -r "$PROJECT_ROOT/teams_adapter" "$temp_dir/"
    cp -r "$PROJECT_ROOT/config" "$temp_dir/"
    
    # Copy only necessary files (not full dependencies - those are in layer)
    # Copy requirements.txt for reference
    cp "$PROJECT_ROOT/requirements.txt" "$temp_dir/"
    
    # Create zip
    cd "$temp_dir"
    zip -r "$LAMBDA_DEPLOY_DIR/${handler_name}.zip" . -q
    
    # Cleanup
    cd "$PROJECT_ROOT"
    rm -rf "$temp_dir"
    
    echo "Created $LAMBDA_DEPLOY_DIR/${handler_name}.zip"
}

# Build each handler
build_lambda_function "query_handler" "aws_agent_core.lambda_handlers.query_handler"
build_lambda_function "teams_webhook_handler" "aws_agent_core.lambda_handlers.teams_webhook_handler"
build_lambda_function "health_handler" "aws_agent_core.lambda_handlers.health_handler"
build_lambda_function "metrics_handler" "aws_agent_core.lambda_handlers.metrics_handler"

echo "Lambda packages built successfully!"
echo "Layer: $PROJECT_ROOT/lambda_layer.zip"
echo "Functions: $LAMBDA_DEPLOY_DIR/*.zip"

