"""Render the LangGraph supervisor graph to a Mermaid PNG."""

from __future__ import annotations

import argparse
from pathlib import Path

import importlib.util
import sys
import types


def _load_local_submodule(module_name: str, file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _ensure_pkg(module_name: str) -> None:
    if module_name in sys.modules:
        return
    pkg = types.ModuleType(module_name)
    pkg.__path__ = []  # mark as package
    sys.modules[module_name] = pkg


def _load_supervisor_graph_module() -> Any:
    """Load local supervisor modules as submodules of the external langgraph package."""
    repo_root = Path(__file__).resolve().parents[1]
    local_state = repo_root / "langgraph" / "state" / "graph_state.py"
    local_planning = repo_root / "langgraph" / "supervisor" / "planning.py"
    local_llm_client = repo_root / "langgraph" / "supervisor" / "llm_client.py"
    local_short_term = repo_root / "langgraph" / "memory" / "short_term.py"
    local_long_term = repo_root / "langgraph" / "memory" / "long_term.py"
    local_langfuse_client = repo_root / "langgraph" / "observability" / "langfuse_client.py"
    local_graph = repo_root / "langgraph" / "supervisor" / "graph.py"

    # Ensure external langgraph package is imported first (avoid local shadowing)
    original_sys_path = list(sys.path)
    sys.path = [p for p in sys.path if Path(p).resolve() not in {repo_root, repo_root / "scripts"}]
    __import__("langgraph")
    try:
        import langgraph.graph as external_graph
        if not hasattr(external_graph, "START"):
            external_graph.START = "__start__"
    except Exception:
        pass
    sys.path = original_sys_path

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Register local subpackages
    _ensure_pkg("langgraph.state")
    _ensure_pkg("langgraph.supervisor")
    _ensure_pkg("langgraph.memory")
    _ensure_pkg("langgraph.observability")

    _load_local_submodule("langgraph.state.graph_state", local_state)
    _load_local_submodule("langgraph.memory.short_term", local_short_term)
    _load_local_submodule("langgraph.memory.long_term", local_long_term)
    _load_local_submodule("langgraph.observability.langfuse_client", local_langfuse_client)
    _load_local_submodule("langgraph.supervisor.llm_client", local_llm_client)
    _load_local_submodule("langgraph.supervisor.planning", local_planning)
    return _load_local_submodule("langgraph.supervisor.graph", local_graph)


def render_graph_png(output_path: Path) -> None:
    supervisor_graph = _load_supervisor_graph_module()
    graph = supervisor_graph.create_supervisor_graph()
    compiled = graph.get_graph()
    png_bytes = compiled.draw_mermaid_png()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png_bytes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render supervisor graph as Mermaid PNG.")
    parser.add_argument(
        "--output",
        default="docs/supervisor_graph.png",
        help="Output PNG path (default: docs/supervisor_graph.png)",
    )
    args = parser.parse_args()

    render_graph_png(Path(args.output))


if __name__ == "__main__":
    main()
