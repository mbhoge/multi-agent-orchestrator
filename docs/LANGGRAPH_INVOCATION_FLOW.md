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
│ 2. Lambda Handler                                                │
│    AWS Lambda function (via API Gateway)                        │
│    → Extracts AgentRequest from event                            │
│    → Calls orchestrator.process_request()                        │
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

### Step 1: Request Arrives at Lambda Handler

**File:** AWS Lambda function handler (configured via API Gateway)

```python
# Lambda handler receives API Gateway event
def lambda_handler(event, context):
    # Extract request from API Gateway event
    request_body = json.loads(event.get("body", "{}"))
    
    # Create AgentRequest from event
    request = AgentRequest(
        query=request_body.get("query", ""),
        session_id=request_body.get("session_id"),
        context=request_body.get("context"),
        agent_preference=request_body.get("agent_preference")
    )
    
    # Create orchestrator instance
    orchestrator = MultiAgentOrchestrator()
    
    # Process request
    response = await orchestrator.process_request(
        request=request,
        agent_id=request_body.get("agent_id"),
        agent_alias_id=request_body.get("agent_alias_id")
    )
    
    return {
        "statusCode": 200,
        "body": json.dumps(response.dict())
    }
```

**What happens:**
- Lambda handler receives POST request from API Gateway at `/api/v1/query`
- Request body is extracted from API Gateway event
- Request body is parsed into `AgentRequest` object
- Creates `MultiAgentOrchestrator` instance
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
  "agent_preference": "market_segment"
}
```

---

### Step 4: LangGraph Supervisor Receives Request

**File:** `langgraph/supervisor.py` (lines 36-86)

The LangGraph supervisor is invoked via HTTP POST request. The supervisor receives the request and processes it through the StateGraph workflow:

```python
# In orchestrator.py - HTTP call to LangGraph
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

**What happens:**
- HTTP POST request is made to LangGraph endpoint (typically via Lambda/API Gateway or direct HTTP)
- LangGraph supervisor's `process_request()` method is called
- Converts request to initial state and invokes StateGraph workflow

---

### Step 5: LangGraph Supervisor Processing (StateGraph Workflow)

**File:** `langgraph/supervisor.py` and `langgraph/supervisor/graph.py`

The supervisor now uses LangGraph's **StateGraph** pattern for declarative workflow management. The processing is handled through a graph of nodes:

```python
async def process_request(
    self,
    request: AgentRequest,
    session_id: str
) -> Dict[str, Any]:
    # Convert AgentRequest to initial state
    initial_state = {
        "query": request.query,
        "session_id": session_id,
        "messages": [],
        "routing_decision": None,
        "agent_responses": [],
        "final_response": None,
        "status": "processing",
        "metadata": {
            **(request.metadata or {}),
            "agent_preference": request.agent_preference,
        },
        "context": request.context or {},
    }
    
    # Invoke StateGraph with thread_id for state correlation
    config = {"configurable": {"thread_id": session_id}}
    result = await self.graph.ainvoke(initial_state, config=config)
    
    # Convert result to response format
    return self._format_response(result)
```

**StateGraph Workflow Nodes:**

The workflow consists of the following nodes executed in sequence with conditional error handling:

1. **`load_state`** - Loads conversation history from short-term memory and appends current user message
   - Retrieves prior conversation history from `short_term_memory`
   - Appends current user query to history
   - Initializes state fields (status, start_time, etc.)

2. **`route_request`** - Gets routing prompt from Langfuse and calls agent_router to determine which agents to invoke
   - Fetches `supervisor_routing` prompt from Langfuse
   - Calls `agent_router.route_request()` to determine which Snowflake agent(s) to call
   - Stores routing decision in state (agents_to_call, routing_reason, confidence)
   - **Conditional edge:** Routes to `handle_error` if status="failed", otherwise continues to `invoke_agents`

3. **`invoke_agents`** - Invokes one or more Snowflake Cortex AI agents based on routing decision
   - Iterates through `agents_to_call` from routing decision
   - Calls `_invoke_snowflake_agent()` for each agent (via HTTP to Snowflake gateway)
   - Collects all agent responses in `agent_responses` array
   - **Conditional edge:** Routes to `handle_error` if status="failed", otherwise continues to `combine_responses`

4. **`combine_responses`** - Combines responses from multiple agents if needed
   - If single agent: uses response directly
   - If multiple agents: combines with agent labels and merges sources
   - Sets `final_response` in state
   - **Conditional edge:** Routes to `handle_error` if status="failed", otherwise continues to `update_memory`

5. **`update_memory`** - Updates short-term and long-term memory with conversation history
   - Appends assistant response to message history
   - Stores updated history in `short_term_memory` (bounded window, max 30 messages)
   - Optionally stores patterns in `long_term_memory` if confidence is high
   - **Regular edge:** Always continues to `log_observability`

6. **`log_observability`** - Logs to Langfuse for observability
   - Logs trace to Langfuse with full state information
   - Calculates execution time
   - Sets final status to "completed"
   - **Regular edge:** Always ends workflow (END)

7. **`handle_error`** - Handles errors if any node sets status to "failed"
   - Logs error details
   - Sets status to "failed" and current_step to "error_handled"
   - **Regular edge:** Always ends workflow (END)

**Graph Structure:**
- **START** → `load_state` → `route_request` → (conditional) → `invoke_agents` → (conditional) → `combine_responses` → (conditional) → `update_memory` → `log_observability` → **END**
- **Error path:** Any node can route to `handle_error` → **END** via conditional edges
- **Conditional edges:** Check `state["status"] == "failed"` to route to error handler

**Key Operations:**
1. **StateGraph Management:** LangGraph handles state automatically through the graph (no manual state_manager calls)
2. **Prompt Management:** Gets routing prompts from Langfuse (in `route_request` node)
3. **Agent Routing:** Uses `agent_router` to decide which agent(s) to use (in `route_request` node)
4. **Memory Management:** Stores in short-term and long-term memory (in `update_memory` node)
5. **Agent Invocation:** Calls Snowflake Cortex AI agents via HTTP (in `invoke_agents` node)
6. **Observability:** Logs to Langfuse (in `log_observability` node)
7. **Error Handling:** Conditional edges automatically route to `handle_error` when status is "failed"

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
            "agents_to_call": List[str],  # Snowflake agent object name(s)
            "routing_reason": str,
            "confidence": float
        }
    """
    # Analyze query to determine which DOMAIN agent object(s) to call
    # - market_segment: segmentation / retention / cohort analytics
    # - drug_discovery: compounds / targets / assays / clinical queries
    # Returns routing decision (agent object names)
```

**Routing Logic:**
- Analyzes query content
- Considers context (data_type, etc.)
- Respects agent_preference if provided
- Returns selected agent with confidence score

---

### Step 7: Invoke Snowflake Agent

**File:** `langgraph/supervisor/graph.py` (lines 405-448)

The `invoke_agents` node calls `_invoke_snowflake_agent()` to invoke Snowflake Cortex AI agents:

```python
async def _invoke_snowflake_agent(
    agent_name: str,
    query: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Invoke Snowflake Cortex AI agent via gateway."""
    logger.info(f"Invoking Snowflake agent {agent_name} for session {session_id}")
    
    import httpx
    try:
        async with httpx.AsyncClient(timeout=langgraph_timeout) as client:
            response = await client.post(
                f"{snowflake_gateway_endpoint}/agents/invoke",
                json={
                    "agent_name": agent_name,
                    "query": query,
                    "session_id": session_id,
                    "context": context or {},
                    "history": (context or {}).get("history", []),
                }
            )
            response.raise_for_status()
            result = response.json()
            result["agent_name"] = agent_name
            return result
    except Exception as e:
        logger.warning(f"Failed to invoke Snowflake agent {agent_name}: {str(e)}")
        return {
            "agent_name": agent_name,
            "response": f"Response from {agent_name} agent for query: {query[:50]}...",
            "sources": []
        }
```

**Configuration:**
- **Endpoint:** `settings.snowflake.cortex_agent_gateway_endpoint` (default: `http://snowflake-cortex:8002`)
- **Path:** `/agents/invoke`
- **Method:** POST
- **Called from:** `invoke_agents` node in StateGraph workflow

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
  "context": {"domain": "market_segment"},
  "agent_preference": null
}

// 3. LangGraph → Snowflake Agent
POST http://snowflake-cortex:8002/agents/invoke
{
  "agent_name": "YOUR_ANALYST_AGENT_NAME",
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
  "selected_agent": "MARKET_SEGMENT_AGENT",
  "routing_reason": "Domain match to 'market_segment'",
  "confidence": 0.95,
  "sources": [...],
  "execution_time": 1.5,
  "session_id": "session-123"
}

// 3. AWS Agent Core → Client
{
  "response": "Sales are $1M",
  "session_id": "session-123",
  "agent_used": "MARKET_SEGMENT_AGENT",
  "confidence": 0.95,
  "sources": [...],
  "execution_time": 1.5,
  "metadata": {
    "trace_id": "...",
    "routing_reason": "Domain match to 'market_segment'"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## Key Components

### 1. HTTP Client (httpx)

**Used in:**
- `aws_agent_core/orchestrator.py` → Calls LangGraph supervisor
- `langgraph/supervisor/graph.py` → Calls Snowflake agents (in `_invoke_snowflake_agent` function)

**Why httpx:**
- Async/await support
- Better timeout handling
- Modern Python HTTP client

### 2. State Management

**Used in:**
- `langgraph/state/graph_state.py` - SupervisorState TypedDict for StateGraph
- `langgraph/supervisor/graph.py` - StateGraph workflow with state management

**Purpose:**
- LangGraph StateGraph automatically manages state throughout the workflow
- State is passed between nodes as a TypedDict
- No manual state create/update calls needed
- Built-in checkpointing support (can add checkpointer for persistence)

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
# supervisor/graph.py - handle_error node
async def handle_error(state: SupervisorState) -> SupervisorState:
    """Handle errors in the workflow."""
    session_id = state["session_id"]
    error = state.get("error", "Unknown error")
    
    logger.error(f"Handling error for session {session_id}: {error}")
    
    state["status"] = "failed"
    state["current_step"] = "error_handled"
    
    return state

# Error handling is automatic via conditional edges in StateGraph
# If any node sets status="failed", the graph routes to handle_error node
```

---

## Summary

1. **Request arrives** at AWS Agent Core Lambda handler via API Gateway
2. **Orchestrator** receives request and prepares to invoke LangGraph
3. **HTTP call** made to LangGraph supervisor endpoint (`/supervisor/process`)
4. **LangGraph supervisor** processes request through **StateGraph workflow**:
   - **load_state** node: Loads conversation history
   - **route_request** node: Gets prompt and routes to appropriate agent(s)
   - **invoke_agents** node: Invokes Snowflake Cortex AI agent(s)
   - **combine_responses** node: Combines multiple agent responses if needed
   - **update_memory** node: Updates conversation history and patterns
   - **log_observability** node: Logs to Langfuse
   - **handle_error** node: Handles errors if any occur (via conditional edges)
5. **Response flows back** through the chain to the client

**Key Points:**
- LangGraph uses **StateGraph pattern** for declarative workflow management
- State is automatically managed by LangGraph (no manual state_manager calls)
- Workflow is defined as a graph with nodes and edges, making it easy to visualize and debug
- Error handling is built-in via conditional edges that route to `handle_error` node
- LangGraph is triggered via **HTTP POST request** from the AWS Agent Core orchestrator



