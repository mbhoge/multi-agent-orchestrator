# Project Setup Guide

## Quick Setup

### Option 1: Using the Setup Script (Recommended)

The `setup_project.py` script creates the entire project structure:

```bash
# Run the setup script
python3 setup_project.py

# Or specify a custom directory
python3 setup_project.py --project-dir my-project

# Open in VS Code automatically
python3 setup_project.py --open-vscode
```

### Option 2: Manual Setup

1. **Clone or copy the project:**
   ```bash
   git clone <repository-url> multi-agent-orchestrator
   # OR
   cp -r /path/to/existing/project multi-agent-orchestrator
   ```

2. **Run setup:**
   ```bash
   cd multi-agent-orchestrator
   ./scripts/setup_env.sh --dev
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Open in VS Code:**
   ```bash
   code .
   ```

## What the Setup Script Creates

The `setup_project.py` script creates:

✅ **Directory Structure**
- All package directories (aws_agent_core, langgraph, snowflake_cortex, etc.)
- Configuration directories
- Docker directories
- Infrastructure directories
- Test directories

✅ **Configuration Files**
- `.gitignore`
- `.env.example`
- `config/agents.yaml`
- `config/logging.yaml`
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`

✅ **Docker Files**
- `docker-compose.yml`
- All Dockerfiles

✅ **Scripts**
- `scripts/setup_env.sh`
- `scripts/run_local.sh`

✅ **VS Code Configuration**
- `.vscode/settings.json`
- `.vscode/extensions.json`
- `.vscode/launch.json`

✅ **Python Package Files**
- All `__init__.py` files

## Important Note

⚠️ **The setup script creates the project structure and configuration files, but NOT the Python source code files.**

You need to:

1. **Copy Python source files** from your existing project, OR
2. **Use git** to clone the complete repository, OR
3. **Manually create** the Python source files based on the architecture

## After Setup

Once the structure is created:

1. **Copy your Python source files:**
   ```bash
   # If you have an existing project
   cp -r /path/to/source/aws_agent_core/* ./aws_agent_core/
   cp -r /path/to/source/langgraph/* ./langgraph/
   # ... etc
   ```

2. **Install dependencies:**
   ```bash
   ./scripts/setup_env.sh --dev
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

4. **Test the setup:**
   ```bash
   # Check Python imports
   python3 -c "from aws_agent_core import MultiAgentOrchestrator; print('✓ Imports work')"
   
   # Run tests
   pytest tests/
   ```

5. **Start services:**
   ```bash
   ./scripts/run_local.sh
   ```

## VS Code Integration

The setup script creates VS Code configuration files:

- **`.vscode/settings.json`**: Python settings, formatters, linters
- **`.vscode/extensions.json`**: Recommended extensions
- **`.vscode/launch.json`**: Debug configurations for all services

### Recommended VS Code Extensions

The script recommends these extensions:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- isort (ms-python.isort)
- Docker (ms-azuretools.vscode-docker)
- YAML (redhat.vscode-yaml)
- Terraform (hashicorp.terraform)

Install them automatically when opening the project, or manually:
```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
# ... etc
```

## Troubleshooting

### Script Permission Denied
```bash
chmod +x setup_project.py
python3 setup_project.py
```

### VS Code Command Not Found
```bash
# Install VS Code command line tool
# On macOS: Cmd+Shift+P -> "Shell Command: Install 'code' command in PATH"
# On Linux: Add to PATH manually
# Then run: code .
```

### Python Not Found
```bash
# Ensure Python 3.11+ is installed
python3 --version

# If not installed:
# macOS: brew install python@3.11
# Ubuntu: sudo apt-get install python3.11
```

## Next Steps

1. ✅ Project structure created
2. ⬜ Copy Python source files
3. ⬜ Install dependencies
4. ⬜ Configure environment
5. ⬜ Run tests
6. ⬜ Start services

See `ARCHITECTURE.md` for detailed architecture and setup instructions.
