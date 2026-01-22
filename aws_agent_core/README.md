## AWS AgentCore Local Agent

This package exposes a local HTTP server compatible with the AgentCore runtime
requirements (`/ping` and `/invocations`) and forwards requests to the
LangGraph supervisor.

### AgentCore Gateway Lambda Target

Use `aws_agent_core/lambda_handlers/agentcore_gateway_handler.py` when the
Lambda function needs to **invoke the AgentCore Runtime SDK**, which then routes
requests through the configured AgentCore Gateway and into the LangGraph supervisor.

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
