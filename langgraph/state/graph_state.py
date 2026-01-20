"""State schema for LangGraph StateGraph."""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class SupervisorState(TypedDict):
    """State schema for LangGraph supervisor workflow.
    
    This TypedDict defines the state structure used throughout the StateGraph workflow.
    All nodes receive and return this state structure.
    """
    
    # Request information
    query: str
    session_id: str
    
    # Conversation history (messages array)
    messages: List[Dict[str, Any]]  # Format: [{"role": "user|assistant", "content": "...", "ts": float}]
    
    # Routing decision
    routing_decision: Optional[Dict[str, Any]]  # Contains: agents_to_call, routing_reason, confidence
    
    # Agent responses
    agent_responses: List[Dict[str, Any]]  # List of responses from invoked agents
    
    # Final response
    final_response: Optional[str]
    
    # Status tracking
    status: str  # "processing", "completed", "failed"
    current_step: Optional[str]  # Current workflow step
    
    # Error handling
    error: Optional[str]
    
    # Metadata
    metadata: Dict[str, Any]
    
    # Context for downstream agents
    context: Optional[Dict[str, Any]]  # Enriched context with history, state snapshots

    # Planner state
    plan: Optional[Dict[str, Dict[str, Any]]]  # Planner output keyed by step number
    plan_current_step: Optional[int]  # 1-based index for current plan step
    replan_flag: Optional[bool]  # If true, planner is requested to regenerate the plan
    last_reason: Optional[str]  # Reason for replan or executor decision
    replan_attempts: Optional[Dict[int, int]]  # Replan attempts per step
    enabled_agents: Optional[List[str]]  # Optional allowlist of agents
    user_query: Optional[str]  # Original user query (immutable)
    agent_query: Optional[str]  # Executor-produced agent query for this step
    
    # Execution tracking
    start_time: Optional[float]  # Timestamp when processing started
    execution_time: Optional[float]  # Total execution time in seconds
