"""State schema definitions for LangGraph."""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime
from shared.models.agent_state import AgentType, RequestStatus


class AgentStateSchema(TypedDict):
    """Schema for LangGraph agent state."""
    
    # Request information
    query: str
    session_id: str
    
    # Agent routing
    selected_agent: Optional[AgentType]
    routing_reason: Optional[str]
    
    # Processing state
    status: RequestStatus
    current_step: Optional[str]
    
    # Memory
    short_term_memory: Dict[str, Any]
    long_term_memory: Dict[str, Any]
    
    # Results
    intermediate_results: List[Dict[str, Any]]
    final_response: Optional[str]
    
    # Metadata
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    # Error handling
    error: Optional[str]
    retry_count: int


class StateUpdate(TypedDict):
    """Update to agent state."""
    
    selected_agent: Optional[AgentType]
    routing_reason: Optional[str]
    status: Optional[RequestStatus]
    current_step: Optional[str]
    intermediate_results: Optional[List[Dict[str, Any]]]
    final_response: Optional[str]
    error: Optional[str]
    metadata: Optional[Dict[str, Any]]

