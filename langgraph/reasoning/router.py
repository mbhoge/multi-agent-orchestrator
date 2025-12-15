"""Request routing logic to Snowflake agents."""

import logging
from typing import Dict, Any, Optional
from shared.models.agent_state import AgentType
from shared.utils.exceptions import AgentRoutingError

logger = logging.getLogger(__name__)


class AgentRouter:
    """Routes requests to appropriate Snowflake Cortex AI agents."""
    
    def __init__(self):
        """Initialize the agent router."""
        # Keywords for routing decisions
        self.analyst_keywords = [
            "query", "sql", "table", "data", "database", "analyze",
            "report", "statistics", "aggregate", "sum", "count", "average"
        ]
        self.search_keywords = [
            "search", "find", "document", "pdf", "ppt", "presentation",
            "file", "content", "text", "unstructured"
        ]
        logger.info("Initialized Agent Router")
    
    def route_request(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        agent_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route a request to the appropriate agent.
        
        Args:
            query: User query
            context: Optional context information
            agent_preference: Optional preferred agent
        
        Returns:
            Routing decision with selected agent and reason
        
        Raises:
            AgentRoutingError: If routing fails
        """
        try:
            query_lower = query.lower()
            
            # Check for explicit agent preference
            if agent_preference:
                agent_type = self._parse_agent_preference(agent_preference)
                if agent_type:
                    return {
                        "selected_agent": agent_type,
                        "routing_reason": f"Explicit agent preference: {agent_preference}",
                        "confidence": 1.0
                    }
            
            # Analyze query for routing
            analyst_score = self._score_analyst_query(query_lower)
            search_score = self._score_search_query(query_lower)
            
            # Check context for hints
            if context:
                if context.get("data_type") == "structured":
                    analyst_score += 0.5
                elif context.get("data_type") == "unstructured":
                    search_score += 0.5
            
            # Make routing decision
            if analyst_score > search_score and analyst_score > 0.3:
                selected_agent = AgentType.CORTEX_ANALYST
                reason = f"Query appears to be for structured data analysis (score: {analyst_score:.2f})"
                confidence = min(analyst_score, 1.0)
            elif search_score > analyst_score and search_score > 0.3:
                selected_agent = AgentType.CORTEX_SEARCH
                reason = f"Query appears to be for unstructured data search (score: {search_score:.2f})"
                confidence = min(search_score, 1.0)
            else:
                # Default to combined agent for ambiguous queries
                selected_agent = AgentType.CORTEX_COMBINED
                reason = "Query is ambiguous, using combined agent"
                confidence = 0.5
            
            logger.info(f"Routed request to {selected_agent.value}: {reason}")
            
            return {
                "selected_agent": selected_agent,
                "routing_reason": reason,
                "confidence": confidence,
                "scores": {
                    "analyst": analyst_score,
                    "search": search_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error routing request: {str(e)}")
            raise AgentRoutingError(f"Failed to route request: {str(e)}") from e
    
    def _score_analyst_query(self, query: str) -> float:
        """Score how well a query matches analyst agent."""
        score = 0.0
        matches = sum(1 for keyword in self.analyst_keywords if keyword in query)
        score = matches / len(self.analyst_keywords) * 2.0  # Normalize
        return min(score, 1.0)
    
    def _score_search_query(self, query: str) -> float:
        """Score how well a query matches search agent."""
        score = 0.0
        matches = sum(1 for keyword in self.search_keywords if keyword in query)
        score = matches / len(self.search_keywords) * 2.0  # Normalize
        return min(score, 1.0)
    
    def _parse_agent_preference(self, preference: str) -> Optional[AgentType]:
        """Parse agent preference string to AgentType."""
        preference_lower = preference.lower()
        if "analyst" in preference_lower:
            return AgentType.CORTEX_ANALYST
        elif "search" in preference_lower:
            return AgentType.CORTEX_SEARCH
        elif "combined" in preference_lower:
            return AgentType.CORTEX_COMBINED
        return None


# Global router instance
agent_router = AgentRouter()

