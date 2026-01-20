"""Minimal LLM client for planner/executor (AWS Bedrock)."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional

import boto3

from shared.config.settings import PlannerLLMSettings

logger = logging.getLogger(__name__)


class PlannerLLMClient:
    """AWS Bedrock client for planner/executor prompts."""

    def __init__(self, settings: PlannerLLMSettings) -> None:
        self.settings = settings

    async def complete(self, *, prompt: str, system: Optional[str] = None) -> str:
        return await asyncio.to_thread(self._invoke, prompt=prompt, system=system)

    def _invoke(self, *, prompt: str, system: Optional[str]) -> str:
        client = boto3.client("bedrock-runtime", region_name=self.settings.region)
        if hasattr(client, "converse"):
            return self._invoke_converse(client, prompt=prompt, system=system)
        return self._invoke_invoke_model(client, prompt=prompt, system=system)

    def _invoke_converse(self, client: Any, *, prompt: str, system: Optional[str]) -> str:
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        kwargs: Dict[str, Any] = {
            "modelId": self.settings.model_id,
            "messages": messages,
            "inferenceConfig": {
                "temperature": self.settings.temperature,
                "maxTokens": self.settings.max_tokens,
            },
        }
        if system:
            kwargs["system"] = [{"text": system}]
        response = client.converse(**kwargs)
        content = response.get("output", {}).get("message", {}).get("content", [])
        return "".join(chunk.get("text", "") for chunk in content if isinstance(chunk, dict)).strip()

    def _invoke_invoke_model(self, client: Any, *, prompt: str, system: Optional[str]) -> str:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
        }
        if system:
            body["system"] = system
        response = client.invoke_model(
            modelId=self.settings.model_id,
            body=json.dumps(body),
        )
        payload = json.loads(response["body"].read())
        try:
            return payload["content"][0]["text"]
        except Exception:
            logger.error("Unexpected Bedrock response shape: %s", payload)
            raise

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """Best-effort JSON extraction from LLM output."""
        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise ValueError(f"Planner returned invalid JSON: {text}")
        return json.loads(match.group(0))
