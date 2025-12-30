"""Microsoft Teams Bot adapter using Bot Framework."""

import logging
from typing import Dict, Any, Optional
from shared.models.request import AgentRequest, AgentResponse
from teams_adapter.message_transformer import TeamsMessageTransformer

logger = logging.getLogger(__name__)


class TeamsBotAdapter:
    """Adapter for Microsoft Teams Bot Framework integration."""
    
    def __init__(self, orchestrator):
        """
        Initialize Teams Bot adapter.
        
        Args:
            orchestrator: MultiAgentOrchestrator instance
        """
        self.orchestrator = orchestrator
        self.transformer = TeamsMessageTransformer()
    
    async def process_teams_activity(
        self,
        activity: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a Teams activity and return response.
        
        Args:
            activity: Microsoft Teams activity object
            
        Returns:
            Teams activity response
        """
        try:
            # Handle different activity types
            activity_type = activity.get("type")
            
            if activity_type == "message":
                return await self._handle_message(activity)
            elif activity_type == "conversationUpdate":
                return await self._handle_conversation_update(activity)
            elif activity_type == "messageReaction":
                return await self._handle_message_reaction(activity)
            else:
                logger.warning(f"Unhandled activity type: {activity_type}")
                return self._build_ack_response(activity)
        
        except Exception as e:
            logger.error(f"Error processing Teams activity: {str(e)}", exc_info=True)
            return self.transformer.build_error_response(
                str(e),
                original_activity=activity,
            )
    
    async def _handle_message(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message activity."""
        # Transform Teams message to AgentRequest
        agent_request = self.transformer.teams_to_agent_request(activity)
        
        # Validate query
        if not agent_request.query:
            return self.transformer.build_error_response(
                "Please provide a query or question.",
                original_activity=activity,
            )
        
        # Send typing indicator (async, don't wait)
        # Note: In production, you'd send this via Bot Framework SDK
        
        # Process request through orchestrator
        try:
            agent_response = await self.orchestrator.process_request(
                request=agent_request,
            )
            
            # Transform response to Teams format
            teams_response = self.transformer.agent_response_to_teams(
                response=agent_response,
                original_activity=activity,
            )
            
            return teams_response
        
        except Exception as e:
            logger.error(f"Error processing agent request: {str(e)}", exc_info=True)
            return self.transformer.build_error_response(
                f"Failed to process request: {str(e)}",
                original_activity=activity,
            )
    
    async def _handle_conversation_update(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation update (member added, etc.)."""
        members_added = activity.get("membersAdded", [])
        
        # Check if bot was added
        for member in members_added:
            if member.get("id") == activity.get("recipient", {}).get("id"):
                # Bot was added to conversation
                return {
                    "type": "message",
                    "text": "👋 Hello! I'm the Multi-Agent Orchestrator. I can help you query your data using AI agents. Just ask me a question!",
                    "conversation": activity.get("conversation", {}),
                }
        
        return self._build_ack_response(activity)
    
    async def _handle_message_reaction(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Handle message reaction activity."""
        # Acknowledge reaction but don't process
        return self._build_ack_response(activity)
    
    def _build_ack_response(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Build acknowledgment response."""
        return {
            "type": "message",
            "text": "✅",
            "conversation": activity.get("conversation", {}),
        }
    
    def call_aws_api_gateway(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call AWS API Gateway endpoint.
        
        Args:
            payload: Data to send in the request
            
        Returns:
            Response from AWS API Gateway
        """
        import requests
        
        url = "https://example.execute-api.aws-region.amazonaws.com/prod/endpoint"
        headers = {
            "Authorization": "Bearer <token>",
            "Content-Type": "application/json",
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

