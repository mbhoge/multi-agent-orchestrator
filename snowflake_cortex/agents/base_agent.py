"""Base agent class for Snowflake Cortex AI agents."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from shared.models.agent_state import AgentType
from shared.utils.exceptions import SnowflakeCortexError

logger = logging.getLogger(__name__)


class BaseCortexAgent(ABC):
    """Base class for Snowflake Cortex AI agents."""
    
    def __init__(self, agent_type: AgentType):
        """
        Initialize the base agent.
        
        Args:
            agent_type: Type of agent
        """
        self.agent_type = agent_type
        logger.info(f"Initialized {agent_type.value} agent")
    
    @abstractmethod
    async def process_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query.
        
        Args:
            query: User query
            session_id: Session identifier
            context: Optional context information
        
        Returns:
            Response dictionary with results
        
        Raises:
            SnowflakeCortexError: If processing fails
        """
        pass
    
    def validate_query(self, query: str) -> bool:
        """
        Validate a query.
        
        Args:
            query: User query
        
        Returns:
            True if valid, False otherwise
        """
        if not query or not query.strip():
            return False
        return True
    
    def prepare_context(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare context for agent processing.
        
        Args:
            context: Optional context dictionary
        
        Returns:
            Prepared context dictionary
        """
        return context or {}

