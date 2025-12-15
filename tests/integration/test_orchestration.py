"""Integration tests for orchestration flow."""

import pytest
from unittest.mock import patch, AsyncMock
from aws_agent_core.orchestrator import MultiAgentOrchestrator
from shared.models.request import AgentRequest


@pytest.mark.asyncio
async def test_full_orchestration_flow():
    """Test full orchestration flow from request to response."""
    orchestrator = MultiAgentOrchestrator()
    request = AgentRequest(
        query="What are the sales for Q4?",
        session_id="integration-test-session"
    )
    
    with patch.object(orchestrator, '_invoke_langgraph', new_callable=AsyncMock) as mock_langgraph:
        mock_langgraph.return_value = {
            "response": "Q4 sales are $1M",
            "selected_agent": "cortex_analyst",
            "routing_reason": "Query is for structured data",
            "confidence": 0.95,
            "sources": []
        }
        
        response = await orchestrator.process_request(request)
        
        assert response.response is not None
        assert response.session_id == request.session_id
        assert response.agent_used is not None
        assert mock_langgraph.called


@pytest.mark.asyncio
async def test_orchestration_with_error_handling():
    """Test orchestration error handling."""
    orchestrator = MultiAgentOrchestrator()
    request = AgentRequest(
        query="Test query",
        session_id="error-test-session"
    )
    
    with patch.object(orchestrator, '_invoke_langgraph', new_callable=AsyncMock) as mock_langgraph:
        mock_langgraph.side_effect = Exception("Test error")
        
        with pytest.raises(Exception):
            await orchestrator.process_request(request)

