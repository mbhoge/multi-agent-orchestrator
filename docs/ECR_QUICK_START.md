# ECR Quick Start Guide

Quick reference for containerizing and pushing images to AWS ECR.

## Prerequisites

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Verify Docker is running
docker info
```

## Quick Steps

### 1. Create ECR Repositories (One-time setup)

```bash
./scripts/create_ecr_repositories.sh
```

Or manually:
```bash
ENVIRONMENT=dev AWS_REGION=us-east-1 ./scripts/create_ecr_repositories.sh
```

### 2. Build and Push All Images

```bash
./scripts/build_and_push_ecr.sh
```

Or with custom environment:
```bash
ENVIRONMENT=prod AWS_REGION=us-west-2 ./scripts/build_and_push_ecr.sh
```

## Manual Steps (Alternative)

### Step 1: Authenticate with ECR

```bash
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

### Step 2: Build Image

```bash
docker build -f docker/aws-agent-core/Dockerfile -t aws-agent-core:latest .
```

### Step 3: Tag Image

```bash
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/multi-agent-orchestrator-dev-aws-agent-core"
docker tag aws-agent-core:latest $ECR_URI:latest
```

### Step 4: Push Image

```bash
docker push $ECR_URI:latest
```

## Image URIs

After pushing, your images will be available at:

```
<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/multi-agent-orchestrator-<ENV>-<SERVICE>:<TAG>
```

Example:
```
123456789012.dkr.ecr.us-east-1.amazonaws.com/multi-agent-orchestrator-dev-aws-agent-core:latest
```

## Services

The following services are containerized:

1. **aws-agent-core** - Port 8080
2. **langgraph** - Port 8001
3. **snowflake-cortex** - Port 8002
4. **langfuse** - Port 3000

## Verify Images

```bash
# List all images in a repository
aws ecr list-images \
    --repository-name multi-agent-orchestrator-dev-aws-agent-core \
    --region us-east-1
```

## Troubleshooting

### Re-authenticate with ECR
```bash
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

### Check repository exists
```bash
aws ecr describe-repositories \
    --repository-names multi-agent-orchestrator-dev-aws-agent-core \
    --region us-east-1
```

For detailed instructions, see: [ECS_CONTAINERIZATION_GUIDE.md](./ECS_CONTAINERIZATION_GUIDE.md)
