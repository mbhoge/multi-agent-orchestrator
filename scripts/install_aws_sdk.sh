#!/bin/bash
#
# AWS SDK Installation Script for Multi-Agent Orchestrator
#
# This shell script installs and verifies the AWS SDK (Boto3) and related
# dependencies required for AWS Agent Core SDK integration.
#
# Prerequisites:
#   - Python 3.11 or higher
#   - pip package manager
#   - Internet connection for downloading packages
#
# Usage:
#   ./scripts/install_aws_sdk.sh
#   ./scripts/install_aws_sdk.sh --upgrade
#   ./scripts/install_aws_sdk.sh --check-only
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"

# AWS SDK packages
BOTO3_VERSION="1.29.0"
BOTOCORE_VERSION="1.32.0"

# Flags
UPGRADE=false
CHECK_ONLY=false
INSTALL_OPTIONAL=false
FROM_REQUIREMENTS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --upgrade)
            UPGRADE=true
            shift
            ;;
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --install-optional)
            INSTALL_OPTIONAL=true
            shift
            ;;
        --from-requirements)
            FROM_REQUIREMENTS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --upgrade              Upgrade packages if already installed"
            echo "  --check-only           Only check installation status"
            echo "  --install-optional     Also install optional packages (AWS CLI)"
            echo "  --from-requirements    Install from requirements.txt"
            echo "  -h, --help             Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_info() {
    echo -e "${BLUE}📦${NC} $1"
}

# Check Python version
check_python_version() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        return 1
    fi

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        print_error "Python 3.11+ required. Current version: $PYTHON_VERSION"
        return 1
    fi

    print_success "Python version: $PYTHON_VERSION"
    return 0
}

# Check pip
check_pip() {
    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip is not available. Please install pip first."
        return 1
    fi

    PIP_VERSION=$(python3 -m pip --version | awk '{print $2}')
    print_success "pip available: $PIP_VERSION"
    return 0
}

# Check if package is installed
is_package_installed() {
    local package=$1
    python3 -c "import $package" 2>/dev/null
}

# Get package version
get_package_version() {
    local package=$1
    python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo ""
}

# Install package
install_package() {
    local package=$1
    local version=$2
    local upgrade_flag=""

    if [ "$UPGRADE" = true ]; then
        upgrade_flag="--upgrade"
    fi

    print_info "Installing ${package}==${version}..."
    if python3 -m pip install "${package}==${version}" $upgrade_flag --quiet; then
        print_success "Successfully installed $package"
        return 0
    else
        print_error "Failed to install $package"
        return 1
    fi
}

# Verify installation
verify_installation() {
    local package=$1
    local min_version=$2

    if is_package_installed "$package"; then
        local version=$(get_package_version "$package")
        if [ -n "$version" ]; then
            print_success "$package is installed (version: $version)"
        else
            print_success "$package is installed (version unknown)"
        fi
        return 0
    else
        print_error "$package is not installed"
        return 1
    fi
}

# Test AWS imports
test_aws_imports() {
    echo ""
    echo "🧪 Testing AWS SDK imports..."
    
    if python3 -c "
import boto3
import botocore
print('✓ boto3 imported successfully')
print('✓ botocore imported successfully')

# Test basic functionality
session = boto3.Session()
region = session.region_name or 'not configured'
print(f'✓ Boto3 session created (region: {region})')
" 2>/dev/null; then
        return 0
    else
        print_error "Failed to import or test AWS SDK"
        return 1
    fi
}

# Install from requirements.txt
install_from_requirements() {
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_warning "Requirements file not found: $REQUIREMENTS_FILE"
        return 1
    fi

    print_info "Installing packages from $REQUIREMENTS_FILE..."
    local upgrade_flag=""
    if [ "$UPGRADE" = true ]; then
        upgrade_flag="--upgrade"
    fi

    if python3 -m pip install -r "$REQUIREMENTS_FILE" $upgrade_flag; then
        print_success "Successfully installed packages from requirements.txt"
        return 0
    else
        print_error "Failed to install from requirements.txt"
        return 1
    fi
}

# Main function
main() {
    echo "============================================================"
    echo "AWS SDK Installation Script"
    echo "============================================================"
    echo ""

    # Check prerequisites
    if ! check_python_version; then
        exit 1
    fi

    if ! check_pip; then
        exit 1
    fi

    # Check-only mode
    if [ "$CHECK_ONLY" = true ]; then
        echo ""
        echo "🔍 Checking installation status..."
        echo ""

        all_ok=true
        if ! verify_installation "boto3" "$BOTO3_VERSION"; then
            all_ok=false
        fi
        if ! verify_installation "botocore" "$BOTOCORE_VERSION"; then
            all_ok=false
        fi

        if [ "$INSTALL_OPTIONAL" = true ]; then
            verify_installation "awscli" "1.32.0" || true
        fi

        if [ "$all_ok" = true ]; then
            test_aws_imports
            echo ""
            print_success "All required packages are installed"
        else
            echo ""
            print_error "Some required packages are missing"
            exit 1
        fi
        return
    fi

    # Installation mode
    echo ""
    echo "📦 Installing AWS SDK packages..."
    echo ""

    if [ "$FROM_REQUIREMENTS" = true ] && [ -f "$REQUIREMENTS_FILE" ]; then
        if ! install_from_requirements; then
            echo ""
            print_warning "Falling back to individual package installation..."
            echo ""
            FROM_REQUIREMENTS=false
        fi
    fi

    if [ "$FROM_REQUIREMENTS" = false ]; then
        # Install boto3
        if is_package_installed "boto3" && [ "$UPGRADE" = false ]; then
            local version=$(get_package_version "boto3")
            print_success "boto3 is already installed (version: $version)"
        else
            if ! install_package "boto3" "$BOTO3_VERSION"; then
                exit 1
            fi
        fi

        # Install botocore
        if is_package_installed "botocore" && [ "$UPGRADE" = false ]; then
            local version=$(get_package_version "botocore")
            print_success "botocore is already installed (version: $version)"
        else
            if ! install_package "botocore" "$BOTOCORE_VERSION"; then
                exit 1
            fi
        fi

        # Install optional packages
        if [ "$INSTALL_OPTIONAL" = true ]; then
            echo ""
            echo "📦 Installing optional packages..."
            echo ""
            if is_package_installed "awscli" && [ "$UPGRADE" = false ]; then
                local version=$(get_package_version "awscli")
                print_success "awscli is already installed (version: $version)"
            else
                install_package "awscli" "1.32.0" || true
            fi
        fi
    fi

    # Verify installation
    echo ""
    echo "============================================================"
    echo "Verification"
    echo "============================================================"
    echo ""

    all_verified=true
    if ! verify_installation "boto3" "$BOTO3_VERSION"; then
        all_verified=false
    fi
    if ! verify_installation "botocore" "$BOTOCORE_VERSION"; then
        all_verified=false
    fi

    if [ "$all_verified" = false ]; then
        echo ""
        print_error "Verification failed"
        exit 1
    fi

    # Test imports
    if ! test_aws_imports; then
        echo ""
        print_error "Import test failed"
        exit 1
    fi

    # Success message
    echo ""
    echo "============================================================"
    echo "✅ AWS SDK Installation Complete!"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "1. Configure AWS credentials (see AWS_SDK_SETUP.md)"
    echo "2. Set up IAM permissions for AWS Agent Core"
    echo "3. Verify AWS region support for Agent Core"
    echo "4. Test AWS connection: aws sts get-caller-identity"
    echo ""
}

# Run main function
main
