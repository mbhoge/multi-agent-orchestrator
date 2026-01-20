"""TruLens client for Snowflake Cortex AI agent observability.

Refactor notes:
- Uses @instrument decorators (TruLens OTel SDK) to trace internal steps.
- Adds RAG Triad evaluations (answer relevance, context relevance, groundedness).
- Provides GPA-style composite scoring for agent evaluations.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from shared.config.settings import TruLensSettings

try:
    # TruLens OpenTelemetry-style instrumentation
    import importlib

    instrument = importlib.import_module("trulens.core.otel.instrument").instrument
    SpanAttributes = importlib.import_module("trulens.otel.semconv.trace").SpanAttributes
    Feedback = importlib.import_module("trulens.core").Feedback
    Selector = importlib.import_module("trulens.core.feedback.selector").Selector
    TruSession = importlib.import_module("trulens.core.session").TruSession
    DefaultDBConnector = importlib.import_module(
        "trulens.core.database.connector.default"
    ).DefaultDBConnector
    OpenAIProvider = importlib.import_module("trulens.providers.openai").OpenAI
    np = importlib.import_module("numpy")
except Exception:  # pragma: no cover - optional dependency
    def instrument(*_args, **_kwargs):  # type: ignore
        def _decorator(func):
            return func

        return _decorator

    class _SpanType:
        RECORD_ROOT = "RECORD_ROOT"
        RETRIEVAL = "RETRIEVAL"
        GENERATION = "GENERATION"
        UNKNOWN = "UNKNOWN"

    class _SpanAttributes:
        SpanType = _SpanType

        class RECORD_ROOT:
            INPUT = "INPUT"
            OUTPUT = "OUTPUT"
            GROUND_TRUTH_OUTPUT = "GROUND_TRUTH_OUTPUT"

        class RETRIEVAL:
            QUERY_TEXT = "QUERY_TEXT"
            RETRIEVED_CONTEXTS = "RETRIEVED_CONTEXTS"

    SpanAttributes = _SpanAttributes  # type: ignore
    Feedback = None
    Selector = None
    TruSession = None
    DefaultDBConnector = None
    OpenAIProvider = None
    np = None

logger = logging.getLogger(__name__)


class TruLensClient:
    """Client for TruLens observability."""
    
    def __init__(self, trulens_settings: TruLensSettings):
        """
        Initialize TruLens client.
        
        Args:
            trulens_settings: TruLens configuration settings
        """
        self.settings = trulens_settings
        self.enabled = trulens_settings.trulens_enabled
        self.app_id = trulens_settings.trulens_app_id
        self.api_key = trulens_settings.trulens_api_key
        self.eval_enabled = os.getenv("TRULENS_EVAL_ENABLED", "true").lower() in {"1", "true", "yes"}
        logger.info(f"Initialized TruLens client: enabled={self.enabled}")
        if self.enabled:
            os.environ.setdefault("TRULENS_OTEL_TRACING", "1")

        self._session = self._init_session()
        self._feedbacks = self._build_feedbacks()

    def _init_session(self) -> Optional[Any]:
        """Initialize a TruLens session for storing traces and evaluations."""
        if not self.enabled or TruSession is None or DefaultDBConnector is None:
            return None
        db_url = os.getenv("TRULENS_DB_URL", "sqlite:///trulens.sqlite")
        try:
            connector = DefaultDBConnector(database_url=db_url)
            return TruSession(connector=connector)
        except Exception as exc:
            logger.warning(f"Failed to initialize TruLens session: {exc}")
            return None

    def _build_feedbacks(self) -> List[Any]:
        """Build RAG Triad feedback functions when a provider is available."""
        if not self.enabled or OpenAIProvider is None or Feedback is None or Selector is None or np is None:
            return []
        try:
            provider = OpenAIProvider(model_engine=os.getenv("TRULENS_EVAL_MODEL", "gpt-4o"))

            f_groundedness = (
                Feedback(provider.groundedness_measure_with_cot_reasons, name="Groundedness")
                .on(
                    {
                        "source": Selector(
                            span_type=SpanAttributes.SpanType.RETRIEVAL,
                            span_attribute=SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS,
                            collect_list=True,
                        )
                    }
                )
                .on_output()
            )

            f_answer_relevance = (
                Feedback(provider.relevance_with_cot_reasons, name="Answer Relevance")
                .on_input()
                .on_output()
            )

            f_context_relevance = (
                Feedback(provider.context_relevance_with_cot_reasons, name="Context Relevance")
                .on(
                    {
                        "question": Selector(
                            span_type=SpanAttributes.SpanType.RETRIEVAL,
                            span_attribute=SpanAttributes.RETRIEVAL.QUERY_TEXT,
                        )
                    }
                )
                .on(
                    {
                        "context": Selector(
                            span_type=SpanAttributes.SpanType.RETRIEVAL,
                            span_attribute=SpanAttributes.RETRIEVED_CONTEXTS,
                            collect_list=False,
                        )
                    }
                )
                .aggregate(np.mean)
            )

            return [f_answer_relevance, f_context_relevance, f_groundedness]
        except Exception as exc:
            logger.warning(f"Failed to build TruLens feedbacks: {exc}")
            return []

    @instrument(
        span_type=SpanAttributes.SpanType.RETRIEVAL,
        attributes={
            SpanAttributes.RETRIEVAL.QUERY_TEXT: "query",
            SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS: "selected_tools",
        },
    )
    def trace_tool_selection(self, query: str, selected_tools: List[str]) -> List[str]:
        """Trace tool selection as a retrieval-like span."""
        return selected_tools

    @instrument(
        span_type=SpanAttributes.SpanType.RETRIEVAL,
        attributes={
            SpanAttributes.RETRIEVAL.QUERY_TEXT: "query",
            SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS: "retrieved_contexts",
        },
    )
    def trace_retrieval_contexts(self, query: str, retrieved_contexts: List[str]) -> List[str]:
        """Trace retrieved contexts for RAG evaluation."""
        return retrieved_contexts

    @instrument(span_type=SpanAttributes.SpanType.GENERATION)
    def trace_tool_execution(
        self, tool_name: str, tool_input: Dict[str, Any], tool_output: Any
    ) -> Any:
        """Trace tool execution as a generation-like span."""
        _ = tool_name, tool_input
        return tool_output

    @instrument(
        span_type=SpanAttributes.SpanType.RECORD_ROOT,
        attributes={
            SpanAttributes.RECORD_ROOT.INPUT: "query",
            SpanAttributes.RECORD_ROOT.OUTPUT: "response",
            SpanAttributes.RECORD_ROOT.GROUND_TRUTH_OUTPUT: "ground_truth",
        },
    )
    def trace_agent_response(
        self, query: str, response: str, ground_truth: Optional[str] = None
    ) -> str:
        """Trace the agent response as the root span."""
        _ = ground_truth
        return response
    
    async def log_agent_execution(
        self,
        session_id: str,
        agent_type: str,
        query: str,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        *,
        selected_tools: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        retrieved_contexts: Optional[List[str]] = None,
        ground_truth: Optional[str] = None,
    ):
        """
        Log agent execution to TruLens.
        
        Args:
            session_id: Session identifier
            agent_type: Type of agent
            query: User query
            result: Agent result
            metadata: Optional metadata
            selected_tools: Tools chosen during planning/selection (if available)
            tool_calls: Tool call list (name/input/output), if available
            ground_truth: Expected answer for evaluations (if available)
        """
        try:
            if not self.enabled:
                return
            
            if not self.app_id or not self.api_key:
                logger.warning("TruLens credentials not configured, skipping logging")
                return
            
            logger.debug(f"Logging agent execution to TruLens: session={session_id}, agent={agent_type}")

            # Trace internal steps if provided
            if selected_tools:
                self.trace_tool_selection(query=query, selected_tools=selected_tools)

            if retrieved_contexts:
                self.trace_retrieval_contexts(query=query, retrieved_contexts=retrieved_contexts)

            for call in tool_calls or []:
                self.trace_tool_execution(
                    tool_name=str(call.get("tool_name", "unknown")),
                    tool_input=call.get("tool_input") or {},
                    tool_output=call.get("tool_output"),
                )

            # Trace the final response as the root span
            response_text = str(result.get("response", ""))
            self.trace_agent_response(query=query, response=response_text, ground_truth=ground_truth)
            
            # In production, this should use the TruLens SDK to register and export traces:
            # Example:
            # from trulens_eval import Tru
            # tru = Tru()
            # tru.add_record(
            #     app_id=self.app_id,
            #     input=query,
            #     output=result.get("response", ""),
            #     metadata={
            #         "session_id": session_id,
            #         "agent_type": agent_type,
            #         "sources": result.get("sources", []),
            #         **(metadata or {})
            #     }
            # )
            
            if self.eval_enabled:
                eval_context = {
                    "retrieved_contexts": retrieved_contexts or [],
                    "sources": result.get("sources", []),
                }
                eval_result = await self.evaluate_response(
                    query=query,
                    response=response_text,
                    context=eval_context,
                )
                result["trulens_eval"] = eval_result

            logger.debug(f"Logged to TruLens: session={session_id}")
            
        except Exception as e:
            logger.error(f"Error logging to TruLens: {str(e)}")
            # Don't raise - observability failures shouldn't break the main flow
            pass
    
    async def evaluate_response(
        self,
        query: str,
        response: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a response using TruLens.
        
        Args:
            query: Original query
            response: Agent response
            context: Optional context
        
        Returns:
            Evaluation results
        """
        try:
            if not self.enabled:
                return {"evaluated": False}
            
            logger.debug("Evaluating response with TruLens")
            
            if OpenAIProvider is None:
                return {"evaluated": False, "error": "TruLens provider not available"}

            provider = OpenAIProvider(model_engine=os.getenv("TRULENS_EVAL_MODEL", "gpt-4o"))
            retrieved_contexts = (context or {}).get("retrieved_contexts") or []

            answer_relevance = provider.relevance_with_cot_reasons(query, response)
            groundedness = provider.groundedness_measure_with_cot_reasons(retrieved_contexts, response)

            context_scores = []
            for ctx in retrieved_contexts:
                context_scores.append(provider.context_relevance_with_cot_reasons(query, ctx))
            context_relevance = float(sum(context_scores) / len(context_scores)) if context_scores else 0.0

            return {
                "evaluated": True,
                "answer_relevance": answer_relevance,
                "context_relevance": context_relevance,
                "groundedness": groundedness,
            }
            
        except Exception as e:
            logger.error(f"Error evaluating with TruLens: {str(e)}")
            return {"evaluated": False, "error": str(e)}

    def evaluate_agent_gpa(
        self,
        *,
        routing_accuracy: float,
        answer_relevance: float,
        context_relevance: float,
        groundedness: float,
        grounding_score: float,
        coverage_score: float,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Compute a GPA-style composite score over core agent evaluation metrics."""
        w = {
            "routing_accuracy": 0.25,
            "answer_relevance": 0.25,
            "context_relevance": 0.15,
            "groundedness": 0.20,
            "grounding_score": 0.15,
            "coverage_score": 0.15,
        }
        if weights:
            w.update({k: float(v) for k, v in weights.items()})
        total = sum(w.values()) or 1.0
        score = (
            routing_accuracy * w["routing_accuracy"]
            + answer_relevance * w["answer_relevance"]
            + context_relevance * w["context_relevance"]
            + groundedness * w["groundedness"]
            + grounding_score * w["grounding_score"]
            + coverage_score * w["coverage_score"]
        ) / total
        return {
            "gpa_score": round(score, 4),
            "weights": w,
        }
