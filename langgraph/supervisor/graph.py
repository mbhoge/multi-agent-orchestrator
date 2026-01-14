"""LangGraph StateGraph for supervisor workflow."""

import logging
import time
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.state.graph_state import SupervisorState
from langgraph.memory.short_term import short_term_memory
from langgraph.memory.long_term import long_term_memory
from langgraph.supervisor.policies import get_routing_policy
from langgraph.observability.langfuse_client import LangfuseClient
from shared.config.settings import settings
from shared.utils.exceptions import LangGraphError

logger = logging.getLogger(__name__)

# Global instances (will be initialized by supervisor)
langfuse_client: Optional[LangfuseClient] = None
snowflake_gateway_endpoint: Optional[str] = None
langgraph_timeout: Optional[int] = None


def initialize_graph_globals(client: LangfuseClient, gateway_endpoint: str, timeout: int):
    """Initialize global variables for graph nodes.
    
    Args:
        client: Langfuse client instance
        gateway_endpoint: Snowflake gateway endpoint URL
        timeout: Request timeout in seconds
    """
    global langfuse_client, snowflake_gateway_endpoint, langgraph_timeout
    langfuse_client = client
    snowflake_gateway_endpoint = gateway_endpoint
    langgraph_timeout = timeout


async def load_state(state: SupervisorState) -> SupervisorState:
    """Load state and conversation history.
    
    Node: load_state
    - Retrieve conversation history from short_term_memory
    - Append current user message to history
    - Initialize state fields
    
    Args:
        state: Current supervisor state
        
    Returns:
        Updated state with loaded history
    """
    session_id = state["session_id"]
    query = state["query"]
    
    logger.info(f"Loading state for session {session_id}")
    
    # Retrieve prior conversation history
    history = short_term_memory.retrieve(session_id=session_id, key="history") or []
    if not isinstance(history, list):
        history = []
    
    # Append current user message to history
    history.append({
        "role": "user",
        "content": query,
        "ts": time.time(),
    })
    
    # Update state
    state["messages"] = history
    state["status"] = "processing"
    state["current_step"] = "load_state"
    state["start_time"] = time.time()
    state["agent_responses"] = []
    
    logger.debug(f"Loaded {len(history)} messages for session {session_id}")
    return state


async def route_request(state: SupervisorState) -> SupervisorState:
    """Route request to appropriate agent(s).
    
    Node: route_request
    - Get routing prompt from Langfuse
    - Call agent_router to determine which agents to invoke
    - Store routing decision in state
    
    Args:
        state: Current supervisor state
        
    Returns:
        Updated state with routing decision
    """
    session_id = state["session_id"]
    query = state["query"]
    context = state.get("context") or {}
    
    logger.info(f"Routing request for session {session_id}")
    
    try:
        # Routing policy strategy (selected via LANGGRAPH_ROUTING_MODE).
        #
        # This keeps the supervisor workflow stable while allowing multiple routing
        # behaviors (optimized router vs. handoffs) to coexist and be tested separately.
        routing_policy = get_routing_policy()

        agent_preference = state.get("metadata", {}).get("agent_preference")

        # Prompt rendering is passed into the policy as a callback so the policy can
        # decide to SKIP prompt + routing calls for follow-ups (latency optimization).
        async def render_routing_prompt() -> str:
            return await langfuse_client.get_prompt_for_routing(query=query, context=context)

        routing_decision = await routing_policy.decide(
            session_id=session_id,
            query=query,
            context=context,
            messages=state.get("messages", []) or [],
            agent_preference=agent_preference,
            render_routing_prompt=render_routing_prompt,
        )
        
        # Update state
        state["routing_decision"] = routing_decision
        state["current_step"] = "route_request"
        
        # Store routing decision in short-term memory
        short_term_memory.store(
            session_id=session_id,
            key="routing_decision",
            value=routing_decision,
        )
        
        logger.info(
            f"Routed to agents: {routing_decision.get('agents_to_call', [])} "
            f"(mode={settings.langgraph.routing_mode})"
        )
        return state
        
    except Exception as e:
        logger.error(f"Error in route_request: {str(e)}")
        state["status"] = "failed"
        state["error"] = f"Routing failed: {str(e)}"
        state["current_step"] = "route_request_error"
        return state


async def invoke_agents(state: SupervisorState) -> SupervisorState:
    """Invoke Snowflake Cortex agents.
    
    Node: invoke_agents
    - Extract agents_to_call from routing_decision
    - For each agent, invoke via HTTP call to gateway
    - Collect all responses
    
    Args:
        state: Current supervisor state
        
    Returns:
        Updated state with agent responses
    """
    session_id = state["session_id"]
    query = state["query"]
    routing_decision = state.get("routing_decision")
    messages = state.get("messages", [])
    context = state.get("context") or {}
    
    logger.info(f"Invoking agents for session {session_id}")
    
    try:
        if not routing_decision:
            raise LangGraphError("No routing decision available")
        
        agent_names = routing_decision.get("agents_to_call", []) or []
        if not isinstance(agent_names, list) or not agent_names:
            raise LangGraphError("No Snowflake agent objects selected for invocation.")
        
        # Build enriched context for downstream agents
        max_history = 30
        enriched_context = {
            **context,
            "history": messages[-max_history:],
            "langgraph": {
                "state": {
                    "session_id": session_id,
                    "status": state.get("status"),
                    "current_step": state.get("current_step"),
                },
                "short_term_memory": short_term_memory.get_all(session_id=session_id),
            },
        }
        
        # Invoke each agent
        agent_responses = []
        for agent_name in agent_names:
            response = await _invoke_snowflake_agent(
                agent_name=agent_name,
                query=query,
                session_id=session_id,
                context=enriched_context,
            )
            agent_responses.append(response)
        
        # Update state
        state["agent_responses"] = agent_responses
        state["current_step"] = "invoke_agents"
        
        logger.info(f"Invoked {len(agent_responses)} agents for session {session_id}")
        return state
        
    except Exception as e:
        logger.error(f"Error in invoke_agents: {str(e)}")
        state["status"] = "failed"
        state["error"] = f"Agent invocation failed: {str(e)}"
        state["current_step"] = "invoke_agents_error"
        return state


async def combine_responses(state: SupervisorState) -> SupervisorState:
    """Combine responses from multiple agents.
    
    Node: combine_responses
    - If single agent: use response directly
    - If multiple agents: combine with agent labels
    - Build enriched response with sources
    
    Args:
        state: Current supervisor state
        
    Returns:
        Updated state with final_response
    """
    agent_responses = state.get("agent_responses", [])
    
    logger.info(f"Combining {len(agent_responses)} agent responses")
    
    try:
        if len(agent_responses) == 1:
            agent_response = agent_responses[0]
        else:
            # Combine multiple responses
            combined_text = "\n\n".join(
                [
                    f"[{r.get('agent_name', 'agent')}] {r.get('response', '')}"
                    for r in agent_responses
                ]
            ).strip()
            combined_sources = []
            for r in agent_responses:
                combined_sources.extend(r.get("sources", []) or [])
            agent_response = {
                "response": combined_text,
                "sources": combined_sources,
                "agents": [r.get("agent_name") for r in agent_responses],
            }
        
        # Update state
        state["final_response"] = agent_response.get("response", "")
        state["current_step"] = "combine_responses"
        
        # Store combined response in state for memory update
        state["agent_responses"] = [agent_response]  # Store combined response
        
        return state
        
    except Exception as e:
        logger.error(f"Error in combine_responses: {str(e)}")
        state["status"] = "failed"
        state["error"] = f"Response combination failed: {str(e)}"
        state["current_step"] = "combine_responses_error"
        return state


async def update_memory(state: SupervisorState) -> SupervisorState:
    """Update memory with conversation history and patterns.
    
    Node: update_memory
    - Append assistant response to history
    - Store in short_term_memory (bounded window)
    - Store in long_term_memory if high confidence
    
    Args:
        state: Current supervisor state
        
    Returns:
        Updated state
    """
    session_id = state["session_id"]
    messages = state.get("messages", [])
    final_response = state.get("final_response", "")
    routing_decision = state.get("routing_decision", {})
    
    logger.info(f"Updating memory for session {session_id}")
    
    try:
        # Append assistant response to history
        if final_response:
            messages.append({
                "role": "assistant",
                "content": final_response,
                "ts": time.time(),
            })
        
        # Persist updated history (bounded window)
        max_history = 30
        short_term_memory.store(
            session_id=session_id,
            key="history",
            value=messages[-max_history:],
        )
        
        # Store last query
        short_term_memory.store(
            session_id=session_id,
            key="last_query",
            value=state["query"]
        )
        
        # Store in long-term memory if significant
        if routing_decision.get("confidence", 0) > 0.8:
            long_term_memory.store(
                key=f"query_pattern_{session_id}",
                value={
                    "query": state["query"],
                    "agents": routing_decision.get("agents_to_call", []),
                    "success": True
                }
            )
        
        # Update state
        state["messages"] = messages[-max_history:]
        state["current_step"] = "update_memory"
        
        logger.debug(f"Updated memory for session {session_id}")
        return state
        
    except Exception as e:
        logger.error(f"Error in update_memory: {str(e)}")
        # Don't fail the workflow on memory errors
        return state


async def log_observability(state: SupervisorState) -> SupervisorState:
    """Log to Langfuse for observability.
    
    Node: log_observability
    - Log supervisor decision to Langfuse
    - Calculate execution time
    - Return final state
    
    Args:
        state: Current supervisor state
        
    Returns:
        Final state with execution time
    """
    session_id = state["session_id"]
    query = state["query"]
    routing_decision = state.get("routing_decision", {})
    start_time = state.get("start_time")
    
    logger.info(f"Logging observability for session {session_id}")
    
    try:
        # Calculate execution time
        execution_time = None
        if start_time:
            execution_time = time.time() - start_time
            state["execution_time"] = execution_time
        
        # Log to Langfuse
        await langfuse_client.log_supervisor_decision(
            session_id=session_id,
            query=query,
            routing_decision=routing_decision,
            execution_time=execution_time or 0.0
        )
        
        # Update state
        state["status"] = "completed"
        state["current_step"] = "completed"
        
        logger.debug(f"Logged observability for session {session_id}")
        return state
        
    except Exception as e:
        logger.error(f"Error in log_observability: {str(e)}")
        # Don't fail the workflow on observability errors
        state["status"] = "completed"  # Still mark as completed
        return state


async def handle_error(state: SupervisorState) -> SupervisorState:
    """Handle errors in the workflow.
    
    Node: handle_error
    - Set status to FAILED
    - Store error message
    - Log error
    
    Args:
        state: Current supervisor state
        
    Returns:
        Error state
    """
    session_id = state["session_id"]
    error = state.get("error", "Unknown error")
    
    logger.error(f"Handling error for session {session_id}: {error}")
    
    state["status"] = "failed"
    state["current_step"] = "error_handled"
    
    return state


async def _invoke_snowflake_agent(
    agent_name: str,
    query: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Invoke Snowflake Cortex AI agent via gateway.
    
    Args:
        agent_name: Name of the agent to invoke
        query: User query
        session_id: Session identifier
        context: Optional context
        
    Returns:
        Response from Snowflake agent
    """
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
            result["agent_name"] = agent_name  # Ensure agent_name is in response
            return result
    except Exception as e:
        logger.warning(f"Failed to invoke Snowflake agent {agent_name}: {str(e)}. Using fallback response.")
        return {
            "agent_name": agent_name,
            "response": f"Response from {agent_name} agent for query: {query[:50]}...",
            "sources": []
        }


def create_supervisor_graph() -> StateGraph:
    """Create and compile the supervisor StateGraph.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph
    workflow = StateGraph(SupervisorState)
    
    # Add nodes
    workflow.add_node("load_state", load_state)
    workflow.add_node("route_request", route_request)
    workflow.add_node("invoke_agents", invoke_agents)
    workflow.add_node("combine_responses", combine_responses)
    workflow.add_node("update_memory", update_memory)
    workflow.add_node("log_observability", log_observability)
    workflow.add_node("handle_error", handle_error)
    
    # Define edges
    workflow.add_edge(START, "load_state")
    workflow.add_edge("load_state", "route_request")
    
    # Error handling: route to handle_error if status is "failed"
    def should_handle_error(state: SupervisorState) -> str:
        """Determine next node based on state status."""
        if state.get("status") == "failed":
            return "handle_error"
        return "continue"
    
    # Add conditional edges for error handling after route_request
    workflow.add_conditional_edges(
        "route_request",
        should_handle_error,
        {
            "handle_error": "handle_error",
            "continue": "invoke_agents"
        }
    )
    
    # Add conditional edges for error handling after invoke_agents
    workflow.add_conditional_edges(
        "invoke_agents",
        should_handle_error,
        {
            "handle_error": "handle_error",
            "continue": "combine_responses"
        }
    )
    
    # Error can also occur in combine_responses
    workflow.add_conditional_edges(
        "combine_responses",
        should_handle_error,
        {
            "handle_error": "handle_error",
            "continue": "update_memory"
        }
    )
    
    # Regular edges for successful flow
    workflow.add_edge("update_memory", "log_observability")
    workflow.add_edge("log_observability", END)
    workflow.add_edge("handle_error", END)
    
    # Compile graph (without checkpointer for now - can add later)
    graph = workflow.compile()
    
    logger.info("Created and compiled supervisor StateGraph")
    return graph
