"""Langfuse configuration."""

import logging
from shared.config.settings import settings

logger = logging.getLogger(__name__)


def get_langfuse_config() -> dict:
    """
    Get Langfuse configuration.
    
    Returns:
        Langfuse configuration dictionary
    """
    return {
        "host": settings.langfuse.langfuse_host,
        "public_key": settings.langfuse.langfuse_public_key,
        "secret_key": settings.langfuse.langfuse_secret_key,
        "project_id": settings.langfuse.langfuse_project_id,
    }

