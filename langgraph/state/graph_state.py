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
    
    # Execution tracking
    start_time: Optional[float]  # Timestamp when processing started
    execution_time: Optional[float]  # Total execution time in seconds
