"""AWS-specific configuration and utilities."""

import boto3
from typing import Optional
from shared.config.settings import AWSSettings


def get_boto3_session(aws_settings: AWSSettings) -> boto3.Session:
    """Create a boto3 session with the provided AWS settings."""
    session_kwargs = {
        "region_name": aws_settings.aws_region,
    }
    
    if aws_settings.aws_access_key_id:
        session_kwargs["aws_access_key_id"] = aws_settings.aws_access_key_id
    if aws_settings.aws_secret_access_key:
        session_kwargs["aws_secret_access_key"] = aws_settings.aws_secret_access_key
    if aws_settings.aws_session_token:
        session_kwargs["aws_session_token"] = aws_settings.aws_session_token
    
    return boto3.Session(**session_kwargs)


def get_bedrock_agent_core_client(aws_settings: AWSSettings):
    """Get AWS Bedrock Agent Core client."""
    session = get_boto3_session(aws_settings)
    return session.client("bedrock-agent-runtime")


def get_ecs_client(aws_settings: AWSSettings):
    """Get ECS client."""
    session = get_boto3_session(aws_settings)
    return session.client("ecs")

