# Testing Snowflake Cortex AI Components

This guide explains how to test the Snowflake Cortex AI components independently.

## Prerequisites

1. **Snowflake Account**: You need a Snowflake account with:
   - Cortex AI enabled
   - Appropriate permissions to use Cortex AI functions
   - A warehouse, database, and schema configured

2. **Environment Configuration**: Set up your `.env` file with:
   ```bash
   SNOWFLAKE_ACCOUNT=your-account-identifier
   SNOWFLAKE_USER=your-username
   SNOWFLAKE_PASSWORD=your-password
   SNOWFLAKE_WAREHOUSE=your-warehouse
   SNOWFLAKE_DATABASE=your-database
   SNOWFLAKE_SCHEMA=PUBLIC
   SNOWFLAKE_ROLE=your-role  # Optional
   ```

3. **Python Dependencies**: Ensure you have installed:
   ```bash
   pip install snowflake-connector-python snowflake-snowpark-python
   ```

## Testing via Snowflake Cortex Agents Run (Recommended)

The current system design uses **Snowflake Cortex Agent objects** invoked via the
**Cortex Agents Run REST API**. The gateway service (`snowflake_cortex/gateway/api.py`)
is the only Snowflake-facing component you need to test locally.

### Using the Gateway Test Script

```bash
# Option 1: Direct Python execution
python tests/snowflake/test_gateway.py
```

### What It Tests

- Gateway health
- `/agents/invoke` calling Snowflake `/api/v2/.../agents/{agent_name}:run`
- `messages[]` built from history
- `tool_choice: {"type":"auto"}` (unless overridden via `context.tool_choice`)

### Expected Output

```
============================================================
Testing Snowflake Cortex AI Search
============================================================

✓ Snowflake configuration found
  Account: your-account
  User: your-user
  Warehouse: your-warehouse
  Database: your-database
  Schema: PUBLIC

Using stage path: @my_stage

============================================================
Test Query 1: machine learning
============================================================

✓ Search completed successfully

Response:
  Found 2 document(s) matching your search:
  1. document1.pdf (relevance: 95.00%)
  2. presentation1.pptx (relevance: 87.00%)

Sources found: 2
  1. document1.pdf (score: 95.00%)
  2. presentation1.pptx (score: 87.00%)
```

### Setting Up a Stage

Before testing, ensure you have a Snowflake stage with documents:

```sql
-- Create a stage
CREATE STAGE my_stage;

-- Upload files to the stage
PUT file:///path/to/document.pdf @my_stage;
PUT file:///path/to/presentation.pptx @my_stage;
```

### Troubleshooting

- **Stage Not Found**: Create a stage in Snowflake and set `SNOWFLAKE_STAGE_PATH`
- **No Documents**: Upload documents to your stage
- **Cortex Search Not Available**: Ensure Cortex AI Search is enabled in your account

## Testing Snowflake Cortex AI Agent Gateway

The Gateway provides a REST API to invoke all agent types.

### Starting the Gateway

```bash
# Option 1: Using Python module
python -m snowflake_cortex.gateway.api

# Option 2: Using uvicorn directly
uvicorn snowflake_cortex.gateway.api:app --host 0.0.0.0 --port 8002

# Option 3: Using the test script (starts gateway automatically)
./scripts/test_gateway.sh
```

### Using the Test Script

```bash
# The script will check if gateway is running and start it if needed
./scripts/test_gateway.sh

# Or test directly
python tests/snowflake/test_gateway.py
```

### What It Tests

- Gateway health endpoint
- Analyst agent invocation
- Search agent invocation
- Combined agent invocation
- Prompt management endpoints

### Expected Output

```
============================================================
Snowflake Cortex AI Agent Gateway Tests
============================================================

Testing Gateway Health Endpoint...
✓ Health check passed: {'status': 'healthy', 'service': 'snowflake-cortex-gateway'}

============================================================
Testing Cortex Analyst Agent
============================================================

Sending request to http://localhost:8002/agents/invoke
Query: What are the total sales?

✓ Request successful

Response:
  Found 1 result(s) for your query:
  Result 1: {'total': 1234567.89}

SQL Query:
  SELECT SUM(amount) as total FROM sales;

Sources: 1
  - {'type': 'structured_data', 'query': 'SELECT SUM(amount)...'}
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:8002/health

# Invoke a Snowflake Cortex Agent object (Agents Run REST API)
# NOTE: agent_name must match the Snowflake agent object name in your configured DB/SCHEMA.
curl -X POST http://localhost:8002/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "YOUR_ANALYST_AGENT_NAME",
    "query": "What are the total sales?",
    "session_id": "test-123",
    "context": {}
  }'

# Invoke Search agent object
curl -X POST http://localhost:8002/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "YOUR_SEARCH_AGENT_NAME",
    "query": "machine learning",
    "session_id": "test-456",
    "context": {"stage_path": "@my_stage"}
  }'

# Get a prompt
curl http://localhost:8002/prompts/supervisor_routing
```

### Direct `agent:run` mode (no agent object) with `tool_resources` (concrete example)

Use this when you want to call Snowflake `POST /api/v2/cortex/agent:run` **directly** (without a Snowflake agent object),
and provide tool configuration in the request body. This follows Snowflake’s tool schema:
[`ToolResource` reference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run#toolresource).

**Request (to this project’s gateway)**:

```bash
curl -X POST http://localhost:8002/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "direct",
    "query": "For 2023, what is total revenue? Also provide relevant supporting documents.",
    "session_id": "session-789",
    "context": {
      "domain": "market_segment",
      "history": [
        {"role": "user", "content": "We are analyzing 2023 performance."},
        {"role": "assistant", "content": "Okay—what metric do you need?"}
      ],
      "tool_choice": {"type": "auto", "name": ["analyst_tool", "search_tool"]},
      "tool_resources": {
        "analyst_tool": {
          "semantic_model_file": "@DB.SCHEMA.STAGE/semantic_model.yaml",
          "execution_environment": {
            "type": "warehouse",
            "warehouse": "MY_WAREHOUSE",
            "query_timeout": 60
          }
        },
        "search_tool": {
          "search_service": "DB.SCHEMA.MY_SEARCH_SERVICE",
          "title_column": "account_name",
          "id_column": "account_id",
          "filter": {
            "@eq": {
              "year": 2023
            }
          }
        }
      }
    }
  }'
```

**What happens:**
- The gateway detects `context.tool_resources` and routes the call to Snowflake `POST /api/v2/cortex/agent:run`
- The gateway builds `messages[]` from `context.history` + current `query`
- Snowflake orchestrates tool usage automatically (constrained to the provided tool names if you set `tool_choice.name`)

### API Endpoints

- `GET /health` - Health check
- `POST /agents/invoke` - Invoke an agent
  - Body: `{"agent_name": "<snowflake_agent_object_name>", "query": "...", "session_id": "...", "context": {...}}`
- `GET /prompts/{prompt_name}` - Get a prompt
- `POST /prompts` - Create a prompt

## Testing Order

Recommended testing order:

1. **First**: Test the Snowflake Gateway (Agents Run REST API)
   ```bash
   ./scripts/test_gateway.sh
   ```

## Common Issues

### Snowflake Connection Issues

- Verify credentials in `.env`
- Check network connectivity
- Ensure warehouse is running
- Verify user permissions

### Cortex AI Not Available

- Ensure Cortex AI is enabled in your Snowflake account
- Check account type (some features require Enterprise edition)
- Verify user has `USAGE` privilege on Cortex AI functions

### Import Errors

- Ensure you're in the project root directory
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### Port Already in Use

If port 8002 is already in use:
```bash
# Find the process
lsof -i :8002

# Kill it
kill -9 <PID>

# Or use a different port
uvicorn snowflake_cortex.gateway.api:app --host 0.0.0.0 --port 8003
```

## Next Steps

After successfully testing individual components:

1. Test the full integration with LangGraph
2. Test the complete orchestration flow
3. Deploy to AWS using Terraform
4. Monitor with observability tools (Langfuse, TruLens)

