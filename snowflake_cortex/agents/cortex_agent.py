"""Cortex AI agent implementation."""

import logging
from typing import Dict, Any, Optional
from shared.models.agent_state import AgentType
from shared.utils.exceptions import SnowflakeCortexError
from snowflake_cortex.agents.base_agent import BaseCortexAgent
from snowflake_cortex.tools.analyst import CortexAnalyst
from snowflake_cortex.tools.search import CortexSearch
from snowflake_cortex.observability.trulens_client import TruLensClient
from shared.config.settings import settings
from langfuse.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)


class CortexAgent(BaseCortexAgent):
    """Cortex AI agent that can use Analyst and Search tools."""
    
    def __init__(self, agent_type: AgentType):
        """
        Initialize the Cortex agent.
        
        Args:
            agent_type: Type of agent
        """
        super().__init__(agent_type)
        self.analyst = CortexAnalyst()
        self.search = CortexSearch()
        self.trulens_client = TruLensClient(settings.trulens)
        self.prompt_manager = get_prompt_manager()
        logger.info(f"Initialized Cortex agent with tools: {agent_type.value}")
    
    async def process_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query using appropriate tools.
        
        Args:
            query: User query
            session_id: Session identifier
            context: Optional context information
        
        Returns:
            Response dictionary with results
        
        Raises:
            SnowflakeCortexError: If processing fails
        """
        if not self.validate_query(query):
            raise SnowflakeCortexError("Invalid query provided")
        
        try:
            logger.info(f"Processing query with {self.agent_type.value} agent: session={session_id}")
            
            prepared_context = self.prepare_context(context)
            
            # Get and apply agent-specific prompt
            enhanced_query = await self._get_agent_prompt(query, prepared_context)
            
            # Route to appropriate tool based on agent type
            if self.agent_type == AgentType.CORTEX_ANALYST:
                result = await self.analyst.analyze_query(
                    query=enhanced_query,
                    session_id=session_id,
                    context=prepared_context
                )
            elif self.agent_type == AgentType.CORTEX_SEARCH:
                result = await self.search.search_query(
                    query=enhanced_query,
                    session_id=session_id,
                    context=prepared_context
                )
            elif self.agent_type == AgentType.CORTEX_COMBINED:
                # Use both tools and combine results
                analyst_result = await self.analyst.analyze_query(
                    query=enhanced_query,
                    session_id=session_id,
                    context=prepared_context
                )
                search_result = await self.search.search_query(
                    query=enhanced_query,
                    session_id=session_id,
                    context=prepared_context
                )
                
                result = {
                    "response": self._combine_results(analyst_result, search_result),
                    "sources": analyst_result.get("sources", []) + search_result.get("sources", []),
                    "agent_type": "combined"
                }
            else:
                raise SnowflakeCortexError(f"Unknown agent type: {self.agent_type}")
            
            # Log to TruLens
            await self.trulens_client.log_agent_execution(
                session_id=session_id,
                agent_type=self.agent_type.value,
                query=query,
                result=result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise SnowflakeCortexError(f"Query processing failed: {str(e)}") from e
    
    def _combine_results(
        self,
        analyst_result: Dict[str, Any],
        search_result: Dict[str, Any]
    ) -> str:
        """
        Combine results from analyst and search tools.
        
        Args:
            analyst_result: Result from analyst tool
            search_result: Result from search tool
        
        Returns:
            Combined response string
        """
        analyst_response = analyst_result.get("response", "")
        search_response = search_result.get("response", "")
        
        combined = f"Structured Data Analysis:\n{analyst_response}\n\n"
        combined += f"Unstructured Data Search:\n{search_response}"
        
        return combined
    
    async def _get_agent_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Get and render agent-specific prompt from Langfuse.
        
        Args:
            query: Original query
            context: Context information
        
        Returns:
            Enhanced query with prompt
        """
        try:
            prompt_name = f"snowflake_{self.agent_type.value}"
            prompt_data = await self.prompt_manager.get_prompt(prompt_name)
            
            if prompt_data:
                return self.prompt_manager.render_prompt(
                    prompt_data["prompt"],
                    {
                        "query": query,
                        "context": str(context),
                        "agent_type": self.agent_type.value
                    }
                )
            
            # Fallback to default prompt
            return query
            
        except Exception as e:
            logger.warning(f"Error getting agent prompt: {str(e)}")
            return query

