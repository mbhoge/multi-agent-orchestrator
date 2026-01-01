#!/usr/bin/env python3
"""
AWS SDK Installation Script for Multi-Agent Orchestrator

This script installs and verifies the AWS SDK (Boto3) and related dependencies
required for AWS Agent Core SDK integration.

Prerequisites:
    - Python 3.11 or higher
    - pip package manager
    - Internet connection for downloading packages

Usage:
    python3 scripts/install_aws_sdk.py
    python3 scripts/install_aws_sdk.py --upgrade
    python3 scripts/install_aws_sdk.py --check-only
"""

import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import Optional, Tuple


# AWS SDK packages and their minimum versions
AWS_PACKAGES = {
    "boto3": "1.29.0",
    "botocore": "1.32.0",
}

# Optional but recommended packages
OPTIONAL_PACKAGES = {
    "awscli": "1.32.0",  # AWS CLI for manual testing
}


def check_python_version() -> bool:
    """Check if Python version is 3.11 or higher."""
    if sys.version_info < (3, 11):
        print(f"❌ Python 3.11+ required. Current version: {sys.version}")
        return False
    print(f"✓ Python version: {sys.version.split()[0]}")
    return True


def check_pip() -> bool:
    """Check if pip is available."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✓ pip available: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pip is not available. Please install pip first.")
        return False


def is_package_installed(package_name: str) -> Tuple[bool, Optional[str]]:
    """Check if a package is installed and return its version if available."""
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            return False, None

        # Try to get version
        try:
            module = importlib.import_module(package_name)
            version = getattr(module, "__version__", None)
            return True, version
        except ImportError:
            return False, None
    except Exception:
        return False, None


def install_package(package_name: str, version: Optional[str] = None, upgrade: bool = False) -> bool:
    """Install a Python package using pip."""
    package_spec = f"{package_name}=={version}" if version else package_name
    upgrade_flag = ["--upgrade"] if upgrade else []

    print(f"📦 Installing {package_spec}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_spec] + upgrade_flag,
            check=True,
            capture_output=True,
        )
        print(f"✓ Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}")
        print(f"Error: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        return False


def verify_installation(package_name: str, min_version: Optional[str] = None) -> bool:
    """Verify that a package is installed and optionally check version."""
    installed, version = is_package_installed(package_name)

    if not installed:
        print(f"❌ {package_name} is not installed")
        return False

    if version:
        print(f"✓ {package_name} is installed (version: {version})")
        if min_version:
            # Simple version comparison (basic check)
            try:
                from packaging import version as pkg_version
                if pkg_version.parse(version) < pkg_version.parse(min_version):
                    print(f"⚠️  Warning: {package_name} version {version} is below recommended {min_version}")
                    return False
            except ImportError:
                # If packaging is not available, skip version check
                pass
    else:
        print(f"✓ {package_name} is installed (version unknown)")

    return True


def test_aws_imports() -> bool:
    """Test if AWS SDK can be imported successfully."""
    print("\n🧪 Testing AWS SDK imports...")
    try:
        import boto3
        import botocore
        print("✓ boto3 imported successfully")
        print("✓ botocore imported successfully")

        # Test basic functionality
        session = boto3.Session()
        print(f"✓ Boto3 session created (region: {session.region_name or 'not configured'})")
        return True
    except ImportError as e:
        print(f"❌ Failed to import AWS SDK: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Warning: AWS SDK imported but error during testing: {e}")
        return False


def install_from_requirements(requirements_file: Path, upgrade: bool = False) -> bool:
    """Install packages from requirements.txt if it exists."""
    if not requirements_file.exists():
        print(f"⚠️  Requirements file not found: {requirements_file}")
        return False

    print(f"\n📦 Installing packages from {requirements_file}...")
    upgrade_flag = ["--upgrade"] if upgrade else []
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)] + upgrade_flag,
            check=True,
        )
        print("✓ Successfully installed packages from requirements.txt")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install from requirements.txt")
        print(f"Error: {e.stderr.decode() if e.stderr else 'Unknown error'}")
        return False


def main():
    """Main installation function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Install and verify AWS SDK (Boto3) for Multi-Agent Orchestrator"
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Upgrade packages if they are already installed",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check installation status without installing",
    )
    parser.add_argument(
        "--install-optional",
        action="store_true",
        help="Also install optional packages (AWS CLI)",
    )
    parser.add_argument(
        "--from-requirements",
        action="store_true",
        help="Install from requirements.txt instead of individual packages",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("AWS SDK Installation Script")
    print("=" * 60)
    print()

    # Check prerequisites
    if not check_python_version():
        sys.exit(1)

    if not check_pip():
        sys.exit(1)

    # Get project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    requirements_file = project_root / "requirements.txt"

    # If check-only mode, just verify installation
    if args.check_only:
        print("\n🔍 Checking installation status...\n")
        all_ok = True
        for package, min_version in AWS_PACKAGES.items():
            if not verify_installation(package, min_version):
                all_ok = False

        if args.install_optional:
            for package, min_version in OPTIONAL_PACKAGES.items():
                verify_installation(package, min_version)

        if all_ok:
            test_aws_imports()
            print("\n✓ All required packages are installed")
        else:
            print("\n❌ Some required packages are missing")
            sys.exit(1)
        return

    # Installation mode
    print("\n📦 Installing AWS SDK packages...\n")

    if args.from_requirements and requirements_file.exists():
        # Install from requirements.txt
        success = install_from_requirements(requirements_file, args.upgrade)
        if not success:
            print("\n⚠️  Falling back to individual package installation...\n")
            args.from_requirements = False

    if not args.from_requirements:
        # Install individual packages
        all_installed = True
        for package, min_version in AWS_PACKAGES.items():
            installed, version = is_package_installed(package)
            if installed and not args.upgrade:
                print(f"✓ {package} is already installed (version: {version})")
            else:
                if not install_package(package, min_version, args.upgrade):
                    all_installed = False

        if not all_installed:
            print("\n❌ Some packages failed to install")
            sys.exit(1)

        # Install optional packages if requested
        if args.install_optional:
            print("\n📦 Installing optional packages...\n")
            for package, min_version in OPTIONAL_PACKAGES.items():
                installed, version = is_package_installed(package)
                if installed and not args.upgrade:
                    print(f"✓ {package} is already installed (version: {version})")
                else:
                    install_package(package, min_version, args.upgrade)

    # Verify installation
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)
    print()

    all_verified = True
    for package, min_version in AWS_PACKAGES.items():
        if not verify_installation(package, min_version):
            all_verified = False

    if not all_verified:
        print("\n❌ Verification failed")
        sys.exit(1)

    # Test imports
    if not test_aws_imports():
        print("\n❌ Import test failed")
        sys.exit(1)

    # Success message
    print("\n" + "=" * 60)
    print("✅ AWS SDK Installation Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Configure AWS credentials (see AWS_SDK_SETUP.md)")
    print("2. Set up IAM permissions for AWS Agent Core")
    print("3. Verify AWS region support for Agent Core")
    print("4. Test AWS connection: aws sts get-caller-identity")
    print()


if __name__ == "__main__":
    main()
