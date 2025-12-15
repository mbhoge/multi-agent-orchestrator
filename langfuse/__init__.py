"""Langfuse configuration and setup.

This package provides utilities for configuring and working with Langfuse
observability platform for the LangGraph supervisor.
"""

from langfuse.config import get_langfuse_config

__version__ = "1.0.0"

__all__ = [
    "get_langfuse_config",
]
