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
└───────────────────────────┬───────────────────────────────────┘
                             │ HTTP REST API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tier 1: AWS Agent Core (Port 8000)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI REST API                                        │  │
│  │  - /api/v1/query (POST)                                  │  │
│  │  - /health (GET)                                         │  │
│  │  - /metrics (GET)                                        │  │
│  └───────────────────┬────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼────────────────────────────────────┐  │
│  │  MultiAgentOrchestrator                                 │  │
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
│  │  LangGraphSupervisor                                     │  │
│  │  - State Management (StateManager)                      │  │
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
│  │  SnowflakeGatewayService (FastAPI)                       │  │
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

1. **AWS Agent Core (Tier 1)**
   - Entry point for all requests
   - REST API layer using FastAPI
   - Orchestrates the entire flow
   - AWS Bedrock Agent Core Runtime SDK integration
   - **Langfuse Prompt Management**: Uses `orchestrator_query` prompt to enhance queries
   - Observability: AWS CloudWatch tracing & metrics

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

```
User Request
    │
    ▼
[FastAPI Router] (/api/v1/query)
    │
    ▼
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
    ├─→ StateManager: Get/Create state
    ├─→ **Gets supervisor_routing prompt from Langfuse**
    ├─→ **Renders routing prompt with query and context**
    ├─→ AgentRouter: Selects which Snowflake agent object(s) to invoke (not tool_choice)
    ├─→ ShortTermMemory: Store query, routing_decision, and history
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

### 2. State Management Flow

```
StateManager (in-memory)
    │
    ├─→ create_state() - New session
    ├─→ get_state() - Retrieve existing
    ├─→ update_state() - Update progress
    └─→ delete_state() - Cleanup
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
│   }                                                          │
│ - Stores in short-term memory (including history)            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Snowflake Cortex Agent Layer                             │
│ - Snowflake Gateway receives request                         │
│ - Calls Snowflake Cortex Agents Run REST API                 │
│ - Sends messages[] (history + current query)                 │
│ - Snowflake agent decides tool_choice and runs tools          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Response Data Flow (Backwards)                           │
│ {                                                            │
│   "response": "Total sales: $1,234,567",                   │
│   "agent_name": "MY_ANALYST_AGENT",                         │
│   "raw_events_count": 42,                                   │
│   "raw_events_sample": [...],                               │
│ }                                                            │
│         ↓                                                   │
│ {                                                            │
│   "response": "...",                                        │
│   "selected_agent": "MY_ANALYST_AGENT",                    │
│   "routing_reason": "...",                                 │
│   "confidence": 0.8,                                        │
│   "sources": [...],                                         │
│   "execution_time": 1.23,                                   │
│   "session_id": "session-123"                              │
│ }                                                            │
│         ↓                                                   │
│ AgentResponse {                                              │
│   response: str,                                            │
│   session_id: str,                                          │
│   agent_used: str,                                          │
│   confidence: float,                                        │
│   sources: List[Dict],                                      │
│   execution_time: float,                                    │
│   metadata: Dict                                            │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
```

### State Data Flow

```
Session State Lifecycle:
┌─────────────┐
│  PENDING    │ ← Initial state
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PROCESSING  │ ← During routing & execution
└──────┬──────┘
       │
       ├─→ COMPLETED (success)
       │
       └─→ FAILED (error)
```

### Memory Data Flow

```
Short-Term Memory (per session):
┌─────────────────────────────────────┐
│ session_id: "session-123"           │
│ ├── last_query: "What are sales?"  │
│ ├── routing_decision: {...}       │
│ └── [TTL: 3600s]                   │
└─────────────────────────────────────┘

Long-Term Memory (persistent):
┌─────────────────────────────────────┐
│ query_pattern_session-123:          │
│ ├── query: "What are sales?"        │
│ ├── agent: "MARKET_SEGMENT_AGENT"  │
│ └── success: true                  │
└─────────────────────────────────────┘
```

---

## Configuration and Setup

### 1. Environment Configuration

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

#### Required Environment Variables

**Application Settings:**
```bash
APP_NAME=multi-agent-orchestrator
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
```

**AWS Configuration:**
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
# Optional:
AWS_SESSION_TOKEN=  # For temporary credentials
AWS_BEDROCK_AGENT_CORE_RUNTIME_ENDPOINT=  # If using AWS Bedrock
```

**LangGraph Configuration:**
```bash
LANGGRAPH_ENDPOINT=http://langgraph:8001  # Docker network name
LANGGRAPH_TIMEOUT=300  # seconds
LANGGRAPH_ENABLE_MEMORY=true
```

**Langfuse Observability & Prompt Management:**
```bash
LANGFUSE_HOST=http://langfuse:3000
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_PROJECT_ID=...
LANGFUSE_DATABASE_URL=postgresql://langfuse:langfuse@postgres:5432/langfuse
# Note: Prompt management uses the same Langfuse credentials
```

**PostgreSQL (for Langfuse):**
```bash
POSTGRES_USER=langfuse
POSTGRES_PASSWORD=langfuse
POSTGRES_DB=langfuse
```

**Snowflake Configuration:**
```bash
SNOWFLAKE_ACCOUNT=your-account-identifier
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=  # Optional
SNOWFLAKE_CORTEX_AGENT_GATEWAY_ENDPOINT=http://snowflake-cortex:8002
```

**TruLens Observability:**
```bash
TRULENS_ENABLED=true
TRULENS_APP_ID=your-app-id
TRULENS_API_KEY=your-api-key
```

### 2. Prompt Configuration

The system uses Langfuse for prompt management. Default prompts are defined in `config/prompts.yaml`:

```yaml
prompts:
  - name: orchestrator_query
    description: "Prompt for AWS Agent Core orchestrator"
    default_template: "You are a multi-agent orchestrator. Process the following query: {query}"
  
  - name: supervisor_routing
    description: "Prompt for LangGraph supervisor routing"
    default_template: "Analyze the following query and determine the best agent: {query}\n\nContext: {context}"
```

**Managing Prompts:**

1. **Via Langfuse UI**: Access http://localhost:3000 to create, update, and version prompts
2. **Via API**: Use Snowflake Gateway endpoints:
   ```bash
   # Get a prompt
   curl http://localhost:8002/prompts/supervisor_routing
   
   # Create a prompt
   curl -X POST http://localhost:8002/prompts \
     -H "Content-Type: application/json" \
     -d '{
       "prompt_name": "custom_prompt",
       "prompt": "Template with {variable}",
       "config": {},
       "labels": ["production"]
     }'
   ```

3. **Prompt Variables**: All prompts support variable substitution using `{variable_name}` syntax

### 3. Agent Configuration

Edit `config/agents.yaml`:

```yaml
agents:
  - domain: market_segment
    agent_name: MARKET_SEGMENT_AGENT
    description: "Domain agent for market segmentation analytics and insights"
    enabled: true
    keywords: ["market", "segment", "churn", "retention"]

  - domain: drug_discovery
    agent_name: DRUG_DISCOVERY_AGENT
    description: "Domain agent for drug discovery and life sciences queries"
    enabled: true
    keywords: ["drug", "compound", "target", "assay", "clinical"]
```

### 4. Setup Steps

#### Step 1: Initial Setup
```bash
cd multi-agent-orchestrator
./scripts/setup_env.sh --dev
```

This will:
- Create Python virtual environment
- Install dependencies from `requirements.txt`
- Install dev dependencies (pytest, black, etc.)
- Create `.env` from `.env.example`
- Create necessary directories

#### Step 2: Configure Environment
```bash
# Edit .env with your actual credentials
nano .env  # or use your preferred editor
```

**Minimum required for local testing:**
- `LOG_LEVEL=INFO`
- `LANGGRAPH_ENDPOINT=http://langgraph:8001`
- `LANGFUSE_HOST=http://langfuse:3000`
- `SNOWFLAKE_CORTEX_AGENT_GATEWAY_ENDPOINT=http://snowflake-cortex:8002`

**For full functionality:**
- Add AWS credentials (if using AWS Bedrock)
- Add Snowflake credentials (if using Snowflake)
- Add Langfuse keys (if using observability)
- Add TruLens keys (if using observability)

#### Step 3: Run with Docker Compose
```bash
./scripts/run_local.sh
```

This will:
- Build Docker images for all services
- Start all containers:
  - `aws-agent-core` (port 8000)
  - `langgraph-supervisor` (port 8001)
  - `snowflake-cortex-agent` (port 8002)
  - `langfuse` (port 3000)
  - `postgres` (for Langfuse)

#### Step 4: Verify Services
```bash
# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# View logs
docker-compose logs -f
```

### 5. Testing the System

#### Send a Test Query
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the total sales for last month?",
    "session_id": "test-session-1",
    "context": {"domain": "market_segment"}
  }'
```

#### Expected Response
```json
{
  "response": "Found 1 result(s) for your query:\n\nResult 1: {...}",
  "session_id": "test-session-1",
  "agent_used": "MARKET_SEGMENT_AGENT",
  "confidence": 0.8,
  "sources": [...],
  "execution_time": 1.23,
  "metadata": {
    "trace_id": "...",
    "routing_reason": "Domain match to 'market_segment'..."
  }
}
```

### 6. Adding New Agents

To add a new domain agent:

1. **Create a Snowflake Cortex agent object** in your Snowflake DB/SCHEMA with domain instructions and tool resources.

2. **Add configuration** in `config/agents.yaml`:
```yaml
agents:
  - domain: my_new_domain
    agent_name: MY_NEW_DOMAIN_AGENT
    enabled: true
    keywords: ["custom", "keywords"]
```

### 7. Customizing Routing

Edit `langgraph/reasoning/router.py` to customize routing logic:

```python
# Update `config/agents.yaml` domain keywords or tweak the domain scoring thresholds.
```

### 8. Observability Setup

**Langfuse:**
1. Sign up at https://langfuse.com
2. Create a project
3. Get API keys (public key, secret key, project ID)
4. Add to `.env`

**TruLens:**
1. Sign up at https://www.trulens.org
2. Create an app
3. Get API keys (app ID, API key)
4. Add to `.env`

**AWS CloudWatch:**
- Automatically configured when AWS credentials are provided
- Traces appear in CloudWatch when using AWS Bedrock Agent Core

---

## Summary

This multi-agent orchestrator provides:

✅ **Scalable Architecture**: Three-tier microservices design
✅ **Intelligent Routing**: Automatic agent selection based on query analysis
✅ **State Management**: Session-based state with memory management
✅ **Prompt Management**: Centralized Langfuse prompt management across all components
✅ **Observability**: Integrated tracing and metrics (AWS, Langfuse, TruLens)
✅ **Flexibility**: Easy to add new agents and customize routing
✅ **Production Ready**: Docker containerization, health checks, error handling

The system is designed to handle both structured (SQL) and unstructured (document search) queries intelligently, routing each request to the most appropriate agent while maintaining state and observability throughout the process. **Langfuse prompt management** enables centralized control and versioning of prompts used across AWS Agent Core, LangGraph Supervisor, and Snowflake Cortex AI agents, allowing for A/B testing, prompt optimization, and consistent behavior across all components.
