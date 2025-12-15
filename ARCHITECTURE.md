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
│  │  CortexAgentGateway                                      │  │
│  │  - Routes to specific agent type                         │  │
│  └───────────────────┬────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼────────────────────────────────────┐  │
│  │  CortexAgent (BaseCortexAgent)                         │  │
│  │  ├── CORTEX_ANALYST → CortexAnalyst tool               │  │
│  │  ├── CORTEX_SEARCH → CortexSearch tool                 │  │
│  │  └── CORTEX_COMBINED → Both tools                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Tools:                                                   │  │
│  │  - CortexAnalyst: SQL generation & execution             │  │
│  │  - CortexSearch: Document search in Snowflake stages     │  │
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
   - Specialized agents for different data types
   - Direct Snowflake integration
   - **Langfuse Prompt Management**: Each agent type uses specific prompts:
     - `snowflake_cortex_analyst` for Analyst agent
     - `snowflake_cortex_search` for Search agent
     - `snowflake_cortex_combined` for Combined agent
   - Observability: TruLens integration

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
    ├─→ AgentRouter: Analyze & route query (using prompt-enhanced query)
    ├─→ ShortTermMemory: Store query & routing
    │
    ▼
[HTTP POST] → Snowflake Gateway (/agents/invoke)
    │
    ▼
[CortexAgentGateway.invoke_agent()]
    │
    ▼
[CortexAgent.process_query()]
    │
    ├─→ **Gets agent-specific prompt from Langfuse**
    │   (snowflake_cortex_analyst/search/combined)
    ├─→ **Renders prompt with query, context, agent_type**
    ├─→ **Uses enhanced query for tool execution**
    │
    ├─→ CortexAnalyst (if structured data) - uses prompt-enhanced query
    ├─→ CortexSearch (if unstructured data) - uses prompt-enhanced query
    └─→ Both (if combined) - uses prompt-enhanced query
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
    └─→ Snowflake Cortex Agents:
        ├─→ snowflake_cortex_analyst: {query}, {semantic_model}, {context}
        ├─→ snowflake_cortex_search: {query}, {context}
        └─→ snowflake_cortex_combined: {query}, {context}
```

---

## How Agents Work Together

### Agent Types

The system has **three specialized agent types**:

1. **CORTEX_ANALYST** (`cortex_analyst`)
   - Purpose: Query structured data (tables, databases)
   - Tool: `CortexAnalyst`
   - Capabilities:
     - Converts natural language to SQL using semantic models
     - Executes SQL queries in Snowflake
     - Returns structured results

2. **CORTEX_SEARCH** (`cortex_search`)
   - Purpose: Search unstructured data (PDFs, PPTs, documents)
   - Tool: `CortexSearch`
   - Capabilities:
     - Searches documents in Snowflake stages
     - Returns relevant document snippets
     - Provides relevance scores

3. **CORTEX_COMBINED** (`cortex_combined`)
   - Purpose: Handle ambiguous queries requiring both data types
   - Tools: Both `CortexAnalyst` and `CortexSearch`
   - Capabilities:
     - Runs both tools in parallel
     - Combines results intelligently
     - Provides comprehensive answers

### Routing Logic

The `AgentRouter` uses **keyword-based scoring** to determine which agent to use:

```python
# Analyst keywords: query, sql, table, data, database, analyze, report, statistics
# Search keywords: search, find, document, pdf, ppt, file, content, unstructured

Scoring Algorithm:
1. Count keyword matches in query
2. Normalize scores (0.0 - 1.0)
3. Check context hints (data_type: structured/unstructured)
4. Apply confidence thresholds
5. Route to highest scoring agent (or combined if ambiguous)
```

### Agent Coordination Example

**Example Query**: "What are the total sales for last month?"

1. **AWS Agent Core** receives request
2. **LangGraph Supervisor** analyzes query:
   - Keywords: "total", "sales", "month" → Analyst keywords detected
   - Score: Analyst=0.8, Search=0.1
   - Decision: Route to `CORTEX_ANALYST`
3. **CortexAgent** (Analyst type) processes:
   - Loads semantic model
   - Converts to SQL: `SELECT SUM(amount) FROM sales WHERE month = ...`
   - Executes query
   - Returns results
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
│ - AgentRouter analyzes query (using prompt-enhanced query)   │
│ - Routing decision: {                                        │
│     "selected_agent": "cortex_analyst",                     │
│     "routing_reason": "Query appears to be for structured...",│
│     "confidence": 0.8                                       │
│   }                                                          │
│ - Stores in short-term memory                               │
│ - Updates state: selected_agent, routing_reason             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Snowflake Cortex Agent Layer                             │
│ - CortexAgentGateway receives request                       │
│ - Routes to CortexAgent (Analyst type)                      │
│ - **Fetches snowflake_cortex_analyst prompt from Langfuse** │
│ - **Renders prompt: {query}, {semantic_model}, {context}**  │
│ - CortexAnalyst tool (using prompt-enhanced query):         │
│   * Loads semantic model                                    │
│   * Converts NL to SQL (with prompt context)                │
│   * Executes SQL in Snowflake                               │
│   * Formats results                                         │
│ - TruLens logs execution                                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Response Data Flow (Backwards)                           │
│ {                                                            │
│   "response": "Total sales: $1,234,567",                   │
│   "sql_query": "SELECT SUM(amount)...",                    │
│   "sources": [{"type": "structured_data", ...}],          │
│   "agent_type": "cortex_analyst"                            │
│ }                                                            │
│         ↓                                                   │
│ {                                                            │
│   "response": "...",                                        │
│   "selected_agent": "cortex_analyst",                      │
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
│ ├── agent: "cortex_analyst"        │
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
  
  - name: snowflake_cortex_analyst
    description: "Prompt for Cortex AI Analyst"
    default_template: "Convert the following natural language query to SQL: {query}\n\nSemantic model context: {semantic_model}"
  
  - name: snowflake_cortex_search
    description: "Prompt for Cortex AI Search"
    default_template: "Search for information related to: {query}\n\nSearch context: {context}"
  
  - name: snowflake_cortex_combined
    description: "Prompt for combined Cortex AI agent"
    default_template: "Process the following query using both structured and unstructured data: {query}\n\nContext: {context}"
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
  - name: cortex_analyst
    type: cortex_analyst
    description: "Cortex AI Analyst for structured data queries"
    enabled: true
    semantic_model: "default_semantic_model"
    config:
      max_query_timeout: 300
      enable_caching: true
  
  - name: cortex_search
    type: cortex_search
    description: "Cortex AI Search for unstructured data queries"
    enabled: true
    config:
      default_stage_path: "@my_stage"
      max_results: 10
      min_relevance_score: 0.5
  
  - name: cortex_combined
    type: cortex_combined
    description: "Combined agent using both Analyst and Search"
    enabled: true
    config:
      use_analyst_first: true
      combine_results: true

semantic_models:
  - name: default_semantic_model
    description: "Default semantic model for SQL generation"
    location: "snowflake://semantic_models/default.yaml"
    version: "1.0"
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
    "context": {"data_type": "structured"}
  }'
```

#### Expected Response
```json
{
  "response": "Found 1 result(s) for your query:\n\nResult 1: {...}",
  "session_id": "test-session-1",
  "agent_used": "cortex_analyst",
  "confidence": 0.8,
  "sources": [...],
  "execution_time": 1.23,
  "metadata": {
    "trace_id": "...",
    "routing_reason": "Query appears to be for structured data..."
  }
}
```

### 6. Adding New Agents

To add a new agent type:

1. **Create agent class** in `snowflake_cortex/agents/`:
```python
from snowflake_cortex.agents.base_agent import BaseCortexAgent

class MyNewAgent(BaseCortexAgent):
    async def process_query(self, query, session_id, context):
        # Implementation
        pass
```

2. **Add to AgentType enum** in `shared/models/agent_state.py`:
```python
class AgentType(str, Enum):
    # ... existing types
    MY_NEW_AGENT = "my_new_agent"
```

3. **Update routing logic** in `langgraph/reasoning/router.py`:
```python
def _score_my_agent_query(self, query: str) -> float:
    # Add scoring logic
    pass
```

4. **Add configuration** in `config/agents.yaml`:
```yaml
agents:
  - name: my_new_agent
    type: my_new_agent
    enabled: true
    config:
      # agent-specific config
```

5. **Register in gateway** in `snowflake_cortex/gateway/api.py`:
```python
agents = {
    # ... existing agents
    AgentType.MY_NEW_AGENT: MyNewAgent(AgentType.MY_NEW_AGENT),
}
```

### 7. Customizing Routing

Edit `langgraph/reasoning/router.py` to customize routing logic:

```python
# Add custom keywords
self.my_agent_keywords = ["custom", "keywords"]

# Modify scoring algorithm
def _score_my_agent_query(self, query: str) -> float:
    # Custom scoring logic
    pass
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
