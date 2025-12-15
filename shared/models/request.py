"""Request and response models."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class AgentRequest(BaseModel):
    """Request model for agent orchestration."""
    
    query: str = Field(..., description="User query or request")
    session_id: Optional[str] = Field(default=None, description="Session ID for state management")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context for the request"
    )
    agent_preference: Optional[str] = Field(
        default=None,
        description="Preferred agent to handle the request"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Request metadata"
    )


class AgentResponse(BaseModel):
    """Response model from agent orchestration."""
    
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    agent_used: str = Field(..., description="Agent that processed the request")
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the response"
    )
    sources: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Source references used in the response"
    )
    execution_time: Optional[float] = Field(
        default=None,
        description="Execution time in seconds"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Response metadata"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional error details"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

