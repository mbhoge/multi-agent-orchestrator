"""
Practical Examples: Using Enhanced __init__.py Files

This file demonstrates the difference between using minimal vs enhanced __init__.py files.
"""

# ============================================================================
# EXAMPLE 1: Importing from aws_agent_core
# ============================================================================

# BEFORE (with minimal __init__.py):
# You had to import from specific submodules:
from aws_agent_core.orchestrator import MultiAgentOrchestrator
from aws_agent_core.runtime.sdk_client import AgentCoreRuntimeClient
from aws_agent_core.observability.metrics import metrics_collector
from aws_agent_core.observability.tracing import tracer

# AFTER (with enhanced __init__.py):
# Now you can import directly from the package:
from aws_agent_core import (
    MultiAgentOrchestrator,
    AgentCoreRuntimeClient,
    metrics_collector,
    tracer
)

# Benefits:
# ✅ Shorter, cleaner imports
# ✅ Clearer what's the public API
# ✅ Easier to remember
# ✅ Less typing

# ============================================================================
# EXAMPLE 2: Using the imports in code
# ============================================================================

# Example: Creating an orchestrator instance
# Both approaches work, but the enhanced version is cleaner:

# BEFORE:
# from aws_agent_core.orchestrator import MultiAgentOrchestrator
# orchestrator = MultiAgentOrchestrator()

# AFTER:
from aws_agent_core import MultiAgentOrchestrator
orchestrator = MultiAgentOrchestrator()

# Example: Using metrics
# BEFORE:
# from aws_agent_core.observability.metrics import metrics_collector
# metrics_collector.increment_counter("requests.total")

# AFTER:
from aws_agent_core import metrics_collector
metrics_collector.increment_counter("requests.total")

# ============================================================================
# EXAMPLE 3: Importing from langfuse
# ============================================================================

# BEFORE:
# from langfuse.config import get_langfuse_config
# config = get_langfuse_config()

# AFTER:
from langfuse import get_langfuse_config
config = get_langfuse_config()

# ============================================================================
# EXAMPLE 4: What __all__ does
# ============================================================================

# When you define __all__ in __init__.py:
# __all__ = ["MultiAgentOrchestrator", "AgentCoreRuntimeClient"]

# It controls what gets imported with:
# from aws_agent_core import *
# 
# This imports ONLY what's in __all__, not everything from submodules.
# This is a best practice for controlling the public API.

# ============================================================================
# EXAMPLE 5: Real-world usage in your project
# ============================================================================

# In tests/unit/test_aws_agent_core.py:
# BEFORE:
# from aws_agent_core.orchestrator import MultiAgentOrchestrator
# from aws_agent_core.runtime.sdk_client import AgentCoreRuntimeClient

# AFTER (cleaner):
# from aws_agent_core import MultiAgentOrchestrator, AgentCoreRuntimeClient

# In aws_agent_core/api/routes.py:
# BEFORE:
# from aws_agent_core.orchestrator import MultiAgentOrchestrator
# from aws_agent_core.observability.metrics import metrics_collector

# AFTER (cleaner):
# from aws_agent_core import MultiAgentOrchestrator, metrics_collector

# ============================================================================
# EXAMPLE 6: Version information
# ============================================================================

# With enhanced __init__.py, you can access version:
from aws_agent_core import __version__
print(f"AWS Agent Core version: {__version__}")  # Output: "1.0.0"

# This is useful for:
# - Logging
# - API responses
# - Debugging
# - Dependency management

# ============================================================================
# EXAMPLE 7: Backward compatibility
# ============================================================================

# IMPORTANT: The old import style STILL WORKS!
# Both of these work:

# Old style (still works):
from aws_agent_core.orchestrator import MultiAgentOrchestrator

# New style (preferred):
from aws_agent_core import MultiAgentOrchestrator

# This means:
# ✅ No breaking changes
# ✅ Gradual migration possible
# ✅ Existing code continues to work

# ============================================================================
# EXAMPLE 8: What NOT to put in __init__.py
# ============================================================================

# ❌ DON'T put heavy computation:
# def expensive_function():
#     # Heavy computation here
#     pass

# ❌ DON'T import everything:
# from aws_agent_core.orchestrator import *
# from aws_agent_core.runtime import *
# # This defeats the purpose

# ❌ DON'T create circular imports:
# # If aws_agent_core imports langgraph, and langgraph imports aws_agent_core
# # This creates a circular dependency

# ✅ DO keep it simple:
# - Import only commonly used classes/functions
# - Keep initialization lightweight
# - Use __all__ to control exports

# ============================================================================
# EXAMPLE 9: Package structure visualization
# ============================================================================

"""
aws_agent_core/
├── __init__.py          ← Enhanced: Exports main classes
├── orchestrator.py     ← Contains MultiAgentOrchestrator
├── runtime/
│   └── sdk_client.py   ← Contains AgentCoreRuntimeClient
└── observability/
    ├── metrics.py       ← Contains metrics_collector
    └── tracing.py       ← Contains tracer

When you do: from aws_agent_core import MultiAgentOrchestrator

Python:
1. Looks at aws_agent_core/__init__.py
2. Sees: from aws_agent_core.orchestrator import MultiAgentOrchestrator
3. Imports orchestrator.py
4. Gets MultiAgentOrchestrator class
5. Makes it available as aws_agent_core.MultiAgentOrchestrator
"""

# ============================================================================
# EXAMPLE 10: Comparison in actual code
# ============================================================================

# File: tests/unit/test_aws_agent_core.py

# BEFORE (verbose):
"""
from aws_agent_core.orchestrator import MultiAgentOrchestrator
from aws_agent_core.runtime.sdk_client import AgentCoreRuntimeClient

def test_orchestrator():
    orchestrator = MultiAgentOrchestrator()
    client = AgentCoreRuntimeClient(...)
"""

# AFTER (clean):
"""
from aws_agent_core import MultiAgentOrchestrator, AgentCoreRuntimeClient

def test_orchestrator():
    orchestrator = MultiAgentOrchestrator()
    client = AgentCoreRuntimeClient(...)
"""

# Benefits:
# - 2 lines instead of 2 lines (same, but clearer)
# - If you need more imports, it's cleaner:
#   from aws_agent_core import (
#       MultiAgentOrchestrator,
#       AgentCoreRuntimeClient,
#       metrics_collector,
#       tracer
#   )
