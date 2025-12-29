"""Lambda handler for Microsoft Teams outgoing webhook."""

import json
import hmac
import hashlib
import base64
import logging
from typing import Dict, Any, Optional
from aws_agent_core.lambda_handlers.utils import (
    get_orchestrator,
    parse_api_gateway_event,
    create_api_gateway_response,
    create_error_response,
)
from shared.config.settings import settings
from teams_adapter.message_transformer import TeamsMessageTransformer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Teams message transformer
_transformer = TeamsMessageTransformer()


def verify_teams_webhook_signature(
    body: str,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify Teams outgoing webhook HMAC signature.
    
    Args:
        body: Request body as string
        signature: HMAC signature from Teams
        secret: Shared secret configured in Teams
        
    Returns:
        True if signature is valid
    """
    try:
        # Teams uses HMAC SHA256
        expected_signature = base64.b64encode(
            hmac.new(
                secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")
        
        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(signature, expected_signature)
    
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}")
        return False


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for Teams outgoing webhook endpoint.
    
    This handler processes Microsoft Teams outgoing webhook requests.
    Teams sends POST requests when users @mention the webhook in a channel.
    
    Args:
        event: API Gateway Lambda event
        context: Lambda context
        
    Returns:
        API Gateway Lambda response (text/plain for Teams)
    """
    try:
        logger.info("Received Teams webhook request")
        
        # Handle OPTIONS request for CORS
        if event.get("httpMethod") == "OPTIONS" or event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
            return create_api_gateway_response(200, {"message": "OK"})
        
        # Parse event
        parsed = parse_api_gateway_event(event)
        headers = parsed["headers"]
        body_str = parsed["raw_body"]
        
        # Verify HMAC signature if secret is configured
        webhook_secret = settings.teams.teams_app_password  # Reuse app password or add separate secret
        if webhook_secret:
            signature = headers.get("authorization", "").replace("Bearer ", "")
            if not signature:
                # Try alternative header name
                signature = headers.get("x-teams-signature", "")
            
            if signature:
                if not verify_teams_webhook_signature(body_str, signature, webhook_secret):
                    logger.warning("Invalid Teams webhook signature")
                    return create_error_response(401, "Invalid signature", "UNAUTHORIZED")
            else:
                logger.warning("Missing Teams webhook signature")
        
        # Parse Teams webhook payload
        try:
            if isinstance(body_str, str):
                webhook_data = json.loads(body_str)
            else:
                webhook_data = body_str
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook body: {str(e)}")
            return create_error_response(400, "Invalid JSON payload", "INVALID_PAYLOAD")
        
        # Extract message text from Teams webhook
        # Teams outgoing webhook format: {"text": "user message", "from": {...}, "channel": {...}}
        message_text = webhook_data.get("text", "").strip()
        
        if not message_text:
            # Return empty response (Teams will show nothing)
            return create_api_gateway_response(
                200,
                {"text": "Please provide a query or question."},
                headers={"Content-Type": "application/json"},
            )
        
        # Transform Teams webhook to AgentRequest
        try:
            # Build context from Teams webhook data
            context_data = {
                "source": "microsoft_teams_webhook",
                "channel_id": webhook_data.get("channel", {}).get("id"),
                "channel_name": webhook_data.get("channel", {}).get("name"),
                "user_id": webhook_data.get("from", {}).get("id"),
                "user_name": webhook_data.get("from", {}).get("name"),
                "tenant_id": webhook_data.get("tenant", {}).get("id"),
            }
            
            # Create session ID from Teams context
            session_id = f"teams_webhook_{context_data.get('channel_id', 'unknown')}_{context_data.get('user_id', 'unknown')}"
            
            from shared.models.request import AgentRequest
            agent_request = AgentRequest(
                query=message_text,
                session_id=session_id,
                context=context_data,
                agent_preference=None,
                metadata={
                    "teams_webhook": True,
                    "webhook_data": webhook_data,
                },
            )
        except Exception as e:
            logger.error(f"Error creating AgentRequest: {str(e)}")
            return create_error_response(400, f"Invalid request format: {str(e)}", "INVALID_REQUEST")
        
        # Process request through orchestrator
        try:
            orchestrator = get_orchestrator()
            import asyncio
            agent_response = asyncio.run(orchestrator.process_request(request=agent_request))
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            # Return error message to Teams
            return create_api_gateway_response(
                200,
                {
                    "text": f"❌ Error processing your request: {str(e)}",
                },
                headers={"Content-Type": "application/json"},
            )
        
        # Format response for Teams
        # Teams outgoing webhooks expect simple text or JSON with "text" field
        # For richer responses, we can return Adaptive Card JSON
        response_text = agent_response.response
        
        # Add metadata if available
        if agent_response.confidence is not None:
            response_text += f"\n\n_Confidence: {agent_response.confidence * 100:.1f}%_"
        
        if agent_response.sources:
            response_text += f"\n\n_Sources: {len(agent_response.sources)}_"
        
        # Teams outgoing webhook response format
        teams_response = {
            "text": response_text,
        }
        
        # Optionally include Adaptive Card for richer formatting
        # Note: Teams outgoing webhooks have limited card support
        # For full Adaptive Cards, use Bot Framework instead
        
        logger.info(f"Teams webhook processed successfully: session_id={agent_response.session_id}")
        
        return create_api_gateway_response(
            200,
            teams_response,
            headers={"Content-Type": "application/json"},
        )
    
    except Exception as e:
        logger.error(f"Error processing Teams webhook: {str(e)}", exc_info=True)
        return create_error_response(
            500,
            f"Internal server error: {str(e)}",
            "INTERNAL_ERROR",
            {"error_type": type(e).__name__},
        )

