"""Lambda handler that invokes AgentCore Runtime SDK."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from aws_agent_core.runtime.sdk_client import AgentCoreRuntimeClient
from shared.config.settings import settings
from shared.utils.exceptions import AWSAgentCoreError

logger = logging.getLogger(__name__)

_runtime_client: Optional[AgentCoreRuntimeClient] = None
_TOOL_NAME_DELIMITER = "___"


def _get_runtime_client() -> AgentCoreRuntimeClient:
    global _runtime_client
    if _runtime_client is None:
        _runtime_client = AgentCoreRuntimeClient(settings.aws)
    return _runtime_client


def _extract_tool_name(context: Any) -> Optional[str]:
    """Extract tool name from AgentCore Lambda context."""
    try:
        custom = getattr(context, "client_context", None)
        if custom and getattr(custom, "custom", None):
            tool_name = custom.custom.get("bedrockAgentCoreToolName")
        else:
            tool_name = None
    except Exception:
        tool_name = None

    if not tool_name or _TOOL_NAME_DELIMITER not in tool_name:
        return tool_name
    return tool_name.split(_TOOL_NAME_DELIMITER, 1)[1]


def _build_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    query = event.get("query") or event.get("prompt")
    if not query:
        raise ValueError("Missing required field: query")
    return {
        "input_text": str(query),
        "session_id": event.get("session_id") or event.get("sessionId"),
        "context": event.get("context") or {},
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AgentCore Gateway Lambda entrypoint."""
    tool_name = _extract_tool_name(context)
    logger.info("AgentCore Lambda invoked tool=%s", tool_name)

    try:
        payload = _build_payload(event or {})
        agent_id = os.getenv("AGENTCORE_AGENT_ID")
        agent_alias_id = os.getenv("AGENTCORE_AGENT_ALIAS_ID")
        if not agent_id or not agent_alias_id:
            raise ValueError("Missing AGENTCORE_AGENT_ID or AGENTCORE_AGENT_ALIAS_ID")

        runtime_client = _get_runtime_client()
        result = runtime_client.invoke_agent_runtime(
            agent_id=agent_id,
            agent_alias_id=agent_alias_id,
            session_id=payload.get("session_id") or "",
            input_text=payload["input_text"],
        )
        return {
            "tool": tool_name,
            "result": result,
        }
    except (ValueError, AWSAgentCoreError) as exc:
        logger.error("AgentCore Lambda error: %s", exc)
        return {
            "tool": tool_name,
            "error": str(exc),
            "errorType": type(exc).__name__,
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unhandled AgentCore Lambda error")
        return {
            "tool": tool_name,
            "error": "Unhandled exception",
            "errorType": type(exc).__name__,
            "details": {"message": str(exc)},
        }
