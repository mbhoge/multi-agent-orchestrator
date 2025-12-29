"""Build Adaptive Cards for Microsoft Teams responses."""

from typing import Optional, List, Dict, Any


class AdaptiveCardBuilder:
    """Builder for Microsoft Teams Adaptive Cards."""
    
    @staticmethod
    def build_response_card(
        response_text: str,
        agent_used: str,
        confidence: Optional[float] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        execution_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build an adaptive card for agent response.
        
        Args:
            response_text: Main response text
            agent_used: Agent that processed the request
            confidence: Confidence score (0.0-1.0)
            sources: List of source references
            execution_time: Execution time in seconds
            metadata: Additional metadata
            
        Returns:
            Adaptive card attachment dictionary
        """
        body = []
        
        # Main response text
        body.append({
            "type": "TextBlock",
            "text": response_text,
            "wrap": True,
            "size": "Medium",
            "weight": "Default",
        })
        
        # Separator
        body.append({"type": "Separator"})
        
        # Metadata section
        facts = []
        facts.append({"title": "Agent", "value": agent_used})
        
        if confidence is not None:
            confidence_pct = f"{confidence * 100:.1f}%"
            facts.append({"title": "Confidence", "value": confidence_pct})
        
        if execution_time is not None:
            facts.append({"title": "Execution Time", "value": f"{execution_time:.2f}s"})
        
        if facts:
            body.append({
                "type": "FactSet",
                "facts": facts,
            })
        
        # Sources section
        if sources:
            body.append({"type": "Separator"})
            body.append({
                "type": "TextBlock",
                "text": "**Sources:**",
                "weight": "Bolder",
                "size": "Small",
            })
            
            for i, source in enumerate(sources[:5], 1):  # Limit to 5 sources
                source_text = source.get("title") or source.get("url") or str(source)
                body.append({
                    "type": "TextBlock",
                    "text": f"{i}. {source_text}",
                    "wrap": True,
                    "size": "Small",
                    "color": "Accent",
                })
        
        # Build card
        card = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": body,
            },
        }
        
        return card
    
    @staticmethod
    def build_error_card(error_message: str) -> Dict[str, Any]:
        """Build an adaptive card for error responses."""
        card = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "❌ Error",
                        "weight": "Bolder",
                        "size": "Large",
                        "color": "Attention",
                    },
                    {
                        "type": "TextBlock",
                        "text": error_message,
                        "wrap": True,
                    },
                ],
            },
        }
        return card
    
    @staticmethod
    def build_processing_card(message: str = "Processing your request...") -> Dict[str, Any]:
        """Build an adaptive card for processing/loading state."""
        card = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "⏳ " + message,
                        "wrap": True,
                    },
                ],
            },
        }
        return card
    
    @staticmethod
    def build_query_input_card(
        placeholder: str = "Enter your query...",
        submit_text: str = "Submit",
    ) -> Dict[str, Any]:
        """Build an adaptive card with query input field."""
        card = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Ask a question:",
                        "weight": "Bolder",
                    },
                    {
                        "type": "Input.Text",
                        "id": "query",
                        "placeholder": placeholder,
                        "isMultiline": True,
                        "maxLength": 1000,
                    },
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": submit_text,
                        "data": {
                            "action": "submit_query",
                        },
                    },
                ],
            },
        }
        return card

