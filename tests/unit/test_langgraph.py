"""Unit tests for LangGraph components."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from langgraph.supervisor import LangGraphSupervisor
from langgraph.reasoning.router import AgentRouter
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


@pytest.fixture
def mock_router():
    """Mock router."""
    return AgentRouter()


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


def test_router_route_request(mock_router):
    """Test agent routing."""
    routing = mock_router.route_request(
        query="Query the database for sales data",
        context=None
    )
    
    assert "agents_to_call" in routing
    assert "routing_reason" in routing
    assert "confidence" in routing
    assert isinstance(routing["agents_to_call"], list)
    assert len(routing["agents_to_call"]) > 0

