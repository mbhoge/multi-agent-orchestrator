"""AWS Agent Core Runtime SDK client wrapper."""

import json
import logging
from typing import Dict, Any, Optional
from shared.config.aws_config import get_bedrock_agent_core_client
from shared.config.settings import AWSSettings
from shared.utils.exceptions import AWSAgentCoreError

logger = logging.getLogger(__name__)


class AgentCoreRuntimeClient:
    """Client for interacting with AWS Agent Core Runtime SDK."""
    
    def __init__(self, aws_settings: AWSSettings):
        """
        Initialize the Agent Core Runtime client.
        
        Args:
            aws_settings: AWS configuration settings
        """
        self.aws_settings = aws_settings
        self.client = get_bedrock_agent_core_client(aws_settings)
        logger.info("Initialized AWS Agent Core Runtime client")
    
    def invoke_agent(
        self,
        agent_id: str,
        agent_alias_id: str,
        session_id: str,
        input_text: str,
        enable_trace: bool = True
    ) -> Dict[str, Any]:
        """
        Invoke an agent using the Agent Core Runtime SDK.
        
        Args:
            agent_id: AWS Bedrock agent ID
            agent_alias_id: Agent alias ID
            session_id: Session identifier
            input_text: Input text for the agent
            enable_trace: Enable tracing for observability
        
        Returns:
            Response from the agent
        
        Raises:
            AWSAgentCoreError: If invocation fails
        """
        try:
            logger.info(
                f"Invoking agent {agent_id} with session {session_id}, "
                f"trace enabled: {enable_trace}"
            )
            
            request_params = {
                "agentId": agent_id,
                "agentAliasId": agent_alias_id,
                "sessionId": session_id,
                "inputText": input_text,
                "enableTrace": enable_trace,
            }
            
            response = self.client.invoke_agent(**request_params)
            
            # Process streaming response
            result = {
                "completion": "",
                "trace_id": None,
                "session_id": session_id,
            }
            
            for event in response.get("completion", []):
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        result["completion"] += chunk["bytes"].decode("utf-8")
                
                if "trace" in event and enable_trace:
                    trace = event["trace"]
                    if "traceId" in trace:
                        result["trace_id"] = trace["traceId"]
            
            logger.info(f"Agent invocation completed for session {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error invoking agent: {str(e)}")
            raise AWSAgentCoreError(f"Failed to invoke agent: {str(e)}") from e
    
    def get_agent_trace(
        self,
        agent_id: str,
        agent_alias_id: str,
        session_id: str,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get trace information for an agent invocation.
        
        Args:
            agent_id: AWS Bedrock agent ID
            agent_alias_id: Agent alias ID
            session_id: Session identifier
            trace_id: Optional trace ID
        
        Returns:
            Trace information
        
        Raises:
            AWSAgentCoreError: If trace retrieval fails
        """
        try:
            logger.info(f"Retrieving trace for session {session_id}, trace_id: {trace_id}")
            
            # Note: Actual API may vary based on AWS Agent Core Runtime SDK
            # This is a placeholder for trace retrieval
            request_params = {
                "agentId": agent_id,
                "agentAliasId": agent_alias_id,
                "sessionId": session_id,
            }
            
            if trace_id:
                request_params["traceId"] = trace_id
            
            # This would use the actual trace API when available
            # For now, return a placeholder structure
            return {
                "trace_id": trace_id,
                "session_id": session_id,
                "status": "completed",
            }
            
        except Exception as e:
            logger.error(f"Error retrieving trace: {str(e)}")
            raise AWSAgentCoreError(f"Failed to retrieve trace: {str(e)}") from e

