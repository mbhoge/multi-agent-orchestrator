## AWS AgentCore Integration

This package provides:

- A **local HTTP server** (for AgentCore dev/runtime parity) with `/ping` and
  `/invocations` endpoints.
- A **Lambda handler** (`agentcore_gateway_handler.py`) that invokes the
  AgentCore Runtime SDK, which in turn calls the LangGraph supervisor running
  in Snowflake Container Services (SPCS).

### Architecture Flow

**Production path:**
`API Gateway` → `Lambda (agentcore_gateway_handler)` → `AgentCore Runtime SDK`
→ `AgentCore Gateway` → `LangGraph Supervisor (SPCS)` → `Snowflake Cortex Agents`

**Local/dev path:**
`AgentCore CLI (agentcore dev)` → `aws_agent_core.api` → `LangGraph Supervisor`

### Project Structure

```
aws_agent_core/
├── api/                       # Local AgentCore-compatible HTTP server
│   ├── __init__.py
│   ├── __main__.py            # Entry point for python -m aws_agent_core.api
│   └── main.py                # /ping and /invocations handlers
├── lambda_handlers/
│   ├── __init__.py
│   └── agentcore_gateway_handler.py  # Lambda handler for AgentCore Runtime SDK
├── runtime/
│   ├── __init__.py
│   └── sdk_client.py           # AgentCore Runtime SDK wrapper
└── orchestrator.py             # Orchestrator wrapper for local dev
```

### AgentCore Gateway Lambda Target

Use `aws_agent_core/lambda_handlers/agentcore_gateway_handler.py` when the
Lambda function must **invoke the AgentCore Runtime SDK**, which then routes
requests through the configured AgentCore Gateway and into the LangGraph
supervisor running in SPCS.

### Quickstart (AgentCore CLI)

1. Install the AgentCore starter toolkit:

```bash
pip install bedrock-agentcore-starter-toolkit
```

2. Create a local agent (pick LangGraph when prompted):

```bash
agentcore create
```

3. Run the local dev server:

```bash
agentcore dev
```

This server listens on port `8080` and expects JSON payloads at `/invocations`.

### Local Run (without AgentCore CLI)

```bash
python -m aws_agent_core.api
```

### Request Shape

```json
{
  "query": "What are the top 3 deals this quarter?",
  "session_id": "session-123",
  "context": {"domain": "market_segment"},
  "agent_preference": null,
  "metadata": {}
}
```

The server also accepts `prompt` as an alias for `query`.

### Required Environment Variables (Lambda)

- `AGENTCORE_AGENT_ID` - AgentCore Agent ID
- `AGENTCORE_AGENT_ALIAS_ID` - AgentCore Agent Alias ID
- `AWS_REGION` - AWS region for the runtime client
