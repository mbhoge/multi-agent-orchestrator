"""Unit tests for Snowflake Cortex components.

Note: The project now invokes Snowflake Cortex Agents via the Cortex Agents Run REST API
through `snowflake_cortex.gateway.agent_gateway.CortexAgentGateway`. The legacy local
`CortexAgent` implementation has been removed.
"""

import pytest
from unittest.mock import patch, AsyncMock
from snowflake_cortex.gateway.agent_gateway import CortexAgentGateway


@pytest.mark.asyncio
async def test_agents_run_gateway_builds_messages_from_history():
    """Test that Agents Run gateway builds correct messages list from context history."""
    gw = CortexAgentGateway()

    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]

    messages = gw._build_messages(query="What's next?", history=history)  # type: ignore[attr-defined]
    assert isinstance(messages, list)
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[-1]["role"] == "user"


@pytest.mark.asyncio
async def test_agents_run_gateway_sse_parser_accumulates_text():
    """Test SSE parsing glue by stubbing _post_sse."""
    gw = CortexAgentGateway()
    with patch.object(gw, "_post_sse", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = ("final answer", [{"response": {"text": {"delta": "final answer"}}}])

        # Patch auth/host resolution to avoid config dependency
        with patch.object(gw, "_snowflake_api_base", return_value="https://example.snowflakecomputing.com"), \
             patch.object(gw, "_auth_headers", return_value={"Authorization": "Bearer x"}):
            # Provide required db/schema for agent object url path
            gw.snowflake_config.cortex_agents_database = "DB"
            gw.snowflake_config.cortex_agents_schema = "SCHEMA"

            result = await gw.invoke_agent(
                agent_name="MY_AGENT",
                query="Q",
                session_id="S",
                context={"history": [{"role": "user", "content": "hi"}]},
            )

        assert result["response"] == "final answer"
        assert result["agent_name"] == "MY_AGENT"

