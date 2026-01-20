## TruLens Tracing and Evaluation (OTel)

This document describes the refactored tracing and evaluation flow for Snowflake
Cortex AI agents. It uses TruLens OpenTelemetry instrumentation and RAG‑Triad
feedback functions to evaluate agent performance.

### Overview

The tracing/evaluation pipeline consists of:
- **Tracing**: OTel spans emitted for tool selection, retrieval contexts, tool execution,
  and final response.
- **Evaluation**: RAG‑Triad metrics (answer relevance, context relevance, groundedness).
- **Storage**: TruLens session storage via SQLite (configurable).

### Environment variables

Set these to enable tracing and evaluation:

```bash
TRULENS_ENABLED=true
TRULENS_OTEL_TRACING=1
TRULENS_EVAL_ENABLED=true
TRULENS_EVAL_MODEL=gpt-4o
TRULENS_DB_URL=sqlite:///trulens.sqlite
PLANNER_LLM_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
PLANNER_LLM_REGION=us-east-1
```

### Instrumented spans

The `TruLensClient` emits spans using `@instrument`:
- **Tool selection** (`SpanType.RETRIEVAL`)
  - `RETRIEVAL.QUERY_TEXT`
  - `RETRIEVAL.RETRIEVED_CONTEXTS` (selected tools)
- **Retrieval contexts** (`SpanType.RETRIEVAL`)
  - `RETRIEVAL.QUERY_TEXT`
  - `RETRIEVAL.RETRIEVED_CONTEXTS` (retrieved text snippets)
- **Tool execution** (`SpanType.GENERATION`)
- **Final response** (`SpanType.RECORD_ROOT`)
  - `RECORD_ROOT.INPUT`
  - `RECORD_ROOT.OUTPUT`
  - `RECORD_ROOT.GROUND_TRUTH_OUTPUT` (if provided)

### RAG‑Triad evaluation

When `TRULENS_EVAL_ENABLED=true`, evaluations run for each agent response:

- **Answer relevance**: query vs final response
- **Context relevance**: query vs each retrieved context
- **Groundedness**: final response vs retrieved contexts

These are computed in `TruLensClient.evaluate_response(...)` using a TruLens provider.

### Execution flow

1. The Cortex agent runs via the gateway.
2. SSE tool calls are parsed to extract retrieved contexts.
3. `TruLensClient.log_agent_execution(...)` traces tool selection, retrieval contexts,
   tool execution, and final response.
4. `evaluate_response(...)` computes RAG‑Triad metrics and attaches the results to
   the agent response payload as `trulens_eval`.

### How to pass ground truth

If you have golden responses for evaluation, pass one of these keys in `context`:
`ground_truth`, `expected_response`, or `golden_response`. The value is traced as
`RECORD_ROOT.GROUND_TRUTH_OUTPUT`.

### References

- Snowflake AI Observability: Evaluate AI Applications  
  https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability/evaluate-ai-applications
- TruLens (Open Source)  
  https://github.com/truera/trulens
- Agent GPA framework overview  
  https://www.snowflake.com/en/engineering-blog/ai-agent-evaluation-gpa-framework/
