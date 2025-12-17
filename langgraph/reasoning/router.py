"""Request routing logic to Snowflake Cortex Agent objects.

This router selects WHICH Snowflake agent object(s) to invoke (by domain).
It does NOT execute tools. Tool orchestration is done by the Snowflake agent.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
from shared.utils.exceptions import AgentRoutingError
from shared.config.settings import settings

logger = logging.getLogger(__name__)


class AgentRouter:
    """Routes requests to appropriate Snowflake Cortex Agent objects."""
    
    def __init__(self):
        """Initialize the agent router."""
        self.registry_path = Path(__file__).resolve().parents[2] / "config" / "agents.yaml"
        self.domain_agents = self._load_domain_agents()
        logger.info("Initialized Agent Router")

    def _load_domain_agents(self) -> List[Dict[str, Any]]:
        """Load domain agent registry from config/agents.yaml."""
        try:
            if not self.registry_path.exists():
                logger.warning(f"Domain agent registry not found at {self.registry_path}")
                return []
            data = yaml.safe_load(self.registry_path.read_text()) or {}
            agents = data.get("agents", []) or []
            # Keep only enabled agents with an agent_name
            enabled = [
                a for a in agents
                if isinstance(a, dict) and a.get("enabled", True) and a.get("agent_name")
            ]
            return enabled
        except Exception as e:
            logger.error(f"Failed to load domain agent registry: {e}")
            return []
    
    def route_request(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        agent_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route a request to the appropriate agent.
        
        Args:
            query: User query
            context: Optional context information
            agent_preference: Optional preferred agent
        
        Returns:
            Routing decision with agents_to_call (list of agent names) and reason
        
        Raises:
            AgentRoutingError: If routing fails
        """
        try:
            query_lower = query.lower()

            if not self.domain_agents:
                # Fallback to a single configured default agent object name
                default_agent = settings.snowflake.cortex_agent_name
                if not default_agent:
                    raise AgentRoutingError(
                        "No domain agents configured (config/agents.yaml) and no default SNOWFLAKE_CORTEX_AGENT_NAME set."
                    )
                return {
                    "agents_to_call": [default_agent],
                    "routing_reason": "No domain registry; using default Snowflake agent",
                    "confidence": 0.5,
                }

            # Check for explicit agent preference (expects an agent name or keywords)
            if agent_preference:
                pref = agent_preference.strip()

                # If pref matches an agent_name directly, honor it.
                for a in self.domain_agents:
                    if pref == a.get("agent_name") or pref == a.get("domain"):
                        return {
                            "agents_to_call": [a["agent_name"]],
                            "routing_reason": f"Explicit agent preference: {pref}",
                            "confidence": 1.0,
                        }

            # Domain-based scoring: keyword matches + optional explicit context.domain
            context_domain = (context or {}).get("domain")
            scored: List[Dict[str, Any]] = []
            for a in self.domain_agents:
                keywords = [k.lower() for k in (a.get("keywords") or []) if isinstance(k, str)]
                matches = sum(1 for k in keywords if k in query_lower)
                score = 0.0
                if keywords:
                    score += (matches / max(len(keywords), 1)) * 1.0
                # Boost if caller provides explicit domain
                if context_domain and isinstance(context_domain, str) and context_domain.lower() == str(a.get("domain", "")).lower():
                    score += 0.75
                scored.append({"agent": a, "score": min(score, 1.0), "matches": matches})

            scored.sort(key=lambda x: x["score"], reverse=True)

            # Multi-agent orchestration rule:
            # - Call the top agent always if it has any signal
            # - Also call the next agent if it's close (within 0.15) and non-trivial
            top = scored[0]
            agents_to_call = []
            if top["score"] >= 0.2:
                agents_to_call.append(top["agent"]["agent_name"])
                reason = f"Domain match to '{top['agent'].get('domain')}' (score={top['score']:.2f})"
                confidence = top["score"]
            else:
                # No strong signal: call all enabled agents (or first N) to let Snowflake decide
                agents_to_call = [a["agent_name"] for a in self.domain_agents[:2]]
                reason = "No strong domain signal; calling multiple domain agents"
                confidence = 0.4

            if len(scored) > 1:
                second = scored[1]
                if second["score"] >= 0.2 and abs(top["score"] - second["score"]) <= 0.15:
                    if second["agent"]["agent_name"] not in agents_to_call:
                        agents_to_call.append(second["agent"]["agent_name"])
                        reason += f"; also calling '{second['agent'].get('domain')}' (score={second['score']:.2f})"

            logger.info(f"Routed request to agents={agents_to_call}: {reason}")
            return {"agents_to_call": agents_to_call, "routing_reason": reason, "confidence": confidence}
            
        except Exception as e:
            logger.error(f"Error routing request: {str(e)}")
            raise AgentRoutingError(f"Failed to route request: {str(e)}") from e

# Global router instance
agent_router = AgentRouter()

