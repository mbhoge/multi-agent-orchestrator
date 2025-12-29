"""AWS Lambda handlers for multi-agent orchestrator."""

from aws_agent_core.lambda_handlers.query_handler import lambda_handler as query_handler
from aws_agent_core.lambda_handlers.teams_webhook_handler import lambda_handler as teams_webhook_handler
from aws_agent_core.lambda_handlers.health_handler import lambda_handler as health_handler
from aws_agent_core.lambda_handlers.metrics_handler import lambda_handler as metrics_handler

__all__ = [
    "query_handler",
    "teams_webhook_handler",
    "health_handler",
    "metrics_handler",
]

