"""Unit tests for routing policy strategies.

These tests validate that we can maintain ONE codebase and swap routing behavior
via the policy strategy interface.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from langgraph.memory.short_term import short_term_memory
from langgraph.supervisor.policies.handoffs import HandoffsPolicy
from langgraph.supervisor.policies.optimized_router import OptimizedRouterPolicy


@pytest.fixture
def session_id() -> str:
    return "test-session-routing-policies"


@pytest.fixture(autouse=True)
def clear_memory(session_id: str):
    """Ensure test isolation (short-term memory is a global singleton)."""
    short_term_memory.clear(session_id)
    yield
    short_term_memory.clear(session_id)


@pytest.mark.asyncio
async def test_optimized_router_reuses_routing_on_followup(session_id: str):
    # Arrange: previous routing decision exists
    short_term_memory.store(
        session_id=session_id,
        key="routing_decision",
        value={"agents_to_call": ["MARKET_SEGMENT_AGENT"], "routing_reason": "prior", "confidence": 0.9},
    )
    short_term_memory.store(session_id=session_id, key="last_query", value="show me market segmentation")

    policy = OptimizedRouterPolicy(followup_reuse_enabled=True, cache_ttl_seconds=60)
    render_prompt = AsyncMock(return_value="rendered prompt SHOULD NOT be used")

    # Act: follow-up style query
    decision = await policy.decide(
        session_id=session_id,
        query="and what about retention?",
        context=None,
        messages=[
            {"role": "user", "content": "show me market segmentation", "ts": 0.0},
            {"role": "assistant", "content": "ok", "ts": 1.0},
        ],
        agent_preference=None,
        render_routing_prompt=render_prompt,
    )

    # Assert: follow-up reuse path should skip prompt rendering
    assert decision["agents_to_call"] == ["MARKET_SEGMENT_AGENT"]
    assert "Follow-up reuse" in decision["routing_reason"]
    render_prompt.assert_not_awaited()


@pytest.mark.asyncio
async def test_optimized_router_uses_cache_for_identical_query(session_id: str):
    policy = OptimizedRouterPolicy(followup_reuse_enabled=False, cache_ttl_seconds=60)

    # Pre-populate cache
    short_term_memory.store(
        session_id=session_id,
        key="routing_cache:show me market segmentation",
        value={"agents_to_call": ["MARKET_SEGMENT_AGENT"], "routing_reason": "cached", "confidence": 0.8},
    )

    render_prompt = AsyncMock(return_value="rendered prompt SHOULD NOT be used")

    decision = await policy.decide(
        session_id=session_id,
        query="show me   market   segmentation",
        context=None,
        messages=[{"role": "user", "content": "x", "ts": 0.0}, {"role": "assistant", "content": "y", "ts": 1.0}],
        agent_preference=None,
        render_routing_prompt=render_prompt,
    )

    assert decision["agents_to_call"] == ["MARKET_SEGMENT_AGENT"]
    assert "Cache hit" in decision["routing_reason"]
    render_prompt.assert_not_awaited()


@pytest.mark.asyncio
async def test_handoffs_uses_active_agent_for_followup(session_id: str):
    short_term_memory.store(session_id=session_id, key="active_agent", value="DRUG_DISCOVERY_AGENT")
    short_term_memory.store(session_id=session_id, key="last_query", value="tell me about compounds")

    policy = HandoffsPolicy(active_agent_ttl_seconds=60)
    render_prompt = AsyncMock(return_value="rendered prompt SHOULD NOT be used")

    decision = await policy.decide(
        session_id=session_id,
        query="and what about targets?",
        context=None,
        messages=[
            {"role": "user", "content": "tell me about compounds", "ts": 0.0},
            {"role": "assistant", "content": "ok", "ts": 1.0},
        ],
        agent_preference=None,
        render_routing_prompt=render_prompt,
    )

    assert decision["agents_to_call"] == ["DRUG_DISCOVERY_AGENT"]
    assert "Handoff" in decision["routing_reason"]
    render_prompt.assert_not_awaited()


@pytest.mark.asyncio
async def test_handoffs_reroutes_when_agent_preference_is_set(session_id: str, monkeypatch):
    # If user forces a domain/agent, we should route (not handoff).
    short_term_memory.store(session_id=session_id, key="active_agent", value="DRUG_DISCOVERY_AGENT")

    # Monkeypatch the router to return a deterministic decision.
    from langgraph.reasoning import router as router_module

    mock_route = Mock(
        return_value={
            "agents_to_call": ["MARKET_SEGMENT_AGENT"],
            "routing_reason": "forced",
            "confidence": 1.0,
        }
    )
    monkeypatch.setattr(router_module.agent_router, "route_request", mock_route)

    policy = HandoffsPolicy(active_agent_ttl_seconds=60)
    render_prompt = AsyncMock(return_value="rendered prompt")

    decision = await policy.decide(
        session_id=session_id,
        query="market segment please",
        context=None,
        messages=[{"role": "user", "content": "x", "ts": 0.0}, {"role": "assistant", "content": "y", "ts": 1.0}],
        agent_preference="market_segment",
        render_routing_prompt=render_prompt,
    )

    assert decision["agents_to_call"] == ["MARKET_SEGMENT_AGENT"]
    assert short_term_memory.retrieve(session_id=session_id, key="active_agent") == "MARKET_SEGMENT_AGENT"
    render_prompt.assert_awaited()
    mock_route.assert_called_once()

