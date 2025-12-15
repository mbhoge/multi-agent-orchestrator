"""Unit tests for AWS Agent Core components."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from aws_agent_core.orchestrator import MultiAgentOrchestrator
from aws_agent_core.runtime.sdk_client import AgentCoreRuntimeClient
from shared.models.request import AgentRequest
from shared.config.settings import AWSSettings


@pytest.fixture
def mock_aws_settings():
    """Mock AWS settings."""
    return AWSSettings(
        aws_region="us-east-1",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret"
    )


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator."""
    with patch('aws_agent_core.orchestrator.AgentCoreRuntimeClient'):
        return MultiAgentOrchestrator()


@pytest.mark.asyncio
async def test_orchestrator_process_request(mock_orchestrator):
    """Test orchestrator request processing."""
    request = AgentRequest(
        query="Test query",
        session_id="test-session"
    )
    
    with patch.object(mock_orchestrator, '_invoke_langgraph', new_callable=AsyncMock) as mock_langgraph:
        mock_langgraph.return_value = {
            "response": "Test response",
            "selected_agent": "cortex_analyst",
            "routing_reason": "Test routing",
            "confidence": 0.9
        }
        
        response = await mock_orchestrator.process_request(request)
        
        assert response.response is not None
        assert response.session_id == "test-session"
        assert mock_langgraph.called


def test_runtime_client_initialization(mock_aws_settings):
    """Test runtime client initialization."""
    with patch('aws_agent_core.runtime.sdk_client.get_bedrock_agent_core_client'):
        client = AgentCoreRuntimeClient(mock_aws_settings)
        assert client.aws_settings == mock_aws_settings


@pytest.mark.asyncio
async def test_runtime_client_invoke_agent(mock_aws_settings):
    """Test runtime client agent invocation."""
    with patch('aws_agent_core.runtime.sdk_client.get_bedrock_agent_core_client') as mock_client:
        mock_client.return_value.invoke_agent.return_value = {
            "completion": [{"chunk": {"bytes": b"Test response"}}]
        }
        
        client = AgentCoreRuntimeClient(mock_aws_settings)
        result = client.invoke_agent(
            agent_id="test-agent",
            agent_alias_id="test-alias",
            session_id="test-session",
            input_text="Test query"
        )
        
        assert "completion" in result

