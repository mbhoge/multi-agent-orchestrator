"""AWS Agent Core orchestrator module.

This package provides the main orchestrator for coordinating multi-agent operations
using AWS Agent Core Runtime SDK, LangGraph, and Snowflake Cortex AI agents.
"""

from aws_agent_core.orchestrator import MultiAgentOrchestrator
from aws_agent_core.runtime.sdk_client import AgentCoreRuntimeClient
from aws_agent_core.observability.metrics import metrics_collector
from aws_agent_core.observability.tracing import tracer

__version__ = "1.0.0"

__all__ = [
    "MultiAgentOrchestrator",
    "AgentCoreRuntimeClient",
    "metrics_collector",
    "tracer",
]
