#!/usr/bin/env python3
"""
Demonstration Script: How __pycache__ is Created

This script demonstrates how Python creates __pycache__ directories
and .pyc files automatically.

Run this script to see __pycache__ creation in action.
"""

import os
import sys
import time
import importlib
from pathlib import Path


def demonstrate_pycache_creation():
    """Demonstrate how __pycache__ is created."""
    
    print("=" * 60)
    print("__pycache__ Creation Demonstration")
    print("=" * 60)
    print()
    
    # Create a demo module
    demo_dir = Path("demo_pycache_test")
    demo_dir.mkdir(exist_ok=True)
    
    demo_module = demo_dir / "demo_module.py"
    demo_module.write_text('''"""Demo module to show __pycache__ creation."""

def hello():
    """Say hello."""
    print("Hello from demo_module!")

def calculate(x, y):
    """Calculate sum."""
    return x + y

VALUE = 42
''')
    
    print("1. Created demo module:")
    print(f"   {demo_module}")
    print()
    
    # Check if __pycache__ exists before import
    cache_dir = demo_dir / "__pycache__"
    print("2. Before importing module:")
    if cache_dir.exists():
        print(f"   ❌ __pycache__ already exists: {cache_dir}")
        print("   (Cleaning up first...)")
        import shutil
        shutil.rmtree(cache_dir)
    else:
        print(f"   ✓ __pycache__ does NOT exist yet")
    print()
    
    # Add to path and import
    sys.path.insert(0, str(demo_dir.parent))
    
    print("3. Importing module...")
    print("   import demo_pycache_test.demo_module")
    time.sleep(0.5)  # Small delay to show the process
    
    import demo_pycache_test.demo_module as demo
    
    print("   ✓ Module imported successfully")
    print()
    
    # Check if __pycache__ was created
    print("4. After importing module:")
    if cache_dir.exists():
        print(f"   ✓ __pycache__ was created: {cache_dir}")
        
        # List contents
        pyc_files = list(cache_dir.glob("*.pyc"))
        if pyc_files:
            print(f"   ✓ Found {len(pyc_files)} .pyc file(s):")
            for pyc_file in pyc_files:
                size = pyc_file.stat().st_size
                mtime = time.ctime(pyc_file.stat().st_mtime)
                print(f"     - {pyc_file.name} ({size} bytes, created: {mtime})")
        else:
            print("   ⚠ No .pyc files found (might be .pyc files)")
    else:
        print(f"   ❌ __pycache__ was NOT created")
    print()
    
    # Show the naming convention
    print("5. Understanding the filename:")
    if pyc_files:
        filename = pyc_files[0].name
        print(f"   Filename: {filename}")
        parts = filename.replace('.pyc', '').split('.')
        if len(parts) >= 2:
            module_name = parts[0]
            implementation = parts[1]
            version = parts[2] if len(parts) > 2 else "unknown"
            print(f"   - Module: {module_name}")
            print(f"   - Implementation: {implementation}")
            print(f"   - Version: {version}")
            print(f"   Format: {{module}}.{{implementation}}-{{version}}.pyc")
    print()
    
    # Demonstrate cache usage
    print("6. Demonstrating cache usage:")
    print("   Importing again (should use cache)...")
    start_time = time.time()
    importlib.reload(demo)
    end_time = time.time()
    print(f"   ✓ Reloaded in {(end_time - start_time)*1000:.2f}ms (uses cache)")
    print()
    
    # Show modification time comparison
    print("7. Cache validation:")
    source_mtime = demo_module.stat().st_mtime
    if pyc_files:
        cache_mtime = pyc_files[0].stat().st_mtime
        if cache_mtime >= source_mtime:
            print("   ✓ Cache is up-to-date (cache is newer or same as source)")
        else:
            print("   ⚠ Cache is stale (source is newer)")
            print("   Python will recompile on next import")
    print()
    
    # Cleanup option
    print("8. Cleanup:")
    response = input("   Delete demo files? (y/N): ")
    if response.lower() == 'y':
        import shutil
        shutil.rmtree(demo_dir)
        print("   ✓ Demo files deleted")
    else:
        print(f"   Demo files kept in: {demo_dir}")
        print("   You can delete manually: rm -rf demo_pycache_test")
    print()
    
    print("=" * 60)
    print("Demonstration Complete!")
    print("=" * 60)
    print()
    print("Key Takeaways:")
    print("  ✓ __pycache__ is created automatically on import")
    print("  ✓ .pyc files contain compiled bytecode")
    print("  ✓ Cache speeds up subsequent imports")
    print("  ✓ Python validates cache freshness automatically")
    print()


def show_project_pycache():
    """Show __pycache__ directories in the current project."""
    
    print("=" * 60)
    print("Finding __pycache__ in Current Project")
    print("=" * 60)
    print()
    
    project_root = Path(".")
    cache_dirs = list(project_root.rglob("__pycache__"))
    
    if cache_dirs:
        print(f"Found {len(cache_dirs)} __pycache__ directory(ies):")
        print()
        for cache_dir in sorted(cache_dirs):
            rel_path = cache_dir.relative_to(project_root)
            pyc_files = list(cache_dir.glob("*.pyc"))
            print(f"  {rel_path}/")
            if pyc_files:
                for pyc_file in sorted(pyc_files):
                    size = pyc_file.stat().st_size
                    print(f"    - {pyc_file.name} ({size} bytes)")
            else:
                print("    (empty)")
            print()
    else:
        print("  No __pycache__ directories found.")
        print("  (This is normal if you haven't run any Python code yet)")
        print()
    
    print("Note: These are automatically excluded from git via .gitignore")
    print()


def show_python_info():
    """Show Python version and bytecode info."""
    
    print("=" * 60)
    print("Python Bytecode Information")
    print("=" * 60)
    print()
    
    print(f"Python Version: {sys.version}")
    print(f"Python Implementation: {sys.implementation.name}")
    print(f"Bytecode Magic Number: {importlib.util.MAGIC_NUMBER.hex()}")
    print()
    
    # Check if bytecode writing is disabled
    if sys.dont_write_bytecode:
        print("⚠ Bytecode writing is DISABLED (sys.dont_write_bytecode = True)")
        print("  __pycache__ will NOT be created")
    else:
        print("✓ Bytecode writing is ENABLED")
        print("  __pycache__ will be created automatically")
    print()
    
    # Check environment variable
    if os.environ.get("PYTHONDONTWRITEBYTECODE"):
        print("⚠ PYTHONDONTWRITEBYTECODE environment variable is set")
        print("  __pycache__ will NOT be created")
    else:
        print("✓ PYTHONDONTWRITEBYTECODE is not set")
    print()


if __name__ == "__main__":
    import importlib.util
    
    print()
    show_python_info()
    print()
    
    show_project_pycache()
    print()
    
    response = input("Run __pycache__ creation demonstration? (Y/n): ")
    if response.lower() != 'n':
        print()
        demonstrate_pycache_creation()
    else:
        print("Skipping demonstration.")
        print()
        print("To see __pycache__ creation:")
        print("  1. Import any Python module")
        print("  2. Check for __pycache__ directory")
        print("  3. Look for .pyc files inside")
        print()
