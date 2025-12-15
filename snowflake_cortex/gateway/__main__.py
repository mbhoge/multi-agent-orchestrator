"""Entry point for Snowflake Cortex Agent Gateway service."""

from snowflake_cortex.gateway.api import app
import uvicorn
from shared.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
