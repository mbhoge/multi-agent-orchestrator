"""Routing policy interface + shared helpers.

The supervisor graph needs a *routing decision* in the standard shape:
  {
    "agents_to_call": ["AGENT_NAME", ...],
    "routing_reason": "human readable",
    "confidence": 0.0..1.0
  }

We keep this contract stable, and swap only the logic that produces it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol


RenderRoutingPrompt = Callable[[], Awaitable[str]]


class RoutingPolicy(Protocol):
    """Strategy interface for routing.

    Implementations may choose to:
    - reuse prior routing decisions for likely follow-up queries,
    - keep an "active agent" for conversational handoffs,
    - cache routing decisions per session,
    - or call an LLM-based router (future).
    """

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
        """Return a routing decision dict (see module docstring)."""


@dataclass(frozen=True)
class FollowUpHeuristics:
    """Configurable heuristics to classify follow-up queries.

    This is intentionally simple and fast (string heuristics) because it runs
    on every request and is used to decide whether we can *skip* routing calls.
    """

    short_query_chars: int = 32


def is_likely_followup(
    query: str,
    *,
    messages: List[Dict[str, Any]],
    last_query: Optional[str] = None,
    heuristics: FollowUpHeuristics = FollowUpHeuristics(),
) -> bool:
    """Best-effort follow-up detector for chat UX.

    Goal: identify turns that probably refer to previous context, so we can reuse
    an earlier routing decision (or hand off to an active agent) and save latency.

    Notes:
    - This is a heuristic; it will never be perfect.
    - We bias towards being conservative (false negatives) rather than aggressive
      (false positives) to avoid routing to the wrong domain.
    """

    # If there's no prior context, it's not a follow-up.
    if not messages or len(messages) < 2:
        return False

    q = (query or "").strip().lower()
    if not q:
        return False

    # Very short turns ("and that?", "ok", "then?") are usually follow-ups.
    if len(q) <= heuristics.short_query_chars:
        return True

    followup_starters = (
        "and ",
        "also ",
        "then ",
        "next ",
        "now ",
        "ok",
        "okay",
        "what about",
        "how about",
        "can you",
        "could you",
        "please",
    )
    if any(q.startswith(s) for s in followup_starters):
        return True

    # Pronoun-heavy turns are commonly follow-ups (when a prior query exists).
    if last_query:
        pronouns = {"it", "that", "this", "those", "these", "them", "they", "he", "she"}
        tokens = {t.strip(".,!?;:()[]{}\"'").lower() for t in q.split()}
        if pronouns.intersection(tokens):
            return True

    return False


def normalize_query_for_cache(query: str) -> str:
    """Normalize user query for per-session cache keys."""
    return " ".join((query or "").strip().lower().split())

