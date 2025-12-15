"""Entry point for AWS Agent Core API service."""

from aws_agent_core.api.main import app
import uvicorn
from shared.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
