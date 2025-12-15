"""Main orchestrator using AWS Agent Core Runtime SDK."""

import logging
import time
from typing import Dict, Any, Optional
import httpx
from shared.config.settings import settings
from shared.models.request import AgentRequest, AgentResponse
from shared.models.agent_state import AgentState, RequestStatus
from shared.utils.exceptions import AWSAgentCoreError, LangGraphError
from aws_agent_core.runtime.sdk_client import AgentCoreRuntimeClient
from aws_agent_core.observability.tracing import tracer
from aws_agent_core.observability.metrics import metrics_collector
from langfuse.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Main orchestrator that coordinates AWS Agent Core, LangGraph, and Snowflake agents."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.runtime_client = AgentCoreRuntimeClient(settings.aws)
        self.langgraph_endpoint = settings.langgraph.langgraph_endpoint
        self.langgraph_timeout = settings.langgraph.langgraph_timeout
        self.prompt_manager = get_prompt_manager()
        logger.info("Initialized Multi-Agent Orchestrator")
    
    async def process_request(
        self,
        request: AgentRequest,
        agent_id: Optional[str] = None,
        agent_alias_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Process a user request through the orchestration pipeline.
        
        Args:
            request: Agent request containing user query
            agent_id: Optional AWS Bedrock agent ID
            agent_alias_id: Optional agent alias ID
        
        Returns:
            Agent response with results
        
        Raises:
            AWSAgentCoreError: If orchestration fails
        """
        start_time = time.time()
        session_id = request.session_id or f"session_{int(time.time() * 1000)}"
        
        with tracer.trace_operation(
            "orchestrate_request",
            metadata={"session_id": session_id, "query": request.query[:100]}
        ) as trace_context:
            try:
                logger.info(f"Processing request for session {session_id}")
                metrics_collector.increment_counter("requests.total")
                
                # Step 0: Get and apply orchestrator prompt
                orchestrator_prompt = await self._get_orchestrator_prompt(request)
                if orchestrator_prompt:
                    # Enhance request with prompt context
                    enhanced_query = orchestrator_prompt
                    request.query = enhanced_query
                    logger.debug(f"Applied orchestrator prompt for session {session_id}")
                
                # Step 1: Invoke LangGraph via AWS Agent Core Runtime SDK
                # In a real implementation, this would use the actual AWS Agent Core
                # For now, we'll call LangGraph directly via HTTP
                langgraph_response = await self._invoke_langgraph(request, session_id)
                
                # Step 2: Extract agent routing decision from LangGraph
                selected_agent = langgraph_response.get("selected_agent")
                routing_reason = langgraph_response.get("routing_reason", "")
                
                # Step 3: If AWS Agent Core agent is configured, use it
                if agent_id and agent_alias_id:
                    # Use AWS Agent Core Runtime SDK to invoke the agent
                    # This would route to LangGraph internally
                    agent_result = self.runtime_client.invoke_agent(
                        agent_id=agent_id,
                        agent_alias_id=agent_alias_id,
                        session_id=session_id,
                        input_text=request.query,
                        enable_trace=True
                    )
                    final_response = agent_result.get("completion", "")
                    trace_id = agent_result.get("trace_id")
                else:
                    # Direct LangGraph response
                    final_response = langgraph_response.get("response", "")
                    trace_id = trace_context.get("trace_id")
                
                # Step 4: Build response
                execution_time = time.time() - start_time
                response = AgentResponse(
                    response=final_response,
                    session_id=session_id,
                    agent_used=selected_agent or "langgraph",
                    confidence=langgraph_response.get("confidence"),
                    sources=langgraph_response.get("sources", []),
                    execution_time=execution_time,
                    metadata={
                        "trace_id": trace_id,
                        "routing_reason": routing_reason,
                        **request.metadata,
                    }
                )
                
                metrics_collector.record_timing("request.processing", execution_time)
                metrics_collector.increment_counter("requests.success")
                
                logger.info(f"Request processed successfully for session {session_id}")
                return response
                
            except Exception as e:
                metrics_collector.increment_counter("requests.error")
                logger.error(f"Error processing request: {str(e)}")
                raise AWSAgentCoreError(f"Orchestration failed: {str(e)}") from e
    
    async def _invoke_langgraph(
        self,
        request: AgentRequest,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Invoke LangGraph supervisor via HTTP.
        
        Args:
            request: Agent request
            session_id: Session identifier
        
        Returns:
            Response from LangGraph
        
        Raises:
            LangGraphError: If LangGraph invocation fails
        """
        try:
            logger.debug(f"Invoking LangGraph for session {session_id}")
            
            async with httpx.AsyncClient(timeout=self.langgraph_timeout) as client:
                response = await client.post(
                    f"{self.langgraph_endpoint}/supervisor/process",
                    json={
                        "query": request.query,
                        "session_id": session_id,
                        "context": request.context,
                        "agent_preference": request.agent_preference,
                    }
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error invoking LangGraph: {str(e)}")
            raise LangGraphError(f"Failed to invoke LangGraph: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error invoking LangGraph: {str(e)}")
            raise LangGraphError(f"LangGraph invocation failed: {str(e)}") from e
    
    async def _get_orchestrator_prompt(
        self,
        request: AgentRequest
    ) -> Optional[str]:
        """
        Get orchestrator prompt from Langfuse.
        
        Args:
            request: Agent request
        
        Returns:
            Rendered prompt string or None
        """
        try:
            prompt_data = await self.prompt_manager.get_prompt("orchestrator_query")
            if prompt_data:
                return self.prompt_manager.render_prompt(
                    prompt_data["prompt"],
                    {
                        "query": request.query,
                        "session_id": request.session_id or "",
                        "context": str(request.context or {})
                    }
                )
            return None
        except Exception as e:
            logger.warning(f"Error getting orchestrator prompt: {str(e)}")
            return None

