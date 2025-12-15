"""FastAPI application for Snowflake Cortex Agent Gateway."""

import logging
from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import uvicorn
from shared.config.settings import settings
from shared.utils.logging import setup_logging
from snowflake_cortex.gateway.agent_gateway import CortexAgentGateway
from snowflake_cortex.agents.cortex_agent import CortexAgent
from shared.models.agent_state import AgentType

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
agents = {
    AgentType.CORTEX_ANALYST: CortexAgent(AgentType.CORTEX_ANALYST),
    AgentType.CORTEX_SEARCH: CortexAgent(AgentType.CORTEX_SEARCH),
    AgentType.CORTEX_COMBINED: CortexAgent(AgentType.CORTEX_COMBINED),
}


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
        agent_type_str = request.get("agent_type", "cortex_combined")
        query = request.get("query", "")
        session_id = request.get("session_id", "")
        context = request.get("context", {})
        
        # Convert string to AgentType
        agent_type = AgentType(agent_type_str)
        
        # Get agent and process query
        agent = agents.get(agent_type)
        if not agent:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type_str}")
        
        result = await agent.process_query(
            query=query,
            session_id=session_id,
            context=context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error invoking agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "snowflake-cortex-gateway"}


if __name__ == "__main__":
    uvicorn.run(
        "snowflake_cortex.gateway.api:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

