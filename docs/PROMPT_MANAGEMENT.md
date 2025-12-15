# Langfuse Prompt Management Integration

This document describes the Langfuse prompt management functionality integrated across the multi-agent orchestrator system.

## Overview

Langfuse prompt management has been integrated into:
- **AWS Agent Core**: Orchestrator uses prompts for query processing
- **LangGraph**: Supervisor uses prompts for routing decisions
- **Snowflake Cortex AI Agents**: Each agent type uses specific prompts

## Architecture

```
Langfuse Prompt Manager
    ├── AWS Agent Core (orchestrator_query)
    ├── LangGraph Supervisor (supervisor_routing)
    └── Snowflake Cortex Agents
        ├── Cortex Analyst (snowflake_cortex_analyst)
        ├── Cortex Search (snowflake_cortex_search)
        └── Combined Agent (snowflake_cortex_combined)
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

### 3. Snowflake Cortex Agents

**Location**: `snowflake_cortex/agents/cortex_agent.py`

**Usage**:
- Each agent type fetches its specific prompt:
  - `snowflake_cortex_analyst` for Analyst agent
  - `snowflake_cortex_search` for Search agent
  - `snowflake_cortex_combined` for Combined agent
- Renders prompt with query, context, and agent-specific variables
- Uses enhanced query for tool execution

**Example**:
```python
enhanced_query = await self._get_agent_prompt(query, prepared_context)
result = await self.analyst.analyze_query(
    query=enhanced_query,
    session_id=session_id,
    context=prepared_context
)
```

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

3. **snowflake_cortex_analyst**
   - Used by: Cortex AI Analyst Agent
   - Variables: `{query}`, `{semantic_model}`, `{context}`
   - Default: "Convert the following natural language query to SQL: {query}\n\nSemantic model context: {semantic_model}"

4. **snowflake_cortex_search**
   - Used by: Cortex AI Search Agent
   - Variables: `{query}`, `{context}`
   - Default: "Search for information related to: {query}\n\nSearch context: {context}"

5. **snowflake_cortex_combined**
   - Used by: Combined Cortex AI Agent
   - Variables: `{query}`, `{context}`
   - Default: "Process the following query using both structured and unstructured data: {query}\n\nContext: {context}"

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

