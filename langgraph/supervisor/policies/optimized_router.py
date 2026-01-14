"""Optimized Router policy.

This keeps the *Router* pattern semantics (route → invoke agents → combine),
but adds low-latency optimizations that are particularly helpful for chat UIs
like Microsoft Teams:

- Follow-up reuse: if the user is likely continuing the same thread, reuse the
  previous routing decision and skip routing altogether.
- Per-session routing cache: cache routing decisions for identical/near-identical
  queries to avoid repeated routing work.

This policy still routes (calls the router) for new topics/domain changes.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from langgraph.memory.short_term import short_term_memory
from langgraph.reasoning.router import agent_router
from shared.config.settings import settings

from .base import (
    RenderRoutingPrompt,
    RoutingPolicy,
    is_likely_followup,
    normalize_query_for_cache,
)

logger = logging.getLogger(__name__)


class OptimizedRouterPolicy(RoutingPolicy):
    """Router-style routing with latency optimizations."""

    def __init__(
        self,
        *,
        followup_reuse_enabled: bool,
        cache_ttl_seconds: int,
    ) -> None:
        self.followup_reuse_enabled = followup_reuse_enabled
        self.cache_ttl_seconds = cache_ttl_seconds

    async def decide(
        self,
        *,
        session_id: str,
        query: str,
        context: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        agent_preference: Optional[str],
        render_routing_prompt: RenderRoutingPrompt,
    ) -> Dict[str, Any]:
        # 1) Follow-up reuse (fast-path): reuse last routing decision.
        if self.followup_reuse_enabled:
            last_query = short_term_memory.retrieve(session_id=session_id, key="last_query")
            last_routing = short_term_memory.retrieve(session_id=session_id, key="routing_decision")
            if (
                last_routing
                and isinstance(last_routing, dict)
                and is_likely_followup(query, messages=messages, last_query=last_query)
            ):
                reused = dict(last_routing)
                reused["routing_reason"] = (
                    "Follow-up reuse: reusing previous routing decision to reduce latency. "
                    + str(last_routing.get("routing_reason", "")).strip()
                ).strip()
                # Keep confidence stable but bounded.
                try:
                    reused["confidence"] = float(reused.get("confidence", 0.8))
                except Exception:
                    reused["confidence"] = 0.8
                return reused

        # 2) Per-session cache (fast-path): identical/near-identical query.
        normalized = normalize_query_for_cache(query)
        cache_key = f"routing_cache:{normalized}"
        cached = short_term_memory.retrieve(session_id=session_id, key=cache_key)
        if cached and isinstance(cached, dict):
            cached_decision = dict(cached)
            cached_decision["routing_reason"] = (
                "Cache hit: reused cached routing decision for identical query. "
                + str(cached.get("routing_reason", "")).strip()
            ).strip()
            return cached_decision

        # 3) Normal routing path: render prompt (Langfuse) then call the router.
        # NOTE: today `agent_router` is keyword-based in this repo; it can later be swapped
        # to an LLM-based router without changing this policy interface.
        routing_prompt = await render_routing_prompt()
        decision = agent_router.route_request(
            query=routing_prompt,
            context=context,
            agent_preference=agent_preference,
        )

        # 4) Populate cache (best-effort).
        try:
            short_term_memory.store(
                session_id=session_id,
                key=cache_key,
                value=decision,
                ttl=self.cache_ttl_seconds,
                metadata={"policy": "optimized_router"},
            )
        except Exception as e:
            logger.debug(f"Failed to store routing cache entry: {e}")

        return decision


def build_optimized_router_policy() -> OptimizedRouterPolicy:
    """Factory with settings-driven defaults."""
    return OptimizedRouterPolicy(
        followup_reuse_enabled=settings.langgraph.routing_followup_reuse_enabled,
        cache_ttl_seconds=settings.langgraph.routing_cache_ttl_seconds,
    )

