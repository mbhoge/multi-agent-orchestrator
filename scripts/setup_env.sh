#!/bin/bash

# Setup script for multi-agent orchestrator project

set -e

echo "Setting up multi-agent orchestrator environment..."

# Create virtual environment
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

# Install development dependencies if requested
if [ "$1" == "--dev" ]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Create logs directory
mkdir -p logs

# Create necessary directories
mkdir -p config
mkdir -p infrastructure/terraform

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Configure Terraform backend in infrastructure/terraform/main.tf"
echo "3. Run 'docker-compose up' to start services locally"
echo "4. Or run 'terraform apply' to deploy to AWS"

