"""Lambda handler for query processing endpoint."""

import json
import logging
from typing import Dict, Any
from aws_agent_core.lambda_handlers.utils import (
    get_orchestrator,
    extract_agent_request_from_event,
    create_api_gateway_response,
    create_error_response,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for /api/v1/query endpoint.
    
    Args:
        event: API Gateway Lambda event
        context: Lambda context
        
    Returns:
        API Gateway Lambda response
    """
    try:
        logger.info(f"Received query request: {event.get('path', 'unknown')}")
        
        # Handle OPTIONS request for CORS
        if event.get("httpMethod") == "OPTIONS" or event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
            return create_api_gateway_response(200, {"message": "OK"})
        
        # Extract AgentRequest from event
        try:
            agent_request = extract_agent_request_from_event(event)
        except ValueError as e:
            logger.error(f"Invalid request: {str(e)}")
            return create_error_response(400, str(e), "INVALID_REQUEST")
        
        # Get orchestrator instance
        orchestrator = get_orchestrator()
        
        # Extract optional agent parameters from query string
        query_params = event.get("queryStringParameters") or {}
        agent_id = query_params.get("agent_id")
        agent_alias_id = query_params.get("agent_alias_id")
        
        # Process request
        import asyncio
        response = asyncio.run(
            orchestrator.process_request(
                request=agent_request,
                agent_id=agent_id,
                agent_alias_id=agent_alias_id,
            )
        )
        
        # Convert response to dict
        if hasattr(response, "dict"):
            response_dict = response.dict()
        elif hasattr(response, "model_dump"):
            response_dict = response.model_dump()
        else:
            response_dict = {
                "response": response.response,
                "session_id": response.session_id,
                "agent_used": response.agent_used,
                "confidence": response.confidence,
                "sources": response.sources,
                "execution_time": response.execution_time,
                "metadata": response.metadata,
            }
        
        logger.info(f"Query processed successfully: session_id={response.session_id}")
        
        return create_api_gateway_response(200, response_dict)
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return create_error_response(
            500,
            f"Internal server error: {str(e)}",
            "INTERNAL_ERROR",
            {"error_type": type(e).__name__},
        )

