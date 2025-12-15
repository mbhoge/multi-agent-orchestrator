# Quick Start Guide - Create Project in VS Code

## 🚀 Fastest Way to Create the Project

### Option 1: Complete Setup (Recommended)

If you have an existing project to copy from:

```bash
# Create complete project from existing source
./create_full_project.sh my-new-project /path/to/existing/project

# This will:
# 1. Create project structure
# 2. Copy all source files
# 3. Open in VS Code
```

### Option 2: Structure Only

If you're starting fresh:

```bash
# Create project structure
python3 setup_project.py --project-dir my-project --open-vscode

# Then manually add your Python source files
```

### Option 3: Step by Step

```bash
# 1. Create structure
python3 setup_project.py --project-dir my-project

# 2. Copy files (if you have existing project)
python3 copy_project_files.py --source /path/to/source --dest my-project

# 3. Open in VS Code
cd my-project
code .
```

## 📋 What Gets Created

✅ **Complete Project Structure**
- All directories and packages
- Configuration files
- Docker setup
- VS Code configuration
- Scripts

✅ **VS Code Integration**
- Python settings
- Debug configurations
- Recommended extensions
- Formatting setup

## 🎯 After Setup

1. **Install dependencies:**
   ```bash
   cd my-project
   ./scripts/setup_env.sh --dev
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start services:**
   ```bash
   ./scripts/run_local.sh
   ```

## 📚 Documentation

- `SETUP_GUIDE.md` - Detailed setup instructions
- `ARCHITECTURE.md` - Complete architecture guide
- `README.md` - Project overview

## ⚡ Quick Commands

```bash
# Create project
python3 setup_project.py --open-vscode

# Copy from existing
python3 copy_project_files.py --source /old/project --dest /new/project

# Setup environment
./scripts/setup_env.sh --dev

# Run services
./scripts/run_local.sh

# Run tests
pytest tests/
```

## 🐛 Troubleshooting

**Permission denied:**
```bash
chmod +x *.sh *.py
```

**VS Code not opening:**
```bash
# Install VS Code command
# Then: code /path/to/project
```

**Python not found:**
```bash
# Ensure Python 3.11+ is installed
python3 --version
```
