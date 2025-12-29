"""Transform Teams messages to/from AgentRequest/AgentResponse."""

import logging
from typing import Dict, Any, Optional
from shared.models.request import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)


class TeamsMessageTransformer:
    """Transforms Microsoft Teams messages to/from internal request/response models."""

    @staticmethod
    def teams_to_agent_request(teams_activity: Dict[str, Any]) -> AgentRequest:
        """
        Transform Teams activity to AgentRequest.
        
        Args:
            teams_activity: Microsoft Teams activity object from Bot Framework
            
        Returns:
            AgentRequest object
        """
        # Extract message text
        text = teams_activity.get("text", "").strip()
        if not text:
            # Try alternative text fields
            text = teams_activity.get("textFormat", "") or ""
            if not text and "attachments" in teams_activity:
                # Handle attachments (e.g., adaptive cards with input)
                for attachment in teams_activity.get("attachments", []):
                    if attachment.get("contentType") == "application/vnd.microsoft.card.adaptive":
                        content = attachment.get("content", {})
                        # Extract text from adaptive card inputs
                        text = TeamsMessageTransformer._extract_text_from_adaptive_card(content)
                        break
        
        # Extract session information
        conversation_id = teams_activity.get("conversation", {}).get("id")
        channel_id = teams_activity.get("channelId")
        user_id = teams_activity.get("from", {}).get("id")
        tenant_id = teams_activity.get("channelData", {}).get("tenant", {}).get("id")
        
        # Build session ID from Teams context
        session_id = f"teams_{conversation_id}_{user_id}" if conversation_id and user_id else None
        
        # Extract context from Teams metadata
        context: Dict[str, Any] = {
            "source": "microsoft_teams",
            "channel_id": channel_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "activity_type": teams_activity.get("type"),
            "channel_data": teams_activity.get("channelData", {}),
        }
        
        # Extract agent preference if mentioned in message
        agent_preference = TeamsMessageTransformer._extract_agent_preference(text)
        
        # Extract metadata
        metadata: Dict[str, Any] = {
            "teams_activity_id": teams_activity.get("id"),
            "reply_to_id": teams_activity.get("replyToId"),
            "timestamp": teams_activity.get("timestamp"),
            "locale": teams_activity.get("locale"),
        }
        
        return AgentRequest(
            query=text,
            session_id=session_id,
            context=context,
            agent_preference=agent_preference,
            metadata=metadata,
        )
    
    @staticmethod
    def agent_response_to_teams(
        response: AgentResponse,
        original_activity: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Transform AgentResponse to Teams activity response.
        
        Args:
            response: AgentResponse object
            original_activity: Original Teams activity (for reply context)
            
        Returns:
            Teams activity response dictionary
        """
        from teams_adapter.adaptive_cards import AdaptiveCardBuilder
        
        # Build adaptive card for rich response
        card_builder = AdaptiveCardBuilder()
        card = card_builder.build_response_card(
            response_text=response.response,
            agent_used=response.agent_used,
            confidence=response.confidence,
            sources=response.sources,
            execution_time=response.execution_time,
            metadata=response.metadata,
        )
        
        # Build Teams activity response
        teams_response: Dict[str, Any] = {
            "type": "message",
            "text": response.response,  # Fallback plain text
            "attachments": [card],
        }
        
        # Add reply context if original activity provided
        if original_activity:
            teams_response["conversation"] = original_activity.get("conversation", {})
            teams_response["from"] = {
                "id": "bot",  # Your bot ID
                "name": "Multi-Agent Orchestrator",
            }
            teams_response["recipient"] = original_activity.get("from", {})
            teams_response["replyToId"] = original_activity.get("id")
        
        return teams_response
    
    @staticmethod
    def _extract_text_from_adaptive_card(card_content: Dict[str, Any]) -> str:
        """Extract text input from adaptive card content."""
        text_parts = []
        
        # Extract from body elements
        body = card_content.get("body", [])
        for element in body:
            if element.get("type") == "Input.Text":
                text_parts.append(element.get("value", ""))
            elif element.get("type") == "TextBlock":
                text_parts.append(element.get("text", ""))
        
        return " ".join(filter(None, text_parts))
    
    @staticmethod
    def _extract_agent_preference(text: str) -> Optional[str]:
        """Extract agent preference from message text."""
        text_lower = text.lower()
        
        # Check for explicit agent mentions
        agent_keywords = {
            "analyst": "analyst",
            "search": "search",
            "market": "market_segment",
            "drug": "drug_discovery",
            "combined": "combined",
        }
        
        for keyword, agent in agent_keywords.items():
            if keyword in text_lower:
                return agent
        
        return None
    
    @staticmethod
    def build_typing_activity(conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Build a typing indicator activity for Teams."""
        return {
            "type": "typing",
            "conversation": conversation,
        }
    
    @staticmethod
    def build_error_response(
        error_message: str,
        original_activity: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build an error response for Teams."""
        from teams_adapter.adaptive_cards import AdaptiveCardBuilder
        
        card_builder = AdaptiveCardBuilder()
        error_card = card_builder.build_error_card(error_message)
        
        response: Dict[str, Any] = {
            "type": "message",
            "text": f"❌ Error: {error_message}",
            "attachments": [error_card],
        }
        
        if original_activity:
            response["conversation"] = original_activity.get("conversation", {})
            response["from"] = {
                "id": "bot",
                "name": "Multi-Agent Orchestrator",
            }
            response["recipient"] = original_activity.get("from", {})
            response["replyToId"] = original_activity.get("id")
        
        return response

