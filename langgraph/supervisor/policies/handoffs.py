"""Handoffs policy.

This implements the *Handoffs* pattern semantics for a chat interface:
- Keep an "active_agent" in short-term memory for the session.
- For likely follow-up queries, hand off directly to the active agent
  (skipping routing and saving latency).
- For domain changes / explicit preferences, re-route and update active agent.

This policy is often a better fit than a stateless router for Teams-like chat,
because follow-up turns are common and skipping routing saves 1 model/service call.
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
)

logger = logging.getLogger(__name__)


def _score_domain_keywords(query: str, domain_agent: Dict[str, Any]) -> float:
    """Cheap keyword score for domain-change detection.

    We intentionally keep this simple; its job is not full routing, just to detect
    when the user likely switched topics away from the active agent.
    """
    q = (query or "").lower()
    keywords = [k.lower() for k in (domain_agent.get("keywords") or []) if isinstance(k, str)]
    if not keywords:
        return 0.0
    matches = sum(1 for k in keywords if k in q)
    return matches / max(len(keywords), 1)


def _detect_domain_change(query: str, *, active_domain: Optional[str]) -> bool:
    """Best-effort domain-change detector.

    If the best keyword-scoring domain differs from the active domain with non-trivial
    signal, we consider it a domain change and re-route.
    """
    if not active_domain:
        return False

    best = None
    best_score = 0.0
    for a in getattr(agent_router, "domain_agents", []) or []:
        score = _score_domain_keywords(query, a)
        if score > best_score:
            best_score = score
            best = a

    if not best or best_score < 0.2:
        return False

    best_domain = str(best.get("domain") or "").lower()
    return best_domain != str(active_domain).lower()


class HandoffsPolicy(RoutingPolicy):
    """Handoffs-style routing for chat UIs."""

    def __init__(self, *, active_agent_ttl_seconds: int) -> None:
        self.active_agent_ttl_seconds = active_agent_ttl_seconds

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
        active_agent = short_term_memory.retrieve(session_id=session_id, key="active_agent")
        active_domain = short_term_memory.retrieve(session_id=session_id, key="active_domain")
        last_query = short_term_memory.retrieve(session_id=session_id, key="last_query")

        # If the caller explicitly requests an agent/domain, do not handoff.
        if agent_preference:
            return await self._route_and_set_active(
                session_id=session_id,
                query=query,
                context=context,
                agent_preference=agent_preference,
                render_routing_prompt=render_routing_prompt,
            )

        # Follow-up handoff: likely continuation + no domain change signals.
        if (
            active_agent
            and isinstance(active_agent, str)
            and is_likely_followup(query, messages=messages, last_query=last_query)
            and not _detect_domain_change(query, active_domain=active_domain if isinstance(active_domain, str) else None)
        ):
            return {
                "agents_to_call": [active_agent],
                "routing_reason": "Handoff: using active agent for follow-up to reduce latency.",
                "confidence": 1.0,
            }

        # Otherwise, perform normal routing and update active agent.
        return await self._route_and_set_active(
            session_id=session_id,
            query=query,
            context=context,
            agent_preference=None,
            render_routing_prompt=render_routing_prompt,
        )

    async def _route_and_set_active(
        self,
        *,
        session_id: str,
        query: str,
        context: Optional[Dict[str, Any]],
        agent_preference: Optional[str],
        render_routing_prompt: RenderRoutingPrompt,
    ) -> Dict[str, Any]:
        routing_prompt = await render_routing_prompt()
        decision = agent_router.route_request(
            query=routing_prompt,
            context=context,
            agent_preference=agent_preference,
        )

        # Update active agent for next turns (best-effort).
        try:
            agents = decision.get("agents_to_call") or []
            if isinstance(agents, list) and agents:
                active_agent = str(agents[0])
                short_term_memory.store(
                    session_id=session_id,
                    key="active_agent",
                    value=active_agent,
                    ttl=self.active_agent_ttl_seconds,
                    metadata={"policy": "handoffs"},
                )

                # Also store active domain (if known) to help detect domain changes.
                active_domain = None
                for a in getattr(agent_router, "domain_agents", []) or []:
                    if a.get("agent_name") == active_agent:
                        active_domain = a.get("domain")
                        break
                if active_domain:
                    short_term_memory.store(
                        session_id=session_id,
                        key="active_domain",
                        value=str(active_domain),
                        ttl=self.active_agent_ttl_seconds,
                        metadata={"policy": "handoffs"},
                    )
        except Exception as e:
            logger.debug(f"Failed to store active agent/domain: {e}")

        return decision


def build_handoffs_policy() -> HandoffsPolicy:
    """Factory with settings-driven defaults."""
    return HandoffsPolicy(active_agent_ttl_seconds=settings.langgraph.handoffs_active_agent_ttl_seconds)

