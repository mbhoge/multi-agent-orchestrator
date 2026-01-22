"""AWS Agent Core Runtime SDK client wrapper."""

import logging
from typing import Any, Dict, Optional

from shared.config.aws_config import get_bedrock_agent_core_client
from shared.config.settings import AWSSettings
from shared.utils.exceptions import AWSAgentCoreError

logger = logging.getLogger(__name__)


class AgentCoreRuntimeClient:
    """Client for invoking the AgentCore Runtime API."""

    def __init__(self, aws_settings: AWSSettings):
        self.aws_settings = aws_settings
        self.client = get_bedrock_agent_core_client(aws_settings)

    def invoke_agent_runtime(
        self,
        *,
        agent_id: str,
        agent_alias_id: str,
        session_id: str,
        input_text: str,
        enable_trace: bool = True,
    ) -> Dict[str, Any]:
        """Invoke an AgentCore runtime agent (LangGraph supervisor)."""
        try:
            logger.info("Invoking AgentCore runtime agent=%s session=%s", agent_id, session_id)
            request_params = {
                "agentId": agent_id,
                "agentAliasId": agent_alias_id,
                "sessionId": session_id,
                "inputText": input_text,
                "enableTrace": enable_trace,
            }
            if hasattr(self.client, "invoke_agent_runtime"):
                response = self.client.invoke_agent_runtime(**request_params)
            else:
                response = self.client.invoke_agent(**request_params)

            completion_text = ""
            for event in response.get("completion", []):
                if "chunk" in event and "bytes" in event["chunk"]:
                    completion_text += event["chunk"]["bytes"].decode("utf-8")

            trace_id: Optional[str] = None
            for event in response.get("completion", []):
                if "trace" in event and "traceId" in event["trace"]:
                    trace_id = event["trace"]["traceId"]

            return {
                "completion": completion_text,
                "trace_id": trace_id,
                "session_id": session_id,
            }
        except Exception as exc:  # pragma: no cover - depends on AWS
            logger.error("AgentCore runtime invocation failed: %s", exc)
            raise AWSAgentCoreError(f"Failed to invoke AgentCore runtime: {exc}") from exc
