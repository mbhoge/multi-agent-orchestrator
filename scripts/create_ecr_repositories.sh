#!/bin/bash
#
# Create ECR Repositories for Multi-Agent Orchestrator
#
# This script creates ECR repositories for all services if they don't exist.
#
# Usage:
#   ./scripts/create_ecr_repositories.sh
#   ENVIRONMENT=prod ./scripts/create_ecr_repositories.sh
#   AWS_REGION=us-west-2 ./scripts/create_ecr_repositories.sh
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

# Services
SERVICES=(
    "aws-agent-core"
    "langgraph"
    "snowflake-cortex"
    "langfuse"
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

# Create ECR repository
create_repository() {
    local repo_name=$1
    
    print_info "Checking repository: $repo_name"
    
    if aws ecr describe-repositories \
        --repository-names "$repo_name" \
        --region "$AWS_REGION" \
        > /dev/null 2>&1; then
        print_success "Repository already exists: $repo_name"
        return 0
    fi
    
    print_info "Creating repository: $repo_name"
    
    if aws ecr create-repository \
        --repository-name "$repo_name" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256 \
        --image-tag-mutability MUTABLE \
        > /dev/null 2>&1; then
        print_success "Repository created: $repo_name"
        return 0
    else
        print_error "Failed to create repository: $repo_name"
        return 1
    fi
}

# Main function
main() {
    echo "============================================================"
    echo "  Create ECR Repositories"
    echo "============================================================"
    echo ""
    echo "Configuration:"
    echo "  Project: $PROJECT_NAME"
    echo "  Environment: $ENVIRONMENT"
    echo "  Region: $AWS_REGION"
    echo ""
    
    # Get AWS account ID
    print_info "Getting AWS account ID..."
    AWS_ACCOUNT_ID=$(get_aws_account_id)
    print_success "AWS Account ID: $AWS_ACCOUNT_ID"
    echo ""
    
    # Create repositories
    print_info "Creating ECR repositories..."
    echo ""
    
    local failed_repos=()
    
    for service in "${SERVICES[@]}"; do
        repo_name="${PROJECT_NAME}-${ENVIRONMENT}-${service}"
        
        if ! create_repository "$repo_name"; then
            failed_repos+=("$repo_name")
        fi
        echo ""
    done
    
    # Summary
    echo "============================================================"
    echo "  Summary"
    echo "============================================================"
    echo ""
    
    if [ ${#failed_repos[@]} -eq 0 ]; then
        print_success "All repositories created successfully!"
        echo ""
        echo "Repository URIs:"
        for service in "${SERVICES[@]}"; do
            repo_name="${PROJECT_NAME}-${ENVIRONMENT}-${service}"
            echo "  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$repo_name"
        done
    else
        print_error "Some repositories failed to create:"
        for repo in "${failed_repos[@]}"; do
            echo "  - $repo"
        done
        exit 1
    fi
    
    echo ""
    print_success "Done!"
}

# Run main function
main
