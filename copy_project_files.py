#!/usr/bin/env python3
"""
Copy Project Files Script

This script copies all Python source files and other project files
from an existing project directory to a new project directory.

Usage:
    python3 copy_project_files.py --source /path/to/source --dest /path/to/dest
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List, Set


class ProjectFileCopier:
    """Copies project files from source to destination."""
    
    # Files and directories to exclude
    EXCLUDE_PATTERNS: Set[str] = {
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.git',
        'venv',
        'env',
        '.venv',
        'node_modules',
        '.pytest_cache',
        '.coverage',
        'htmlcov',
        '.tox',
        'dist',
        'build',
        '*.egg-info',
        '.terraform',
        '*.tfstate',
        '*.tfstate.*',
        '.env',
        'logs',
        '*.log',
    }
    
    # Directories to copy
    COPY_DIRECTORIES: List[str] = [
        'aws_agent_core',
        'langgraph',
        'snowflake_cortex',
        'shared',
        'langfuse',
        'tests',
        'infrastructure',
    ]
    
    # Files to copy from root
    COPY_FILES: List[str] = [
        'README.md',
        'ARCHITECTURE.md',
        '__INIT__EXPLANATION.md',
        '__INIT__EXAMPLES.py',
        '__INIT__SUMMARY.md',
        'SETUP_GUIDE.md',
    ]
    
    def __init__(self, source_dir: str, dest_dir: str):
        self.source = Path(source_dir).resolve()
        self.dest = Path(dest_dir).resolve()
        
    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        path_str = str(path)
        name = path.name
        
        # Check exact matches
        if name in self.EXCLUDE_PATTERNS:
            return True
        
        # Check patterns
        for pattern in self.EXCLUDE_PATTERNS:
            if pattern.startswith('*') and path_str.endswith(pattern[1:]):
                return True
            if pattern in path_str:
                return True
        
        return False
    
    def copy_directory(self, source_dir: Path, dest_dir: Path):
        """Recursively copy a directory."""
        if not source_dir.exists():
            print(f"  ⚠ Source directory not found: {source_dir}")
            return
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        copied = 0
        for item in source_dir.rglob('*'):
            if item.is_dir():
                continue
            
            if self.should_exclude(item):
                continue
            
            # Calculate relative path
            rel_path = item.relative_to(source_dir)
            dest_path = dest_dir / rel_path
            
            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(item, dest_path)
            copied += 1
        
        print(f"  ✓ Copied {copied} files from {source_dir.name}")
    
    def copy_file(self, filename: str):
        """Copy a single file."""
        source_file = self.source / filename
        dest_file = self.dest / filename
        
        if not source_file.exists():
            print(f"  ⚠ File not found: {filename}")
            return
        
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, dest_file)
        print(f"  ✓ Copied: {filename}")
    
    def run(self):
        """Run the copy process."""
        if not self.source.exists():
            print(f"❌ Source directory does not exist: {self.source}")
            return False
        
        if not self.dest.exists():
            print(f"❌ Destination directory does not exist: {self.dest}")
            print(f"   Please run setup_project.py first to create the structure")
            return False
        
        print("=" * 60)
        print("Copying Project Files")
        print("=" * 60)
        print(f"\nSource: {self.source}")
        print(f"Destination: {self.dest}\n")
        
        # Copy directories
        print("Copying directories...")
        for directory in self.COPY_DIRECTORIES:
            source_dir = self.source / directory
            dest_dir = self.dest / directory
            self.copy_directory(source_dir, dest_dir)
        
        print("\nCopying files...")
        for filename in self.COPY_FILES:
            self.copy_file(filename)
        
        print("\n" + "=" * 60)
        print("Copy Complete!")
        print("=" * 60)
        print(f"\nFiles copied to: {self.dest}")
        print("\nNext steps:")
        print("1. Review copied files")
        print("2. Run: ./scripts/setup_env.sh --dev")
        print("3. Configure .env file")
        print("4. Run: ./scripts/run_local.sh")
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Copy project files from source to destination"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source project directory"
    )
    parser.add_argument(
        "--dest",
        required=True,
        help="Destination project directory"
    )
    
    args = parser.parse_args()
    
    copier = ProjectFileCopier(args.source, args.dest)
    success = copier.run()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
