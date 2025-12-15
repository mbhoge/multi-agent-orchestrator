# Project Setup Scripts - Complete Guide

## 📦 Available Scripts

### 1. `setup_project.py` - Create Project Structure

**Purpose:** Creates the complete project directory structure, configuration files, and VS Code setup.

**Usage:**
```bash
# Basic usage
python3 setup_project.py

# Custom directory
python3 setup_project.py --project-dir my-project

# Open in VS Code automatically
python3 setup_project.py --open-vscode
```

**What it creates:**
- ✅ All directory structure
- ✅ Configuration files (.gitignore, .env.example, config files)
- ✅ Docker files (docker-compose.yml, Dockerfiles)
- ✅ Requirements files
- ✅ Shell scripts (setup_env.sh, run_local.sh)
- ✅ VS Code configuration (.vscode/ folder)
- ✅ Python package __init__.py files
- ✅ pyproject.toml
- ✅ README.md

**What it does NOT create:**
- ❌ Python source code files (you need to add these)

---

### 2. `copy_project_files.py` - Copy Source Files

**Purpose:** Copies all Python source files from an existing project to a new project.

**Usage:**
```bash
python3 copy_project_files.py \
    --source /path/to/existing/project \
    --dest /path/to/new/project
```

**What it copies:**
- ✅ All Python files from aws_agent_core/
- ✅ All Python files from langgraph/
- ✅ All Python files from snowflake_cortex/
- ✅ All Python files from shared/
- ✅ All test files
- ✅ Documentation files
- ✅ Infrastructure files

**What it excludes:**
- ❌ __pycache__ directories
- ❌ .git directory
- ❌ venv directories
- ❌ .env files
- ❌ Log files
- ❌ Build artifacts

---

### 3. `create_full_project.sh` - Complete Setup

**Purpose:** Master script that combines structure creation and file copying, then opens in VS Code.

**Usage:**
```bash
# Create from existing project
./create_full_project.sh my-project /path/to/source

# Or just create structure
./create_full_project.sh my-project
```

**What it does:**
1. Runs `setup_project.py` to create structure
2. Runs `copy_project_files.py` to copy source files (if source provided)
3. Opens project in VS Code

---

## 🎯 Use Cases

### Use Case 1: Create New Project from Existing

```bash
# You have an existing project and want to create a copy
./create_full_project.sh new-project /path/to/existing/project
```

### Use Case 2: Create Fresh Project Structure

```bash
# You want to start fresh with just the structure
python3 setup_project.py --project-dir my-project --open-vscode
```

### Use Case 3: Copy Files to Existing Structure

```bash
# You already have the structure, just need to copy files
python3 copy_project_files.py \
    --source /old/project \
    --dest /new/project
```

---

## 📋 Step-by-Step Workflow

### Complete Setup (Recommended)

```bash
# 1. Create project structure
python3 setup_project.py --project-dir multi-agent-orchestrator

# 2. Copy source files (if you have existing project)
python3 copy_project_files.py \
    --source /home/mbhoge/multi-agent-orchestrator \
    --dest ./multi-agent-orchestrator

# 3. Open in VS Code
cd multi-agent-orchestrator
code .

# 4. Setup environment
./scripts/setup_env.sh --dev

# 5. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 6. Start services
./scripts/run_local.sh
```

### Quick Setup (One Command)

```bash
# If you have existing project
./create_full_project.sh my-project /path/to/source

# Then follow steps 4-6 above
```

---

## 🔧 Script Details

### `setup_project.py` Options

```bash
python3 setup_project.py [OPTIONS]

Options:
  --project-dir DIR    Project directory name (default: multi-agent-orchestrator)
  --open-vscode        Open project in VS Code after setup
  -h, --help          Show help message
```

### `copy_project_files.py` Options

```bash
python3 copy_project_files.py [OPTIONS]

Options:
  --source DIR        Source project directory (required)
  --dest DIR          Destination project directory (required)
  -h, --help          Show help message
```

### `create_full_project.sh` Usage

```bash
./create_full_project.sh [PROJECT_DIR] [SOURCE_DIR]

Arguments:
  PROJECT_DIR         Project directory name (default: multi-agent-orchestrator)
  SOURCE_DIR          Source directory to copy from (optional)
```

---

## 📁 Project Structure Created

```
multi-agent-orchestrator/
├── aws_agent_core/
│   ├── __init__.py
│   ├── api/
│   ├── observability/
│   ├── runtime/
│   └── orchestrator.py
├── langgraph/
│   ├── __init__.py
│   ├── memory/
│   ├── observability/
│   ├── reasoning/
│   ├── state/
│   └── supervisor.py
├── snowflake_cortex/
│   ├── __init__.py
│   ├── agents/
│   ├── gateway/
│   ├── observability/
│   ├── semantic_models/
│   └── tools/
├── shared/
│   ├── config/
│   ├── models/
│   └── utils/
├── langfuse/
├── config/
├── docker/
├── infrastructure/
├── scripts/
├── tests/
├── .vscode/          # VS Code configuration
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## ✅ Verification

After running the scripts, verify the setup:

```bash
# Check structure
ls -la multi-agent-orchestrator/

# Check Python imports (after copying source files)
cd multi-agent-orchestrator
python3 -c "from aws_agent_core import MultiAgentOrchestrator; print('✓ OK')"

# Check VS Code settings
cat .vscode/settings.json

# Check scripts are executable
ls -la scripts/*.sh
```

---

## 🐛 Troubleshooting

### Issue: Permission Denied

```bash
chmod +x setup_project.py
chmod +x copy_project_files.py
chmod +x create_full_project.sh
chmod +x scripts/*.sh
```

### Issue: Python Not Found

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Install if needed
# macOS: brew install python@3.11
# Ubuntu: sudo apt-get install python3.11
```

### Issue: VS Code Command Not Found

```bash
# Install VS Code command line tool
# macOS: Cmd+Shift+P -> "Shell Command: Install 'code' command in PATH"
# Linux: Add to PATH manually or use full path
```

### Issue: Source Files Not Copied

```bash
# Check source directory exists
ls -la /path/to/source

# Run copy manually
python3 copy_project_files.py --source /path/to/source --dest ./project
```

---

## 📚 Related Documentation

- `QUICK_START.md` - Quick reference guide
- `SETUP_GUIDE.md` - Detailed setup instructions
- `ARCHITECTURE.md` - Complete architecture documentation
- `README.md` - Project overview

---

## 💡 Tips

1. **Always run setup_project.py first** to create the structure
2. **Use copy_project_files.py** to copy from existing projects
3. **Use create_full_project.sh** for one-command setup
4. **Check .vscode/ folder** for VS Code integration
5. **Review .env.example** before creating .env
6. **Run scripts/setup_env.sh** to install dependencies

---

## 🎉 Success Checklist

- [ ] Project structure created
- [ ] Source files copied (if applicable)
- [ ] VS Code opened
- [ ] Dependencies installed (`./scripts/setup_env.sh --dev`)
- [ ] Environment configured (`.env` file created)
- [ ] Services can start (`./scripts/run_local.sh`)
- [ ] Tests can run (`pytest tests/`)

---

## 📞 Need Help?

1. Check the documentation files
2. Review error messages carefully
3. Verify all prerequisites are met
4. Check file permissions
5. Ensure Python 3.11+ is installed
