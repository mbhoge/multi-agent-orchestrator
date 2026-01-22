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
│    POST /invocations                                            │
│    { "query": "What are sales?", "session_id": "session-123" }   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. AgentCore HTTP Server                                        │
│    aws_agent_core/api/main.py                                    │
│    → Parses JSON payload                                         │
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
│ 4. Invoke LangGraph (in-process)                                │
│    _invoke_langgraph()                                          │
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
│ 6. Planner + Executor (LLM)                                     │
│    langgraph/supervisor/planning.py + llm_client.py             │
│    → plan_request() → execute_plan()                            │
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

### Step 1: Request Arrives at AgentCore HTTP Server

**File:** `aws_agent_core/api/main.py`

```python
# AgentCore HTTP server receives JSON payload at /invocations
payload = json.loads(raw_body.decode("utf-8") or "{}")
request = AgentRequest(
    query=payload.get("query") or payload.get("prompt"),
    session_id=payload.get("session_id"),
    context=payload.get("context"),
    agent_preference=payload.get("agent_preference"),
    metadata=payload.get("metadata", {}),
)
response = asyncio.run(orchestrator.process_request(request))
```

**What happens:**
- HTTP server receives POST request at `/invocations`
- JSON body is parsed into `AgentRequest`
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
    
    # Step 2: Extract planner/executor decision
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

### Step 3: In-Process Call to LangGraph

**File:** `aws_agent_core/orchestrator.py`

```python
async def _invoke_langgraph(
    self,
    request: AgentRequest,
    session_id: str
) -> Dict[str, Any]:
    """Invoke LangGraph supervisor in-process."""
    return await self.supervisor.process_request(request=request, session_id=session_id)
```

**Configuration:**
- No external endpoint required (in-process invocation)

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

The LangGraph supervisor is invoked in-process. The supervisor receives the request and processes it through the StateGraph workflow:

```python
# In orchestrator.py - in-process call to LangGraph
async def _invoke_langgraph(
    self,
    request: AgentRequest,
    session_id: str
) -> Dict[str, Any]:
    """Invoke LangGraph supervisor in-process."""
    return await self.supervisor.process_request(request=request, session_id=session_id)
```

**What happens:**
- `LangGraphSupervisor.process_request()` is called directly
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

2. **`plan_request`** - LLM planner generates a numbered plan (Bedrock SLM)
   - Builds planner prompt and calls the planner LLM
   - Parses JSON plan and stores it in state and short-term memory
   - **Conditional edge:** Routes to `handle_error` if status="failed", otherwise continues to `execute_plan`

3. **`execute_plan`** - LLM executor selects next agent and query (Bedrock SLM)
   - Builds executor prompt and calls the executor LLM
   - Parses JSON decision (`replan`, `goto`, `reason`, `query`)
   - Produces `routing_decision` in standard shape (agents_to_call, routing_reason, confidence)
   - **Conditional edge:** Routes to `handle_error` if status="failed", otherwise continues to `invoke_agents`

4. **`invoke_agents`** - Invokes one or more Snowflake Cortex AI agents based on routing decision
   - Iterates through `agents_to_call` from routing decision
   - Calls `_invoke_snowflake_agent()` for each agent (via HTTP to Snowflake gateway)
   - Collects all agent responses in `agent_responses` array
   - **Conditional edge:** Routes to `handle_error` if status="failed", otherwise continues to `combine_responses`

5. **`combine_responses`** - Combines responses from multiple agents if needed
   - If single agent: uses response directly
   - If multiple agents: combines with agent labels and merges sources
   - Sets `final_response` in state
   - **Conditional edge:** Routes to `handle_error` if status="failed", otherwise continues to `update_memory`

6. **`advance_plan`** - Advances plan step or triggers replan
   - Increments `plan_current_step` if additional steps exist
   - Routes to `plan_request` when `replan_flag` is true

7. **`update_memory`** - Updates short-term and long-term memory with conversation history
   - Appends assistant response to message history
   - Stores updated history in `short_term_memory` (bounded window, max 30 messages)
   - Optionally stores patterns in `long_term_memory` if confidence is high
   - **Regular edge:** Always continues to `log_observability`

8. **`log_observability`** - Logs to Langfuse for observability
   - Logs trace to Langfuse with full state information
   - Calculates execution time
   - Sets final status to "completed"
   - **Regular edge:** Always ends workflow (END)

9. **`handle_error`** - Handles errors if any node sets status to "failed"
   - Logs error details
   - Sets status to "failed" and current_step to "error_handled"
   - **Regular edge:** Always ends workflow (END)

**Graph Structure:**
- **START** → `load_state` → `plan_request` → (conditional) → `execute_plan` → (conditional) → `invoke_agents` → (conditional) → `combine_responses` → (conditional) → `advance_plan` → (conditional) → `update_memory` → `log_observability` → **END**
- **Error path:** Any node can route to `handle_error` → **END** via conditional edges
- **Conditional edges:** Check `state["status"] == "failed"` to route to error handler

**Key Operations:**
1. **StateGraph Management:** LangGraph handles state automatically through the graph (no manual state_manager calls)
2. **Planner/Executor Prompts:** LLM prompts drive plan + agent selection (plan_request/execute_plan)
3. **Agent Selection:** Executor produces routing decision shape
4. **Memory Management:** Stores in short-term and long-term memory (in `update_memory` node)
5. **Agent Invocation:** Calls Snowflake Cortex AI agents via HTTP (in `invoke_agents` node)
6. **Observability:** Logs to Langfuse (in `log_observability` node)
7. **Error Handling:** Conditional edges automatically route to `handle_error` when status is "failed"

---

### Step 6: Planner + Executor Decision

**Files:** `langgraph/supervisor/planning.py`, `langgraph/supervisor/llm_client.py`

The planner builds a numbered plan, and the executor decides the next agent + query.
The executor output is converted to the standard routing decision shape:

```json
{
  "agents_to_call": ["AGENT_NAME"],
  "routing_reason": "Executor: <reason>",
  "confidence": 0.7
}
```

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

## Invocation Path (Current Implementation)

```
AWS Agent Core → in-process LangGraph → Snowflake Agent
```

**Behavior:**
- `/invocations` triggers the LangGraph supervisor in-process (no HTTP hop to LangGraph)
- The supervisor invokes Snowflake agents over HTTP

---

## Configuration

### Environment Variables

**LangGraph Supervisor (in-process):**
```bash
LANGFUSE_HOST=http://langfuse:3000
SNOWFLAKE_CORTEX_AGENT_GATEWAY_ENDPOINT=http://snowflake-cortex:8002
```

### Docker Compose Network

All services communicate via Docker network:
- `aws-agent-core:8080` → in-process LangGraph supervisor
- `aws-agent-core:8080` → `snowflake-cortex:8002`

---

## Request/Response Flow

### Request Flow

```json
// 1. Client → AWS Agent Core
POST /invocations
{
  "query": "What are sales?",
  "session_id": "session-123"
}

// 2. LangGraph (in-process) → Snowflake Agent
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

// 2. LangGraph (in-process) → AWS Agent Core
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
    "routing_reason": "Domain match to 'market_segment'"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

---

## Key Components

### 1. HTTP Client (httpx)

**Used in:**
- `langgraph/supervisor/graph.py` → Calls Snowflake agents (in `_invoke_snowflake_agent` function)

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

---

## Error Handling

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

1. **Request arrives** at AWS Agent Core `/invocations` endpoint
2. **Orchestrator** receives request and invokes LangGraph in-process
3. **LangGraph supervisor** processes request through **StateGraph workflow**:
   - **load_state** node: Loads conversation history
   - **plan_request/execute_plan** nodes: Planner/executor select next agent(s)
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
- LangGraph is triggered **in-process** by the AWS Agent Core orchestrator



