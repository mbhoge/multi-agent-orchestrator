#!/usr/bin/env python3
"""
Multi-Agent Orchestrator Project Setup Script

This script creates the entire project structure in VS Code.
Run this script to set up a fresh copy of the multi-agent orchestrator project.

Usage:
    python3 setup_project.py [--project-dir PROJECT_DIR] [--open-vscode]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List


class ProjectSetup:
    """Sets up the multi-agent orchestrator project structure."""
    
    def __init__(self, project_dir: str = "multi-agent-orchestrator"):
        self.project_dir = Path(project_dir).resolve()
        self.files_created = 0
        self.dirs_created = 0
        
    def create_directory_structure(self):
        """Create all required directories."""
        directories = [
            # Main package directories
            "aws_agent_core/api",
            "langgraph/memory",
            "langgraph/observability",
            "langgraph/reasoning",
            "langgraph/state",
            "snowflake_cortex/agents",
            "snowflake_cortex/gateway",
            "snowflake_cortex/observability",
            "snowflake_cortex/semantic_models",
            # snowflake_cortex/tools removed (tools are Snowflake-managed via agent objects or tool_specs/tool_resources)
            "shared/config",
            "shared/models",
            "shared/utils",
            "langfuse",
            "config",
            "docker/aws-agent-core",
            "docker/langfuse",
            "docker/langgraph",
            "docker/snowflake-cortex",
            "scripts",
            "infrastructure/scripts",
            "infrastructure/terraform/ecr",
            "infrastructure/terraform/ecs",
            "infrastructure/terraform/iam",
            "infrastructure/terraform/networking",
            "tests/unit",
            "tests/integration",
            "tests/fixtures",
            "logs",
        ]
        
        print("Creating directory structure...")
        for directory in directories:
            dir_path = self.project_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.dirs_created += 1
            print(f"  ✓ Created: {directory}")
        
        print(f"\n✓ Created {self.dirs_created} directories\n")
    
    def create_file(self, file_path: str, content: str, executable: bool = False):
        """Create a file with content."""
        full_path = self.project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if executable:
            os.chmod(full_path, 0o755)
        
        self.files_created += 1
        return full_path
    
    def create_python_files(self):
        """Create all Python package __init__.py files."""
        init_files = [
            "aws_agent_core/__init__.py",
            "aws_agent_core/api/__init__.py",
            "langgraph/__init__.py",
            "langgraph/memory/__init__.py",
            "langgraph/observability/__init__.py",
            "langgraph/reasoning/__init__.py",
            "langgraph/state/__init__.py",
            "snowflake_cortex/__init__.py",
            "snowflake_cortex/agents/__init__.py",
            "snowflake_cortex/gateway/__init__.py",
            "snowflake_cortex/observability/__init__.py",
            "snowflake_cortex/semantic_models/__init__.py",
            # snowflake_cortex/tools/__init__.py removed
            "shared/__init__.py",
            "shared/config/__init__.py",
            "shared/models/__init__.py",
            "shared/utils/__init__.py",
            "langfuse/__init__.py",
            "scripts/__init__.py",
            "tests/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py",
            "tests/fixtures/__init__.py",
        ]
        
        print("Creating Python package files...")
        for init_file in init_files:
            content = f'"""Package initialization for {init_file.split("/")[0]}."""\n\n'
            self.create_file(init_file, content)
            print(f"  ✓ Created: {init_file}")
        print()
    
    def create_config_files(self):
        """Create configuration files."""
        print("Creating configuration files...")
        
        # .gitignore
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment variables
.env
.env.local
.env.*.local
.env.prod

# Logs
logs/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Terraform
.terraform/
*.tfstate
*.tfstate.*
.terraform.lock.hcl
terraform.tfvars
*.tfvars

# Docker
.dockerignore

# OS
.DS_Store
Thumbs.db

# Project specific
config/aws_credentials.json
*.pem
*.key
"""
        self.create_file(".gitignore", gitignore_content)
        
        # .env.example
        env_example_content = """# Multi-Agent Orchestrator Environment Configuration

# Application Settings
APP_NAME=multi-agent-orchestrator
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_SESSION_TOKEN=
AWS_BEDROCK_AGENT_CORE_RUNTIME_ENDPOINT=

# LangGraph Configuration
LANGGRAPH_ENDPOINT=http://langgraph:8001
LANGGRAPH_TIMEOUT=300
LANGGRAPH_ENABLE_MEMORY=true

# Langfuse Observability
LANGFUSE_HOST=http://langfuse:3000
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_PROJECT_ID=your-langfuse-project-id
LANGFUSE_DATABASE_URL=postgresql://langfuse:langfuse@postgres:5432/langfuse

# PostgreSQL for Langfuse
POSTGRES_USER=langfuse
POSTGRES_PASSWORD=langfuse
POSTGRES_DB=langfuse

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your-account-identifier
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=
SNOWFLAKE_CORTEX_AGENT_GATEWAY_ENDPOINT=http://snowflake-cortex:8002

# TruLens Observability
TRULENS_ENABLED=true
TRULENS_APP_ID=your-trulens-app-id
TRULENS_API_KEY=your-trulens-api-key
"""
        self.create_file(".env.example", env_example_content)
        
        # config/agents.yaml
        agents_yaml = """# Agent Configuration
# This file defines multiple Snowflake Cortex AI agents

agents:
  - name: cortex_analyst
    type: cortex_analyst
    description: "Cortex AI Analyst for structured data queries"
    enabled: true
    semantic_model: "default_semantic_model"
    config:
      max_query_timeout: 300
      enable_caching: true
  
  - name: cortex_search
    type: cortex_search
    description: "Cortex AI Search for unstructured data queries"
    enabled: true
    config:
      default_stage_path: "@my_stage"
      max_results: 10
      min_relevance_score: 0.5
  
  - name: cortex_combined
    type: cortex_combined
    description: "Combined agent using both Analyst and Search"
    enabled: true
    config:
      use_analyst_first: true
      combine_results: true

semantic_models:
  - name: default_semantic_model
    description: "Default semantic model for SQL generation"
    location: "snowflake://semantic_models/default.yaml"
    version: "1.0"
"""
        self.create_file("config/agents.yaml", agents_yaml)
        
        # config/logging.yaml
        logging_yaml = """version: 1
disable_existing_loggers: false

formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: logs/multi-agent-orchestrator.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    encoding: utf8

loggers:
  aws_agent_core:
    level: INFO
    handlers: [console, file]
    propagate: false
  
  langgraph:
    level: INFO
    handlers: [console, file]
    propagate: false
  
  snowflake_cortex:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
"""
        self.create_file("config/logging.yaml", logging_yaml)
        
        print(f"  ✓ Created configuration files\n")
    
    def create_requirements_files(self):
        """Create requirements files."""
        print("Creating requirements files...")
        
        requirements = """# Core dependencies
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0

# AWS SDK
boto3==1.29.7
botocore==1.32.7

# HTTP client
httpx==0.25.2

# LangGraph (when available, using placeholder)
# langgraph==0.0.1  # Update when official package is available

# Langfuse
langfuse==2.0.0

# Snowflake
snowflake-connector-python==3.7.0
snowflake-snowpark-python==1.9.0

# TruLens
trulens-eval==0.18.0

# Utilities
pyyaml==6.0.1
python-multipart==0.0.6

# Logging
structlog==23.2.0
"""
        self.create_file("requirements.txt", requirements)
        
        requirements_dev = """# Development dependencies
-r requirements.txt

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code quality
black==23.11.0
flake8==6.1.0
mypy==1.7.1
isort==5.12.0

# Type stubs
types-pyyaml==6.0.12.11
types-python-dateutil==2.8.19.14
"""
        self.create_file("requirements-dev.txt", requirements_dev)
        
        print(f"  ✓ Created requirements files\n")
    
    def create_docker_files(self):
        """Create Docker configuration files."""
        print("Creating Docker files...")
        
        # docker-compose.yml
        docker_compose = """version: '3.8'

services:
  aws-agent-core:
    build:
      context: .
      dockerfile: docker/aws-agent-core/Dockerfile
    container_name: aws-agent-core
    ports:
      - "8080:8080"
    environment:
      - AWS_REGION=${AWS_REGION:-us-east-1}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    env_file:
      - .env
    networks:
      - orchestrator-network
    restart: unless-stopped

  langgraph:
    build:
      context: .
      dockerfile: docker/langgraph/Dockerfile
    container_name: langgraph-supervisor
    ports:
      - "8001:8001"
    environment:
      - LANGFUSE_HOST=http://langfuse:3000
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - LANGFUSE_PROJECT_ID=${LANGFUSE_PROJECT_ID}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    env_file:
      - .env
    depends_on:
      - langfuse
      - snowflake-cortex
    networks:
      - orchestrator-network
    restart: unless-stopped

  snowflake-cortex:
    build:
      context: .
      dockerfile: docker/snowflake-cortex/Dockerfile
    container_name: snowflake-cortex-agent
    ports:
      - "8002:8002"
    environment:
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
      - SNOWFLAKE_USER=${SNOWFLAKE_USER}
      - SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}
      - SNOWFLAKE_WAREHOUSE=${SNOWFLAKE_WAREHOUSE}
      - SNOWFLAKE_DATABASE=${SNOWFLAKE_DATABASE}
      - SNOWFLAKE_SCHEMA=${SNOWFLAKE_SCHEMA:-PUBLIC}
      - TRULENS_ENABLED=${TRULENS_ENABLED:-true}
      - TRULENS_APP_ID=${TRULENS_APP_ID}
      - TRULENS_API_KEY=${TRULENS_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    env_file:
      - .env
    networks:
      - orchestrator-network
    restart: unless-stopped

  langfuse:
    build:
      context: .
      dockerfile: docker/langfuse/Dockerfile
    container_name: langfuse
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=${LANGFUSE_DATABASE_URL:-postgresql://langfuse:langfuse@postgres:5432/langfuse}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
    env_file:
      - .env
    depends_on:
      - postgres
    networks:
      - orchestrator-network
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: langfuse-postgres
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-langfuse}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-langfuse}
      - POSTGRES_DB=${POSTGRES_DB:-langfuse}
    volumes:
      - langfuse-db-data:/var/lib/postgresql/data
    networks:
      - orchestrator-network
    restart: unless-stopped

networks:
  orchestrator-network:
    driver: bridge

volumes:
  langfuse-db-data:
"""
        self.create_file("docker-compose.yml", docker_compose)
        
        # Dockerfiles
        dockerfiles = {
            "docker/aws-agent-core/Dockerfile": """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "-m", "aws_agent_core.api"]
""",
            "docker/langgraph/Dockerfile": """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "-m", "langgraph"]
""",
            "docker/snowflake-cortex/Dockerfile": """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8002

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "-m", "snowflake_cortex.gateway"]
""",
            "docker/langfuse/Dockerfile": """# Langfuse Dockerfile
# This uses the official Langfuse Docker image
FROM langfuse/langfuse:latest

# Expose Langfuse port
EXPOSE 3000

# Langfuse configuration is handled via environment variables
# See Langfuse documentation for configuration options
""",
        }
        
        for file_path, content in dockerfiles.items():
            self.create_file(file_path, content)
        
        print(f"  ✓ Created Docker files\n")
    
    def create_scripts(self):
        """Create shell scripts."""
        print("Creating shell scripts...")
        
        setup_env = """#!/bin/bash

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
"""
        self.create_file("scripts/setup_env.sh", setup_env, executable=True)
        
        run_local = """#!/bin/bash

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
"""
        self.create_file("scripts/run_local.sh", run_local, executable=True)
        
        print(f"  ✓ Created shell scripts\n")
    
    def create_pyproject_toml(self):
        """Create pyproject.toml."""
        print("Creating pyproject.toml...")
        
        pyproject = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "multi-agent-orchestrator"
version = "1.0.0"
description = "Multi-agent orchestrator with AWS Agent Core, LangGraph, and Snowflake Cortex AI"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "pytest-cov>=4.1.0",
    "black>=23.11.0",
    "flake8>=6.1.0",
    "mypy>=1.7.1",
    "isort>=5.12.0",
]

[tool.black]
line-length = 100
target-version = ['py311']
include = '\\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
"""
        self.create_file("pyproject.toml", pyproject)
        print(f"  ✓ Created pyproject.toml\n")
    
    def create_vscode_settings(self):
        """Create VS Code settings."""
        print("Creating VS Code settings...")
        
        vscode_dir = self.project_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        settings_json = """{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": true,
        "editor.rulers": [100]
    },
    "[yaml]": {
        "editor.defaultFormatter": "redhat.vscode-yaml"
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true
    },
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ]
}
"""
        self.create_file(".vscode/settings.json", settings_json)
        
        extensions_json = """{
    "recommendations": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-python.black-formatter",
        "ms-python.isort",
        "ms-azuretools.vscode-docker",
        "redhat.vscode-yaml",
        "hashicorp.terraform"
    ]
}
"""
        self.create_file(".vscode/extensions.json", extensions_json)
        
        launch_json = """{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "AWS Agent Core API",
            "type": "python",
            "request": "launch",
            "module": "aws_agent_core.api",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "LangGraph Supervisor",
            "type": "python",
            "request": "launch",
            "module": "langgraph",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "Snowflake Cortex Gateway",
            "type": "python",
            "request": "launch",
            "module": "snowflake_cortex.gateway",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
"""
        self.create_file(".vscode/launch.json", launch_json)
        
        print(f"  ✓ Created VS Code configuration\n")
    
    def create_readme(self):
        """Create README.md."""
        print("Creating README.md...")
        
        readme = """# Multi-Agent Orchestrator

A containerized multi-agent orchestrator system built with AWS Agent Core, LangGraph, and Snowflake Cortex AI agents.

## Quick Start

1. **Setup environment:**
   ```bash
   ./scripts/setup_env.sh --dev
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run locally:**
   ```bash
   ./scripts/run_local.sh
   ```

## Project Structure

See `ARCHITECTURE.md` for detailed architecture documentation.

## Documentation

- `ARCHITECTURE.md` - Complete architecture and setup guide
- `__INIT__EXPLANATION.md` - Python package structure explanation
- `__INIT__EXAMPLES.py` - Code examples for package imports

## License

MIT License
"""
        self.create_file("README.md", readme)
        print(f"  ✓ Created README.md\n")
    
    def setup_git(self):
        """Initialize git repository if not already initialized."""
        if (self.project_dir / ".git").exists():
            print("Git repository already exists, skipping initialization.\n")
            return
        
        print("Initializing git repository...")
        try:
            subprocess.run(
                ["git", "init"],
                cwd=self.project_dir,
                check=True,
                capture_output=True
            )
            print("  ✓ Git repository initialized\n")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  ⚠ Git not available, skipping git initialization\n")
    
    def open_in_vscode(self):
        """Open project in VS Code."""
        print("Opening project in VS Code...")
        try:
            subprocess.run(
                ["code", str(self.project_dir)],
                check=False
            )
            print("  ✓ Opened in VS Code\n")
        except FileNotFoundError:
            print("  ⚠ VS Code 'code' command not found")
            print(f"  Please open manually: code {self.project_dir}\n")
    
    def run(self, open_vscode: bool = False):
        """Run the complete setup process."""
        print("=" * 60)
        print("Multi-Agent Orchestrator Project Setup")
        print("=" * 60)
        print(f"\nProject directory: {self.project_dir}\n")
        
        if self.project_dir.exists() and any(self.project_dir.iterdir()):
            response = input(
                f"Directory {self.project_dir} already exists and is not empty.\n"
                "Continue anyway? (y/N): "
            )
            if response.lower() != 'y':
                print("Setup cancelled.")
                return
        
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.create_directory_structure()
            self.create_python_files()
            self.create_config_files()
            self.create_requirements_files()
            self.create_docker_files()
            self.create_scripts()
            self.create_pyproject_toml()
            self.create_vscode_settings()
            self.create_readme()
            self.setup_git()
            
            print("=" * 60)
            print("Setup Complete!")
            print("=" * 60)
            print(f"\n✓ Created {self.dirs_created} directories")
            print(f"✓ Created {self.files_created} files")
            print(f"\nProject location: {self.project_dir}")
            print("\nNext steps:")
            print("1. Copy your Python source files to the project")
            print("2. Run: ./scripts/setup_env.sh --dev")
            print("3. Configure .env file")
            print("4. Run: ./scripts/run_local.sh")
            
            if open_vscode:
                self.open_in_vscode()
            else:
                print(f"\nTo open in VS Code: code {self.project_dir}")
            
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup Multi-Agent Orchestrator project structure"
    )
    parser.add_argument(
        "--project-dir",
        default="multi-agent-orchestrator",
        help="Project directory name (default: multi-agent-orchestrator)"
    )
    parser.add_argument(
        "--open-vscode",
        action="store_true",
        help="Open project in VS Code after setup"
    )
    
    args = parser.parse_args()
    
    setup = ProjectSetup(project_dir=args.project_dir)
    setup.run(open_vscode=args.open_vscode)


if __name__ == "__main__":
    main()
