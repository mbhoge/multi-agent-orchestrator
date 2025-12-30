"""API route handlers."""

import logging
from shared.models.request import AgentRequest, AgentResponse, ErrorResponse
from aws_agent_core.orchestrator import MultiAgentOrchestrator

logger = logging.getLogger(__name__)

# Global orchestrator instance
_orchestrator: Optional[MultiAgentOrchestrator] = None


def get_orchestrator() -> MultiAgentOrchestrator:
    """Dependency to get orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator()
    return _orchestrator


async def process_query(
    request: AgentRequest,
    orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator),
    agent_id: Optional[str] = None,
    agent_alias_id: Optional[str] = None
):
    """
    Process a user query through the multi-agent orchestrator.
    
    Args:
        request: Agent request with user query
        orchestrator: Orchestrator instance
        agent_id: Optional AWS Bedrock agent ID
        agent_alias_id: Optional agent alias ID
    
    Returns:
        Agent response with results
    
    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Received query request: {request.query[:100]}")
        response = await orchestrator.process_request(
            request=request,
            agent_id=agent_id,
            agent_alias_id=agent_alias_id
        )
        return response
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "aws-agent-core-orchestrator"
    }


async def get_metrics(orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator)):
    """
    Get metrics from the orchestrator.
    
    Args:
        orchestrator: Orchestrator instance
    
    Returns:
        Metrics data
    """
    from aws_agent_core.observability.metrics import metrics_collector
    return metrics_collector.get_all_metrics()

