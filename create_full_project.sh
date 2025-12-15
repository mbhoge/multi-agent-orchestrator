#!/bin/bash
#
# Complete Project Creation Script for VS Code
#
# This script creates the entire multi-agent orchestrator project
# and opens it in VS Code.
#
# Usage:
#   ./create_full_project.sh [--project-dir DIR] [--source-dir DIR]
#

set -e

PROJECT_DIR="${1:-multi-agent-orchestrator}"
SOURCE_DIR="${2:-}"

echo "============================================================"
echo "Multi-Agent Orchestrator - Complete Project Setup"
echo "============================================================"
echo ""

# Step 1: Create project structure
echo "Step 1: Creating project structure..."
python3 setup_project.py --project-dir "$PROJECT_DIR"

# Step 2: Copy source files if source directory provided
if [ -n "$SOURCE_DIR" ] && [ -d "$SOURCE_DIR" ]; then
    echo ""
    echo "Step 2: Copying source files from $SOURCE_DIR..."
    python3 copy_project_files.py --source "$SOURCE_DIR" --dest "$PROJECT_DIR"
else
    echo ""
    echo "Step 2: Skipping source file copy (no source directory provided)"
    echo "        To copy files later, run:"
    echo "        python3 copy_project_files.py --source /path/to/source --dest $PROJECT_DIR"
fi

# Step 3: Open in VS Code
echo ""
echo "Step 3: Opening project in VS Code..."
cd "$PROJECT_DIR"
code .

echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Project location: $(pwd)"
echo ""
echo "Next steps:"
echo "1. Review the project structure in VS Code"
if [ -z "$SOURCE_DIR" ]; then
    echo "2. Copy your Python source files to the project"
fi
echo "3. Run: ./scripts/setup_env.sh --dev"
echo "4. Configure: cp .env.example .env && nano .env"
echo "5. Run: ./scripts/run_local.sh"
echo ""
