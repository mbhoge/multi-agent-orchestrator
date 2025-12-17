"""Multi-agent supervisor for LangGraph."""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from shared.config.settings import settings
from shared.models.request import AgentRequest
from shared.models.agent_state import AgentState, RequestStatus
from shared.utils.exceptions import LangGraphError
from langgraph.state.state_manager import state_manager
from langgraph.memory.short_term import short_term_memory
from langgraph.memory.long_term import long_term_memory
from langgraph.reasoning.router import agent_router
from langgraph.observability.langfuse_client import LangfuseClient

logger = logging.getLogger(__name__)


class LangGraphSupervisor:
    """Supervisor that manages multi-agent coordination using LangGraph."""
    
    def __init__(self):
        """Initialize the supervisor."""
        self.langfuse_client = LangfuseClient(settings.langfuse)
        logger.info("Initialized LangGraph Supervisor")
    
    async def process_request(
        self,
        request: AgentRequest,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process a request through the LangGraph supervisor.
        
        Args:
            request: Agent request
            session_id: Session identifier
        
        Returns:
            Response with routing decision and results
        
        Raises:
            LangGraphError: If processing fails
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing request in LangGraph supervisor: session={session_id}")
            
            # Retrieve prior conversation history (short-term, per session)
            # Stored as a list of {role, content, ts} dicts.
            history = short_term_memory.retrieve(session_id=session_id, key="history") or []
            if not isinstance(history, list):
                history = []

            # Append the current user message to history
            history.append(
                {
                    "role": "user",
                    "content": request.query,
                    "ts": time.time(),
                }
            )

            # Initialize or retrieve state
            state = state_manager.get_state(session_id)
            if not state:
                state = state_manager.create_state(
                    query=request.query,
                    session_id=session_id,
                    initial_metadata=request.metadata
                )
            
            # Update state to processing
            state_manager.update_state(session_id, {
                "status": RequestStatus.PROCESSING,
                "current_step": "routing"
            })
            
            # Get prompt for routing decision
            routing_prompt = await self.langfuse_client.get_prompt_for_routing(
                query=request.query,
                context=request.context
            )
            
            # Route request to appropriate agent (using prompt-enhanced query)
            routing_decision = agent_router.route_request(
                query=routing_prompt,
                context=request.context,
                agent_preference=request.agent_preference
            )
            
            # Update state with routing decision
            state_manager.update_state(session_id, {
                "routing_reason": routing_decision["routing_reason"],
                "current_step": "agent_invocation"
            })
            
            # Store in short-term memory
            short_term_memory.store(
                session_id=session_id,
                key="last_query",
                value=request.query
            )
            short_term_memory.store(
                session_id=session_id,
                key="routing_decision",
                value=routing_decision,
            )

            # Persist updated history (keep a bounded window to avoid unbounded growth)
            max_history = 30  # messages
            short_term_memory.store(
                session_id=session_id,
                key="history",
                value=history[-max_history:],
            )

            # Build an enriched context sent to downstream agents
            # - Include the most recent history window
            # - Include state snapshot and memory snapshot (bounded/serializable)
            state_snapshot = None
            try:
                # AgentState is pydantic; model_dump() yields JSON-friendly dict
                state_snapshot = state.model_dump()
            except Exception:
                state_snapshot = {"session_id": session_id}

            enriched_context = {
                **(request.context or {}),
                "history": history[-max_history:],
                "langgraph": {
                    "state": state_snapshot,
                    "short_term_memory": short_term_memory.get_all(session_id=session_id),
                },
            }
            
            # Invoke one or more Snowflake Cortex Agents via gateway.
            # LangGraph acts as the orchestrator here (it does NOT decide tool_choice).
            agent_names = routing_decision.get("agents_to_call", []) or []
            if not isinstance(agent_names, list) or not agent_names:
                raise LangGraphError("No Snowflake agent objects selected for invocation.")

            agent_responses = []
            for agent_name in agent_names:
                agent_responses.append(
                    await self._invoke_snowflake_agent(
                        agent_name=agent_name,
                        query=request.query,
                        session_id=session_id,
                        context=enriched_context,
                    )
                )

            # Combine responses if multiple agents were called
            if len(agent_responses) == 1:
                agent_response = agent_responses[0]
            else:
                combined_text = "\n\n".join(
                    [
                        f"[{r.get('agent_name', 'agent')}] {r.get('response', '')}"
                        for r in agent_responses
                    ]
                ).strip()
                combined_sources = []
                for r in agent_responses:
                    combined_sources.extend(r.get("sources", []) or [])
                agent_response = {
                    "response": combined_text,
                    "sources": combined_sources,
                    "agents": [r.get("agent_name") for r in agent_responses],
                }
            
            # Append assistant response to history
            history.append(
                {
                    "role": "assistant",
                    "content": agent_response.get("response", ""),
                    "ts": time.time(),
                }
            )
            short_term_memory.store(
                session_id=session_id,
                key="history",
                value=history[-max_history:],
            )

            # Update state with response
            state_manager.update_state(session_id, {
                "status": RequestStatus.COMPLETED,
                "final_response": agent_response.get("response", ""),
                "current_step": "completed"
            })
            
            # Store in long-term memory if significant
            if routing_decision.get("confidence", 0) > 0.8:
                long_term_memory.store(
                    key=f"query_pattern_{session_id}",
                    value={
                        "query": request.query,
                        "agent": routing_decision["selected_agent"].value,
                        "success": True
                    }
                )
            
            execution_time = time.time() - start_time
            
            # Log to Langfuse
            await self.langfuse_client.log_supervisor_decision(
                session_id=session_id,
                query=request.query,
                routing_decision=routing_decision,
                execution_time=execution_time
            )
            
            return {
                "response": agent_response.get("response", ""),
                "selected_agent": ",".join(agent_names),
                "routing_reason": routing_decision["routing_reason"],
                "confidence": routing_decision.get("confidence", 0.5),
                "sources": agent_response.get("sources", []),
                "execution_time": execution_time,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in LangGraph supervisor: {str(e)}")
            
            # Update state with error
            if state_manager.get_state(session_id):
                state_manager.update_state(session_id, {
                    "status": RequestStatus.FAILED,
                    "error": str(e)
                })
            
            raise LangGraphError(f"Supervisor processing failed: {str(e)}") from e
    
    async def _invoke_snowflake_agent(
        self,
        agent_name: str,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke Snowflake Cortex AI agent via gateway.
        
        Args:
            agent_type: Type of agent to invoke
            query: User query
            session_id: Session identifier
            context: Optional context
        
        Returns:
            Response from Snowflake agent
        """
        # This would make an HTTP call to the Snowflake Cortex agent service
        # For now, return a placeholder response
        logger.info(f"Invoking Snowflake agent object {agent_name} for session {session_id}")
        
        # Make HTTP call to the Snowflake Cortex agent service
        import httpx
        try:
            async with httpx.AsyncClient(timeout=settings.langgraph.langgraph_timeout) as client:
                response = await client.post(
                    f"{settings.snowflake.cortex_agent_gateway_endpoint}/agents/invoke",
                    json={
                        "agent_name": agent_name,
                        "query": query,
                        "session_id": session_id,
                        # Backward compatible: context contains history + state snapshots
                        "context": context or {},
                        # Forward compatible: also provide dedicated history field if present
                        "history": (context or {}).get("history", []),
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to invoke Snowflake agent via gateway: {str(e)}. Using fallback response.")
            return {
                "response": f"Response from {agent_name} agent for query: {query[:50]}...",
                "sources": []
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

