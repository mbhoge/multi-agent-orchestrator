# Migration Guide: GitHub to Bitbucket

This guide outlines the changes needed to migrate the multi-agent-orchestrator project from GitHub to Bitbucket.

## Overview

The good news is that your project has minimal GitHub-specific dependencies, making the migration straightforward. Most changes are related to repository URLs, CI/CD workflows (if you add them), and documentation references.

## Required Changes

### 1. Git Remote URL

**Current (GitHub):**
```bash
git remote -v
origin  https://github.com/mbhoge/multi-agent-orchestrator.git
```

**Change to (Bitbucket):**
```bash
# Remove existing remote
git remote remove origin

# Add Bitbucket remote
git remote add origin https://bitbucket.org/mbhoge/multi-agent-orchestrator.git

# Or using SSH (recommended for Bitbucket)
git remote add origin git@bitbucket.org:mbhoge/multi-agent-orchestrator.git
```

**Commands:**
```bash
cd /home/mbhoge/multi-agent-orchestrator
git remote set-url origin https://bitbucket.org/mbhoge/multi-agent-orchestrator.git
# Or for SSH:
git remote set-url origin git@bitbucket.org:mbhoge/multi-agent-orchestrator.git
```

### 2. Repository URL Format Differences

| GitHub | Bitbucket |
|--------|-----------|
| `https://github.com/username/repo.git` | `https://bitbucket.org/username/repo.git` |
| `git@github.com:username/repo.git` | `git@bitbucket.org:username/repo.git` |

### 3. README.md Updates

**File:** `README.md`

Update any repository references:
- Line 258: "Fork the repository" → Update if Bitbucket uses different terminology
- Line 278: "open an issue on the repository" → Update URL to Bitbucket

**Example changes:**
```markdown
## Contributing

1. Fork the repository (Bitbucket: Create a branch)
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request (Bitbucket: Create a pull request)

## Support

For issues and questions, please open an issue on the [Bitbucket repository](https://bitbucket.org/mbhoge/multi-agent-orchestrator/issues).
```

### 4. CI/CD Workflows (If Added Later)

**GitHub Actions** (`.github/workflows/`) vs **Bitbucket Pipelines** (`bitbucket-pipelines.yml`)

If you plan to add CI/CD:

**GitHub Actions format:**
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest
```

**Bitbucket Pipelines format:**
```yaml
# bitbucket-pipelines.yml
image: python:3.11

pipelines:
  default:
    - step:
        name: Test
        caches:
          - pip
        script:
          - pip install -r requirements.txt
          - pip install -r requirements-dev.txt
          - pytest
```

### 5. Authentication & CLI Tools

**GitHub CLI (`gh`):**
```bash
gh repo create multi-agent-orchestrator --public
```

**Bitbucket CLI (`bb`):**
```bash
# Install Bitbucket CLI
pip install bitbucket-cli

# Or use Bitbucket REST API
curl -X POST https://api.bitbucket.org/2.0/repositories/mbhoge/multi-agent-orchestrator \
  -H "Authorization: Bearer YOUR_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{"scm": "git", "is_private": false}'
```

### 6. Webhooks & Integrations

If you have any webhooks or integrations configured:
- **GitHub webhooks**: `https://api.github.com/...`
- **Bitbucket webhooks**: `https://bitbucket.org/...` (different API structure)

Update any webhook URLs in:
- AWS Lambda functions
- External services
- Monitoring tools

### 7. Branch Protection Rules

**GitHub:**
- Settings → Branches → Branch protection rules

**Bitbucket:**
- Repository settings → Branch permissions
- Different UI but similar functionality

### 8. Issue Tracking

**GitHub Issues:**
- Built-in issue tracker
- URL: `https://github.com/username/repo/issues`

**Bitbucket Issues:**
- Also has built-in issue tracker
- URL: `https://bitbucket.org/username/repo/issues`
- Similar functionality, slightly different UI

### 9. Pull Requests vs Merge Requests

**Terminology:**
- GitHub: Pull Requests (PRs)
- Bitbucket: Pull Requests (also called PRs, but some teams call them Merge Requests)

No code changes needed, just terminology in documentation.

### 10. SSH Key Configuration

**GitHub SSH:**
```bash
ssh -T git@github.com
```

**Bitbucket SSH:**
```bash
ssh -T git@bitbucket.org
```

Ensure your SSH key is added to Bitbucket account settings.

## Migration Steps

### Step 1: Create Bitbucket Repository

1. Log in to Bitbucket
2. Click "Create repository"
3. Name: `multi-agent-orchestrator`
4. Choose public/private
5. **Do NOT initialize with README** (you already have one)
6. Copy the repository URL

### Step 2: Update Git Remote

```bash
cd /home/mbhoge/multi-agent-orchestrator

# Update remote URL
git remote set-url origin https://bitbucket.org/mbhoge/multi-agent-orchestrator.git

# Verify
git remote -v
```

### Step 3: Push to Bitbucket

```bash
# Push main branch
git push -u origin main

# If you have other branches
git push --all origin
git push --tags origin
```

### Step 4: Update Documentation

Update `README.md` with Bitbucket-specific references (see section 3 above).

### Step 5: Verify

1. Check repository on Bitbucket
2. Verify all files are present
3. Test cloning: `git clone https://bitbucket.org/mbhoge/multi-agent-orchestrator.git`

## No Changes Required

These aspects work the same on both platforms:

✅ **Git commands** - All standard git commands work identically  
✅ **Branching strategy** - Git branches work the same way  
✅ **Docker configurations** - No changes needed  
✅ **Terraform scripts** - No changes needed  
✅ **Python code** - No changes needed  
✅ **Docker Compose** - No changes needed  
✅ **Environment variables** - No changes needed  
✅ **Project structure** - No changes needed  

## Bitbucket-Specific Features to Consider

### 1. Bitbucket Pipelines (CI/CD)

If you want to add CI/CD, Bitbucket Pipelines uses YAML configuration:

```yaml
# bitbucket-pipelines.yml
image: python:3.11

definitions:
  services:
    docker:
      memory: 3072

pipelines:
  default:
    - step:
        name: Build and Test
        services:
          - docker
        script:
          - pip install -r requirements.txt
          - pip install -r requirements-dev.txt
          - pytest
    - step:
        name: Build Docker Images
        script:
          - docker build -t aws-agent-core:latest -f docker/aws-agent-core/Dockerfile .
```

### 2. Bitbucket App Passwords

For API access, Bitbucket uses App Passwords instead of Personal Access Tokens:
- Settings → Personal settings → App passwords
- Create app password with repository read/write permissions

### 3. Repository Settings

- **Access keys**: For deployment automation
- **Repository variables**: For CI/CD secrets
- **Deployments**: Built-in deployment tracking

## Quick Migration Script

Here's a script to automate the migration:

```bash
#!/bin/bash
# migrate-to-bitbucket.sh

set -e

BITBUCKET_USER="mbhoge"
REPO_NAME="multi-agent-orchestrator"
BITBUCKET_URL="https://bitbucket.org/${BITBUCKET_USER}/${REPO_NAME}.git"

echo "Migrating to Bitbucket..."
echo "Repository URL: ${BITBUCKET_URL}"

# Update remote
git remote set-url origin "${BITBUCKET_URL}"

# Verify
echo ""
echo "Current remotes:"
git remote -v

echo ""
echo "Ready to push! Run:"
echo "  git push -u origin main"
echo "  git push --all origin"
echo "  git push --tags origin"
```

## Troubleshooting

### Issue: Authentication failed
**Solution:** Use App Passwords for HTTPS or configure SSH keys for SSH

### Issue: Repository not found
**Solution:** Ensure repository is created on Bitbucket first

### Issue: Push rejected
**Solution:** Check branch permissions and ensure you have write access

## Summary

The migration from GitHub to Bitbucket is straightforward for this project because:

1. ✅ No GitHub Actions workflows in the project
2. ✅ No GitHub-specific API integrations
3. ✅ Standard Git operations work identically
4. ✅ All code and configurations are platform-agnostic

**Main changes:**
- Update git remote URL
- Update documentation references
- Consider Bitbucket Pipelines if adding CI/CD

The project will function identically on Bitbucket!
