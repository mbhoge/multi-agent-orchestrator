# Quick Testing Guide

## Testing Snowflake Cortex AI Components

### 1. Test Snowflake Cortex AI Analyst

**Command:**
```bash
./scripts/test_analyst.sh
```

**Or directly:**
```bash
python tests/snowflake/test_analyst.py
```

**What it does:**
- Connects to Snowflake
- Converts natural language queries to SQL using Cortex AI Analyst
- Executes SQL queries
- Displays results

**Requirements:**
- Snowflake credentials in `.env` file
- Cortex AI enabled in Snowflake account

---

### 2. Test Snowflake Cortex AI Search

**Command:**
```bash
./scripts/test_search.sh
```

**Or directly:**
```bash
python tests/snowflake/test_search.py
```

**With custom stage:**
```bash
SNOWFLAKE_STAGE_PATH=@my_stage python tests/snowflake/test_search.py
```

**What it does:**
- Connects to Snowflake
- Searches unstructured data in Snowflake stages
- Uses Cortex AI Search function
- Displays search results with relevance scores

**Requirements:**
- Snowflake credentials in `.env` file
- A Snowflake stage with documents
- Cortex AI Search enabled

---

### 3. Test Snowflake Cortex AI Agent Gateway

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
- Analyst agent via API
- Search agent via API
- Combined agent via API
- Prompt management endpoints

**Manual Testing with curl:**
```bash
# Health check
curl http://localhost:8002/health

# Invoke Analyst
curl -X POST http://localhost:8002/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "cortex_analyst",
    "query": "What are the total sales?",
    "session_id": "test-123",
    "context": {}
  }'

# Invoke Search
curl -X POST http://localhost:8002/agents/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "cortex_search",
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

