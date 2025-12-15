"""Sample data for testing."""

from shared.models.request import AgentRequest
from shared.models.agent_state import AgentState, AgentType, RequestStatus


def sample_agent_request() -> AgentRequest:
    """Create a sample agent request."""
    return AgentRequest(
        query="What are the total sales for last month?",
        session_id="test-session-123",
        context={"data_type": "structured"},
        metadata={"source": "test"}
    )


def sample_agent_state() -> AgentState:
    """Create a sample agent state."""
    return AgentState(
        query="What are the total sales for last month?",
        session_id="test-session-123",
        selected_agent=AgentType.CORTEX_ANALYST,
        routing_reason="Query is for structured data analysis",
        status=RequestStatus.PROCESSING
    )


def sample_routing_decision() -> dict:
    """Create a sample routing decision."""
    return {
        "selected_agent": AgentType.CORTEX_ANALYST,
        "routing_reason": "Query matches analyst keywords",
        "confidence": 0.85,
        "scores": {
            "analyst": 0.85,
            "search": 0.15
        }
    }

