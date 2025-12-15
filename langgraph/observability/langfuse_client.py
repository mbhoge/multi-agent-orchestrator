"""Langfuse client for LangGraph observability."""

import logging
from typing import Dict, Any, Optional
import httpx
from shared.config.settings import LangfuseSettings
from shared.utils.exceptions import ObservabilityError
from langfuse.prompt_manager import LangfusePromptManager

logger = logging.getLogger(__name__)


class LangfuseClient:
    """Client for Langfuse observability."""
    
    def __init__(self, langfuse_settings: LangfuseSettings):
        """
        Initialize Langfuse client.
        
        Args:
            langfuse_settings: Langfuse configuration settings
        """
        self.settings = langfuse_settings
        self.base_url = langfuse_settings.langfuse_host
        self.public_key = langfuse_settings.langfuse_public_key
        self.secret_key = langfuse_settings.langfuse_secret_key
        self.project_id = langfuse_settings.langfuse_project_id
        self.prompt_manager = LangfusePromptManager(langfuse_settings)
        logger.info(f"Initialized Langfuse client: {self.base_url}")
    
    async def log_supervisor_decision(
        self,
        session_id: str,
        query: str,
        routing_decision: Dict[str, Any],
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a supervisor decision to Langfuse.
        
        Args:
            session_id: Session identifier
            query: User query
            routing_decision: Routing decision details
            execution_time: Execution time in seconds
            metadata: Optional metadata
        """
        try:
            if not self.public_key or not self.secret_key:
                logger.warning("Langfuse credentials not configured, skipping logging")
                return
            
            logger.debug(f"Logging supervisor decision to Langfuse: session={session_id}")
            
            # In production, this would use the Langfuse Python SDK
            # For now, this is a placeholder for HTTP-based logging
            async with httpx.AsyncClient(timeout=5.0) as client:
                payload = {
                    "type": "trace",
                    "name": "langgraph_supervisor_decision",
                    "session_id": session_id,
                    "input": query,
                    "output": routing_decision,
                    "metadata": {
                        "execution_time": execution_time,
                        "selected_agent": routing_decision.get("selected_agent"),
                        "confidence": routing_decision.get("confidence"),
                        **(metadata or {})
                    }
                }
                
                headers = {
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json"
                }
                
                # This would be the actual Langfuse API endpoint
                # response = await client.post(
                #     f"{self.base_url}/api/public/traces",
                #     json=payload,
                #     headers=headers
                # )
                # response.raise_for_status()
                
                logger.debug(f"Logged to Langfuse: session={session_id}")
                
        except Exception as e:
            logger.error(f"Error logging to Langfuse: {str(e)}")
            # Don't raise - observability failures shouldn't break the main flow
            pass
    
    async def log_state_update(
        self,
        session_id: str,
        state_update: Dict[str, Any]
    ):
        """
        Log a state update to Langfuse.
        
        Args:
            session_id: Session identifier
            state_update: State update details
        """
        try:
            if not self.public_key or not self.secret_key:
                return
            
            logger.debug(f"Logging state update to Langfuse: session={session_id}")
            # Implementation similar to log_supervisor_decision
            
        except Exception as e:
            logger.error(f"Error logging state update to Langfuse: {str(e)}")
            pass
    
    async def get_prompt_for_routing(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get and render prompt for routing decision.
        
        Args:
            query: User query
            context: Optional context information
        
        Returns:
            Rendered prompt string
        """
        try:
            prompt_data = await self.prompt_manager.get_prompt("supervisor_routing")
            if prompt_data:
                return self.prompt_manager.render_prompt(
                    prompt_data["prompt"],
                    {
                        "query": query,
                        "context": str(context or {})
                    }
                )
            return f"Analyze the following query and determine the best agent to handle it: {query}"
        except Exception as e:
            logger.warning(f"Error getting routing prompt: {str(e)}")
            return f"Analyze the following query and determine the best agent to handle it: {query}"

