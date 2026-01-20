"""Snowflake Cortex Agents Run REST client."""

import logging
import json
from typing import Dict, Any, Optional, List, Tuple
import httpx
from shared.config.settings import settings
from shared.utils.exceptions import SnowflakeCortexError
from snowflake_cortex.observability.trulens_client import TruLensClient

logger = logging.getLogger(__name__)


class CortexAgentGateway:
    """Client for Snowflake Cortex Agents Run REST API.

    This implements the Snowflake Cortex Agents Run API described here:
    https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run
    """
    
    def __init__(self):
        """Initialize the agent gateway client."""
        self.snowflake_config = settings.snowflake
        self.trulens_client = TruLensClient(settings.trulens)
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

    def _normalize_tool_call(self, call: Dict[str, Any]) -> Dict[str, Any]:
        """Best-effort normalization of a tool call event into a common shape."""
        tool_name = call.get("tool_name") or call.get("name")
        tool_input = call.get("tool_input") or call.get("input") or call.get("arguments")
        tool_output = call.get("tool_output") or call.get("output") or call.get("result") or call.get("response")

        # Handle OpenAI-style function call shape: {"function": {"name": "...", "arguments": "..."}}
        if not tool_name and isinstance(call.get("function"), dict):
            tool_name = call["function"].get("name")
            tool_input = tool_input or call["function"].get("arguments")

        # Attempt to parse JSON string inputs for readability
        if isinstance(tool_input, str):
            try:
                tool_input = json.loads(tool_input)
            except Exception:
                pass

        return {
            "tool_name": str(tool_name or "unknown"),
            "tool_input": tool_input if isinstance(tool_input, dict) else (tool_input or {}),
            "tool_output": tool_output,
        }

    def _extract_tool_calls(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract tool calls from SSE events (best-effort, schema-agnostic)."""
        calls: List[Dict[str, Any]] = []
        for ev in events or []:
            if not isinstance(ev, dict):
                continue

            if isinstance(ev.get("tool_calls"), list):
                for c in ev["tool_calls"]:
                    if isinstance(c, dict):
                        calls.append(self._normalize_tool_call(c))

            for key in ("tool_call", "tool"):
                if isinstance(ev.get(key), dict):
                    calls.append(self._normalize_tool_call(ev[key]))

            # Some providers emit typed events
            if ev.get("type") in {"tool_call", "tool_result"} and isinstance(ev.get("data"), dict):
                calls.append(self._normalize_tool_call(ev["data"]))

        return calls

    def _extract_retrieved_contexts(self, tool_calls: List[Dict[str, Any]]) -> List[str]:
        """Collect textual contexts from tool outputs for RAG evaluations."""
        contexts: List[str] = []
        for call in tool_calls or []:
            output = call.get("tool_output")
            if isinstance(output, str):
                contexts.append(output)
            elif isinstance(output, list):
                contexts.extend([str(item) for item in output if isinstance(item, str)])
            elif isinstance(output, dict):
                for key in ("content", "text", "summary", "snippet", "answer", "result"):
                    if isinstance(output.get(key), str):
                        contexts.append(output[key])
        return contexts

    def _extract_selected_tools(self, ctx: Dict[str, Any], events: List[Dict[str, Any]]) -> List[str]:
        """Best-effort extraction of selected tool names."""
        selected: List[str] = []

        tool_choice = ctx.get("tool_choice")
        if isinstance(tool_choice, dict):
            names = tool_choice.get("name")
            if isinstance(names, list):
                selected.extend([str(n) for n in names if n])

        for key in ("tools", "tool_specs"):
            if isinstance(ctx.get(key), list):
                for item in ctx[key]:
                    if isinstance(item, dict) and item.get("name"):
                        selected.append(str(item["name"]))

        if isinstance(ctx.get("tool_resources"), dict):
            selected.extend([str(k) for k in ctx["tool_resources"].keys() if k])

        for call in self._extract_tool_calls(events):
            name = call.get("tool_name")
            if name:
                selected.append(str(name))

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for name in selected:
            if name not in seen:
                seen.add(name)
                unique.append(name)
        return unique

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

            result = {
                "response": final_text or "(no response text parsed from SSE)",
                "agent_name": agent_name,
                "session_id": session_id,
                "raw_events_count": len(events),
                "raw_events_sample": events[:5],
                "sources": [],
            }

            # Observability: capture tool calls and trace execution via TruLens
            try:
                tool_calls = self._extract_tool_calls(events)
                selected_tools = self._extract_selected_tools(ctx, events)
                retrieved_contexts = self._extract_retrieved_contexts(tool_calls)
                ground_truth = (
                    ctx.get("ground_truth")
                    or ctx.get("expected_response")
                    or ctx.get("golden_response")
                )
                await self.trulens_client.log_agent_execution(
                    session_id=session_id,
                    agent_type=agent_name,
                    query=query,
                    result=result,
                    metadata={"raw_events_count": len(events)},
                    selected_tools=selected_tools,
                    tool_calls=tool_calls,
                    retrieved_contexts=retrieved_contexts,
                    ground_truth=ground_truth,
                )
            except Exception:
                logger.debug("TruLens logging failed (best-effort).")

            return result
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error invoking Cortex agent: {str(e)}")
            raise SnowflakeCortexError(f"Failed to invoke Cortex agent: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error invoking Cortex agent: {str(e)}")
            raise SnowflakeCortexError(f"Cortex agent invocation failed: {str(e)}") from e


# Global gateway instance
agent_gateway = CortexAgentGateway()

