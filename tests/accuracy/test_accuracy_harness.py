"""Accuracy verification harness using Langfuse + TruLens hooks."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import httpx
import pytest
import yaml

from langgraph.observability.langfuse_client import LangfuseClient
from shared.config.settings import settings
from snowflake_cortex.observability.trulens_client import TruLensClient


def _load_dataset(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "cases" not in data:
        raise ValueError("Golden set dataset must include 'cases'.")
    return data


def _normalize_agents(selected_agent: Optional[str]) -> List[str]:
    if not selected_agent:
        return []
    return [a.strip() for a in selected_agent.split(",") if a.strip()]


def _extract_sources(sources: Any) -> List[str]:
    extracted: List[str] = []
    if not sources:
        return extracted
    if isinstance(sources, list):
        for item in sources:
            if isinstance(item, str):
                extracted.append(item)
            elif isinstance(item, dict):
                for key in ("file", "title", "name", "id", "source", "document", "doc", "url"):
                    if item.get(key):
                        extracted.append(str(item.get(key)))
    elif isinstance(sources, dict):
        for key in ("file", "title", "name", "id", "source", "document", "doc", "url"):
            if sources.get(key):
                extracted.append(str(sources.get(key)))
    return [s for s in extracted if s]


def _facts_coverage(response_text: str, expected_facts: List[str]) -> bool:
    text = (response_text or "").lower()
    return all(fact.lower() in text for fact in expected_facts)


@pytest.mark.accuracy
@pytest.mark.asyncio
async def test_accuracy_golden_set() -> None:
    if os.getenv("ACCURACY_EVAL_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        pytest.skip("Accuracy eval disabled. Set ACCURACY_EVAL_ENABLED=true to run.")

    if not settings.trulens.trulens_enabled:
        pytest.skip("TruLens disabled. Set TRULENS_ENABLED=true to run accuracy evals.")

    dataset_path = os.getenv(
        "ACCURACY_DATASET_PATH",
        os.path.join(os.path.dirname(__file__), "golden_set.yaml"),
    )
    dataset = _load_dataset(dataset_path)
    dataset_id = str(dataset.get("dataset_id", "unknown"))

    endpoint = os.getenv("ACCURACY_EVAL_ENDPOINT", "http://localhost:8000/api/v1/query")
    timeout = float(os.getenv("ACCURACY_EVAL_TIMEOUT", "120"))
    require_trulens = os.getenv("ACCURACY_REQUIRE_TRULENS", "true").lower() in {"1", "true", "yes"}

    trulens = TruLensClient(settings.trulens)
    langfuse = LangfuseClient(settings.langfuse)

    failures: List[str] = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        for case in dataset.get("cases", []):
            case_id = str(case.get("id", "unknown"))
            session_id = f"accuracy-{dataset_id}-{case_id}-{int(time.time())}"
            query = case["query"]
            expected_agent = case["expected_agent"]
            expected_facts = case.get("expected_facts", [])
            min_scores = case.get("min_scores", {})
            require_sources = bool(case.get("require_sources", False))

            payload = {
                "query": query,
                "session_id": session_id,
                "context": {"domain": case.get("domain")},
                "metadata": {
                    "eval_run_id": dataset_id,
                    "case_id": case_id,
                    "expected_agent": expected_agent,
                },
            }

            try:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
            except httpx.RequestError as exc:
                pytest.skip(f"Accuracy endpoint unreachable: {exc}")

            data = response.json()
            response_text = str(data.get("response", ""))
            selected_agent = data.get("selected_agent") or data.get("agent_used") or ""
            sources = data.get("sources") or []

            # Metrics: routing accuracy
            selected_agents = _normalize_agents(selected_agent)
            routing_ok = expected_agent in selected_agents

            # Metrics: coverage (expected facts/phrases)
            coverage_ok = _facts_coverage(response_text, expected_facts)

            # Metrics: grounding (response references sources if available)
            source_tokens = _extract_sources(sources)
            sources_present = bool(sources)
            sources_referenced = False
            if source_tokens:
                response_lower = response_text.lower()
                sources_referenced = any(token.lower() in response_lower for token in source_tokens)
            elif sources_present:
                sources_referenced = True  # No extractable token; accept presence as grounding signal.
            grounding_ok = sources_referenced if sources_present else True
            if require_sources and not sources_present:
                grounding_ok = False

            # Metrics: answer quality (TruLens)
            eval_scores = await trulens.evaluate_response(
                query=query,
                response=response_text,
                context={"domain": case.get("domain"), "expected_facts": expected_facts},
            )
            evaluated = bool(eval_scores.get("evaluated"))
            relevance = float(eval_scores.get("relevance_score", 0.0) or 0.0)
            completeness = float(eval_scores.get("completeness_score", 0.0) or 0.0)
            min_relevance = float(min_scores.get("relevance", 0.0))
            min_completeness = float(min_scores.get("completeness", 0.0))
            quality_ok = (
                evaluated
                and relevance >= min_relevance
                and completeness >= min_completeness
            )

            if require_trulens and not evaluated:
                quality_ok = False

            # Log to Langfuse (best-effort)
            try:
                await langfuse.log_supervisor_decision(
                    session_id=session_id,
                    query=query,
                    routing_decision={
                        "selected_agent": selected_agent,
                        "routing_reason": data.get("routing_reason", ""),
                        "confidence": data.get("confidence", None),
                    },
                    execution_time=float(data.get("execution_time") or 0.0),
                    metadata={
                        "eval_run_id": dataset_id,
                        "case_id": case_id,
                        "expected_agent": expected_agent,
                        "routing_ok": routing_ok,
                        "coverage_ok": coverage_ok,
                        "grounding_ok": grounding_ok,
                        "sources_present": sources_present,
                        "sources_referenced": sources_referenced,
                        "relevance_score": relevance,
                        "completeness_score": completeness,
                    },
                )
            except Exception:
                # Langfuse is best-effort; do not fail the test on logging.
                pass

            # Aggregate failures for reporting
            if not routing_ok:
                failures.append(f"{case_id}: routing_ok=false (expected {expected_agent}, got {selected_agents})")
            if not coverage_ok:
                failures.append(f"{case_id}: coverage_ok=false (expected facts missing)")
            if not grounding_ok:
                failures.append(f"{case_id}: grounding_ok=false (sources missing or not referenced)")
            if not quality_ok:
                failures.append(
                    f"{case_id}: quality_ok=false (relevance={relevance:.2f}, completeness={completeness:.2f})"
                )

    if failures:
        failure_report = "\n".join(failures)
        pytest.fail(f"Accuracy evaluation failed:\n{failure_report}")
