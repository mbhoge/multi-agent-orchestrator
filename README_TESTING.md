# Quick Testing Guide

## Testing Snowflake Cortex AI Components

### 1. Test Snowflake Cortex AI Agent Gateway (Agents Run REST)

**Step 1: Start the Gateway**
```bash
# Option 1
python -m snowflake_cortex.gateway.api

# Option 2
uvicorn snowflake_cortex.gateway.api:app --host 0.0.0.0 --port 8002
```

**Step 2: Run Tests**
```bash
./scripts/test_gateway.sh
```

**Or directly:**
```bash
python tests/snowflake/test_gateway.py
```

**What it tests:**
- Gateway health endpoint
- Snowflake agent object(s) via Agents Run REST API
- Prompt management endpoints

**Manual Testing with curl:**
```bash
# Health check
curl http://localhost:8002/health

# Invoke Snowflake Cortex Agent object (Agents Run REST API)
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
```

---

## Environment Setup

Create `.env` file with:
```bash
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=PUBLIC
```

## Full Documentation

See `docs/TESTING_SNOWFLAKE.md` for detailed testing instructions.

