"""Utility functions for Lambda handlers."""

import json
import logging
from typing import Dict, Any, Optional
from aws_agent_core.orchestrator import MultiAgentOrchestrator
from shared.models.request import AgentRequest

logger = logging.getLogger(__name__)

# Global orchestrator instance (reused across Lambda invocations)
_orchestrator: Optional[MultiAgentOrchestrator] = None


def get_orchestrator() -> MultiAgentOrchestrator:
    """Get or create orchestrator instance (reused across invocations)."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator()
    return _orchestrator


def parse_api_gateway_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse API Gateway event and extract request data.
    
    Args:
        event: API Gateway Lambda event
        
    Returns:
        Parsed request data
    """
    # Extract HTTP method
    http_method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method", "GET"))
    
    # Extract path
    path = event.get("path", event.get("requestContext", {}).get("http", {}).get("path", "/"))
    
    # Extract query parameters
    query_params = event.get("queryStringParameters") or {}
    
    # Extract path parameters
    path_params = event.get("pathParameters") or {}
    
    # Extract headers
    headers = event.get("headers") or {}
    # Normalize headers (API Gateway lowercases them)
    normalized_headers = {k.lower(): v for k, v in headers.items()}
    
    # Extract body
    body = event.get("body", "")
    body_data = {}
    if body:
        try:
            if isinstance(body, str):
                body_data = json.loads(body)
            else:
                body_data = body
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse body as JSON: {body}")
            body_data = {"raw": body}
    
    return {
        "http_method": http_method,
        "path": path,
        "query_params": query_params,
        "path_params": path_params,
        "headers": normalized_headers,
        "body": body_data,
        "raw_body": body,
    }


def create_api_gateway_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Create API Gateway Lambda response.
    
    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Optional response headers
        
    Returns:
        API Gateway Lambda response format
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }
    
    if headers:
        default_headers.update(headers)
    
    # Serialize body if it's not a string
    if isinstance(body, (dict, list)):
        body_str = json.dumps(body)
    else:
        body_str = str(body)
    
    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": body_str,
    }


def create_error_response(
    status_code: int,
    error_message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create error response for API Gateway.
    
    Args:
        status_code: HTTP status code
        error_message: Error message
        error_code: Optional error code
        details: Optional error details
        
    Returns:
        API Gateway error response
    """
    error_body = {
        "error": error_message,
        "error_code": error_code,
        "details": details or {},
    }
    
    return create_api_gateway_response(status_code, error_body)


def extract_agent_request_from_event(event: Dict[str, Any]) -> AgentRequest:
    """
    Extract AgentRequest from API Gateway event.
    
    Args:
        event: API Gateway Lambda event
        
    Returns:
        AgentRequest object
        
    Raises:
        ValueError: If request is invalid
    """
    parsed = parse_api_gateway_event(event)
    body = parsed["body"]
    
    # Extract required fields
    query = body.get("query")
    if not query:
        raise ValueError("Missing required field: query")
    
    # Extract optional fields
    session_id = body.get("session_id")
    context = body.get("context", {})
    agent_preference = body.get("agent_preference")
    metadata = body.get("metadata", {})
    
    return AgentRequest(
        query=query,
        session_id=session_id,
        context=context,
        agent_preference=agent_preference,
        metadata=metadata,
    )

