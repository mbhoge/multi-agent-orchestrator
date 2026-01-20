"""Planner/executor prompt helpers and agent descriptions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

MAX_REPLANS = 2


def _load_agent_registry() -> List[Dict[str, Any]]:
    repo_root = Path(__file__).resolve().parents[2]
    agents_path = repo_root / "config" / "agents.yaml"
    if not agents_path.exists():
        return []
    data = yaml.safe_load(agents_path.read_text()) or {}
    return data.get("agents", []) or []


def get_agent_descriptions() -> Dict[str, Dict[str, Any]]:
    """Return structured agent descriptions from config/agents.yaml."""
    descriptions: Dict[str, Dict[str, Any]] = {}
    for agent in _load_agent_registry():
        if not isinstance(agent, dict) or not agent.get("enabled", True):
            continue
        agent_name = agent.get("agent_name")
        if not agent_name:
            continue
        descriptions[str(agent_name)] = {
            "name": str(agent_name),
            "capability": agent.get("description") or f"Domain agent for {agent.get('domain')}",
            "use_when": f"Queries related to {agent.get('domain')}",
            "limitations": "Limited to configured Snowflake Cortex domain and tools.",
            "output_format": "Structured or textual response with sources when available.",
        }
    return descriptions


def _get_enabled_agents(state: Optional[Dict[str, Any]] = None) -> List[str]:
    """Return enabled agents from state or fall back to all domain agents."""
    descriptions = get_agent_descriptions()
    baseline = list(descriptions.keys())
    if not state:
        return baseline
    val = state.get("enabled_agents")
    if isinstance(val, list) and val:
        allowed = set(descriptions.keys())
        return [a for a in val if a in allowed]
    return baseline


def format_agent_list_for_planning(state: Optional[Dict[str, Any]] = None) -> str:
    """Format agent descriptions for the planning prompt."""
    descriptions = get_agent_descriptions()
    enabled_list = _get_enabled_agents(state)
    agent_list = []
    for agent_key in enabled_list:
        details = descriptions.get(agent_key, {})
        agent_list.append(f"  - `{agent_key}`: {details.get('capability', '')}".strip())
    return "\n".join(agent_list)


def format_agent_guidelines_for_planning(state: Optional[Dict[str, Any]] = None) -> str:
    """Format agent usage guidelines for the planning prompt."""
    descriptions = get_agent_descriptions()
    enabled = set(_get_enabled_agents(state))
    guidelines = []
    for agent_key in enabled:
        details = descriptions.get(agent_key, {})
        use_when = details.get("use_when", "it is relevant")
        guidelines.append(f"- Use `{agent_key}` when {use_when.lower()}.")
    return "\n".join(guidelines)


def format_agent_guidelines_for_executor(state: Optional[Dict[str, Any]] = None) -> str:
    """Format agent usage guidelines for the executor prompt."""
    return format_agent_guidelines_for_planning(state)


def plan_prompt(state: Dict[str, Any]) -> str:
    """Build the prompt that instructs the LLM to return a high-level plan."""
    replan_flag = state.get("replan_flag", False)
    user_query = state.get("user_query", state.get("query", ""))
    prior_plan = state.get("plan") or {}
    replan_reason = state.get("last_reason", "")

    agent_list = format_agent_list_for_planning(state)
    agent_guidelines = format_agent_guidelines_for_planning(state)
    enabled_list = _get_enabled_agents(state)
    planner_agent_enum = " | ".join(enabled_list) if enabled_list else "agent"

    prompt = f"""
You are the Planner in a multi-agent system. Break the user's request into a sequence
of numbered steps (1, 2, 3, ...). Each step has a clear action and a single assigned agent.

Available agents:
{agent_list}

Return ONLY valid JSON (no markdown, no explanations) in this form:
{{
  "1": {{
    "agent": "{planner_agent_enum}",
    "action": "string"
  }},
  "2": {{ ... }}
}}

Guidelines:
{agent_guidelines}
""".strip()

    if replan_flag:
        prompt += f"""

The current plan needs revision because: {replan_reason}

Current plan:
{json.dumps(prior_plan, indent=2)}

When replanning:
- Focus on unblocking the workflow.
- Only modify steps that prevent progress.
""".strip()
    else:
        prompt += "\nGenerate a new plan from scratch."

    prompt += f'\nUser query: "{user_query}"'
    return prompt


def executor_prompt(state: Dict[str, Any]) -> str:
    """Build the single-turn JSON prompt that drives the executor."""
    step = int(state.get("plan_current_step", 1))
    latest_plan: Dict[str, Any] = state.get("plan") or {}
    plan_block: Dict[str, Any] = latest_plan.get(str(step), {})
    attempts = (state.get("replan_attempts", {}) or {}).get(step, 0)

    executor_guidelines = format_agent_guidelines_for_executor(state)
    enabled_agents = _get_enabled_agents(state)
    plan_agent = plan_block.get("agent", enabled_agents[0] if enabled_agents else "agent")

    prompt = f"""
You are the executor in a multi-agent system with agents: {", ".join(enabled_agents)}.

Tasks:
1. Decide if the current plan needs revision -> "replan": true|false
2. Decide which agent to run next -> "goto": "<agent_name>"
3. Give one-sentence justification -> "reason": "<text>"
4. Write the exact question that the chosen agent should answer -> "query": "<text>"

Guidelines:
{executor_guidelines}
- After {MAX_REPLANS} replans for the same step, move on.

Respond ONLY with valid JSON:
{{
  "replan": true|false,
  "goto": "<{' | '.join(enabled_agents) if enabled_agents else 'agent'}>",
  "reason": "<1 sentence>",
  "query": "<text>"
}}

Context:
- User query: {state.get("user_query")}
- Current step: {step}
- Current plan step: {plan_block}
- Attempts: {attempts}
- Just-replanned: {state.get("replan_flag")}
- Assigned agent: {plan_agent}
""".strip()

    return prompt


def agent_system_prompt(suffix: str) -> str:
    """Base system prompt for agent execution."""
    return (
        "You are a helpful AI assistant, collaborating with other assistants. "
        "Use the provided tools to progress towards answering the question. "
        "If you are unable to fully answer, that's OK; another assistant can continue. "
        "If you have the final answer or deliverable, prefix your response with FINAL ANSWER.\n"
        f"{suffix}"
    )
