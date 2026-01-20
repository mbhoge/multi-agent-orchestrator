# Routing strategies (Deprecated)

**Status:** Deprecated. The supervisor has moved to a **planner‑only** flow where an LLM
planner and executor decide which agent(s) to run. The old routing policies are no longer
used in the main graph.

The previous routing strategies remain in the codebase for reference:
- `langgraph/supervisor/policies/optimized_router.py`
- `langgraph/supervisor/policies/handoffs.py`

If you want to restore policy‑based routing, you would need to re‑introduce the
`route_request` node into the StateGraph and rewire the edges accordingly.

---

## Current approach (planner‑only)

The planner/executor flow replaces routing policies:
- **Planner**: generates a numbered plan with assigned agents
- **Executor**: selects the next agent + agent query and produces a routing decision

See:
- `langgraph/supervisor/planning.py`
- `langgraph/supervisor/llm_client.py`
- `langgraph/supervisor/graph.py`

