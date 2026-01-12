"""Multi-agent supervisor for LangGraph."""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
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


# FastAPI app for LangGraph supervisor
app = FastAPI(
    title="LangGraph Supervisor API",
    description="API for LangGraph multi-agent supervisor",
    version="1.0.0"
)

supervisor = LangGraphSupervisor()


@app.post("/supervisor/process")
async def process_supervisor_request(request: Dict[str, Any]):
    """
    Process a request through the LangGraph supervisor.
    
    Args:
        request: Request dictionary with query, session_id, etc.
    
    Returns:
        Supervisor response
    """
    try:
        agent_request = AgentRequest(
            query=request.get("query", ""),
            session_id=request.get("session_id"),
            context=request.get("context"),
            agent_preference=request.get("agent_preference")
        )
        
        response = await supervisor.process_request(
            request=agent_request,
            session_id=agent_request.session_id or f"session_{int(time.time() * 1000)}"
        )
        
        return response
    except Exception as e:
        logger.error(f"Error in supervisor endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "langgraph-supervisor"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "langgraph.supervisor:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

