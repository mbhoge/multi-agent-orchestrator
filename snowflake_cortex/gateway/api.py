"""FastAPI application for Snowflake Cortex Agent Gateway."""

import logging
from fastapi import FastAPI, HTTPException
from typing import Dict, Any, Optional
import uvicorn
from shared.config.settings import settings
from shared.utils.logging import setup_logging
from snowflake_cortex.gateway.agent_gateway import CortexAgentGateway
from shared.models.agent_state import AgentType
from langfuse.prompt_manager import get_prompt_manager

# Setup logging
setup_logging(log_level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Snowflake Cortex AI Agent Gateway API",
    description="API for Snowflake Cortex AI Agent Gateway",
    version="1.0.0"
)

# Initialize gateway and agents
gateway = CortexAgentGateway()
prompt_manager = get_prompt_manager()


@app.post("/agents/invoke")
async def invoke_agent(request: Dict[str, Any]):
    """
    Invoke a Snowflake Cortex AI agent.
    
    Args:
        request: Request dictionary with agent_type, query, session_id, context
    
    Returns:
        Agent response
    """
    try:
        agent_name = request.get("agent_name")
        query = request.get("query", "")
        session_id = request.get("session_id", "")
        context = request.get("context", {}) or {}

        # Accept either:
        # - history embedded in context (preferred)
        # - history as a dedicated top-level field (forward compatible)
        # Merge if provided at top-level.
        history = request.get("history")
        if history is not None and "history" not in context:
            context["history"] = history
        
        # Resolve agent name from request or fall back to configured defaults.
        if not agent_name:
            agent_name = (
                settings.snowflake.cortex_agent_name_combined
                or settings.snowflake.cortex_agent_name
            )
        if not agent_name:
            raise HTTPException(
                status_code=400,
                detail="Missing agent_name and no default Snowflake agent configured (SNOWFLAKE_CORTEX_AGENT_NAME[_COMBINED]).",
            )

        # Invoke Snowflake Cortex Agent via Agents Run REST API (Snowflake decides tool_choice)
        result = await gateway.invoke_agent(
            agent_name=agent_name,
            query=query,
            session_id=session_id,
            context=context,
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "snowflake-cortex-gateway"}


@app.get("/prompts/{prompt_name}")
async def get_prompt(prompt_name: str, version: Optional[int] = None):
    """
    Get a prompt from Langfuse.
    
    Args:
        prompt_name: Name of the prompt
        version: Optional version number
    
    Returns:
        Prompt data
    """
    try:
        prompt_data = await prompt_manager.get_prompt(
            prompt_name=prompt_name,
            version=version
        )
        if not prompt_data:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")
        return prompt_data
    except Exception as e:
        logger.error(f"Error getting prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prompts")
async def create_prompt(request: Dict[str, Any]):
    """
    Create a new prompt in Langfuse.
    
    Args:
        request: Request with prompt_name, prompt, config, labels
    
    Returns:
        Created prompt data
    """
    try:
        prompt_data = await prompt_manager.create_prompt(
            prompt_name=request.get("prompt_name"),
            prompt=request.get("prompt", ""),
            config=request.get("config"),
            labels=request.get("labels")
        )
        return prompt_data
    except Exception as e:
        logger.error(f"Error creating prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "snowflake_cortex.gateway.api:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

