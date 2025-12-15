"""Integration tests for agent flow."""

import pytest
from unittest.mock import patch, AsyncMock
from langgraph.supervisor import LangGraphSupervisor
from shared.models.request import AgentRequest


@pytest.mark.asyncio
async def test_langgraph_to_snowflake_flow():
    """Test flow from LangGraph to Snowflake agents."""
    supervisor = LangGraphSupervisor()
    request = AgentRequest(
        query="Search for documents about machine learning",
        session_id="agent-flow-test"
    )
    
    with patch.object(supervisor, '_invoke_snowflake_agent', new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = {
            "response": "Found 5 documents about machine learning",
            "sources": [
                {"file": "ml_intro.pdf", "score": 0.95}
            ]
        }
        
        response = await supervisor.process_request(request, "agent-flow-test")
        
        assert "response" in response
        assert "selected_agent" in response
        assert mock_agent.called

