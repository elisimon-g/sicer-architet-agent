from __future__ import annotations

import logging
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - startup guard for environments without MCP installed
    FastMCP = None

from sicer_architet_agent.analyzers.repository import profile_workspace
from sicer_architet_agent.graph import plan_multimodule_change as build_change_plan

LOGGER = logging.getLogger(__name__)
mcp = FastMCP("sicer-architet-agent") if FastMCP is not None else None


def _ensure_server() -> None:
    if mcp is None:
        raise RuntimeError(
            "The MCP SDK is not installed. Install project dependencies before starting the MCP server."
        )


def detect_project_type(workspace_path: str = ".") -> str:
    """Inspect a workspace and summarize its dominant architectural signals.

    Args:
        workspace_path: Absolute or relative path to the workspace root.
    """
    profile = profile_workspace(Path(workspace_path).resolve())
    return profile.to_markdown()


def list_modules(workspace_path: str = ".") -> str:
    """List Maven modules, packaging, dependencies, and quick indicators.

    Args:
        workspace_path: Absolute or relative path to the workspace root.
    """
    profile = profile_workspace(Path(workspace_path).resolve())
    if not profile.modules:
        return f"No Maven modules found in `{profile.workspace_path}`."
    return profile.to_markdown()


def plan_multimodule_change(request: str, workspace_path: str = ".") -> str:
    """Create a safe multi-module change plan for a requested modification.

    Args:
        request: Natural-language description of the desired change.
        workspace_path: Absolute or relative path to the workspace root.
    """
    plan = build_change_plan(str(Path(workspace_path).resolve()), request)
    return plan.to_markdown()


if mcp is not None:
    mcp.tool()(detect_project_type)
    mcp.tool()(list_modules)
    mcp.tool()(plan_multimodule_change)


def main() -> None:
    _ensure_server()
    logging.basicConfig(level=logging.INFO)
    LOGGER.info("Starting sicer-architet-agent MCP server")
    assert mcp is not None
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
