#!/bin/bash
#
# Build and Push Docker Images to AWS ECR
#
# This script builds Docker images for all services and pushes them to ECR.
# It will create ECR repositories if they don't exist.
#
# Usage:
#   ./scripts/build_and_push_ecr.sh
#   ENVIRONMENT=prod ./scripts/build_and_push_ecr.sh
#   AWS_REGION=us-west-2 ./scripts/build_and_push_ecr.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PROJECT_NAME="multi-agent-orchestrator"

# Services to build and push
SERVICES=(
    "aws-agent-core"
    "langgraph"
    "snowflake-cortex"
    "langfuse"
)

# Dockerfile paths (matching actual directory structure)
declare -A DOCKERFILE_PATHS=(
    ["aws-agent-core"]="docker/aws-agent-core/Dockerfile"
    ["langgraph"]="docker/langgraph/Dockerfile"
    ["snowflake-cortex"]="docker/snowflake-cortex/Dockerfile"
    ["langfuse"]="docker/langfuse/Dockerfile"
)

# Port mappings for services
declare -A SERVICE_PORTS=(
    ["aws-agent-core"]="8000"
    ["langgraph"]="8001"
    ["snowflake-cortex"]="8002"
    ["langfuse"]="3000"
)

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Get AWS account ID
get_aws_account_id() {
    local account_id
    account_id=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    
    if [ -z "$account_id" ] || [ "$account_id" == "None" ]; then
        print_error "Unable to get AWS account ID. Please check your AWS credentials."
        exit 1
    fi
    
    echo "$account_id"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Create ECR repository if it doesn't exist
create_ecr_repository() {
    local repo_name=$1
    
    print_info "Checking ECR repository: $repo_name"
    
    if aws ecr describe-repositories \
        --repository-names "$repo_name" \
        --region "$AWS_REGION" \
        > /dev/null 2>&1; then
        print_success "Repository $repo_name already exists"
        return 0
    fi
    
    print_info "Creating ECR repository: $repo_name"
    
    if aws ecr create-repository \
        --repository-name "$repo_name" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256 \
        --image-tag-mutability MUTABLE \
        > /dev/null 2>&1; then
        print_success "Repository $repo_name created successfully"
    else
        print_error "Failed to create repository $repo_name"
        exit 1
    fi
}

# Authenticate Docker with ECR
authenticate_ecr() {
    print_info "Authenticating Docker with ECR..."
    
    if aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin \
        "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com" > /dev/null 2>&1; then
        print_success "Docker authenticated with ECR"
    else
        print_error "Failed to authenticate with ECR"
        exit 1
    fi
}

# Build Docker image
build_image() {
    local service=$1
    local dockerfile_path=${DOCKERFILE_PATHS[$service]}
    local image_tag="${service}:latest"
    
    if [ ! -f "$dockerfile_path" ]; then
        print_error "Dockerfile not found: $dockerfile_path"
        return 1
    fi
    
    print_info "Building image: $image_tag"
    print_info "Using Dockerfile: $dockerfile_path"
    
    if docker build \
        -f "$dockerfile_path" \
        -t "$image_tag" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        . > /tmp/docker-build-${service}.log 2>&1; then
        print_success "Image built successfully: $image_tag"
        return 0
    else
        print_error "Failed to build image: $image_tag"
        print_error "Build logs saved to: /tmp/docker-build-${service}.log"
        cat /tmp/docker-build-${service}.log
        return 1
    fi
}

# Tag image for ECR
tag_image() {
    local service=$1
    local repo_name=$2
    local ecr_uri="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name"
    local version_tag
    
    # Get version from git or use timestamp
    if git rev-parse --short HEAD > /dev/null 2>&1; then
        version_tag=$(git rev-parse --short HEAD)
    else
        version_tag=$(date +%Y%m%d-%H%M%S)
    fi
    
    print_info "Tagging image: ${service}:latest"
    
    # Tag as latest
    docker tag "${service}:latest" "${ecr_uri}:latest"
    print_success "Tagged: ${ecr_uri}:latest"
    
    # Tag with version
    docker tag "${service}:latest" "${ecr_uri}:${version_tag}"
    print_success "Tagged: ${ecr_uri}:${version_tag}"
    
    # Also tag with environment
    docker tag "${service}:latest" "${ecr_uri}:${ENVIRONMENT}"
    print_success "Tagged: ${ecr_uri}:${ENVIRONMENT}"
}

# Push image to ECR
push_image() {
    local repo_name=$1
    local ecr_uri="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name"
    local version_tag
    
    # Get version from git or use timestamp
    if git rev-parse --short HEAD > /dev/null 2>&1; then
        version_tag=$(git rev-parse --short HEAD)
    else
        version_tag=$(date +%Y%m%d-%H%M%S)
    fi
    
    print_info "Pushing image: $ecr_uri"
    
    # Push latest tag
    if docker push "${ecr_uri}:latest" > /tmp/docker-push-${repo_name}-latest.log 2>&1; then
        print_success "Pushed: ${ecr_uri}:latest"
    else
        print_error "Failed to push: ${ecr_uri}:latest"
        cat /tmp/docker-push-${repo_name}-latest.log
        return 1
    fi
    
    # Push version tag
    if docker push "${ecr_uri}:${version_tag}" > /tmp/docker-push-${repo_name}-${version_tag}.log 2>&1; then
        print_success "Pushed: ${ecr_uri}:${version_tag}"
    else
        print_warning "Failed to push version tag (non-critical)"
    fi
    
    # Push environment tag
    if docker push "${ecr_uri}:${ENVIRONMENT}" > /tmp/docker-push-${repo_name}-${ENVIRONMENT}.log 2>&1; then
        print_success "Pushed: ${ecr_uri}:${ENVIRONMENT}"
    else
        print_warning "Failed to push environment tag (non-critical)"
    fi
    
    return 0
}

# Main function
main() {
    echo "============================================================"
    echo "  Build and Push Docker Images to AWS ECR"
    echo "============================================================"
    echo ""
    echo "Configuration:"
    echo "  Project: $PROJECT_NAME"
    echo "  Environment: $ENVIRONMENT"
    echo "  Region: $AWS_REGION"
    echo ""
    
    # Pre-flight checks
    print_info "Running pre-flight checks..."
    check_docker
    
    # Get AWS account ID
    print_info "Getting AWS account ID..."
    AWS_ACCOUNT_ID=$(get_aws_account_id)
    print_success "AWS Account ID: $AWS_ACCOUNT_ID"
    echo ""
    
    # Create ECR repositories
    print_info "Setting up ECR repositories..."
    for service in "${SERVICES[@]}"; do
        repo_name="${PROJECT_NAME}-${ENVIRONMENT}-${service}"
        create_ecr_repository "$repo_name"
    done
    echo ""
    
    # Authenticate with ECR
    authenticate_ecr
    echo ""
    
    # Build, tag, and push images
    print_info "Building and pushing images..."
    echo ""
    
    local failed_services=()
    
    for service in "${SERVICES[@]}"; do
        repo_name="${PROJECT_NAME}-${ENVIRONMENT}-${service}"
        ecr_uri="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name"
        
        echo "------------------------------------------------------------"
        echo "Processing: $service"
        echo "------------------------------------------------------------"
        
        # Build image
        if ! build_image "$service"; then
            failed_services+=("$service")
            continue
        fi
        
        # Tag image
        tag_image "$service" "$repo_name"
        
        # Push image
        if ! push_image "$repo_name"; then
            failed_services+=("$service")
            continue
        fi
        
        echo ""
    done
    
    # Summary
    echo "============================================================"
    echo "  Summary"
    echo "============================================================"
    echo ""
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        print_success "All images built and pushed successfully!"
        echo ""
        echo "ECR Image URIs:"
        for service in "${SERVICES[@]}"; do
            repo_name="${PROJECT_NAME}-${ENVIRONMENT}-${service}"
            ecr_uri="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name"
            echo "  $service:"
            echo "    ${ecr_uri}:latest"
            echo "    ${ecr_uri}:${ENVIRONMENT}"
            if git rev-parse --short HEAD > /dev/null 2>&1; then
                echo "    ${ecr_uri}:$(git rev-parse --short HEAD)"
            fi
        done
    else
        print_error "Some services failed to build/push:"
        for service in "${failed_services[@]}"; do
            echo "  - $service"
        done
        exit 1
    fi
    
    echo ""
    print_success "Done!"
}

# Run main function
main
