"""Policy factory (strategy selection) driven by config.

Config:
  LANGGRAPH_ROUTING_MODE=optimized_router|handoffs

Why a factory:
- Centralizes selection logic (no branching scattered through the graph).
- Makes it easy to unit test both strategies independently.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from shared.config.settings import settings

from .base import RoutingPolicy
from .handoffs import build_handoffs_policy
from .optimized_router import build_optimized_router_policy

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_routing_policy() -> RoutingPolicy:
    """Return the configured routing policy (cached singleton)."""

    mode = (settings.langgraph.routing_mode or "").strip().lower()

    if mode in {"handoffs", "handoff"}:
        logger.info("Routing policy selected: handoffs")
        return build_handoffs_policy()

    # Default (and fallback) mode.
    logger.info("Routing policy selected: optimized_router")
    return build_optimized_router_policy()

