"""Agent state models for LangGraph state management."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AgentType(str, Enum):
    """Types of agents available."""
    
    CORTEX_ANALYST = "cortex_analyst"
    CORTEX_SEARCH = "cortex_search"
    CORTEX_COMBINED = "cortex_combined"


class RequestStatus(str, Enum):
    """Status of a request."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentState(BaseModel):
    """State model for LangGraph agent state."""
    
    # Request information
    query: str = Field(..., description="User query")
    session_id: str = Field(..., description="Session identifier")
    
    # Agent routing
    selected_agent: Optional[AgentType] = Field(
        default=None,
        description="Selected agent to handle the request"
    )
    routing_reason: Optional[str] = Field(
        default=None,
        description="Reason for agent selection"
    )
    
    # Processing state
    status: RequestStatus = Field(default=RequestStatus.PENDING, description="Request status")
    current_step: Optional[str] = Field(default=None, description="Current processing step")
    
    # Memory
    short_term_memory: Dict[str, Any] = Field(
        default_factory=dict,
        description="Short-term memory for current session"
    )
    long_term_memory: Dict[str, Any] = Field(
        default_factory=dict,
        description="Long-term memory across sessions"
    )
    
    # Results
    intermediate_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Intermediate processing results"
    )
    final_response: Optional[str] = Field(default=None, description="Final response")
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional state metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="State creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    # Error handling
    error: Optional[str] = Field(default=None, description="Error message if any")
    retry_count: int = Field(default=0, description="Number of retries attempted")


class MemoryEntry(BaseModel):
    """Entry in memory storage."""
    
    key: str = Field(..., description="Memory key")
    value: Any = Field(..., description="Memory value")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Entry timestamp")
    ttl: Optional[int] = Field(default=None, description="Time to live in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Entry metadata")

