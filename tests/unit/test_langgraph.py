"""Unit tests for LangGraph components."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from langgraph.supervisor import LangGraphSupervisor
from langgraph.reasoning.router import AgentRouter
from langgraph.state.state_manager import StateManager
from shared.models.request import AgentRequest
from shared.models.agent_state import AgentType


@pytest.fixture
def mock_supervisor():
    """Mock supervisor."""
    with patch('langgraph.supervisor.LangfuseClient'):
        return LangGraphSupervisor()


@pytest.fixture
def mock_router():
    """Mock router."""
    return AgentRouter()


@pytest.fixture
def mock_state_manager():
    """Mock state manager."""
    return StateManager()


@pytest.mark.asyncio
async def test_supervisor_process_request(mock_supervisor):
    """Test supervisor request processing."""
    request = AgentRequest(
        query="Test query",
        session_id="test-session"
    )
    
    with patch.object(mock_supervisor, '_invoke_snowflake_agent', new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = {
            "response": "Test response",
            "sources": []
        }
        
        response = await mock_supervisor.process_request(request, "test-session")
        
        assert "response" in response
        assert "selected_agent" in response


def test_router_route_request(mock_router):
    """Test agent routing."""
    routing = mock_router.route_request(
        query="Query the database for sales data",
        context=None
    )
    
    assert "selected_agent" in routing
    assert "routing_reason" in routing
    assert routing["selected_agent"] in [AgentType.CORTEX_ANALYST, AgentType.CORTEX_SEARCH, AgentType.CORTEX_COMBINED]


def test_state_manager_create_state(mock_state_manager):
    """Test state creation."""
    state = mock_state_manager.create_state(
        query="Test query",
        session_id="test-session"
    )
    
    assert state.session_id == "test-session"
    assert state.query == "Test query"


def test_state_manager_update_state(mock_state_manager):
    """Test state update."""
    state = mock_state_manager.create_state(
        query="Test query",
        session_id="test-session"
    )
    
    updated = mock_state_manager.update_state(
        session_id="test-session",
        update={"status": "processing"}
    )
    
    assert updated is not None
    assert updated.status.value == "processing"

