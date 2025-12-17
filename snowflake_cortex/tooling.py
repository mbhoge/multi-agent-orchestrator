"""Helpers for Snowflake Cortex Agents Run tool configuration.

These helpers are used when calling `POST /api/v2/cortex/agent:run` (no agent object)
and you want to provide tool specs/resources in the request body.

Reference: `https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run#toolresource`
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def tool_choice_auto(names: Optional[List[str]] = None) -> Dict[str, Any]:
    """Build a ToolChoice with automatic selection, optionally constrained to tool names."""
    tc: Dict[str, Any] = {"type": "auto"}
    if names:
        tc["name"] = names
    return tc


def tool_spec_generic(
    *,
    name: str,
    description: str,
    input_schema: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a generic ToolSpec."""
    return {
        "type": "generic",
        "name": name,
        "description": description,
        "input_schema": input_schema,
    }


def tool_resource_cortex_analyst_text_to_sql(
    *,
    semantic_model_file: Optional[str] = None,
    semantic_view: Optional[str] = None,
    warehouse: Optional[str] = None,
    query_timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """Build a ToolResource for cortex_analyst_text_to_sql.

    Exactly one of semantic_model_file or semantic_view should be provided (Snowflake requirement).
    """
    resource: Dict[str, Any] = {}
    if semantic_model_file:
        resource["semantic_model_file"] = semantic_model_file
    if semantic_view:
        resource["semantic_view"] = semantic_view
    if warehouse or query_timeout is not None:
        env: Dict[str, Any] = {"type": "warehouse"}
        if warehouse:
            env["warehouse"] = warehouse
        if query_timeout is not None:
            env["query_timeout"] = int(query_timeout)
        resource["execution_environment"] = env
    return resource


def tool_resource_cortex_search(
    *,
    search_service: str,
    title_column: Optional[str] = None,
    id_column: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a ToolResource for cortex_search."""
    resource: Dict[str, Any] = {"search_service": search_service}
    if title_column:
        resource["title_column"] = title_column
    if id_column:
        resource["id_column"] = id_column
    if filter is not None:
        resource["filter"] = filter
    return resource


