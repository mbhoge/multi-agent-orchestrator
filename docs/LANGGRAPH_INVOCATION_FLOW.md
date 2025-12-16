# LangGraph Agent Invocation Flow from AWS Agent Core

## Overview

This document explains how the LangGraph agent is triggered when a request comes through AWS Agent Core orchestrator.

## 📊 Complete Visual Process Flow

For a **comprehensive pictorial representation** with detailed process flow, prompt management, observability (logging and tracing), state management, and memory operations, see:

**[COMPLETE_PROCESS_FLOW_DIAGRAM.md](./COMPLETE_PROCESS_FLOW_DIAGRAM.md)**

The complete diagram includes:
- ✅ Full data flow visualization
- ✅ Prompt management integration points
- ✅ Observability checkpoints (AWS Tracing, Langfuse, Metrics, TruLens)
- ✅ State management lifecycle
- ✅ Memory management (short-term and long-term)
- ✅ All HTTP communication flows
- ✅ Data transformations at each step
- ✅ Error handling paths

---

## Simplified Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Client Request                                               │
│    POST /api/v1/query                                           │
│    { "query": "What are sales?", "session_id": "session-123" }   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FastAPI Route Handler                                        │
│    aws_agent_core/api/routes.py                                 │
│    @router.post("/query")                                       │
│    → process_query()                                            │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. MultiAgentOrchestrator                                       │
│    aws_agent_core/orchestrator.py                               │
│    → process_request()                                         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Invoke LangGraph (HTTP Call)                                │
│    _invoke_langgraph()                                          │
│    POST http://langgraph:8001/supervisor/process                │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. LangGraph Supervisor                                         │
│    langgraph/supervisor.py                                      │
│    → process_request()                                          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Agent Router                                                 │
│    langgraph/reasoning/router.py                               │
│    → route_request()                                            │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Invoke Snowflake Agent                                       │
│    → _invoke_snowflake_agent()                                  │
│    POST http://snowflake-cortex:8002/agents/invoke              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Response Flow Back                                           │
│    Snowflake → LangGraph → AWS Agent Core → Client              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Code Flow

### Step 1: Request Arrives at FastAPI

**File:** `aws_agent_core/api/routes.py`

```python
@router.post("/query", response_model=AgentResponse)
async def process_query(
    request: AgentRequest,
    orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator),
    agent_id: Optional[str] = None,
    agent_alias_id: Optional[str] = None
):
    # Calls orchestrator.process_request()
    response = await orchestrator.process_request(
        request=request,
        agent_id=agent_id,
        agent_alias_id=agent_alias_id
    )
    return response
```

**What happens:**
- FastAPI receives POST request to `/api/v1/query`
- Request body is parsed into `AgentRequest` object
- Dependency injection provides `MultiAgentOrchestrator` instance
- Calls `orchestrator.process_request()`

---

### Step 2: Orchestrator Processes Request

**File:** `aws_agent_core/orchestrator.py`

```python
async def process_request(
    self,
    request: AgentRequest,
    agent_id: Optional[str] = None,
    agent_alias_id: Optional[str] = None
) -> AgentResponse:
    # Step 0: Get orchestrator prompt (optional)
    orchestrator_prompt = await self._get_orchestrator_prompt(request)
    
    # Step 1: Invoke LangGraph via HTTP
    langgraph_response = await self._invoke_langgraph(request, session_id)
    
    # Step 2: Extract routing decision
    selected_agent = langgraph_response.get("selected_agent")
    
    # Step 3: Use AWS Agent Core if configured, otherwise use LangGraph response
    if agent_id and agent_alias_id:
        # Use AWS Agent Core Runtime SDK
        agent_result = self.runtime_client.invoke_agent(...)
    else:
        # Use direct LangGraph response
        final_response = langgraph_response.get("response", "")
    
    # Step 4: Build and return response
    return AgentResponse(...)
```

**Key Points:**
- Orchestrator acts as the coordinator
- It decides whether to use AWS Agent Core SDK or direct LangGraph call
- If no AWS agent IDs provided, it calls LangGraph directly

---

### Step 3: HTTP Call to LangGraph

**File:** `aws_agent_core/orchestrator.py` (lines 123-162)

```python
async def _invoke_langgraph(
    self,
    request: AgentRequest,
    session_id: str
) -> Dict[str, Any]:
    """Invoke LangGraph supervisor via HTTP."""
    async with httpx.AsyncClient(timeout=self.langgraph_timeout) as client:
        response = await client.post(
            f"{self.langgraph_endpoint}/supervisor/process",
            json={
                "query": request.query,
                "session_id": session_id,
                "context": request.context,
                "agent_preference": request.agent_preference,
            }
        )
        response.raise_for_status()
        return response.json()
```

**Configuration:**
- **Endpoint:** `settings.langgraph.langgraph_endpoint` (default: `http://langgraph:8001`)
- **Path:** `/supervisor/process`
- **Method:** POST
- **Timeout:** `settings.langgraph.langgraph_timeout` (default: 300 seconds)

**Request Payload:**
```json
{
  "query": "What are the total sales for last month?",
  "session_id": "session-123",
  "context": {
    "data_type": "structured"
  },
  "agent_preference": "cortex_analyst"
}
```

---

### Step 4: LangGraph Supervisor Receives Request

**File:** `langgraph/supervisor.py` (lines 213-240)

```python
@app.post("/supervisor/process")
async def process_supervisor_request(request: Dict[str, Any]):
    """Process a request through the LangGraph supervisor."""
    agent_request = AgentRequest(
        query=request.get("query", ""),
        session_id=request.get("session_id"),
        context=request.get("context"),
        agent_preference=request.get("agent_preference")
    )
    
    response = await supervisor.process_request(
        request=agent_request,
        session_id=agent_request.session_id or f"session_{int(time.time() * 1000)}"
    )
    
    return response
```

**What happens:**
- FastAPI endpoint receives HTTP POST request
- Converts dictionary to `AgentRequest` object
- Calls `supervisor.process_request()`

---

### Step 5: LangGraph Supervisor Processing

**File:** `langgraph/supervisor.py` (lines 28-155)

```python
async def process_request(
    self,
    request: AgentRequest,
    session_id: str
) -> Dict[str, Any]:
    # 1. Initialize or retrieve state
    state = state_manager.get_state(session_id)
    
    # 2. Update state to processing
    state_manager.update_state(session_id, {
        "status": RequestStatus.PROCESSING,
        "current_step": "routing"
    })
    
    # 3. Get prompt for routing decision
    routing_prompt = await self.langfuse_client.get_prompt_for_routing(
        query=request.query,
        context=request.context
    )
    
    # 4. Route request to appropriate agent
    routing_decision = agent_router.route_request(
        query=routing_prompt,
        context=request.context,
        agent_preference=request.agent_preference
    )
    
    # 5. Store in short-term memory
    short_term_memory.store(...)
    
    # 6. Invoke Snowflake Cortex AI agent
    agent_response = await self._invoke_snowflake_agent(
        agent_type=routing_decision["selected_agent"],
        query=request.query,
        session_id=session_id,
        context=request.context
    )
    
    # 7. Update state with response
    state_manager.update_state(session_id, {
        "status": RequestStatus.COMPLETED,
        "final_response": agent_response.get("response", "")
    })
    
    # 8. Store in long-term memory if significant
    if routing_decision.get("confidence", 0) > 0.8:
        long_term_memory.store(...)
    
    # 9. Log to Langfuse
    await self.langfuse_client.log_supervisor_decision(...)
    
    # 10. Return response
    return {
        "response": agent_response.get("response", ""),
        "selected_agent": routing_decision["selected_agent"].value,
        "routing_reason": routing_decision["routing_reason"],
        "confidence": routing_decision.get("confidence", 0.5),
        "sources": agent_response.get("sources", []),
        "execution_time": execution_time,
        "session_id": session_id
    }
```

**Key Operations:**
1. **State Management:** Maintains conversation state
2. **Prompt Management:** Gets routing prompts from Langfuse
3. **Agent Routing:** Uses `agent_router` to decide which agent to use
4. **Memory Management:** Stores in short-term and long-term memory
5. **Agent Invocation:** Calls Snowflake Cortex AI agents
6. **Observability:** Logs to Langfuse

---

### Step 6: Agent Router Decision

**File:** `langgraph/reasoning/router.py`

```python
def route_request(
    self,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    agent_preference: Optional[str] = None
) -> Dict[str, Any]:
    """
    Route request to appropriate agent based on query analysis.
    
    Returns:
        {
            "selected_agent": AgentType,
            "routing_reason": str,
            "confidence": float
        }
    """
    # Analyze query to determine which agent to use
    # - cortex_analyst: For structured data queries
    # - cortex_search: For unstructured data queries
    # Returns routing decision
```

**Routing Logic:**
- Analyzes query content
- Considers context (data_type, etc.)
- Respects agent_preference if provided
- Returns selected agent with confidence score

---

### Step 7: Invoke Snowflake Agent

**File:** `langgraph/supervisor.py` (lines 157-200)

```python
async def _invoke_snowflake_agent(
    self,
    agent_type: AgentType,
    query: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Invoke Snowflake Cortex AI agent via gateway."""
    async with httpx.AsyncClient(timeout=settings.langgraph.langgraph_timeout) as client:
        response = await client.post(
            f"{settings.snowflake.cortex_agent_gateway_endpoint}/agents/invoke",
            json={
                "agent_type": agent_type.value,
                "query": query,
                "session_id": session_id,
                "context": context or {}
            }
        )
        response.raise_for_status()
        return response.json()
```

**Configuration:**
- **Endpoint:** `settings.snowflake.cortex_agent_gateway_endpoint` (default: `http://snowflake-cortex:8002`)
- **Path:** `/agents/invoke`
- **Method:** POST

---

## Two Invocation Paths

### Path 1: Direct LangGraph Invocation (Current Implementation)

```
AWS Agent Core → HTTP → LangGraph → Snowflake Agent
```

**When used:**
- No `agent_id` and `agent_alias_id` provided in request
- Direct orchestration without AWS Bedrock Agent Core

**Code Path:**
```python
# orchestrator.py line 72
langgraph_response = await self._invoke_langgraph(request, session_id)

# orchestrator.py line 92-94
final_response = langgraph_response.get("response", "")
```

---

### Path 2: AWS Agent Core Runtime SDK (Future/Alternative)

```
AWS Agent Core → AWS Bedrock Agent Core Runtime SDK → LangGraph → Snowflake Agent
```

**When used:**
- `agent_id` and `agent_alias_id` provided in request
- Using AWS Bedrock Agent Core managed infrastructure

**Code Path:**
```python
# orchestrator.py line 79-88
if agent_id and agent_alias_id:
    agent_result = self.runtime_client.invoke_agent(
        agent_id=agent_id,
        agent_alias_id=agent_alias_id,
        session_id=session_id,
        input_text=request.query,
        enable_trace=True
    )
    final_response = agent_result.get("completion", "")
```

**Note:** In this path, AWS Agent Core Runtime SDK would internally route to LangGraph (if configured in the Bedrock agent).

---

## Configuration

### Environment Variables

**AWS Agent Core Orchestrator:**
```bash
LANGGRAPH_ENDPOINT=http://langgraph:8001
LANGGRAPH_TIMEOUT=300
```

**LangGraph Supervisor:**
```bash
LANGFUSE_HOST=http://langfuse:3000
SNOWFLAKE_CORTEX_AGENT_GATEWAY_ENDPOINT=http://snowflake-cortex:8002
```

### Docker Compose Network

All services communicate via Docker network:
- `aws-agent-core:8000` → `langgraph:8001`
- `langgraph:8001` → `snowflake-cortex:8002`

---

## Request/Response Flow

### Request Flow

```json
// 1. Client → AWS Agent Core
POST /api/v1/query
{
  "query": "What are sales?",
  "session_id": "session-123"
}

// 2. AWS Agent Core → LangGraph
POST http://langgraph:8001/supervisor/process
{
  "query": "What are sales?",
  "session_id": "session-123",
  "context": {},
  "agent_preference": null
}

// 3. LangGraph → Snowflake Agent
POST http://snowflake-cortex:8002/agents/invoke
{
  "agent_type": "cortex_analyst",
  "query": "What are sales?",
  "session_id": "session-123",
  "context": {}
}
```

### Response Flow

```json
// 1. Snowflake Agent → LangGraph
{
  "response": "Sales are $1M",
  "sources": [...]
}

// 2. LangGraph → AWS Agent Core
{
  "response": "Sales are $1M",
  "selected_agent": "cortex_analyst",
  "routing_reason": "Query requires structured data",
  "confidence": 0.95,
  "sources": [...],
  "execution_time": 1.5,
  "session_id": "session-123"
}

// 3. AWS Agent Core → Client
{
  "response": "Sales are $1M",
  "session_id": "session-123",
  "agent_used": "cortex_analyst",
  "confidence": 0.95,
  "sources": [...],
  "execution_time": 1.5,
  "metadata": {
    "trace_id": "...",
    "routing_reason": "Query requires structured data"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## Key Components

### 1. HTTP Client (httpx)

**Used in:**
- `aws_agent_core/orchestrator.py` → Calls LangGraph
- `langgraph/supervisor.py` → Calls Snowflake agents

**Why httpx:**
- Async/await support
- Better timeout handling
- Modern Python HTTP client

### 2. State Management

**Used in:**
- `langgraph/state/state_manager.py`

**Purpose:**
- Maintains conversation state
- Tracks request status
- Stores routing decisions

### 3. Memory Management

**Used in:**
- `langgraph/memory/short_term.py` → Session-level memory
- `langgraph/memory/long_term.py` → Persistent memory

**Purpose:**
- Short-term: Current session context
- Long-term: Learning from past interactions

### 4. Observability

**Used in:**
- `langgraph/observability/langfuse_client.py` → Langfuse logging
- `aws_agent_core/observability/tracing.py` → AWS tracing
- `aws_agent_core/observability/metrics.py` → Metrics collection

---

## Error Handling

### HTTP Errors

```python
# orchestrator.py
except httpx.HTTPError as e:
    logger.error(f"HTTP error invoking LangGraph: {str(e)}")
    raise LangGraphError(f"Failed to invoke LangGraph: {str(e)}") from e
```

### General Errors

```python
# supervisor.py
except Exception as e:
    logger.error(f"Error in LangGraph supervisor: {str(e)}")
    state_manager.update_state(session_id, {
        "status": RequestStatus.FAILED,
        "error": str(e)
    })
    raise LangGraphError(f"Supervisor processing failed: {str(e)}") from e
```

---

## Summary

1. **Request arrives** at AWS Agent Core FastAPI endpoint
2. **Orchestrator** receives request and prepares to invoke LangGraph
3. **HTTP call** made to LangGraph supervisor endpoint (`/supervisor/process`)
4. **LangGraph supervisor** processes request:
   - Manages state
   - Routes to appropriate agent
   - Invokes Snowflake agent
   - Returns response
5. **Response flows back** through the chain to the client

**Key Point:** LangGraph is triggered via **HTTP POST request** from the AWS Agent Core orchestrator, not through AWS Bedrock Agent Core Runtime SDK (unless agent IDs are provided).
