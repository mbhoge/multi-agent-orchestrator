"""Application settings using Pydantic for validation."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class AWSSettings(BaseSettings):
    """AWS configuration settings."""
    
    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    aws_session_token: Optional[str] = Field(default=None, description="AWS session token")
    bedrock_agent_core_runtime_endpoint: Optional[str] = Field(
        default=None, 
        description="AWS Bedrock Agent Core Runtime endpoint"
    )
    
    class Config:
        env_prefix = "AWS_"
        case_sensitive = False


class LangGraphSettings(BaseSettings):
    """LangGraph configuration settings."""
    
    langgraph_endpoint: str = Field(
        default="http://langgraph:8001",
        description="LangGraph service endpoint"
    )
    langgraph_timeout: int = Field(default=300, description="Request timeout in seconds")
    enable_memory: bool = Field(default=True, description="Enable memory management")
    
    class Config:
        env_prefix = "LANGGRAPH_"
        case_sensitive = False


class LangfuseSettings(BaseSettings):
    """Langfuse observability settings."""
    
    langfuse_host: str = Field(
        default="http://langfuse:3000",
        description="Langfuse host URL"
    )
    langfuse_public_key: Optional[str] = Field(default=None, description="Langfuse public key")
    langfuse_secret_key: Optional[str] = Field(default=None, description="Langfuse secret key")
    langfuse_project_id: Optional[str] = Field(default=None, description="Langfuse project ID")
    
    class Config:
        env_prefix = "LANGFUSE_"
        case_sensitive = False


class SnowflakeSettings(BaseSettings):
    """Snowflake configuration settings."""
    
    snowflake_account: Optional[str] = Field(default=None, description="Snowflake account identifier")
    snowflake_user: Optional[str] = Field(default=None, description="Snowflake username")
    snowflake_password: Optional[str] = Field(default=None, description="Snowflake password")
    snowflake_warehouse: Optional[str] = Field(default=None, description="Snowflake warehouse")
    snowflake_database: Optional[str] = Field(default=None, description="Snowflake database")
    snowflake_schema: str = Field(default="PUBLIC", description="Snowflake schema")
    snowflake_role: Optional[str] = Field(default=None, description="Snowflake role")
    snowflake_api_host: Optional[str] = Field(
        default=None,
        description="Snowflake account URL, e.g. https://<account>.snowflakecomputing.com",
    )
    snowflake_auth_token: Optional[str] = Field(
        default=None,
        description="Bearer token for Snowflake REST APIs (OAuth/token-based auth)",
    )

    # Cortex Agents Run API config (agent object path form)
    cortex_agents_database: Optional[str] = Field(
        default=None,
        description="Snowflake database containing the Cortex Agent object",
    )
    cortex_agents_schema: Optional[str] = Field(
        default=None,
        description="Snowflake schema containing the Cortex Agent object",
    )
    cortex_agent_name: Optional[str] = Field(
        default=None,
        description="Cortex Agent object name to call via :run",
    )

    # Optional: multiple Snowflake agent objects (used when LangGraph orchestrates multiple agent runs)
    cortex_agent_name_analyst: Optional[str] = Field(
        default=None,
        description="Cortex Agent object name specialized for structured data (analyst)",
    )
    cortex_agent_name_search: Optional[str] = Field(
        default=None,
        description="Cortex Agent object name specialized for unstructured search",
    )
    cortex_agent_name_combined: Optional[str] = Field(
        default=None,
        description="Cortex Agent object name that can use both analyst and search tools",
    )

    # Tool names (must match the agent's configured tool identifiers)
    cortex_tool_names_analyst: str = Field(
        default="analyst_tool",
        description="Tool name for analyst tool in Cortex Agents",
    )
    cortex_tool_names_search: str = Field(
        default="search_tool",
        description="Tool name for search tool in Cortex Agents",
    )
    cortex_agent_gateway_endpoint: Optional[str] = Field(
        default="http://snowflake-cortex:8002",
        description="Snowflake Cortex AI Agent Gateway endpoint"
    )
    
    class Config:
        env_prefix = "SNOWFLAKE_"
        case_sensitive = False


class TruLensSettings(BaseSettings):
    """TruLens observability settings."""
    
    trulens_enabled: bool = Field(default=True, description="Enable TruLens observability")
    trulens_app_id: Optional[str] = Field(default=None, description="TruLens app ID")
    trulens_api_key: Optional[str] = Field(default=None, description="TruLens API key")
    
    class Config:
        env_prefix = "TRULENS_"
        case_sensitive = False


class TeamsSettings(BaseSettings):
    """Microsoft Teams Bot Framework settings."""
    
    teams_enabled: bool = Field(default=False, description="Enable Microsoft Teams integration")
    teams_app_id: Optional[str] = Field(default=None, description="Microsoft Teams app ID (Bot ID)")
    teams_app_password: Optional[str] = Field(default=None, description="Microsoft Teams app password (Bot Secret)")
    teams_tenant_id: Optional[str] = Field(default=None, description="Microsoft Teams tenant ID")
    teams_webhook_url: Optional[str] = Field(
        default=None,
        description="Teams webhook URL (for incoming webhooks, optional)"
    )
    
    class Config:
        env_prefix = "TEAMS_"
        case_sensitive = False


class AppSettings(BaseSettings):
    """Main application settings."""
    
    app_name: str = Field(default="multi-agent-orchestrator", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    aws: AWSSettings = Field(default_factory=AWSSettings)
    langgraph: LangGraphSettings = Field(default_factory=LangGraphSettings)
    langfuse: LangfuseSettings = Field(default_factory=LangfuseSettings)
    snowflake: SnowflakeSettings = Field(default_factory=SnowflakeSettings)
    trulens: TruLensSettings = Field(default_factory=TruLensSettings)
    teams: TeamsSettings = Field(default_factory=TeamsSettings)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = AppSettings()

