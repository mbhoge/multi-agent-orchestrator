"""Unit tests for Snowflake Cortex components."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from snowflake_cortex.agents.cortex_agent import CortexAgent
from snowflake_cortex.tools.analyst import CortexAnalyst
from snowflake_cortex.tools.search import CortexSearch
from shared.models.agent_state import AgentType


@pytest.fixture
def mock_cortex_agent():
    """Mock Cortex agent."""
    with patch('snowflake_cortex.agents.cortex_agent.CortexAnalyst'), \
         patch('snowflake_cortex.agents.cortex_agent.CortexSearch'), \
         patch('snowflake_cortex.agents.cortex_agent.TruLensClient'):
        return CortexAgent(AgentType.CORTEX_ANALYST)


@pytest.mark.asyncio
async def test_cortex_agent_process_query(mock_cortex_agent):
    """Test Cortex agent query processing."""
    with patch.object(mock_cortex_agent.analyst, 'analyze_query', new_callable=AsyncMock) as mock_analyst:
        mock_analyst.return_value = {
            "response": "Analyst response",
            "sources": []
        }
        
        result = await mock_cortex_agent.process_query(
            query="Test query",
            session_id="test-session"
        )
        
        assert "response" in result
        assert mock_analyst.called


@pytest.mark.asyncio
async def test_cortex_analyst_analyze_query():
    """Test Cortex Analyst query analysis."""
    with patch('snowflake_cortex.tools.analyst.SemanticModelLoader'), \
         patch('snowflake_cortex.tools.analyst.snowflake.connector'):
        analyst = CortexAnalyst()
        
        with patch.object(analyst, '_convert_to_sql', new_callable=AsyncMock) as mock_convert, \
             patch.object(analyst, '_execute_query', new_callable=AsyncMock) as mock_execute:
            mock_convert.return_value = "SELECT * FROM table"
            mock_execute.return_value = [{"column1": "value1"}]
            
            result = await analyst.analyze_query(
                query="Test query",
                session_id="test-session"
            )
            
            assert "response" in result
            assert "sql_query" in result


@pytest.mark.asyncio
async def test_cortex_search_search_query():
    """Test Cortex Search query."""
    with patch('snowflake_cortex.tools.search.snowflake.connector'):
        search = CortexSearch()
        
        with patch.object(search, '_perform_search', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {"file": "test.pdf", "content": "Test content", "score": 0.9}
            ]
            
            result = await search.search_query(
                query="Test query",
                session_id="test-session"
            )
            
            assert "response" in result
            assert "sources" in result

