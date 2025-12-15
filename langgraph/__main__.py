"""Entry point for LangGraph Supervisor service."""

from langgraph.supervisor import app
import uvicorn
from shared.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
