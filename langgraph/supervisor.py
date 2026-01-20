"""Multi-agent supervisor for LangGraph."""

import logging
from typing import Dict, Any, Optional
from shared.config.settings import settings
from shared.models.request import AgentRequest
from shared.utils.exceptions import LangGraphError
from langgraph.observability.langfuse_client import LangfuseClient
from langgraph.supervisor.graph import (
    create_supervisor_graph,
    initialize_graph_globals
)

logger = logging.getLogger(__name__)


class LangGraphSupervisor:
    """Supervisor that manages multi-agent coordination using LangGraph StateGraph."""
    
    def __init__(self):
        """Initialize the supervisor."""
        self.langfuse_client = LangfuseClient(settings.langfuse)
        
        # Initialize graph globals
        initialize_graph_globals(
            client=self.langfuse_client,
            gateway_endpoint=settings.snowflake.cortex_agent_gateway_endpoint,
            timeout=settings.langgraph.langgraph_timeout
        )
        
        # Create and compile the StateGraph
        self.graph = create_supervisor_graph()
        
        logger.info("Initialized LangGraph Supervisor with StateGraph")
    
    async def process_request(
        self,
        request: AgentRequest,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process a request through the LangGraph supervisor StateGraph.
        
        Args:
            request: Agent request
            session_id: Session identifier
        
        Returns:
            Response with routing decision and results
        
        Raises:
            LangGraphError: If processing fails
        """
        try:
            logger.info(f"Processing request in LangGraph supervisor: session={session_id}")
            
            # Convert AgentRequest to initial state
            initial_state = {
                "query": request.query,
                "session_id": session_id,
                "messages": [],
                "routing_decision": None,
                "agent_responses": [],
                "final_response": None,
                "status": "processing",
                "current_step": None,
                "error": None,
                "plan": None,
                "plan_current_step": 1,
                "replan_flag": False,
                "last_reason": None,
                "replan_attempts": {},
                "enabled_agents": request.metadata.get("enabled_agents") if request.metadata else None,
                "user_query": request.query,
                "agent_query": None,
                "metadata": {
                    **(request.metadata or {}),
                    "agent_preference": request.agent_preference,
                },
                "context": request.context or {},
                "start_time": None,
                "execution_time": None,
            }
            
            # Invoke graph with thread_id for state correlation
            config = {"configurable": {"thread_id": session_id}}
            result = await self.graph.ainvoke(initial_state, config=config)
            
            # Convert result to response format
            return self._format_response(result)
            
        except Exception as e:
            logger.error(f"Error in LangGraph supervisor: {str(e)}")
            raise LangGraphError(f"Supervisor processing failed: {str(e)}") from e
    
    def _format_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Format state result into API response format.
        
        Args:
            state: Final state from graph execution
            
        Returns:
            Formatted response dictionary
        """
        routing_decision = state.get("routing_decision", {})
        agent_responses = state.get("agent_responses", [])
        final_response = state.get("final_response", "")
        
        # Extract agent names from routing decision or responses
        agent_names = []
        if routing_decision:
            agent_names = routing_decision.get("agents_to_call", [])
        elif agent_responses:
            agent_names = [r.get("agent_name") for r in agent_responses if r.get("agent_name")]
        
        # Extract sources from agent responses
        sources = []
        if agent_responses:
            for response in agent_responses:
                if isinstance(response, dict):
                    sources.extend(response.get("sources", []) or [])
        
        return {
            "response": final_response,
            "selected_agent": ",".join(agent_names) if agent_names else "",
            "routing_reason": routing_decision.get("routing_reason", "") if routing_decision else "",
            "confidence": routing_decision.get("confidence", 0.5) if routing_decision else 0.5,
            "sources": sources,
            "execution_time": state.get("execution_time"),
            "session_id": state.get("session_id"),
        }

