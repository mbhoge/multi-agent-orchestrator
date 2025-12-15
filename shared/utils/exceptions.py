"""Custom exceptions for the multi-agent orchestrator."""


class MultiAgentOrchestratorError(Exception):
    """Base exception for multi-agent orchestrator errors."""
    pass


class AWSAgentCoreError(MultiAgentOrchestratorError):
    """Exception raised for AWS Agent Core related errors."""
    pass


class LangGraphError(MultiAgentOrchestratorError):
    """Exception raised for LangGraph related errors."""
    pass


class SnowflakeCortexError(MultiAgentOrchestratorError):
    """Exception raised for Snowflake Cortex AI related errors."""
    pass


class AgentRoutingError(MultiAgentOrchestratorError):
    """Exception raised when agent routing fails."""
    pass


class MemoryError(MultiAgentOrchestratorError):
    """Exception raised for memory management errors."""
    pass


class ObservabilityError(MultiAgentOrchestratorError):
    """Exception raised for observability related errors."""
    pass


class ConfigurationError(MultiAgentOrchestratorError):
    """Exception raised for configuration errors."""
    pass

