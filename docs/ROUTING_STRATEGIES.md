# Routing strategies (Strategy + config flag)

This repository supports **multiple routing behaviors** (aka “policies” / “strategies”) **in a single codebase**.

The goal is to keep:
- the **LangGraph supervisor workflow** stable (load state → route → invoke → combine → memory → observability)
- while letting you **swap only the routing logic** at runtime for clean A/B testing (especially for low latency chat in Teams).

The implementation lives in:
- `langgraph/supervisor/policies/`

---

## What changes between strategies?

Only **how we decide `routing_decision`** (which Snowflake agent(s) to call).

Everything else is shared:
- state schema (`langgraph/state/graph_state.py`)
- memory (`langgraph/memory/*`)
- agent invocation (`invoke_agents`)
- response synthesis (`combine_responses`)
- observability (`langfuse_client`)

---

## Available strategies

### 1) `optimized_router` (default)

**Best when**: you want Router-style behavior, but need lower latency for chat.

Behavior:
- Uses router selection to pick agent(s)
- **Follow-up reuse**: for likely follow-up turns, it **reuses the previous routing decision**
- **Per-session cache**: for identical queries, it **reuses cached routing**

Code: `langgraph/supervisor/policies/optimized_router.py`

### 2) `handoffs`

**Best when**: you have a conversational UI (Teams) with lots of follow-ups and want
to **skip routing calls** when possible.

Behavior:
- Maintains an **`active_agent`** in short-term memory for the session
- For likely follow-ups, routes directly to `active_agent` (**handoff**)
- If the user explicitly requests an agent/domain, it re-routes and updates `active_agent`

Code: `langgraph/supervisor/policies/handoffs.py`

---

## Configuration

All settings are under the `LANGGRAPH_` prefix (see `shared/config/settings.py`).

### Select a routing mode

Set one of:
- `LANGGRAPH_ROUTING_MODE=optimized_router`
- `LANGGRAPH_ROUTING_MODE=handoffs`

### Optimization knobs

These work as standard environment variables (all optional):

- `LANGGRAPH_ROUTING_FOLLOWUP_REUSE_ENABLED=true|false`  
  Enables the follow-up reuse fast-path (used by `optimized_router`).

- `LANGGRAPH_ROUTING_CACHE_TTL_SECONDS=300`  
  TTL for per-session cache entries (used by `optimized_router`).

- `LANGGRAPH_HANDOFFS_ACTIVE_AGENT_TTL_SECONDS=3600`  
  TTL for `active_agent` memory (used by `handoffs`).

> Note: `.env.example` may be filtered by your tooling. Even if you can’t edit it,
> these env vars still work in Docker Compose, Lambda env vars, or your shell.

---

## How the supervisor uses the strategy

The supervisor’s `route_request` node calls the selected policy via:
- `langgraph/supervisor/policies/factory.py` → `get_routing_policy()`

Key design detail:
- The policy receives an async callback `render_routing_prompt()`.
- This allows the policy to **skip prompt rendering / routing calls** for follow-ups,
  which is important for meeting strict latency targets.

---

## Unit testing

### Run only routing policy unit tests

```bash
pytest -q tests/unit/test_routing_policies.py
```

### Run all unit tests

```bash
pytest -q tests/unit
```

### What the tests assert

`tests/unit/test_routing_policies.py` verifies that:
- `optimized_router`:
  - reuses prior routing decisions for follow-ups (no prompt render)
  - reuses cached routing for identical queries (no prompt render)
- `handoffs`:
  - uses `active_agent` for follow-ups (no prompt render)
  - re-routes when `agent_preference` is present and updates `active_agent`

### Test isolation note

Short-term memory is a **global singleton** (`langgraph/memory/short_term.py`).
The tests clear the session’s memory before/after each test to prevent cross-test interference.

