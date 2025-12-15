"""Langfuse configuration and setup.

This package provides utilities for configuring and working with Langfuse
observability platform for the LangGraph supervisor, including prompt management.
"""

from langfuse.config import get_langfuse_config
from langfuse.prompt_manager import LangfusePromptManager, get_prompt_manager

__version__ = "1.0.0"

__all__ = [
    "get_langfuse_config",
    "LangfusePromptManager",
    "get_prompt_manager",
]
