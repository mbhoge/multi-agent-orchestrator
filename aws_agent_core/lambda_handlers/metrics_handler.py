"""Lambda handler for metrics endpoint."""

import logging
from typing import Dict, Any
from aws_agent_core.lambda_handlers.utils import (
    get_orchestrator,
    create_api_gateway_response,
    create_error_response,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for /metrics endpoint.
    
    Args:
        event: API Gateway Lambda event
        context: Lambda context
        
    Returns:
        API Gateway Lambda response
    """
    try:
        logger.info("Metrics requested")
        
        # Handle OPTIONS request for CORS
        if event.get("httpMethod") == "OPTIONS" or event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
            return create_api_gateway_response(200, {"message": "OK"})
        
        # Get orchestrator instance
        orchestrator = get_orchestrator()
        
        # Get metrics
        from aws_agent_core.observability.metrics import metrics_collector
        metrics = metrics_collector.get_all_metrics()
        
        return create_api_gateway_response(200, metrics)
    
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}", exc_info=True)
        return create_error_response(
            500,
            f"Failed to retrieve metrics: {str(e)}",
            "METRICS_ERROR",
        )

