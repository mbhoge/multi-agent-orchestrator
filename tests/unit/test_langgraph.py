"""Unit tests for LangGraph components."""

import pytest
from unittest.mock import patch, AsyncMock
from langgraph.supervisor import LangGraphSupervisor
from shared.models.request import AgentRequest


@pytest.fixture
def mock_supervisor():
    """Mock supervisor."""
    with patch('langgraph.supervisor.LangfuseClient'), \
         patch('langgraph.supervisor.graph.initialize_graph_globals'), \
         patch('langgraph.supervisor.graph.create_supervisor_graph') as mock_graph:
        # Mock the graph's ainvoke method
        mock_graph_instance = AsyncMock()
        mock_graph_instance.ainvoke = AsyncMock(return_value={
            "query": "Test query",
            "session_id": "test-session",
            "messages": [],
            "routing_decision": {
                "agents_to_call": ["test_agent"],
                "routing_reason": "Test routing",
                "confidence": 0.9
            },
            "agent_responses": [{
                "agent_name": "test_agent",
                "response": "Test response",
                "sources": []
            }],
            "final_response": "Test response",
            "status": "completed",
            "execution_time": 1.5
        })
        mock_graph.return_value = mock_graph_instance
        return LangGraphSupervisor()


@pytest.mark.asyncio
async def test_supervisor_process_request(mock_supervisor):
    """Test supervisor request processing with StateGraph."""
    request = AgentRequest(
        query="Test query",
        session_id="test-session"
    )
    
    response = await mock_supervisor.process_request(request, "test-session")
    
    assert "response" in response
    assert "selected_agent" in response
    assert response["response"] == "Test response"

