"""LangGraph supervisor HTTP server for Snowflake Container Services."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from langgraph.supervisor import LangGraphSupervisor
from shared.models.request import AgentRequest
from shared.utils.exceptions import LangGraphError

logger = logging.getLogger(__name__)

_supervisor: Optional[LangGraphSupervisor] = None


def _get_supervisor() -> LangGraphSupervisor:
    global _supervisor
    if _supervisor is None:
        _supervisor = LangGraphSupervisor()
    return _supervisor


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
    payload = {
        "message": message,
        "errorType": error_type,
        "requestId": request_id,
        "details": details or {},
    }
    _json_response(handler, status, payload, request_id)


class LangGraphRequestHandler(BaseHTTPRequestHandler):
    server_version = "LangGraphSupervisor/1.0"

    def do_GET(self) -> None:
        request_id = str(uuid.uuid4())
        path = urlparse(self.path).path
        if path == "/ping":
            _json_response(self, HTTPStatus.OK, {"status": "ok"}, request_id)
            return
        _error_response(
            self,
            status=HTTPStatus.NOT_FOUND,
            message="Not Found",
            error_type="NotFound",
            request_id=request_id,
        )

    def do_POST(self) -> None:
        request_id = str(uuid.uuid4())
        path = urlparse(self.path).path
        if path not in {"/invocations", "/supervisor/process"}:
            _error_response(
                self,
                status=HTTPStatus.NOT_FOUND,
                message="Not Found",
                error_type="NotFound",
                request_id=request_id,
            )
            return

        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            _error_response(
                self,
                status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                message="Content-Type must be application/json",
                error_type="UnsupportedMediaType",
                request_id=request_id,
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0

        raw_body = self.rfile.read(content_length) if content_length else b""
        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            _error_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                message="Invalid JSON payload",
                error_type="BadRequest",
                request_id=request_id,
                details={"error": str(exc)},
            )
            return

        query = payload.get("query") or payload.get("prompt")
        if not query:
            _error_response(
                self,
                status=HTTPStatus.BAD_REQUEST,
                message="Missing required field: query",
                error_type="BadRequest",
                request_id=request_id,
            )
            return

        session_id = payload.get("session_id") or payload.get("sessionId") or str(uuid.uuid4())
        context = payload.get("context") or {}
        agent_preference = payload.get("agent_preference") or payload.get("agentPreference")
        metadata = payload.get("metadata") or {}

        agent_request = AgentRequest(
            query=str(query),
            session_id=session_id,
            context=context,
            agent_preference=agent_preference,
            metadata=metadata,
        )

        try:
            supervisor = _get_supervisor()
            response = asyncio.run(supervisor.process_request(agent_request, session_id=session_id))
            response_dict = response if isinstance(response, dict) else response
            _json_response(self, HTTPStatus.OK, response_dict, request_id)
        except LangGraphError as exc:
            logger.error("LangGraph invocation failed: %s", exc)
            _error_response(
                self,
                status=HTTPStatus.BAD_GATEWAY,
                message=str(exc),
                error_type=type(exc).__name__,
                request_id=request_id,
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Unhandled LangGraph invocation error")
            _error_response(
                self,
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                message="Internal server error",
                error_type=type(exc).__name__,
                request_id=request_id,
                details={"error": str(exc)},
            )


def run(host: str = "0.0.0.0", port: int = 8001) -> None:
    """Run the LangGraph supervisor HTTP server."""
    server = ThreadingHTTPServer((host, port), LangGraphRequestHandler)
    logger.info("LangGraph supervisor listening on %s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("LangGraph supervisor shutting down")
    finally:
        server.server_close()
