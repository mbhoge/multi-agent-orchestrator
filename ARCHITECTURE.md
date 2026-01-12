# Multi-Agent Orchestrator - Architecture & Configuration Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Interactions](#component-interactions)
3. [How Agents Work Together](#how-agents-work-together)
4. [Data Flow Through the System](#data-flow-through-the-system)
5. [Configuration and Setup](#configuration-and-setup)

---

## Architecture Overview

The Multi-Agent Orchestrator follows a **three-tier microservices architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        User/Client                              │
│  ┌──────────────────────┐  ┌──────────────────────────────┐   │
│  │  HTTP REST API       │  │  Microsoft Teams             │   │
│  │  (Direct API calls)  │  │  (Outgoing Webhook)           │   │
│  └──────────┬───────────┘  └──────────┬───────────────────┘   │
└─────────────┼─────────────────────────┼─────────────────────────┘
              │ HTTPS                    │ HTTPS
              ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  AWS API Gateway (HTTP API v2)                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  REST API Endpoints                                       │  │
│  │  - POST /api/v1/query                                     │  │
│  │  - POST /api/teams/webhook                                │  │
│  │  - GET /health                                            │  │
│  │  - GET /metrics                                           │  │
│  └───────────────────┬────────────────────────────────────┘  │
└───────────────────────┼───────────────────────────────────────┘
                        │ Lambda Invoke
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tier 1: AWS Lambda Functions                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Query Handler Lambda                                    │  │
│  │  - Processes /api/v1/query requests                      │  │
│  │  - Extracts AgentRequest from API Gateway event         │  │
│  └───────────────────┬────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼────────────────────────────────────┐  │
│  │  Teams Webhook Handler Lambda                           │  │
│  │  - Processes /api/teams/webhook requests                 │  │
│  │  - Verifies HMAC signature                              │  │
│  │  - Transforms Teams webhook → AgentRequest              │  │
│  └───────────────────┬────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼────────────────────────────────────┐  │
│  │  MultiAgentOrchestrator (Shared across Lambdas)        │  │
│  │  - Coordinates all agents                               │  │
│  │  - AWS Agent Core Runtime SDK integration              │  │
│  │  - Observability (Tracing & Metrics)                   │  │
│  └───────────────────┬────────────────────────────────────┘  │
└───────────────────────┼───────────────────────────────────────┘
                        │ HTTP (httpx)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tier 2: LangGraph Supervisor (Port 8001)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LangGraphSupervisor (StateGraph)                       │  │
│  │  - StateGraph Workflow (automatic state management)     │  │
│  │  - Memory Management (Short-term & Long-term)           │  │
│  │  - Request Routing (AgentRouter)                        │  │
│  │  - Langfuse Observability                                │  │
│  └───────────────────┬────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼────────────────────────────────────┐  │
│  │  AgentRouter                                           │  │
│  │  - Analyzes query intent                                │  │
│  │  - Routes to appropriate agent                          │  │
│  │  - Returns routing decision with confidence             │  │
│  └───────────────────┬────────────────────────────────────┘  │
└───────────────────────┼───────────────────────────────────────┘
                        │ HTTP (httpx)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tier 3: Snowflake Cortex Agents (Port 8002)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SnowflakeGatewayService (Lambda)                        │  │
│  │  - Accepts /agents/invoke                                │  │
│  │  - Calls Snowflake Cortex Agents Run REST API            │  │
│  └───────────────────┬────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼────────────────────────────────────┐  │
│  │  CortexAgentGatewayClient (REST)                        │  │
│  │  - POST /api/v2/.../agents/{agent_name}:run             │  │
│  │  - Sends messages[] (history + current query)           │  │
│  │  - Snowflake agent orchestrates tool usage server-side  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Snowflake Cortex Agent Objects (in Snowflake)           │  │
│  │  - Analyst agent object (structured)                     │  │
│  │  - Search agent object (unstructured)                    │  │
│  │  - Combined agent object (both tools)                    │  │
│  │  - Tools invoked via agent orchestration (tool_choice)   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Supporting Services                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Langfuse (Port 3000)                                    │  │
│  │  ┌────────────────────┐  ┌────────────────────┐        │  │
│  │  │  Observability    │  │  Prompt Management  │        │  │
│  │  │  - Tracing         │  │  - Prompt Store    │        │  │
│  │  │  - Monitoring      │  │  - Version Control │        │  │
│  │  │  - Logging         │  │  - Template Render │        │  │
│  │  └────────────────────┘  └────────────────────┘        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────┐                                         │
│  │  PostgreSQL      │                                         │
│  │  (Langfuse DB)   │                                         │
│  │  - State storage │                                         │
│  │  - Prompt data   │                                         │
│  └──────────────────┘                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **AWS API Gateway + Lambda (Tier 1)**
   - Entry point for all requests (REST API and Microsoft Teams)
   - **AWS API Gateway HTTP API v2**: Routes requests to Lambda functions
   - **Lambda Functions**: Serverless handlers for each endpoint
     - Query Handler: Processes `/api/v1/query` requests
     - Teams Webhook Handler: Processes `/api/teams/webhook` (outgoing webhook)
     - Health Handler: Health check endpoint
     - Metrics Handler: Metrics endpoint
   - **Microsoft Teams Integration**: Outgoing webhook with HMAC signature verification
   - **Teams Adapter**: Transforms Teams webhook payloads ↔ AgentRequest/Response
   - Orchestrates the entire flow through shared `MultiAgentOrchestrator`
   - AWS Bedrock Agent Core Runtime SDK integration
   - **Langfuse Prompt Management**: Uses `orchestrator_query` prompt to enhance queries
   - Observability: AWS CloudWatch Logs & Metrics (native Lambda integration)

2. **LangGraph Supervisor (Tier 2)**
   - Multi-agent coordination and state management
   - Intelligent routing based on query analysis
   - Memory management (session-based and persistent)
   - **Langfuse Prompt Management**: Uses `supervisor_routing` prompt for routing decisions
   - Observability: Langfuse integration for tracing and monitoring

3. **Snowflake Cortex Agents (Tier 3)**
   - Snowflake-hosted agent objects invoked via **Cortex Agents Run REST API**
   - Gateway service (`snowflake_cortex/gateway/api.py`) calls Snowflake `/api/v2/...:run`
   - LangGraph passes **query + context + history** to Snowflake
   - **Tool orchestration (tool_choice) is decided by the Snowflake agent**
   - Observability: TruLens integration (optional / future hookup)

4. **Langfuse Prompt Management (Cross-cutting)**
   - Centralized prompt storage and versioning
   - Prompt template rendering with variable substitution
   - Prompt caching for performance
   - Integration across all tiers for consistent prompt usage

---

## Component Interactions

### 1. Request Flow

**Option A: Direct REST API**
```
User Request (HTTPS POST)
    │
    ▼
[AWS API Gateway] (/api/v1/query)
    │
    ▼
[Query Handler Lambda]
    │
    ├─→ [Extract AgentRequest from API Gateway event]
    │
    ▼
[MultiAgentOrchestrator.process_request()]
    │
    ▼
[AgentResponse]
    │
    ▼
[API Gateway Response] → User
```

**Option B: Microsoft Teams Outgoing Webhook**
```
Teams @mention in Channel
    │
    ▼
[Teams sends HTTPS POST to API Gateway] (/api/teams/webhook)
    │
    ▼
[Teams Webhook Handler Lambda]
    │
    ├─→ [Verify HMAC signature]
    ├─→ [Parse Teams webhook payload]
    ├─→ [Transform to AgentRequest]
    │
    ▼
[MultiAgentOrchestrator.process_request()]
    │
    ▼
[AgentResponse]
    │
    ├─→ [Format response for Teams (text/JSON)]
    │
    ▼
[API Gateway Response] → Teams Channel
```

**Common Flow (after transformation)**
```
[MultiAgentOrchestrator.process_request()]
    │
    ├─→ Creates session_id
    ├─→ Starts AWS tracing
    ├─→ Records metrics
    ├─→ **Gets orchestrator_query prompt from Langfuse**
    ├─→ **Renders prompt with query, session_id, context**
    ├─→ **Enhances request query with prompt**
    │
    ▼
[HTTP POST] → LangGraph Supervisor (/supervisor/process)
    │
    ▼
[LangGraphSupervisor.process_request()]
    │
    ├─→ StateGraph.ainvoke() - Invokes workflow
    │   │
    │   ├─→ load_state node: Load conversation history
    │   ├─→ route_request node: Get prompt from Langfuse & route
    │   ├─→ invoke_agents node: Invoke Snowflake agent(s)
    │   ├─→ combine_responses node: Combine multiple responses
    │   ├─→ update_memory node: Update history and patterns
    │   └─→ log_observability node: Log to Langfuse
    │
    ▼
[HTTP POST] → Snowflake Gateway (/agents/invoke)
    │
    ▼
[CortexAgentGateway.invoke_agent()]
    │
    ▼
[Snowflake Cortex Agents Run REST API]
    │
    ├─→ POST /api/v2/.../agents/{agent_name}:run
    ├─→ Body: messages[] (history + current query)
    ├─→ Snowflake agent orchestrates tool usage (analyst/search) server-side
    │
    ▼
[Response flows back through layers]
    │
    ▼
User receives AgentResponse
```

### 2. State Management Flow (StateGraph)

```
StateGraph (LangGraph - automatic state management)
    │
    ├─→ load_state node - Load conversation history from memory
    ├─→ route_request node - Update state with routing decision
    ├─→ invoke_agents node - Update state with agent responses
    ├─→ combine_responses node - Update state with final response
    ├─→ update_memory node - Update conversation history
    └─→ log_observability node - Finalize state (status="completed")
    
State is automatically passed between nodes via StateGraph.
No manual create_state() or update_state() calls needed.
```

### 3. Memory Management Flow

```
ShortTermMemory (Session-scoped, TTL-based)
    │
    ├─→ store() - Store session data
    ├─→ retrieve() - Get session data
    └─→ clear() - Clear session

LongTermMemory (Persistent, cross-session)
    │
    ├─→ store() - Store patterns
    ├─→ retrieve() - Get by key
    ├─→ search() - Search patterns
    └─→ delete() - Remove entry
```

### 4. Prompt Management Flow

```
LangfusePromptManager
    │
    ├─→ get_prompt(name, version, labels) - Fetch prompt with caching
    ├─→ create_prompt(name, prompt, config, labels) - Create new prompt
    ├─→ update_prompt(name, prompt, config, labels) - Update existing
    ├─→ render_prompt(template, variables) - Render with variables
    └─→ clear_cache(name) - Clear cached prompts

Prompt Usage Flow:
    │
    ├─→ AWS Agent Core: orchestrator_query prompt
    │   └─→ Variables: {query}, {session_id}, {context}
    │
    ├─→ LangGraph Supervisor: supervisor_routing prompt
    │   └─→ Variables: {query}, {context}
    │
    └─→ Snowflake Cortex Agent Objects (Snowflake-managed):
        └─→ Prompts/instructions are configured inside Snowflake agent objects
```

---

## How Agents Work Together

### Snowflake Agent Objects (recommended)

Instead of local `CortexAgent` implementations, the system invokes **Snowflake Cortex Agent objects** via the
**Cortex Agents Run REST API** ([Snowflake docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run)).

Typical setup (domain agents):

1. **market_segment agent object**
   - Domain-specific instructions (in Snowflake)
   - Uses `cortex_analyst_text_to_sql` and/or `cortex_search` as needed
2. **drug_discovery agent object**
   - Domain-specific instructions (in Snowflake)
   - Uses `cortex_analyst_text_to_sql` and/or `cortex_search` as needed

### Routing Logic

The `AgentRouter` uses **domain keyword scoring** (and optional `context.domain`) to determine which Snowflake agent object(s) to call.
Domain agents are defined in `config/agents.yaml`.

### Agent Coordination Example

**Example Query**: "What are the total sales for last month?"

1. **AWS Agent Core** receives request
2. **LangGraph Supervisor** analyzes query:
   - Determines likely domain (e.g., `market_segment`)
   - Decision: Call the Snowflake domain agent object (e.g., `MARKET_SEGMENT_AGENT`)
3. **Snowflake Gateway** calls Snowflake:
   - POST `/api/v2/databases/{db}/schemas/{schema}/agents/{agent_name}:run`
   - Sends messages[] with history + current user query
4. **Snowflake agent** orchestrates tool usage server-side and returns response
4. **Response flows back** through all layers with metadata

---

## Data Flow Through the System

### Request Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Request (JSON)                                       │
│ {                                                            │
│   "query": "What are total sales?",                         │
│   "session_id": "session-123",                              │
│   "context": {"data_type": "structured"},                  │
│   "agent_preference": null,                                  │
│   "metadata": {}                                             │
│ }                                                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. AWS Agent Core Layer                                     │
│ - Validates request                                         │
│ - Creates/uses session_id                                   │
│ - Starts trace context                                      │
│ - Records metrics (requests.total++)                         │
│ - **Fetches orchestrator_query prompt from Langfuse**      │
│ - **Renders prompt: {query}, {session_id}, {context}**       │
│ - **Enhances request.query with rendered prompt**           │
│ - Transforms to AgentRequest model                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. LangGraph Supervisor Layer                               │
│ - Retrieves/creates AgentState                              │
│ - Updates state: status=PROCESSING                           │
│ - **Fetches supervisor_routing prompt from Langfuse**       │
│ - **Renders routing prompt: {query}, {context}**             │
│ - AgentRouter selects agent object(s)                        │
│ - Routing decision: {                                        │
│     "agents_to_call": ["MARKET_SEGMENT_AGENT"],             │
│     "routing_reason": "Domain match to 'market_segment'...", │
│     "confidence": 0.8                                       │ 
