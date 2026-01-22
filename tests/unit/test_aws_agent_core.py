"""Unit tests for AWS Agent Core components."""

from unittest.mock import AsyncMock, patch

import pytest

from aws_agent_core.orchestrator import MultiAgentOrchestrator
from shared.models.request import AgentRequest


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator."""
    return MultiAgentOrchestrator()


@pytest.mark.asyncio
async def test_orchestrator_process_request(mock_orchestrator):
    """Test orchestrator request processing."""
    request = AgentRequest(
        query="Test query",
        session_id="test-session"
    )
    
    with patch.object(mock_orchestrator, "_invoke_langgraph", new_callable=AsyncMock) as mock_langgraph:
        mock_langgraph.return_value = {
            "response": "Test response",
            "selected_agent": "cortex_analyst",
            "routing_reason": "Test routing",
            "confidence": 0.9,
            "sources": [],
        }

        response = await mock_orchestrator.process_request(request)

        assert response.response == "Test response"
        assert response.session_id == "test-session"
        assert response.agent_used == "cortex_analyst"
        assert mock_langgraph.called

