"""LangGraph StateGraph for supervisor workflow."""

import logging
import time
import json
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, START, END
from langgraph.state.graph_state import SupervisorState
from langgraph.memory.short_term import short_term_memory
from langgraph.memory.long_term import long_term_memory
from langgraph.observability.langfuse_client import LangfuseClient
from langgraph.supervisor.planning import plan_prompt, executor_prompt
from langgraph.supervisor.llm_client import PlannerLLMClient
from shared.config.settings import settings
from shared.utils.exceptions import LangGraphError

logger = logging.getLogger(__name__)

# Global instances (will be initialized by supervisor)
langfuse_client: Optional[LangfuseClient] = None
snowflake_gateway_endpoint: Optional[str] = None
langgraph_timeout: Optional[int] = None
planner_llm_client: Optional[PlannerLLMClient] = None


def initialize_graph_globals(client: LangfuseClient, gateway_endpoint: str, timeout: int):
    """Initialize global variables for graph nodes.
    
    Args:
        client: Langfuse client instance
        gateway_endpoint: Snowflake gateway endpoint URL
        timeout: Request timeout in seconds
    """
    global langfuse_client, snowflake_gateway_endpoint, langgraph_timeout, planner_llm_client
    langfuse_client = client
    snowflake_gateway_endpoint = gateway_endpoint
    langgraph_timeout = timeout
    planner_llm_client = PlannerLLMClient(settings.planner_llm)


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


async def plan_request(state: SupervisorState) -> SupervisorState:
    """Plan request into numbered steps with assigned sub-agents.
    
    Node: plan_request
    - Create a plan from the query + context
    - Store plan in state and short-term memory
    """
    session_id = state["session_id"]
    query = state["query"]
    context = state.get("context") or {}
    
    logger.info(f"Planning request for session {session_id}")
    
    try:
        # Build planner prompt and call LLM
        if not planner_llm_client:
            raise LangGraphError("Planner LLM client not initialized.")

        planner_prompt = plan_prompt(state)
        llm_reply = await planner_llm_client.complete(prompt=planner_prompt)
        parsed_plan = planner_llm_client.extract_json(llm_reply)

        # Accept {"plan": {...}} or direct plan dict
        plan = parsed_plan.get("plan") if isinstance(parsed_plan, dict) else None
        if not plan and isinstance(parsed_plan, dict):
            plan = parsed_plan

        if not isinstance(plan, dict) or not plan:
            raise LangGraphError(f"Planner returned invalid plan: {llm_reply}")

        # Store planner prompt/output for traceability
        state.setdefault("metadata", {})["planner_prompt"] = planner_prompt
        state.setdefault("metadata", {})["planner_output"] = llm_reply

        state["plan"] = plan
        state["plan_current_step"] = 1
        state["replan_flag"] = False
        state["last_reason"] = ""
        state["current_step"] = "plan_request"

        short_term_memory.store(
            session_id=session_id,
            key="plan",
            value=plan,
        )

        return state
    except Exception as e:
        logger.error(f"Error in plan_request: {str(e)}")
        state["status"] = "failed"
        state["error"] = f"Planning failed: {str(e)}"
        state["current_step"] = "plan_request_error"
        return state


async def execute_plan(state: SupervisorState) -> SupervisorState:
    """Convert the plan into a routing decision for this request.

    Node: execute_plan
    - Extract agents from the plan
    - Set routing_decision for downstream invocation
    """
    session_id = state["session_id"]
    plan = state.get("plan") or {}
    step_index = int(state.get("plan_current_step") or 1)
    step_key = str(step_index)
    plan_block = plan.get(step_key) if isinstance(plan, dict) else None

    logger.info(f"Executing plan for session {session_id}")

    try:
        if not planner_llm_client:
            raise LangGraphError("Executor LLM client not initialized.")

        executor_prompt_text = executor_prompt(state)
        executor_reply = await planner_llm_client.complete(prompt=executor_prompt_text)
        executor_json = planner_llm_client.extract_json(executor_reply)

        # Store executor prompt/output for traceability
        state.setdefault("metadata", {})["executor_prompt"] = executor_prompt_text
        state.setdefault("metadata", {})["executor_output"] = executor_reply

        if not isinstance(plan_block, dict) or not plan_block.get("agent"):
            raise LangGraphError("Planner produced no step with an agent.")

        if executor_json.get("replan"):
            attempts = state.get("replan_attempts", {}) or {}
            attempts[step_index] = int(attempts.get(step_index, 0)) + 1
            state["replan_attempts"] = attempts
            state["replan_flag"] = True
            state["last_reason"] = str(executor_json.get("reason") or "Executor requested replan.")
            state["current_step"] = "execute_plan_replan"
            return state

        agent_name = str(executor_json.get("goto") or plan_block.get("agent"))
        agent_query = str(executor_json.get("query") or plan_block.get("action") or state.get("query"))

        routing_decision = {
            "agents_to_call": [agent_name],
            "routing_reason": f"Executor: {executor_json.get('reason', '')}".strip(),
            "confidence": 0.7,
        }

        state["routing_decision"] = routing_decision
        state["agent_query"] = agent_query
        state["replan_flag"] = False
        state["last_reason"] = str(executor_json.get("reason") or "")
        state["current_step"] = "execute_plan"
        
        short_term_memory.store(
            session_id=session_id,
            key="routing_decision",
            value=routing_decision,
        )
        
        return state
    except Exception as e:
        logger.error(f"Error in execute_plan: {str(e)}")
        state["status"] = "failed"
        state["error"] = f"Plan execution failed: {str(e)}"
        state["current_step"] = "execute_plan_error"
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
    query = state.get("agent_query") or state["query"]
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
                    "plan": state.get("plan"),
                    "plan_current_step": state.get("plan_current_step"),
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


async def advance_plan(state: SupervisorState) -> SupervisorState:
    """Advance planner step or mark for replan."""
    plan = state.get("plan") or {}
    step = int(state.get("plan_current_step") or 1)

    # If executor requested a replan, keep step index and return.
    if state.get("replan_flag"):
        state["current_step"] = "advance_plan_replan"
        return state

    if isinstance(plan, dict) and str(step + 1) in plan:
        state["plan_current_step"] = step + 1
    state["current_step"] = "advance_plan"
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
    workflow.add_node("plan_request", plan_request)
    workflow.add_node("execute_plan", execute_plan)
    workflow.add_node("invoke_agents", invoke_agents)
    workflow.add_node("combine_responses", combine_responses)
    workflow.add_node("advance_plan", advance_plan)
    workflow.add_node("update_memory", update_memory)
    workflow.add_node("log_observability", log_observability)
    workflow.add_node("handle_error", handle_error)
    
    # Define edges
    workflow.add_edge(START, "load_state")
    workflow.add_edge("load_state", "plan_request")
    
    # Error handling: route to handle_error if status is "failed"
    def should_handle_error(state: SupervisorState) -> str:
        """Determine next node based on state status."""
        if state.get("status") == "failed":
            return "handle_error"
        return "continue"
    
    # Add conditional edges for error handling after plan_request
    workflow.add_conditional_edges(
        "plan_request",
        should_handle_error,
        {
            "handle_error": "handle_error",
            "continue": "execute_plan",
        },
    )

    workflow.add_conditional_edges(
        "execute_plan",
        should_handle_error,
        {
            "handle_error": "handle_error",
            "continue": "invoke_agents",
        },
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
            "continue": "advance_plan"
        }
    )

    def should_continue_plan(state: SupervisorState) -> str:
        """Determine next step in planning flow."""
        if state.get("status") == "failed":
            return "handle_error"
        if state.get("replan_flag"):
            return "replan"
        plan = state.get("plan") or {}
        step = int(state.get("plan_current_step") or 1)
        if isinstance(plan, dict) and str(step) in plan:
            return "continue"
        return "done"

    workflow.add_conditional_edges(
        "advance_plan",
        should_continue_plan,
        {
            "handle_error": "handle_error",
            "replan": "plan_request",
            "continue": "execute_plan",
            "done": "update_memory",
        },
    )
    
    # Regular edges for successful flow
    workflow.add_edge("update_memory", "log_observability")
    workflow.add_edge("log_observability", END)
    workflow.add_edge("handle_error", END)
    
    # Compile graph (without checkpointer for now - can add later)
    graph = workflow.compile()
    
    logger.info("Created and compiled supervisor StateGraph")
    return graph
