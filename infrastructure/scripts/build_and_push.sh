#!/bin/bash

# Script to build and push Docker images to ECR

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: Unable to get AWS account ID"
    exit 1
fi

ECR_REPOS=(
    "aws-agent-core"
    "langgraph"
    "snowflake-cortex"
)

PROJECT_NAME="multi-agent-orchestrator"
ENVIRONMENT="${ENVIRONMENT:-dev}"

echo "Building and pushing Docker images to ECR..."
echo "Region: $AWS_REGION"
echo "Account: $AWS_ACCOUNT_ID"

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push each image
for repo in "${ECR_REPOS[@]}"; do
    ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-$repo"
    
    echo ""
    echo "Building $repo..."
    docker build -f docker/$repo/Dockerfile -t $repo:latest .
    
    echo "Tagging $repo..."
    docker tag $repo:latest $ECR_URI:latest
    
    echo "Pushing $repo to ECR..."
    docker push $ECR_URI:latest
    
    echo "$repo pushed successfully!"
done

echo ""
echo "All images pushed to ECR!"
echo ""
echo "ECR repository URLs:"
for repo in "${ECR_REPOS[@]}"; do
    echo "  - $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME-$ENVIRONMENT-$repo"
done

