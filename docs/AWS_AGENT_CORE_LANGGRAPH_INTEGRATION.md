# AWS Agent Core SDK Integration with LangGraph Supervisor

This document explores the possibilities of calling LangGraph Supervisor agent using the AWS Agent Core SDK, based on research and official AWS documentation.

## Table of Contents

1. [Integration Approaches](#integration-approaches)
2. [Approach 1: Deploy LangGraph as Agent Core Agent](#approach-1-deploy-langgraph-as-agent-core-agent)
3. [Approach 2: Use Agent Core Tools/Actions to Call LangGraph](#approach-2-use-agent-core-toolsactions-to-call-langgraph)
4. [Approach 3: Direct HTTP Invocation (Current Implementation)](#approach-3-direct-http-invocation-current-implementation)
5. [Code Examples](#code-examples)
6. [References](#references)

---

## Integration Approaches

Based on AWS documentation and best practices, there are **three main approaches** to integrate AWS Agent Core SDK with LangGraph Supervisor:

### 1. **Deploy LangGraph as an Agent Core Agent** (Recommended)
   - Wrap LangGraph supervisor as an Agent Core agent
   - Deploy using `BedrockAgentCoreApp`
   - Native integration with Agent Core Runtime

### 2. **Use Agent Core Tools/Actions**
   - Define LangGraph as a custom action/tool
   - Agent Core invokes LangGraph via action groups
   - Useful for multi-agent orchestration

### 3. **Direct HTTP Invocation** (Current Implementation)
   - Agent Core orchestrator makes HTTP calls to LangGraph
   - Simple but less integrated
   - Requires manual connection management

---

## Approach 1: Deploy LangGraph as Agent Core Agent

This is the **recommended approach** according to AWS documentation. It involves wrapping your LangGraph supervisor as an Agent Core agent and deploying it using the AWS Agent Core SDK.

### Implementation Example

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from typing import TypedDict, List
from langgraph.graph.message import add_messages

# Initialize the language model
llm = init_chat_model(
    "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    model_provider="bedrock_converse",
)

# Define the agent's state
class State(TypedDict):
    messages: List[dict]
    session_id: str
    context: dict

# Build LangGraph supervisor
graph_builder = StateGraph(State)

# Add supervisor nodes
def supervisor_node(state: State):
    """Supervisor node that routes to appropriate agents."""
    # Your routing logic here
    return {"messages": state["messages"]}

def process_query_node(state: State):
    """Process the query using selected agent."""
    # Your processing logic here
    return {"messages": state["messages"]}

# Add nodes and edges
graph_builder.add_node("supervisor", supervisor_node)
graph_builder.add_node("process", process_query_node)
graph_builder.add_edge("supervisor", "process")

# Compile the graph
graph = graph_builder.compile()

# Initialize the Agent Core application
app = BedrockAgentCoreApp()

@app.entrypoint
def agent_invocation(payload, context):
    """
    Entry point for Agent Core invocations.
    
    Args:
        payload: Request payload from Agent Core
        context: Runtime context
    
    Returns:
        Response dictionary
    """
    user_message = payload.get("prompt", "No prompt found in input.")
    session_id = payload.get("session_id", "")
    query_context = payload.get("context", {})
    
    # Invoke LangGraph supervisor
    result = graph.invoke({
        "messages": [{"role": "user", "content": user_message}],
        "session_id": session_id,
        "context": query_context
    })
    
    return {
        "result": result['messages'][-1].content if result.get('messages') else "",
        "session_id": session_id
    }

# Run the application
if __name__ == "__main__":
    app.run()
```

### Key Benefits

- ✅ Native integration with Agent Core Runtime
- ✅ Automatic scaling and resource management
- ✅ Built-in observability and tracing
- ✅ Memory management via AgentCore Memory
- ✅ Secure execution environment

### Deployment Steps

1. **Package your agent:**
   ```bash
   # Create deployment package
   pip install bedrock-agentcore-sdk langgraph langchain-aws
   ```

2. **Deploy to Agent Core Runtime:**
   ```bash
   # Using AWS CLI or SDK
   aws bedrock-agent create-agent \
     --agent-name "langgraph-supervisor" \
     --agent-resource-role-arn "arn:aws:iam::ACCOUNT:role/AgentRole" \
     --foundation-model "anthropic.claude-3-5-sonnet-20241022-v1:0"
   ```

3. **Create agent alias:**
   ```bash
   aws bedrock-agent create-agent-alias \
     --agent-id "AGENT_ID" \
     --agent-alias-name "production"
   ```

---

## Approach 2: Use Agent Core Tools/Actions to Call LangGraph

In this approach, LangGraph Supervisor is exposed as a custom action/tool that Agent Core can invoke. This is useful when you want Agent Core to decide when to call LangGraph.

### Implementation Example

#### Step 1: Define LangGraph as an Action Group

```python
# langgraph_action.py
import httpx
from typing import Dict, Any

class LangGraphAction:
    """Action handler for LangGraph supervisor."""
    
    def __init__(self, langgraph_endpoint: str):
        self.endpoint = langgraph_endpoint
    
    def invoke_supervisor(
        self,
        query: str,
        session_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke LangGraph supervisor.
        
        Args:
            query: User query
            session_id: Session identifier
            context: Additional context
        
        Returns:
            Response from LangGraph
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/supervisor/process",
                json={
                    "query": query,
                    "session_id": session_id,
                    "context": context
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
```

#### Step 2: Register Action in Agent Core

```python
# agent_core_config.py
from aws_agent_core.runtime.sdk_client import AgentCoreRuntimeClient
from langgraph_action import LangGraphAction

# Initialize action handler
langgraph_action = LangGraphAction("http://langgraph:8001")

# Define action schema for Agent Core
LANGGRAPH_ACTION_SCHEMA = {
    "name": "invoke_langgraph_supervisor",
    "description": "Invoke LangGraph supervisor to route query to appropriate agent",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "User query to process"
            },
            "session_id": {
                "type": "string",
                "description": "Session identifier"
            },
            "context": {
                "type": "object",
                "description": "Additional context for routing"
            }
        },
        "required": ["query", "session_id"]
    }
}

# Register action with Agent Core
def register_langgraph_action(agent_id: str, action_group_name: str):
    """Register LangGraph action with Agent Core."""
    client = AgentCoreRuntimeClient()
    
    # Create action group
    client.create_action_group(
        agent_id=agent_id,
        action_group_name=action_group_name,
        action_group_executor={
            "lambda": "arn:aws:lambda:REGION:ACCOUNT:function:langgraph-action-handler"
        },
        action_group_state="ENABLED",
        api_schema={
            "s3": {
                "s3BucketName": "your-bucket",
                "s3ObjectKey": "langgraph-action-schema.json"
            }
        }
    )
```

#### Step 3: Lambda Handler for Action Execution

```python
# lambda_handler.py
import json
import httpx

def lambda_handler(event, context):
    """
    Lambda handler for LangGraph action execution.
    
    Event structure:
    {
        "actionGroupInvocationInput": {
            "actionGroupName": "LangGraphActionGroup",
            "verb": "invoke_supervisor",
            "parameters": {
                "query": "...",
                "session_id": "...",
                "context": {...}
            }
        }
    }
    """
    action_input = event.get("actionGroupInvocationInput", {})
    parameters = action_input.get("parameters", {})
    
    query = parameters.get("query")
    session_id = parameters.get("session_id")
    context = parameters.get("context", {})
    
    # Invoke LangGraph supervisor
    try:
        response = httpx.post(
            "http://langgraph:8001/supervisor/process",
            json={
                "query": query,
                "session_id": session_id,
                "context": context
            },
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()
        
        return {
            "actionGroupInvocationOutput": {
                "text": json.dumps(result)
            }
        }
    except Exception as e:
        return {
            "actionGroupInvocationOutput": {
                "text": f"Error: {str(e)}"
            }
        }
```

### Key Benefits

- ✅ Agent Core decides when to invoke LangGraph
- ✅ Can combine multiple tools/actions
- ✅ Native Agent Core tool orchestration
- ✅ Built-in error handling and retries

---

## Approach 3: Direct HTTP Invocation (Current Implementation)

This is the approach currently used in the codebase. It's simpler but less integrated.

### Current Implementation

```python
# aws_agent_core/orchestrator.py
async def _invoke_langgraph(
    self,
    request: AgentRequest,
    session_id: str
) -> Dict[str, Any]:
    """
    Invoke LangGraph supervisor via HTTP.
    """
    try:
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
    except httpx.HTTPError as e:
        raise LangGraphError(f"Failed to invoke LangGraph: {str(e)}")
```

### Comparison with Agent Core SDK Approach

| Aspect | Direct HTTP | Agent Core SDK |
|--------|-------------|----------------|
| Integration | Manual | Native |
| Observability | Manual | Built-in |
| Scaling | Manual | Automatic |
| Memory Management | Manual | AgentCore Memory |
| Error Handling | Manual | Built-in |
| Complexity | Low | Medium |

---

## Using Agent Core Runtime SDK to Invoke Agents

If you want to use the Agent Core Runtime SDK to invoke an agent (which internally calls LangGraph), here's how:

### Example: Invoking Agent via Runtime SDK

```python
import boto3
from botocore.exceptions import ClientError

class AgentCoreRuntimeClient:
    """Client for AWS Agent Core Runtime SDK."""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client(
            'bedrock-agent-runtime',
            region_name=region_name
        )
    
    def invoke_agent(
        self,
        agent_id: str,
        agent_alias_id: str,
        session_id: str,
        input_text: str,
        enable_trace: bool = True
    ) -> dict:
        """
        Invoke an Agent Core agent.
        
        Args:
            agent_id: Agent identifier
            agent_alias_id: Agent alias identifier
            session_id: Session identifier
            input_text: Input text to process
            enable_trace: Enable tracing
        
        Returns:
            Agent response
        """
        try:
            response = self.client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=enable_trace
            )
            
            # Stream the response
            completion = ""
            trace_id = None
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
                elif 'trace' in event:
                    trace = event['trace']
                    if 'traceId' in trace:
                        trace_id = trace['traceId']
            
            return {
                "completion": completion,
                "trace_id": trace_id
            }
            
        except ClientError as e:
            raise AWSAgentCoreError(f"Failed to invoke agent: {str(e)}")
```

### Usage Example

```python
# Initialize client
client = AgentCoreRuntimeClient(region_name="us-east-1")

# Invoke agent (which internally uses LangGraph)
result = client.invoke_agent(
    agent_id="YOUR_AGENT_ID",
    agent_alias_id="YOUR_ALIAS_ID",
    session_id="session-123",
    input_text="What are the total sales for last month?",
    enable_trace=True
)

print(f"Response: {result['completion']}")
print(f"Trace ID: {result['trace_id']}")
```

---

## Integration with AgentCore Memory

AWS Agent Core provides memory management that can be integrated with LangGraph for state persistence.

### Short-Term Memory (Conversation State)

```python
from langgraph_checkpoint_aws import AgentCoreMemorySaver

# Initialize memory saver
MEMORY_ID = "your-memory-id"
REGION = "us-east-1"

checkpointer = AgentCoreMemorySaver(MEMORY_ID, region_name=REGION)

# Use with LangGraph
graph = graph_builder.compile(checkpointer=checkpointer)
```

### Long-Term Memory (Knowledge Search)

```python
from langgraph_checkpoint_aws import AgentCoreMemoryStore

# Initialize memory store
store = AgentCoreMemoryStore(MEMORY_ID, region_name=REGION)

# Search in long-term memory
results = store.search(
    query="user query",
    limit=5
)
```

---

## Recommended Architecture

Based on AWS best practices, the recommended architecture is:

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Agent Core Runtime                     │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         Agent Core Agent (LangGraph Wrapper)          │  │
│  │                                                         │  │
│  │  @app.entrypoint                                       │  │
│  │  def agent_invocation(payload, context):             │  │
│  │      result = langgraph_supervisor.invoke(...)        │  │
│  │      return result                                     │  │
│  └────────────────────────────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │            LangGraph Supervisor (Internal)             │  │
│  │                                                         │  │
│  │  - State management                                     │  │
│  │  - Agent routing                                        │  │
│  │  - Memory integration                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         Snowflake Cortex Agents (via HTTP)             │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## References

### Official AWS Documentation

1. **Using Any Agent Framework with Agent Core**
   - URL: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/using-any-agent-framework.html
   - Description: Comprehensive guide on integrating LangGraph and other frameworks with Agent Core SDK

2. **Integrating AgentCore Memory with LangGraph**
   - URL: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-integrate-lang.html
   - Description: Guide on integrating AgentCore Memory for state persistence and long-term memory search

3. **Agent Core Starter Toolkit**
   - URL: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-toolkit.html
   - Description: Getting started guide for deploying agents to Agent Core Runtime

### AWS Blog Posts

4. **Building Multi-Agent Systems with LangGraph and Amazon Bedrock**
   - URL: https://aws.amazon.com/blogs/machine-learning/build-multi-agent-systems-with-langgraph-and-amazon-bedrock/
   - Description: AWS blog post with practical examples and best practices

### Architecture Resources

5. **Multi-Agent Orchestration on AWS**
   - URL: https://d1.awsstatic.com/onedam/marketing-channels/website/aws/en_US/solutions/approved/documents/architecture-diagrams/multi-agent-orchestration-on-aws.pdf
   - Description: Architecture diagrams and best practices for multi-agent systems

### GitHub Repositories

6. **AWS Bedrock Agent Core SDK (TypeScript)**
   - URL: https://github.com/aws/bedrock-agentcore-sdk-typescript
   - Description: Official SDK repository with examples

### Python SDK Documentation

7. **Boto3 Bedrock Agent Runtime**
   - URL: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime.html
   - Description: Python SDK documentation for invoking agents

---

## Migration Path from Current Implementation

To migrate from the current direct HTTP approach to the recommended Agent Core SDK approach:

### Step 1: Wrap LangGraph as Agent Core Agent

```python
# langgraph_agent_core_wrapper.py
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langgraph.supervisor import LangGraphSupervisor

app = BedrockAgentCoreApp()
supervisor = LangGraphSupervisor()

@app.entrypoint
def agent_invocation(payload, context):
    query = payload.get("prompt", "")
    session_id = payload.get("session_id", "")
    context_data = payload.get("context", {})
    
    result = supervisor.process_request(
        query=query,
        session_id=session_id,
        context=context_data
    )
    
    return {"result": result.response}

if __name__ == "__main__":
    app.run()
```

### Step 2: Update Orchestrator to Use Agent Core SDK

```python
# aws_agent_core/orchestrator.py (Updated)
async def _invoke_langgraph(
    self,
    request: AgentRequest,
    session_id: str
) -> Dict[str, Any]:
    """
    Invoke LangGraph via Agent Core Runtime SDK.
    """
    try:
        # Use Agent Core Runtime SDK instead of direct HTTP
        result = self.runtime_client.invoke_agent(
            agent_id=self.langgraph_agent_id,
            agent_alias_id=self.langgraph_agent_alias_id,
            session_id=session_id,
            input_text=request.query,
            enable_trace=True
        )
        
        return {
            "response": result["completion"],
            "selected_agent": "langgraph",
            "trace_id": result.get("trace_id")
        }
    except Exception as e:
        raise LangGraphError(f"Failed to invoke LangGraph via Agent Core: {str(e)}")
```

### Step 3: Deploy LangGraph Agent

```bash
# Package and deploy
aws bedrock-agent create-agent \
  --agent-name "langgraph-supervisor" \
  --foundation-model "anthropic.claude-3-5-sonnet-20241022-v1:0" \
  --agent-resource-role-arn "arn:aws:iam::ACCOUNT:role/AgentRole"
```

---

## Summary

### Key Takeaways

1. **Recommended Approach**: Deploy LangGraph as an Agent Core agent using `BedrockAgentCoreApp`
2. **Benefits**: Native integration, automatic scaling, built-in observability, memory management
3. **Alternative**: Use Agent Core actions/tools if you need Agent Core to decide when to call LangGraph
4. **Current Approach**: Direct HTTP works but lacks native integration benefits

### Next Steps

1. Review the official AWS documentation links provided
2. Evaluate migration to Agent Core SDK approach
3. Consider AgentCore Memory integration for state persistence
4. Test the integration in a development environment
5. Plan deployment strategy for production

---

**Last Updated**: 2024  
**Based on**: AWS Official Documentation and Best Practices
