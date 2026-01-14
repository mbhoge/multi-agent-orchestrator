# ECS Containerization and ECR Registration Guide

This guide provides step-by-step instructions to containerize the multi-agent orchestrator application and register Docker images in AWS ECR for deployment on ECS.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [ECR Repository Setup](#ecr-repository-setup)
3. [Building Docker Images](#building-docker-images)
4. [Pushing Images to ECR](#pushing-images-to-ecr)
5. [Verification](#verification)
6. [ECS Task Definition](#ecs-task-definition)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. AWS Account and Permissions

Ensure you have:
- AWS account with appropriate permissions
- AWS CLI installed and configured
- Docker installed and running
- Access to ECR repositories

### 2. Required AWS Permissions

Your IAM user/role needs:
- `ecr:CreateRepository`
- `ecr:DescribeRepositories`
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:GetDownloadUrlForLayer`
- `ecr:BatchGetImage`
- `ecr:PutImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`

### 3. Environment Variables

Set the following environment variables:

```bash
export AWS_REGION="us-east-1"  # Your AWS region
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ENVIRONMENT="dev"  # dev, staging, or prod
export PROJECT_NAME="multi-agent-orchestrator"
```

Or create a `.env.ecr` file:

```bash
AWS_REGION=us-east-1
ENVIRONMENT=dev
PROJECT_NAME=multi-agent-orchestrator
```

---

## ECR Repository Setup

### Step 1: Verify AWS Credentials

```bash
# Check AWS credentials
aws sts get-caller-identity

# Should output:
# {
#     "UserId": "...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-username"
# }
```

### Step 2: Get AWS Account ID

```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account ID: $AWS_ACCOUNT_ID"
```

### Step 3: Create ECR Repositories (if they don't exist)

The application has 4 main services that need separate ECR repositories:

1. **aws-agent-core** - AWS Agent Core orchestrator
2. **langgraph** - LangGraph supervisor
3. **snowflake-cortex** - Snowflake Cortex agents
4. **langfuse** - Langfuse observability service (optional)

#### Option A: Create Repositories Using AWS CLI

```bash
# Set variables
AWS_REGION="us-east-1"
ENVIRONMENT="dev"
PROJECT_NAME="multi-agent-orchestrator"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create repositories
for service in aws-agent-core langgraph snowflake-cortex langfuse; do
    REPO_NAME="${PROJECT_NAME}-${ENVIRONMENT}-${service}"
    
    echo "Creating ECR repository: $REPO_NAME"
    
    aws ecr create-repository \
        --repository-name "$REPO_NAME" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256 \
        --image-tag-mutability MUTABLE \
        || echo "Repository $REPO_NAME may already exist"
done
```

#### Option B: Use the Provided Script

```bash
# Make script executable
chmod +x scripts/create_ecr_repositories.sh

# Run the script
./scripts/create_ecr_repositories.sh
```

### Step 4: Verify Repositories

```bash
# List all repositories
aws ecr describe-repositories --region $AWS_REGION

# List repositories for this project
aws ecr describe-repositories \
    --region $AWS_REGION \
    --repository-names \
        multi-agent-orchestrator-dev-aws-agent-core \
        multi-agent-orchestrator-dev-langgraph \
        multi-agent-orchestrator-dev-snowflake-cortex \
        multi-agent-orchestrator-dev-langfuse
```

---

## Building Docker Images

### Step 1: Navigate to Project Root

```bash
cd /path/to/multi-agent-orchestrator
```

### Step 2: Build Images Locally (Optional - for testing)

```bash
# Build AWS Agent Core
docker build -f docker/aws-agent-core/Dockerfile -t aws-agent-core:latest .

# Build LangGraph
docker build -f docker/langgraph/Dockerfile -t langgraph:latest .

# Build Snowflake Cortex
docker build -f docker/snowflake-cortex/Dockerfile -t snowflake-cortex:latest .

# Build Langfuse (if needed)
docker build -f docker/langfuse/Dockerfile -t langfuse:latest .
```

### Step 3: Test Images Locally (Optional)

```bash
# Test AWS Agent Core
docker run -p 8000:8000 \
    -e AWS_REGION=us-east-1 \
    -e LANGGRAPH_ENDPOINT=http://localhost:8001 \
    aws-agent-core:latest

# Test LangGraph
docker run -p 8001:8001 \
    -e LANGFUSE_HOST=http://localhost:3000 \
    langgraph:latest
```

---

## Pushing Images to ECR

### Step 1: Authenticate Docker with ECR

```bash
# Get ECR login token
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

**Expected output:**
```
Login Succeeded
```

### Step 2: Tag Images for ECR

ECR requires images to be tagged with the full ECR repository URI.

```bash
# Set variables
AWS_REGION="us-east-1"
ENVIRONMENT="dev"
PROJECT_NAME="multi-agent-orchestrator"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Tag AWS Agent Core
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-aws-agent-core"
docker tag aws-agent-core:latest $ECR_URI:latest
docker tag aws-agent-core:latest $ECR_URI:$(git rev-parse --short HEAD)  # Git commit hash as version

# Tag LangGraph
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-langgraph"
docker tag langgraph:latest $ECR_URI:latest
docker tag langgraph:latest $ECR_URI:$(git rev-parse --short HEAD)

# Tag Snowflake Cortex
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-snowflake-cortex"
docker tag snowflake-cortex:latest $ECR_URI:latest
docker tag snowflake-cortex:latest $ECR_URI:$(git rev-parse --short HEAD)

# Tag Langfuse (if needed)
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-langfuse"
docker tag langfuse:latest $ECR_URI:latest
docker tag langfuse:latest $ECR_URI:$(git rev-parse --short HEAD)
```

### Step 3: Push Images to ECR

```bash
# Push AWS Agent Core
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-aws-agent-core"
docker push $ECR_URI:latest
docker push $ECR_URI:$(git rev-parse --short HEAD)

# Push LangGraph
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-langgraph"
docker push $ECR_URI:latest
docker push $ECR_URI:$(git rev-parse --short HEAD)

# Push Snowflake Cortex
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-snowflake-cortex"
docker push $ECR_URI:latest
docker push $ECR_URI:$(git rev-parse --short HEAD)

# Push Langfuse (if needed)
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-langfuse"
docker push $ECR_URI:latest
docker push $ECR_URI:$(git rev-parse --short HEAD)
```

### Step 4: Use Automated Build Script (Recommended)

```bash
# Make script executable
chmod +x scripts/build_and_push_ecr.sh

# Run the script
./scripts/build_and_push_ecr.sh

# Or with custom environment
ENVIRONMENT=prod ./scripts/build_and_push_ecr.sh
```

---

## Verification

### Step 1: List Images in ECR

```bash
# List images in AWS Agent Core repository
aws ecr list-images \
    --repository-name multi-agent-orchestrator-dev-aws-agent-core \
    --region $AWS_REGION

# List images in LangGraph repository
aws ecr list-images \
    --repository-name multi-agent-orchestrator-dev-langgraph \
    --region $AWS_REGION

# List images in Snowflake Cortex repository
aws ecr list-images \
    --repository-name multi-agent-orchestrator-dev-snowflake-cortex \
    --region $AWS_REGION
```

### Step 2: Get Image Details

```bash
# Get image details
aws ecr describe-images \
    --repository-name multi-agent-orchestrator-dev-aws-agent-core \
    --region $AWS_REGION \
    --image-ids imageTag=latest
```

### Step 3: Verify Image URI

The image URI format is:
```
<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/<REPOSITORY_NAME>:<TAG>
```

Example:
```
123456789012.dkr.ecr.us-east-1.amazonaws.com/multi-agent-orchestrator-dev-aws-agent-core:latest
```

---

## ECS Task Definition

After pushing images to ECR, you can use them in ECS task definitions.

### Example Task Definition (JSON)

```json
{
  "family": "multi-agent-orchestrator-aws-agent-core",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "aws-agent-core",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/multi-agent-orchestrator-dev-aws-agent-core:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        },
        {
          "name": "LANGGRAPH_ENDPOINT",
          "value": "http://langgraph:8001"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/multi-agent-orchestrator-dev-aws-agent-core",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Register Task Definition

```bash
aws ecs register-task-definition \
    --cli-input-json file://infrastructure/ecs/task-definitions/aws-agent-core.json \
    --region $AWS_REGION
```

---

## Complete Workflow Script

For convenience, use the provided script that automates all steps:

```bash
# Build and push all images
./scripts/build_and_push_ecr.sh

# This script will:
# 1. Verify AWS credentials
# 2. Get AWS account ID
# 3. Create ECR repositories (if they don't exist)
# 4. Authenticate Docker with ECR
# 5. Build all Docker images
# 6. Tag images with ECR URIs
# 7. Push images to ECR
# 8. Display image URIs
```

---

## Troubleshooting

### Issue: "Repository does not exist"

**Solution:**
```bash
# Create the repository first
aws ecr create-repository \
    --repository-name multi-agent-orchestrator-dev-aws-agent-core \
    --region us-east-1
```

### Issue: "no basic auth credentials"

**Solution:**
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

### Issue: "denied: Your authorization token has expired"

**Solution:**
ECR tokens expire after 12 hours. Re-authenticate:
```bash
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

### Issue: "Cannot connect to the Docker daemon"

**Solution:**
```bash
# Start Docker service
sudo systemctl start docker  # Linux
# Or ensure Docker Desktop is running (macOS/Windows)
```

### Issue: "Image build fails"

**Solution:**
```bash
# Check Dockerfile syntax
docker build -f docker/aws-agent-core/Dockerfile -t test-image .

# Check for missing files
ls -la requirements.txt
ls -la aws_agent_core/
```

### Issue: "Push fails with layer size error"

**Solution:**
ECR has a 10GB layer size limit. Optimize your Dockerfile:
```dockerfile
# Use multi-stage builds
# Remove unnecessary files
# Use .dockerignore
```

### Issue: "Permission denied"

**Solution:**
Check IAM permissions:
```bash
# Verify permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME

# Or check role permissions
aws iam list-attached-role-policies --role-name YOUR_ROLE_NAME
```

---

## Best Practices

### 1. Use Version Tags

Instead of only using `latest`, tag images with versions:

```bash
VERSION=$(git rev-parse --short HEAD)
docker tag aws-agent-core:latest $ECR_URI:$VERSION
docker push $ECR_URI:$VERSION
```

### 2. Enable Image Scanning

```bash
aws ecr put-image-scanning-configuration \
    --repository-name multi-agent-orchestrator-dev-aws-agent-core \
    --image-scanning-configuration scanOnPush=true \
    --region $AWS_REGION
```

### 3. Use .dockerignore

Create a `.dockerignore` file to exclude unnecessary files:

```
.git
.gitignore
.env
*.md
tests/
.vscode/
__pycache__/
*.pyc
```

### 4. Optimize Docker Images

- Use multi-stage builds
- Minimize layers
- Remove unnecessary packages
- Use specific base image tags

### 5. Automate with CI/CD

Consider setting up CI/CD pipelines (GitHub Actions, GitLab CI, etc.) to automatically build and push images on code changes.

---

## Quick Reference

### ECR Repository Naming Convention

```
<PROJECT_NAME>-<ENVIRONMENT>-<SERVICE_NAME>
```

Example:
- `multi-agent-orchestrator-dev-aws-agent-core`
- `multi-agent-orchestrator-prod-langgraph`

### Image URI Format

```
<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/<REPOSITORY_NAME>:<TAG>
```

### Common Commands

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# List repositories
aws ecr describe-repositories --region $AWS_REGION

# List images
aws ecr list-images --repository-name <REPO_NAME> --region $AWS_REGION

# Delete image
aws ecr batch-delete-image \
    --repository-name <REPO_NAME> \
    --image-ids imageTag=<TAG> \
    --region $AWS_REGION
```

---

## Next Steps

After successfully pushing images to ECR:

1. ✅ Create ECS task definitions using the ECR image URIs
2. ✅ Create ECS services
3. ✅ Configure load balancers
4. ✅ Set up CloudWatch logging
5. ✅ Configure auto-scaling
6. ✅ Set up CI/CD pipelines

For ECS deployment instructions, see:
- `docs/ECS_DEPLOYMENT_GUIDE.md` (if exists)
- `infrastructure/terraform/` for Terraform configurations

---

**Last Updated**: 2024  
**Maintained By**: Multi-Agent Orchestrator Team
