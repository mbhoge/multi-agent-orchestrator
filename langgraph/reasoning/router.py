"""Request routing logic to Snowflake Cortex Agent objects.

This router selects WHICH Snowflake agent object(s) to invoke.
It does NOT decide tool_choice (Snowflake agent orchestration decides tools).
"""

import logging
from typing import Dict, Any, Optional
from shared.utils.exceptions import AgentRoutingError
from shared.config.settings import settings

logger = logging.getLogger(__name__)


class AgentRouter:
    """Routes requests to appropriate Snowflake Cortex Agent objects."""
    
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
            Routing decision with agents_to_call (list of agent names) and reason
        
        Raises:
            AgentRoutingError: If routing fails
        """
        try:
            query_lower = query.lower()
            
            # Resolve configured Snowflake agent object names
            analyst_agent = settings.snowflake.cortex_agent_name_analyst
            search_agent = settings.snowflake.cortex_agent_name_search
            combined_agent = settings.snowflake.cortex_agent_name_combined or settings.snowflake.cortex_agent_name

            if not combined_agent and not analyst_agent and not search_agent:
                raise AgentRoutingError(
                    "No Snowflake agent objects configured. Set SNOWFLAKE_CORTEX_AGENT_NAME[_COMBINED] "
                    "or SNOWFLAKE_CORTEX_AGENT_NAME_ANALYST/SEARCH."
                )

            # Check for explicit agent preference (expects an agent name or keywords)
            if agent_preference:
                pref = agent_preference.strip()
                if pref in (analyst_agent, search_agent, combined_agent):
                    return {
                        "agents_to_call": [pref],
                        "routing_reason": f"Explicit agent preference (agent object): {pref}",
                        "confidence": 1.0,
                    }
                # keyword-based preference fallback
                if "analyst" in pref.lower() and analyst_agent:
                    return {
                        "agents_to_call": [analyst_agent],
                        "routing_reason": "Explicit agent preference: analyst",
                        "confidence": 1.0,
                    }
                if "search" in pref.lower() and search_agent:
                    return {
                        "agents_to_call": [search_agent],
                        "routing_reason": "Explicit agent preference: search",
                        "confidence": 1.0,
                    }
                if "combined" in pref.lower() and combined_agent:
                    return {
                        "agents_to_call": [combined_agent],
                        "routing_reason": "Explicit agent preference: combined",
                        "confidence": 1.0,
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
            
            # Decide which Snowflake agent object(s) to call.
            # - If a combined agent object exists, prefer it for ambiguous queries.
            # - Otherwise call multiple specialized agents.
            agents_to_call = []
            if analyst_score > search_score and analyst_score > 0.3 and analyst_agent:
                agents_to_call = [analyst_agent]
                reason = f"Structured intent detected; calling analyst agent (score: {analyst_score:.2f})"
                confidence = min(analyst_score, 1.0)
            elif search_score > analyst_score and search_score > 0.3 and search_agent:
                agents_to_call = [search_agent]
                reason = f"Unstructured intent detected; calling search agent (score: {search_score:.2f})"
                confidence = min(search_score, 1.0)
            else:
                # Ambiguous: call combined if available; else call both available agents.
                if combined_agent:
                    agents_to_call = [combined_agent]
                    reason = "Ambiguous intent; calling combined agent"
                    confidence = 0.5
                else:
                    if analyst_agent:
                        agents_to_call.append(analyst_agent)
                    if search_agent:
                        agents_to_call.append(search_agent)
                    reason = "Ambiguous intent; calling multiple agents"
                    confidence = 0.5
            
            logger.info(f"Routed request to agents={agents_to_call}: {reason}")
            
            return {
                "agents_to_call": agents_to_call,
                "routing_reason": reason,
                "confidence": confidence,
                "scores": {"analyst": analyst_score, "search": search_score},
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
    
# Global router instance
agent_router = AgentRouter()

