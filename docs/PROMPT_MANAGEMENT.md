# Langfuse Prompt Management Integration

This document describes the Langfuse prompt management functionality integrated across the multi-agent orchestrator system.

## Overview

Langfuse prompt management is integrated into:
- **AWS Agent Core**: Orchestrator uses prompts for query processing
- **LangGraph**: Supervisor uses prompts for routing decisions
- **Snowflake Tier (Gateway)**: Pass-through only (Snowflake agent objects manage their own prompts/instructions)

## Architecture

```
Langfuse Prompt Manager
    ├── AWS Agent Core (orchestrator_query)
    ├── LangGraph Supervisor (supervisor_routing)
    └── Snowflake Cortex Agent Objects (in Snowflake)
        └── Prompts/instructions live with the agent object configuration
```

## Prompt Manager

The `LangfusePromptManager` class provides:

- **get_prompt()**: Fetch prompts from Langfuse with caching
- **create_prompt()**: Create new prompts in Langfuse
- **update_prompt()**: Update existing prompts
- **render_prompt()**: Render prompt templates with variables
- **clear_cache()**: Clear cached prompts

## Integration Points

### 1. AWS Agent Core Orchestrator

**Location**: `aws_agent_core/orchestrator.py`

**Usage**:
- Fetches `orchestrator_query` prompt before processing requests
- Renders prompt with query, session_id, and context
- Enhances user query with prompt context

**Example**:
```python
orchestrator_prompt = await self._get_orchestrator_prompt(request)
if orchestrator_prompt:
    enhanced_query = orchestrator_prompt
    request.query = enhanced_query
```

### 2. LangGraph Supervisor

**Location**: `langgraph/supervisor.py` and `langgraph/observability/langfuse_client.py`

**Usage**:
- Fetches `supervisor_routing` prompt for routing decisions
- Renders prompt with query and context
- Uses enhanced prompt for agent routing

**Example**:
```python
routing_prompt = await self.langfuse_client.get_prompt_for_routing(
    query=request.query,
    context=request.context
)
routing_decision = agent_router.route_request(
    query=routing_prompt,
    context=request.context
)
```

### 3. Snowflake Cortex Agent Objects (Snowflake-managed prompts)

**Location (code)**: `snowflake_cortex/gateway/agent_gateway.py` (REST client)

**Usage**:
- The system invokes Snowflake Cortex **agent objects** via the **Cortex Agents Run REST API**
- Prompting/instructions for tools live **inside Snowflake agent object configuration**
- We send `messages[]` (history + current query) and optionally `tool_choice` hints

**Reference**: `https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run`

### 4. Snowflake Gateway API

**Location**: `snowflake_cortex/gateway/api.py`

**Endpoints**:
- `GET /prompts/{prompt_name}` - Get a prompt by name
- `POST /prompts` - Create a new prompt

**Usage**:
```bash
# Get a prompt
curl http://localhost:8002/prompts/supervisor_routing

# Create a prompt
curl -X POST http://localhost:8002/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_name": "custom_prompt",
    "prompt": "Custom prompt template with {variable}",
    "config": {},
    "labels": ["production"]
  }'
```

## Prompt Templates

### Available Prompts

1. **orchestrator_query**
   - Used by: AWS Agent Core Orchestrator
   - Variables: `{query}`, `{session_id}`, `{context}`
   - Default: "You are a multi-agent orchestrator. Process the following query: {query}"

2. **supervisor_routing**
   - Used by: LangGraph Supervisor
   - Variables: `{query}`, `{context}`
   - Default: "Analyze the following query and determine the best agent to handle it: {query}\n\nContext: {context}"

3. **snowflake_agent_domain_prompt** (optional / Snowflake-side)
   - Used by: Snowflake Cortex Agent objects (configured in Snowflake, not fetched by this codebase)
   - Variables: N/A (Snowflake agent object configuration)
   - Note: The codebase does not fetch per-agent prompts from Langfuse for Snowflake domain agents; it sends `messages[]` and optional `tool_choice` hints.

## Configuration

### Environment Variables

No additional environment variables are required. The prompt manager uses the existing Langfuse configuration:
- `LANGFUSE_HOST`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_PROJECT_ID`

### Prompt Configuration File

Default prompts are defined in `config/prompts.yaml`. This file serves as documentation and can be used to initialize prompts in Langfuse.

## Caching

The prompt manager implements caching to reduce API calls:
- Prompts are cached by name and version
- Cache can be cleared per prompt or globally
- Cache is checked before fetching from Langfuse

## Error Handling

- If Langfuse is unavailable, fallback prompts are used
- Errors in prompt fetching don't break the main flow
- Warnings are logged for debugging

## Best Practices

1. **Version Control**: Use Langfuse versioning for prompt changes
2. **Labels**: Use labels to organize prompts (e.g., "production", "staging")
3. **Testing**: Test prompt changes in a staging environment first
4. **Monitoring**: Monitor prompt usage and performance in Langfuse UI
5. **Documentation**: Document prompt variables and usage in code comments

## Future Enhancements

- A/B testing of prompts
- Prompt performance metrics
- Automatic prompt optimization
- Integration with prompt versioning workflows

