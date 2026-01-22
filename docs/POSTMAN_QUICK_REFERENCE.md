# Postman Quick Reference Guide

## Quick Setup

### 1. Import Collection
1. Open Postman
2. Click **Import** button
3. Select `Multi-Agent_Orchestrator.postman_collection.json`
4. Click **Import**

### 2. Import Environment
1. Click **Environments** in left sidebar
2. Click **Import**
3. Select `Multi-Agent_Orchestrator.postman_environment.json`
4. Select the environment from dropdown

### 3. Start Service
```bash
# Local development
./scripts/run_local.sh

# Or with Docker Compose
docker-compose up aws-agent-core
```

---

## Endpoints at a Glance

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/invocations` | POST | Process user query |
| `/ping` | GET | Health check |
| `/ping` | GET | Readiness check |

---

## Quick Request Examples

### Process Query (Minimal)
```json
POST http://localhost:8080/invocations
Content-Type: application/json

{
  "query": "What are the total sales for last month?"
}
```

### Process Query (Full)
```json
POST http://localhost:8080/invocations
Content-Type: application/json

{
  "query": "Analyze sales trends",
  "session_id": "session-123",
  "context": {
    "data_type": "structured"
  },
  "agent_preference": "market_segment",
  "metadata": {
    "user_id": "user-123"
  }
}
```

### Health Check
```
GET http://localhost:8080/ping
```

### Get Metrics
```
GET http://localhost:8080/ping
```

---

## Request Body Schema

### Required Fields
- `query` (string) - User query

### Optional Fields
- `session_id` (string) - Session identifier
- `context` (object) - Additional context
- `agent_preference` (string) - Preferred agent
- `metadata` (object) - Request metadata

---

## Response Schema

### Success Response (200)
```json
{
  "response": "string",
  "session_id": "string",
  "agent_used": "string",
  "confidence": 0.95,
  "sources": [],
  "execution_time": 1.23,
  "metadata": {},
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Error Response (500)
```json
{
  "detail": "Error message"
}
```

---

## Query Parameters

### Process Query Endpoint
- `agent_id` (optional) - AWS Bedrock agent ID
- `agent_alias_id` (optional) - AWS Bedrock agent alias ID

**Example:**
```
POST /invocations
```

---

## Common Use Cases

### 1. Structured Data Query
```json
{
  "query": "What are the total sales?",
  "context": {
    "data_type": "structured"
  },
  "agent_preference": "market_segment"
}
```

### 2. Unstructured Data Query
```json
{
  "query": "Find documents about AI",
  "context": {
    "data_type": "unstructured"
  },
  "agent_preference": "drug_discovery"
}
```

### 3. Session-based Conversation
```json
// First request
{
  "query": "What are sales for Q1?",
  "session_id": "session-001"
}

// Follow-up request
{
  "query": "What about Q2?",
  "session_id": "session-001"
}
```

---

## Testing Checklist

- [ ] Service is running (check health endpoint)
- [ ] Base URL is correct in environment
- [ ] Content-Type header is set to `application/json`
- [ ] Request body is valid JSON
- [ ] Session ID is provided for stateful requests
- [ ] Response status is 200 for success
- [ ] Response contains required fields

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check if service is running on port 8000 |
| 500 Internal Server Error | Check service logs |
| Invalid JSON | Validate JSON syntax |
| CORS error | Check CORS configuration in main.py |

---

## API Documentation URLs

- **Health**: http://localhost:8080/ping

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `base_url` | `http://localhost:8080` | API base URL |
| `api_version` | `v1` | API version |
| `session_id` | `session-123` | Default session ID |
| `agent_id` | `` | AWS agent ID (optional) |
| `agent_alias_id` | `` | AWS agent alias ID (optional) |

---

## Notes

- Use consistent `session_id` for conversation context
- `agent_preference` is a hint; LangGraph may override
- Provide relevant `context` for better routing
- Check `execution_time` in response for performance monitoring
- Use `metadata` field to track requests across your system



