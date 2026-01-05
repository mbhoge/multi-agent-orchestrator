# Postman API Specification for Multi-Agent Orchestrator

## Base URL

**Local Development:**
```
http://localhost:8000
```

**Production:**
```
https://your-domain.com
```

**Docker/Container:**
```
http://aws-agent-core:8000
```

---

## Updated API Endpoints

The FastAPI-based HTTP server has been removed. All API endpoints are now managed through AWS API Gateway.

### Updated Endpoints:
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/query` | Process a user query through the orchestrator |
| `POST` | `/api/teams/webhook` | Microsoft Teams webhook endpoint |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/metrics` | Get orchestrator metrics |

### Base URL:
```
https://your-api-gateway-url.amazonaws.com/prod
```

---

## API Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/query` | Process a user query through the orchestrator |
| `GET` | `/api/v1/health` | Health check endpoint |
| `GET` | `/api/v1/metrics` | Get orchestrator metrics |

---

## 1. Process Query Endpoint

### Endpoint Details

**URL:** `POST /api/v1/query`

**Description:** Process a user query through the multi-agent orchestrator. This endpoint routes the query through LangGraph supervisor to appropriate Snowflake Cortex AI agents.

### Headers

```
Content-Type: application/json
Accept: application/json
```

### Query Parameters (Optional)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | string | No | AWS Bedrock agent ID (if using AWS Agent Core) |
| `agent_alias_id` | string | No | AWS Bedrock agent alias ID (if using AWS Agent Core) |

### Request Body Schema

```json
{
  "query": "string (required)",
  "session_id": "string (optional)",
  "context": {
    "key": "value (optional)"
  },
  "agent_preference": "string (optional)",
  "metadata": {
    "key": "value (optional)"
  }
}
```

### Request Body Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `query` | string | **Yes** | User query or request | `"What are the total sales for last month?"` |
| `session_id` | string | No | Session ID for state management | `"session-123"` |
| `context` | object | No | Additional context for the request | `{"data_type": "structured"}` |
| `agent_preference` | string | No | Preferred Snowflake agent object name or domain (e.g., `market_segment`, `drug_discovery`) | `"market_segment"` |
| `metadata` | object | No | Request metadata | `{"user_id": "user-123", "request_id": "req-456"}` |

### Example Request 1: Basic Query

**URL:** `POST http://localhost:8000/api/v1/query`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "query": "What are the total sales for last month?",
  "session_id": "session-123"
}
```

### Example Request 2: Query with Context

**URL:** `POST http://localhost:8000/api/v1/query`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "query": "Analyze sales trends for Q4 2024",
  "session_id": "session-456",
  "context": {
    "data_type": "structured",
    "time_range": "Q4 2024",
    "department": "sales"
  },
  "agent_preference": "market_segment",
  "metadata": {
    "user_id": "user-789",
    "request_source": "web_app"
  }
}
```

### Example Request 3: Query with AWS Agent IDs

**URL:** `POST http://localhost:8000/api/v1/query?agent_id=AGENT123&agent_alias_id=ALIAS456`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "query": "Search for documents about machine learning",
  "session_id": "session-789",
  "context": {
    "data_type": "unstructured",
    "document_type": "research_papers"
  },
  "agent_preference": "drug_discovery"
}
```

### Response Schema

**Success Response (200 OK):**

```json
{
  "response": "string",
  "session_id": "string",
  "agent_used": "string",
  "confidence": 0.95,
  "sources": [
    {
      "type": "string",
      "reference": "string",
      "metadata": {}
    }
  ],
  "execution_time": 1.234,
  "metadata": {
    "trace_id": "string",
    "routing_reason": "string"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | Agent response text |
| `session_id` | string | Session identifier |
| `agent_used` | string | Agent object(s) that processed the request (Snowflake agent name(s) or "langgraph") |
| `confidence` | float | Confidence score (0.0 to 1.0) |
| `sources` | array | Source references used in the response |
| `execution_time` | float | Execution time in seconds |
| `metadata` | object | Response metadata (trace_id, routing_reason, etc.) |
| `timestamp` | string | Response timestamp (ISO 8601) |

### Example Response

```json
{
  "response": "The total sales for last month were $1,234,567. This represents a 15% increase compared to the previous month.",
  "session_id": "session-123",
  "agent_used": "MARKET_SEGMENT_AGENT",
  "confidence": 0.92,
  "sources": [
    {
      "type": "database",
      "reference": "sales_fact_table",
      "metadata": {
        "table": "sales_fact",
        "query": "SELECT SUM(amount) FROM sales_fact WHERE month = '2024-12'"
      }
    }
  ],
  "execution_time": 1.45,
  "metadata": {
    "trace_id": "trace-abc123",
    "routing_reason": "Query requires structured data analysis",
    "user_id": "user-789",
    "request_source": "web_app"
  },
  "timestamp": "2024-01-15T10:30:01.450Z"
}
```

### Error Response (500 Internal Server Error)

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Example Error Response

```json
{
  "detail": "Orchestration failed: LangGraph service unavailable"
}
```

---

## 2. Health Check Endpoint

### Endpoint Details

**URL:** `GET /api/v1/health`

**Description:** Check the health status of the orchestrator service.

### Headers

```
Accept: application/json
```

### Request

**URL:** `GET http://localhost:8000/api/v1/health`

No body or query parameters required.

### Response Schema

**Success Response (200 OK):**

```json
{
  "status": "healthy",
  "service": "aws-agent-core-orchestrator"
}
```

### Example Response

```json
{
  "status": "healthy",
  "service": "aws-agent-core-orchestrator"
}
```

---

## 3. Metrics Endpoint

### Endpoint Details

**URL:** `GET /api/v1/metrics`

**Description:** Get metrics from the orchestrator including request counts, timing, and performance data.

### Headers

```
Accept: application/json
```

### Request

**URL:** `GET http://localhost:8000/api/v1/metrics`

No body or query parameters required.

### Response Schema

**Success Response (200 OK):**

```json
{
  "counters": {
    "requests.total": 1000,
    "requests.success": 950,
    "requests.error": 50
  },
  "timings": {
    "request.processing": {
      "count": 1000,
      "sum": 1234.56,
      "avg": 1.23,
      "min": 0.45,
      "max": 5.67
    }
  },
  "gauges": {}
}
```

### Example Response

```json
{
  "counters": {
    "requests.total": 1250,
    "requests.success": 1200,
    "requests.error": 50
  },
  "timings": {
    "request.processing": {
      "count": 1250,
      "sum": 1875.0,
      "avg": 1.5,
      "min": 0.3,
      "max": 8.2
    },
    "langgraph.invocation": {
      "count": 1200,
      "sum": 960.0,
      "avg": 0.8,
      "min": 0.2,
      "max": 3.5
    }
  },
  "gauges": {
    "active_sessions": 15
  }
}
```

---

## Postman Collection Setup

### Environment Variables

Create a Postman environment with these variables:

| Variable | Initial Value | Current Value | Description |
|----------|---------------|---------------|-------------|
| `base_url` | `http://localhost:8000` | `http://localhost:8000` | Base URL for the API |
| `session_id` | `session-123` | `session-123` | Default session ID |
| `agent_id` | `` | `` | AWS Bedrock agent ID (optional) |
| `agent_alias_id` | `` | `` | AWS Bedrock agent alias ID (optional) |

### Collection Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `api_version` | `v1` | API version |
| `content_type` | `application/json` | Content type header |

---

## Complete Postman Request Examples

### 1. Process Query - Structured Data

**Method:** `POST`

**URL:** `{{base_url}}/api/{{api_version}}/query`

**Headers:**
```
Content-Type: {{content_type}}
Accept: {{content_type}}
```

**Body (raw JSON):**
```json
{
  "query": "What are the total sales for Q4 2024?",
  "session_id": "{{session_id}}",
  "context": {
    "data_type": "structured",
    "time_range": "Q4 2024"
  },
  "agent_preference": "market_segment",
  "metadata": {
    "user_id": "user-123",
    "request_source": "postman"
  }
}
```

### 2. Process Query - Unstructured Data

**Method:** `POST`

**URL:** `{{base_url}}/api/{{api_version}}/query`

**Headers:**
```
Content-Type: {{content_type}}
Accept: {{content_type}}
```

**Body (raw JSON):**
```json
{
  "query": "Find all documents related to machine learning best practices",
  "session_id": "{{session_id}}",
  "context": {
    "data_type": "unstructured",
    "document_type": "research_papers"
  },
  "agent_preference": "drug_discovery"
}
```

### 3. Process Query - With AWS Agent IDs

**Method:** `POST`

**URL:** `{{base_url}}/api/{{api_version}}/query?agent_id={{agent_id}}&agent_alias_id={{agent_alias_id}}`

**Headers:**
```
Content-Type: {{content_type}}
Accept: {{content_type}}
```

**Body (raw JSON):**
```json
{
  "query": "Analyze customer feedback from last quarter",
  "session_id": "{{session_id}}",
  "context": {
    "data_type": "mixed",
    "analysis_type": "sentiment"
  }
}
```

### 4. Health Check

**Method:** `GET`

**URL:** `{{base_url}}/api/{{api_version}}/health`

**Headers:**
```
Accept: {{content_type}}
```

### 5. Get Metrics

**Method:** `GET`

**URL:** `{{base_url}}/api/{{api_version}}/metrics`

**Headers:**
```
Accept: {{content_type}}
```

---

## Testing Scenarios

### Scenario 1: Basic Query Flow

1. **Health Check** → Verify service is running
2. **Process Query** → Send a simple query
3. **Get Metrics** → Check request was recorded

### Scenario 2: Session Management

1. **Process Query** → Send query with `session_id: "session-001"`
2. **Process Query** → Send follow-up query with same `session_id`
3. Verify context is maintained across requests

### Scenario 3: Error Handling

1. **Process Query** → Send invalid query (empty string)
2. Verify error response format
3. **Get Metrics** → Verify error counter incremented

### Scenario 4: Agent Selection

1. **Process Query** → Send query with `agent_preference: "market_segment"` (domain)
2. Verify response uses the market segment Snowflake agent object
3. **Process Query** → Send query with `agent_preference: "drug_discovery"` (domain)
4. Verify different domain agent is used

---

## Common Issues and Troubleshooting

### Issue: Connection Refused

**Error:** `Connection refused` or `ECONNREFUSED`

**Solution:**
- Verify the service is running: `docker-compose ps`
- Check the port: Default is `8000`
- Verify firewall settings

### Issue: 500 Internal Server Error

**Error:** `{"detail": "Orchestration failed: ..."}`

**Solution:**
- Check service logs: `docker-compose logs aws-agent-core`
- Verify LangGraph service is running
- Check environment variables are set correctly

### Issue: CORS Error

**Error:** CORS policy error in browser

**Solution:**
- CORS is configured to allow all origins (`allow_origins=["*"]`)
- For production, update CORS settings in `main.py`

### Issue: Timeout

**Error:** Request timeout

**Solution:**
- Increase timeout in Postman settings
- Check LangGraph timeout configuration
- Verify network connectivity

---

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

You can use these endpoints to explore the API interactively.

---

## Authentication (Future Enhancement)

Currently, the API does not require authentication. For production, consider adding:

- API Key authentication
- OAuth 2.0
- AWS IAM authentication
- JWT tokens

---

## Rate Limiting (Future Enhancement)

Currently, there are no rate limits. For production, consider implementing:

- Per-IP rate limiting
- Per-user rate limiting
- Request throttling

---

## Notes

1. **Session Management:** Use consistent `session_id` values to maintain conversation context
2. **Agent Preference:** The `agent_preference` field is a hint; LangGraph may override based on query analysis
3. **Context:** Provide relevant context to improve routing and response quality
4. **Metadata:** Use metadata to track requests across your system
5. **Error Handling:** Always check the response status code and handle errors appropriately

---

## Setting Up AWS SDK (Boto3) and Dependencies

### Prerequisites
1. Ensure you have Python 3 installed on your system.
2. Install `pip` (Python package manager) if not already installed.
3. Ensure you have access to the `requirements.txt` file in the project directory.

### Steps to Set Up
1. Navigate to the project directory:
   ```bash
   cd /path/to/project
   ```
2. Run the setup script:
   ```bash
   ./setup_aws_sdk.sh
   ```
3. The script will:
   - Check for Python 3 and `pip`.
   - Install `virtualenv` if not already installed.
   - Create a virtual environment and activate it.
   - Install dependencies from `requirements.txt` (including `boto3`).

### Expected Outcome
- A virtual environment (`venv`) will be created in the project directory.
- All dependencies, including `boto3`, will be installed.
- The setup is complete, and you can now interact with AWS services programmatically.

### Troubleshooting
- If you encounter permission issues, try running the script with `sudo`:
  ```bash
  sudo ./setup_aws_sdk.sh
  ```
- Ensure `requirements.txt` is present in the project directory. If not, manually install `boto3`:
  ```bash
  pip3 install boto3
  ```



