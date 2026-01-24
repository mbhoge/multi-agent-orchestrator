"""HTTP server for Snowflake Cortex Agent Gateway (SPCS-friendly).

This module intentionally uses the standard library `http.server` to keep the
runtime lightweight (and consistent with `langgraph/api/main.py`).

Endpoints:
- GET  /ping, /health
- POST /agents/invoke
- GET  /prompts/{prompt_name}
- POST /prompts
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from langfuse import get_prompt_manager
from shared.utils.exceptions import ObservabilityError, SnowflakeCortexError
from snowflake_cortex.gateway.agent_gateway import agent_gateway

logger = logging.getLogger(__name__)


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any], request_id: str) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("X-Request-Id", request_id)
    handler.end_headers()
    handler.wfile.write(body)


def _error_response(
    handler: BaseHTTPRequestHandler,
    *,
    status: int,
    message: str,
    error_type: str,
    request_id: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    _json_response(
        handler,
        status,
        {
            "message": message,
            "errorType": error_type,
            "requestId": request_id,
            "details": details or {},
        },
        request_id,
    )


def _read_json(handler: BaseHTTPRequestHandler, request_id: str) -> Optional[Dict[str, Any]]:
    content_type = handler.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        _error_response(
            handler,
            status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            message="Content-Type must be application/json",
            error_type="UnsupportedMediaType",
            request_id=request_id,
        )
        return None

    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except ValueError:
        content_length = 0

    raw_body = handler.rfile.read(content_length) if content_length else b""
    try:
        parsed = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        _error_response(
            handler,
            status=HTTPStatus.BAD_REQUEST,
            message="Invalid JSON payload",
            error_type="BadRequest",
            request_id=request_id,
            details={"error": str(exc)},
        )
        return None

    if not isinstance(parsed, dict):
        _error_response(
            handler,
            status=HTTPStatus.BAD_REQUEST,
            message="JSON payload must be an object",
            error_type="BadRequest",
            request_id=request_id,
        )
        return None

    return parsed


class SnowflakeCortexGatewayHandler(BaseHTTPRequestHandler):
    server_version = "SnowflakeCortexGateway/1.0"

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        request_id = str(uuid.uuid4())
        path = urlparse(self.path).path

        if path in {"/ping", "/health"}:
            _json_response(
                self,
                HTTPStatus.OK,
                {"status": "healthy", "service": "snowflake-cortex-gateway"},
                request_id,
            )
            return

        if path.startswith("/prompts/"):
            prompt_name = path[len("/prompts/") :].strip("/")
            if not prompt_name:
                _error_response(
                    self,
                    status=HTTPStatus.BAD_REQUEST,
                    message="Missing prompt name",
                    error_type="BadRequest",
                    request_id=request_id,
                )
                return
            try:
                prompt_manager = get_prompt_manager()
                prompt_data = asyncio.run(prompt_manager.get_prompt(prompt_name))
                if not prompt_data:
                    _error_response(
                        self,
                        status=HTTPStatus.NOT_FOUND,
                        message="Prompt not found",
                        error_type="NotFound",
                        request_id=request_id,
                        details={"prompt_name": prompt_name},
                    )
                    return
                _json_response(self, HTTPStatus.OK, prompt_data, request_id)
                return
            except Exception as exc:
                _error_response(
                    self,
                    status=HTTPStatus.BAD_GATEWAY,
                    message="Failed to fetch prompt",
                    error_type=type(exc).__name__,
                    request_id=request_id,
                    details={"error": str(exc), "prompt_name": prompt_name},
                )
                return

        _error_response(
            self,
            status=HTTPStatus.NOT_FOUND,
            message="Not Found",
            error_type="NotFound",
            request_id=request_id,
        )

    def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
        request_id = str(uuid.uuid4())
        path = urlparse(self.path).path

        if path == "/agents/invoke":
            payload = _read_json(self, request_id)
            if payload is None:
                return

            agent_name = payload.get("agent_name") or payload.get("agentName")
            query = payload.get("query") or payload.get("prompt")
            if not agent_name or not query:
                _error_response(
                    self,
                    status=HTTPStatus.BAD_REQUEST,
                    message="Missing required fields: agent_name, query",
                    error_type="BadRequest",
                    request_id=request_id,
                )
                return

            session_id = payload.get("session_id") or payload.get("sessionId") or str(uuid.uuid4())
            context = payload.get("context") or {}
            if not isinstance(context, dict):
                context = {}

            # Accept `history` either nested in context or as a top-level field
            history = payload.get("history")
            if history is not None and "history" not in context:
                context["history"] = history

            try:
                result = asyncio.run(
                    agent_gateway.invoke_agent(
                        agent_name=str(agent_name),
                        query=str(query),
                        session_id=str(session_id),
                        context=context,
                    )
                )
                _json_response(self, HTTPStatus.OK, result, request_id)
                return
            except (SnowflakeCortexError, ObservabilityError) as exc:
                logger.error("Gateway invocation failed: %s", exc)
                _error_response(
                    self,
                    status=HTTPStatus.BAD_GATEWAY,
                    message=str(exc),
                    error_type=type(exc).__name__,
                    request_id=request_id,
                )
                return
            except Exception as exc:  # pragma: no cover
                logger.exception("Unhandled gateway error")
                _error_response(
                    self,
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    message="Internal server error",
                    error_type=type(exc).__name__,
                    request_id=request_id,
                    details={"error": str(exc)},
                )
                return

        if path == "/prompts":
            payload = _read_json(self, request_id)
            if payload is None:
                return

            prompt_name = payload.get("prompt_name") or payload.get("promptName") or payload.get("name")
            prompt = payload.get("prompt")
            if not prompt_name or not isinstance(prompt, str):
                _error_response(
                    self,
                    status=HTTPStatus.BAD_REQUEST,
                    message="Missing required fields: prompt_name, prompt",
                    error_type="BadRequest",
                    request_id=request_id,
                )
                return

            config = payload.get("config")
            labels = payload.get("labels")

            try:
                prompt_manager = get_prompt_manager()
                created = asyncio.run(
                    prompt_manager.create_prompt(
                        prompt_name=str(prompt_name),
                        prompt=str(prompt),
                        config=config if isinstance(config, dict) else None,
                        labels=labels if isinstance(labels, list) else None,
                    )
                )
                _json_response(self, HTTPStatus.OK, created, request_id)
                return
            except Exception as exc:
                _error_response(
                    self,
                    status=HTTPStatus.BAD_GATEWAY,
                    message="Failed to create prompt",
                    error_type=type(exc).__name__,
                    request_id=request_id,
                    details={"error": str(exc), "prompt_name": prompt_name},
                )
                return

        _error_response(
            self,
            status=HTTPStatus.NOT_FOUND,
            message="Not Found",
            error_type="NotFound",
            request_id=request_id,
        )


def run(host: str = "0.0.0.0", port: int = 8002) -> None:
    """Run the Snowflake Cortex Agent Gateway HTTP server."""
    server = ThreadingHTTPServer((host, port), SnowflakeCortexGatewayHandler)
    logger.info("Snowflake Cortex gateway listening on %s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Snowflake Cortex gateway shutting down")
    finally:
        server.server_close()


def main() -> None:
    """CLI entrypoint for `python -m snowflake_cortex.gateway`."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("GATEWAY_PORT", "8002")))
    run(host=host, port=port)

