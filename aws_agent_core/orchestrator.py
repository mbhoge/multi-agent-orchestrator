"""Main orchestrator that invokes the LangGraph supervisor in-process."""

import logging
import time
from typing import Any, Dict

from langgraph.supervisor import LangGraphSupervisor
from shared.models.request import AgentRequest, AgentResponse
from shared.utils.exceptions import AWSAgentCoreError

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Main orchestrator that invokes the LangGraph supervisor directly."""
    
    def __init__(self) -> None:
        """Initialize the orchestrator."""
        self.supervisor = LangGraphSupervisor()
        logger.info("Initialized Multi-Agent Orchestrator (LangGraph supervisor)")
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process a user request through the LangGraph supervisor.
        
        Args:
            request: Agent request containing user query
        
        Returns:
            Agent response with results
        
        Raises:
            AWSAgentCoreError: If orchestration fails
        """
        start_time = time.time()
        session_id = request.session_id or f"session_{int(time.time() * 1000)}"
        try:
            logger.info(f"Processing request for session {session_id}")
            langgraph_response = await self._invoke_langgraph(request, session_id)
            selected_agent = langgraph_response.get("selected_agent") or "langgraph"
            routing_reason = langgraph_response.get("routing_reason", "")
            execution_time = time.time() - start_time

            response = AgentResponse(
                response=str(langgraph_response.get("response", "")),
                session_id=session_id,
                agent_used=selected_agent,
                confidence=langgraph_response.get("confidence"),
                sources=langgraph_response.get("sources", []),
                execution_time=execution_time,
                metadata={
                    "routing_reason": routing_reason,
                    **(request.metadata or {}),
                },
            )

            logger.info(f"Request processed successfully for session {session_id}")
            return response
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise AWSAgentCoreError(f"Orchestration failed: {str(e)}") from e
    
    async def _invoke_langgraph(self, request: AgentRequest, session_id: str) -> Dict[str, Any]:
        """
        Invoke LangGraph supervisor in-process.
        
        Args:
            request: Agent request
            session_id: Session identifier
        
        Returns:
            Response from LangGraph
        """
        logger.debug(f"Invoking LangGraph for session {session_id}")
        return await self.supervisor.process_request(request=request, session_id=session_id)

