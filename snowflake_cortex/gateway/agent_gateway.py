"""Snowflake Cortex Agents Run REST client."""

import logging
import json
from typing import Dict, Any, Optional, List, Tuple
import httpx
from shared.config.settings import settings
from shared.utils.exceptions import SnowflakeCortexError

logger = logging.getLogger(__name__)


class CortexAgentGateway:
    """Client for Snowflake Cortex Agents Run REST API.

    This implements the Snowflake Cortex Agents Run API described here:
    https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run
    """
    
    def __init__(self):
        """Initialize the agent gateway client."""
        self.snowflake_config = settings.snowflake
        logger.info("Initialized Cortex Agent Gateway client (Agents Run API)")

    def _snowflake_api_base(self) -> str:
        """Resolve Snowflake API base host."""
        if self.snowflake_config.snowflake_api_host:
            return self.snowflake_config.snowflake_api_host.rstrip("/")
        if self.snowflake_config.snowflake_account:
            # Best-effort default; some accounts require region/cloud-specific hosts.
            return f"https://{self.snowflake_config.snowflake_account}.snowflakecomputing.com"
        raise SnowflakeCortexError("Missing Snowflake API host (SNOWFLAKE_API_HOST) or account (SNOWFLAKE_ACCOUNT)")

    def _auth_headers(self) -> Dict[str, str]:
        """Authorization headers for Snowflake REST APIs."""
        if not self.snowflake_config.snowflake_auth_token:
            raise SnowflakeCortexError(
                "Missing Snowflake auth token for Cortex Agents Run API (SNOWFLAKE_AUTH_TOKEN)."
            )
        return {
            "Authorization": f"Bearer {self.snowflake_config.snowflake_auth_token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

    def _build_messages(self, query: str, history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Convert internal history format into Snowflake 'messages' schema."""
        messages: List[Dict[str, Any]] = []
        if history and isinstance(history, list):
            for msg in history:
                role = msg.get("role")
                content = msg.get("content")
                if role not in ("user", "assistant") or not isinstance(content, str):
                    continue
                messages.append(
                    {
                        "role": role,
                        "content": [{"type": "text", "text": content}],
                    }
                )
        # Ensure current user message is included (append if needed)
        if not messages or messages[-1].get("role") != "user" or messages[-1]["content"][0]["text"] != query:
            messages.append({"role": "user", "content": [{"type": "text", "text": query}]})
        return messages

    def _tool_choice(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve Snowflake tool_choice for an agent run.

        Per your design, we default to **automatic tool selection** and let the Snowflake
        agent decide which tool(s) to invoke:

            {"type": "auto"}

        If a caller explicitly provides `context["tool_choice"]`, we pass it through to
        allow constraining tools for specific requests.
        """
        if "tool_choice" in ctx and isinstance(ctx["tool_choice"], dict):
            return ctx["tool_choice"]
        return {"type": "auto"}

    async def _post_sse(self, url: str, body: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
        """POST to an SSE endpoint, accumulate text deltas and return (final_text, events)."""
        events: List[Dict[str, Any]] = []
        text_parts: List[str] = []

        async with httpx.AsyncClient(timeout=900.0) as client:
            async with client.stream("POST", url, headers=self._auth_headers(), json=body) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        data = line[len("data:") :].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                            events.append(obj)
                            # Best-effort: collect any text deltas we see.
                            # Snowflake emits multiple event types; we capture common shapes.
                            # If a specific schema is needed, refine parsing here.
                            if isinstance(obj, dict):
                                # Some implementations may include direct fields
                                if "text" in obj and isinstance(obj["text"], str):
                                    text_parts.append(obj["text"])
                                # Nested response objects
                                if "response" in obj and isinstance(obj["response"], dict):
                                    r = obj["response"]
                                    if "text" in r and isinstance(r["text"], str):
                                        text_parts.append(r["text"])
                                    if "text" in r and isinstance(r["text"], dict) and "delta" in r["text"]:
                                        delta = r["text"]["delta"]
                                        if isinstance(delta, str):
                                            text_parts.append(delta)
                        except Exception:
                            # Ignore non-JSON lines
                            continue
        return ("".join(text_parts).strip(), events)

    def _should_use_direct_agent_run(self, ctx: Dict[str, Any]) -> bool:
        """Use /api/v2/cortex/agent:run when caller provides tool specs/resources in context."""
        return bool(ctx.get("tool_resources") or ctx.get("tools") or ctx.get("tool_specs"))
    
    async def invoke_agent(
        self,
        agent_name: str,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Invoke a Snowflake Cortex Agent via the Cortex Agents Run REST API.
        
        Args:
            agent_name: Snowflake Cortex Agent object name (database/schema configured separately)
            query: User query
            session_id: Session identifier
            context: Optional context information (may include history/thread metadata)
        
        Returns:
            Response from the agent
        
        Raises:
            SnowflakeCortexError: If invocation fails
        """
        try:
            ctx = context or {}
            history = ctx.get("history")

            # Threading is optional; if provided, Snowflake expects only the current message.
            thread_id = ctx.get("thread_id")
            parent_message_id = ctx.get("parent_message_id")

            messages = self._build_messages(query=query, history=history if not thread_id else None)

            # Choose endpoint form:
            # 1) Agent object run: /api/v2/databases/{db}/schemas/{schema}/agents/{name}:run
            # 2) No agent object: /api/v2/cortex/agent:run (requires full configuration in body)
            base = self._snowflake_api_base()
            if self._should_use_direct_agent_run(ctx):
                url = f"{base}/api/v2/cortex/agent:run"
            elif self.snowflake_config.cortex_agents_database and self.snowflake_config.cortex_agents_schema and agent_name:
                url = (
                    f"{base}/api/v2/databases/{self.snowflake_config.cortex_agents_database}"
                    f"/schemas/{self.snowflake_config.cortex_agents_schema}"
                    f"/agents/{agent_name}:run"
                )
            else:
                # Fallback to generic endpoint (requires agent config in request body in real usage)
                url = f"{base}/api/v2/cortex/agent:run"

            body: Dict[str, Any] = {
                # If thread_id is set, Snowflake expects parent_message_id as well.
                # If not using threads, messages should include full history + current message.
                "messages": messages,
            }

            # tool_choice defaults to auto (Snowflake agent decides); can be overridden via context["tool_choice"]
            body["tool_choice"] = self._tool_choice(ctx)

            # If calling /api/v2/cortex/agent:run directly (no agent object), allow passing tool specs/resources.
            # This matches Snowflake's tool_spec/tool_resources schema.
            if url.endswith("/api/v2/cortex/agent:run"):
                if isinstance(ctx.get("tools"), list):
                    body["tools"] = ctx["tools"]
                if isinstance(ctx.get("tool_specs"), list):
                    body["tool_specs"] = ctx["tool_specs"]
                if isinstance(ctx.get("tool_resources"), dict):
                    body["tool_resources"] = ctx["tool_resources"]
                # Optional advanced fields supported by Snowflake (pass-through)
                for k in ("models", "instructions", "orchestration"):
                    if k in ctx:
                        body[k] = ctx[k]

            if thread_id is not None and parent_message_id is not None:
                body["thread_id"] = int(thread_id)
                body["parent_message_id"] = int(parent_message_id)
                # When using threads, only current message should be sent.
                body["messages"] = [{"role": "user", "content": [{"type": "text", "text": query}]}]

            logger.info(
                f"Calling Snowflake Cortex Agents Run API url={url} session={session_id} agent_name={agent_name}"
            )
            final_text, events = await self._post_sse(url=url, body=body)

            return {
                "response": final_text or "(no response text parsed from SSE)",
                "agent_name": agent_name,
                "session_id": session_id,
                "raw_events_count": len(events),
                "raw_events_sample": events[:5],
                "sources": [],
            }
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error invoking Cortex agent: {str(e)}")
            raise SnowflakeCortexError(f"Failed to invoke Cortex agent: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error invoking Cortex agent: {str(e)}")
            raise SnowflakeCortexError(f"Cortex agent invocation failed: {str(e)}") from e


# Global gateway instance
agent_gateway = CortexAgentGateway()

