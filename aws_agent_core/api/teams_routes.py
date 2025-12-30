"""Microsoft Teams Bot Framework webhook routes."""

import logging
from aws_agent_core.orchestrator import MultiAgentOrchestrator
from teams_adapter.teams_bot import TeamsBotAdapter
from teams_adapter.message_transformer import TeamsMessageTransformer

logger = logging.getLogger(__name__)

# Global instances
_orchestrator: Optional[MultiAgentOrchestrator] = None
_teams_adapter: Optional[TeamsBotAdapter] = None


def get_teams_adapter() -> TeamsBotAdapter:
    """Dependency to get Teams adapter instance."""
    global _orchestrator, _teams_adapter
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator()
    if _teams_adapter is None:
        _teams_adapter = TeamsBotAdapter(_orchestrator)
    return _teams_adapter


@router.post("/webhook")
async def teams_webhook(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """
    Microsoft Teams Bot Framework webhook endpoint.
    
    This endpoint receives activities from Microsoft Teams and processes them
    through the multi-agent orchestrator.
    
    Args:
        request: FastAPI request object
        authorization: Authorization header (for Bot Framework authentication)
    
    Returns:
        Teams activity response
    """
    try:
        # Get Teams adapter
        adapter = get_teams_adapter()
        
        # Parse request body
        activity = await request.json()
        
        logger.info(f"Received Teams activity: {activity.get('type')}")
        
        # Process activity
        response = await adapter.process_teams_activity(activity)
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing Teams webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook")
async def teams_webhook_verification(
    request: Request,
):
    """
    Microsoft Teams webhook verification endpoint.
    
    Teams may send GET requests for verification during bot registration.
    This endpoint handles those verification requests.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Verification response
    """
    # Extract verification token if present
    verification_token = request.query_params.get("validationToken")
    
    if verification_token:
        # Return plain text verification token
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=verification_token)
    
    # Otherwise return health status
    return {
        "status": "ok",
        "service": "teams-webhook",
        "message": "Teams webhook endpoint is active",
    }


@router.post("/messages")
async def send_teams_message(
    request: Request,
):
    """
    Send a proactive message to Teams (for testing/admin purposes).
    
    This endpoint allows sending messages to Teams channels programmatically.
    Note: This requires Teams Bot Framework proactive messaging setup.
    
    Args:
        request: FastAPI request object with message payload
    
    Returns:
        Success response
    """
    try:
        payload = await request.json()
        
        # Extract required fields
        conversation_id = payload.get("conversation_id")
        message_text = payload.get("message")
        
        if not conversation_id or not message_text:
            raise HTTPException(
                status_code=400,
                detail="conversation_id and message are required",
            )
        
        # TODO: Implement proactive messaging using Bot Framework SDK
        # This requires Bot Framework Connector Service integration
        
        logger.info(f"Proactive message request: conversation_id={conversation_id}")
        
        return {
            "status": "accepted",
            "message": "Message queued for delivery",
            "conversation_id": conversation_id,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending proactive message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

