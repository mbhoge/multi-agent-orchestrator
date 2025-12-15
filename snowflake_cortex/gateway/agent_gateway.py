"""Snowflake Cortex AI Agent Gateway client."""

import logging
from typing import Dict, Any, Optional
import httpx
from shared.config.settings import settings
from shared.models.agent_state import AgentType
from shared.utils.exceptions import SnowflakeCortexError

logger = logging.getLogger(__name__)


class CortexAgentGateway:
    """Client for Snowflake Cortex AI Agent Gateway."""
    
    def __init__(self):
        """Initialize the agent gateway client."""
        self.endpoint = settings.snowflake.cortex_agent_gateway_endpoint
        self.snowflake_config = settings.snowflake
        logger.info(f"Initialized Cortex Agent Gateway: {self.endpoint}")
    
    async def invoke_agent(
        self,
        agent_type: AgentType,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke a Snowflake Cortex AI agent via the gateway.
        
        Args:
            agent_type: Type of agent to invoke
            query: User query
            session_id: Session identifier
            context: Optional context information
        
        Returns:
            Response from the agent
        
        Raises:
            SnowflakeCortexError: If invocation fails
        """
        try:
            logger.info(f"Invoking Cortex agent {agent_type.value} via gateway: session={session_id}")
            
            # In production, this would use the Snowflake Cortex AI Agent Gateway API
            # For now, this is a placeholder that would route to the appropriate agent
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "agent_type": agent_type.value,
                    "query": query,
                    "session_id": session_id,
                    "context": context or {}
                }
                
                # This would be the actual gateway endpoint
                # response = await client.post(
                #     f"{self.endpoint}/agents/invoke",
                #     json=payload,
                #     headers=self._get_auth_headers()
                # )
                # response.raise_for_status()
                # return response.json()
                
                # Placeholder response
                return {
                    "response": f"Response from {agent_type.value} agent for: {query[:50]}...",
                    "sources": [],
                    "agent_type": agent_type.value
                }
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error invoking Cortex agent: {str(e)}")
            raise SnowflakeCortexError(f"Failed to invoke Cortex agent: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error invoking Cortex agent: {str(e)}")
            raise SnowflakeCortexError(f"Cortex agent invocation failed: {str(e)}") from e
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Snowflake API."""
        # In production, this would generate proper Snowflake authentication
        return {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {snowflake_token}",
        }


# Global gateway instance
agent_gateway = CortexAgentGateway()

