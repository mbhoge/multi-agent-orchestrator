"""Routing policy strategies for the LangGraph supervisor.

Why this package exists:
- We want ONE codebase, ONE supervisor graph, and TWO routing behaviors.
- We isolate the variable part (routing decision logic) behind a small strategy interface.
- We select the strategy at runtime via config (LANGGRAPH_ROUTING_MODE).

This keeps the workflow (state load → routing → invoke agents → combine → memory → observability)
stable and testable, while allowing A/B testing of routing behavior.
"""

from .factory import get_routing_policy
from .base import RoutingPolicy

__all__ = ["RoutingPolicy", "get_routing_policy"]

