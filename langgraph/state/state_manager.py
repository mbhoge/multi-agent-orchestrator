"""State manager for LangGraph agent state."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from shared.models.agent_state import AgentState, RequestStatus
from langgraph.state.schema import AgentStateSchema, StateUpdate

logger = logging.getLogger(__name__)


class StateManager:
    """Manages agent state for LangGraph."""
    
    def __init__(self):
        """Initialize the state manager."""
        self.states: Dict[str, AgentState] = {}
        logger.info("Initialized State Manager")
    
    def create_state(
        self,
        query: str,
        session_id: str,
        initial_metadata: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Create a new agent state.
        
        Args:
            query: User query
            session_id: Session identifier
            initial_metadata: Optional initial metadata
        
        Returns:
            Created agent state
        """
        state = AgentState(
            query=query,
            session_id=session_id,
            metadata=initial_metadata or {}
        )
        self.states[session_id] = state
        logger.debug(f"Created state for session {session_id}")
        return state
    
    def get_state(self, session_id: str) -> Optional[AgentState]:
        """
        Get state for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Agent state or None if not found
        """
        return self.states.get(session_id)
    
    def update_state(
        self,
        session_id: str,
        update: StateUpdate
    ) -> Optional[AgentState]:
        """
        Update agent state.
        
        Args:
            session_id: Session identifier
            update: State update dictionary
        
        Returns:
            Updated agent state or None if not found
        """
        state = self.states.get(session_id)
        if not state:
            logger.warning(f"State not found for session {session_id}")
            return None
        
        # Update fields
        if "selected_agent" in update:
            state.selected_agent = update["selected_agent"]
        if "routing_reason" in update:
            state.routing_reason = update["routing_reason"]
        if "status" in update:
            state.status = update["status"]
        if "current_step" in update:
            state.current_step = update["current_step"]
        if "intermediate_results" in update:
            state.intermediate_results = update["intermediate_results"]
        if "final_response" in update:
            state.final_response = update["final_response"]
        if "error" in update:
            state.error = update["error"]
        if "metadata" in update:
            state.metadata.update(update["metadata"])
        
        state.updated_at = datetime.utcnow()
        logger.debug(f"Updated state for session {session_id}")
        return state
    
    def delete_state(self, session_id: str) -> bool:
        """
        Delete state for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if deleted, False if not found
        """
        if session_id in self.states:
            del self.states[session_id]
            logger.debug(f"Deleted state for session {session_id}")
            return True
        return False
    
    def get_all_sessions(self) -> List[str]:
        """
        Get all session IDs.
        
        Returns:
            List of session IDs
        """
        return list(self.states.keys())


# Global state manager instance
state_manager = StateManager()

