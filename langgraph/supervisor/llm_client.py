"""Minimal LLM client for planner/executor (Snowflake Cortex)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    import snowflake.connector  # type: ignore[import-not-found]
except Exception:
    snowflake = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from snowflake.snowpark import Session  # type: ignore[import-not-found]
except Exception:
    Session = None  # type: ignore

from shared.config.settings import PlannerLLMSettings, settings

logger = logging.getLogger(__name__)


class PlannerLLMClient:
    """Snowflake Cortex client for planner/executor prompts."""

    def __init__(self, settings: PlannerLLMSettings) -> None:
        self.settings = settings

    async def complete(self, *, prompt: str, system: Optional[str] = None) -> str:
        return await asyncio.to_thread(self._invoke, prompt=prompt, system=system)

    def _invoke(self, *, prompt: str, system: Optional[str]) -> str:
        model = os.getenv("SNOWFLAKE_CORTEX_LLM_MODEL", self.settings.model_id)
        mode = os.getenv("SNOWFLAKE_CORTEX_MODE", "connector").lower()
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        if mode == "snowpark":
            return self._invoke_snowpark(model=model, prompt=full_prompt)
        return self._invoke_connector(model=model, prompt=full_prompt)

    def _invoke_connector(self, *, model: str, prompt: str) -> str:
        if snowflake is None:
            raise RuntimeError("snowflake-connector-python not available")
        conn = snowflake.connector.connect(
            account=settings.snowflake.snowflake_account,
            user=settings.snowflake.snowflake_user,
            password=settings.snowflake.snowflake_password,
            role=settings.snowflake.snowflake_role,
            warehouse=settings.snowflake.snowflake_warehouse,
            database=settings.snowflake.snowflake_database,
            schema=settings.snowflake.snowflake_schema,
        )
        sql = "SELECT CORTEX.COMPLETE(%(model)s, %(prompt)s) AS result"
        try:
            with conn.cursor() as cur:
                cur.execute(sql, {"model": model, "prompt": prompt})
                row = cur.fetchone()
                return str(row[0]) if row else ""
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _invoke_snowpark(self, *, model: str, prompt: str) -> str:
        if Session is None:
            raise RuntimeError("snowflake-snowpark-python not available")
        session = Session.builder.configs(
            {
                "account": settings.snowflake.snowflake_account,
                "user": settings.snowflake.snowflake_user,
                "password": settings.snowflake.snowflake_password,
                "role": settings.snowflake.snowflake_role,
                "warehouse": settings.snowflake.snowflake_warehouse,
                "database": settings.snowflake.snowflake_database,
                "schema": settings.snowflake.snowflake_schema,
            }
        ).create()
        sql = "SELECT CORTEX.COMPLETE(%(model)s, %(prompt)s) AS result"
        try:
            rows = session.sql(sql, params={"model": model, "prompt": prompt}).collect()
            return str(rows[0][0]) if rows else ""
        finally:
            try:
                session.close()
            except Exception:
                pass

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
