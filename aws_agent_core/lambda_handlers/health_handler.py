"""Lambda handler for health check endpoint."""

import logging
from typing import Dict, Any
from aws_agent_core.lambda_handlers.utils import create_api_gateway_response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for /health endpoint.
    
    Args:
        event: API Gateway Lambda event
        context: Lambda context
        
    Returns:
        API Gateway Lambda response
    """
    try:
        logger.info("Health check requested")
        
        # Handle OPTIONS request for CORS
        if event.get("httpMethod") == "OPTIONS" or event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
            return create_api_gateway_response(200, {"message": "OK"})
        
        health_status = {
            "status": "healthy",
            "service": "aws-agent-core-orchestrator",
            "runtime": "aws-lambda",
        }
        
        return create_api_gateway_response(200, health_status)
    
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}", exc_info=True)
        return create_api_gateway_response(
            500,
            {
                "status": "unhealthy",
                "error": str(e),
            },
        )

