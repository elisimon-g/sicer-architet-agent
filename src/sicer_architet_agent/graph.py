from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, TypedDict

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - exercised only in environments without langgraph
    START = "__start__"
    END = "__end__"

    class _CompiledGraph:
        def __init__(self, nodes: dict[str, Callable], edges: dict[str, str]) -> None:
            self._nodes = nodes
            self._edges = edges

        def invoke(self, state: dict) -> dict:
            current = self._edges[START]
            result = dict(state)
            while current != END:
                update = self._nodes[current](result)
                result.update(update)
                current = self._edges[current]
            return result

    class StateGraph:  # type: ignore[override]
        def __init__(self, _state_type: object) -> None:
            self._nodes: dict[str, Callable] = {}
            self._edges: dict[str, str] = {}

        def add_node(self, name: str, fn: Callable) -> None:
            self._nodes[name] = fn

        def add_edge(self, source: str, target: str) -> None:
            self._edges[source] = target

        def compile(self) -> _CompiledGraph:
            return _CompiledGraph(self._nodes, self._edges)

from sicer_architet_agent.analyzers.repository import profile_workspace
from sicer_architet_agent.models import ChangePlan, ModuleInfo, WorkspaceProfile


class PlannerState(TypedDict, total=False):
    workspace_path: str
    request: str
    profile: WorkspaceProfile
    primary_module: str
    secondary_modules: list[str]
    entry_points: list[str]
    files_to_read: list[str]
    risks: list[str]
    steps: list[str]
    rationale: str


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_-]+", text.lower()) if len(token) > 2}


def _score_module(module: ModuleInfo, tokens: set[str]) -> int:
    score = 0
    lowered_name = module.name.lower()
    for token in tokens:
        if token in lowered_name:
            score += 5
        if token in module.path.lower():
            score += 3

    indicators = set(module.indicators)
    semantic_map = {
        "reporting": {"report", "pdf", "excel", "jrxml", "jasper"},
        "frontend": {"frontend", "angular", "ui", "typescript"},
        "rest": {"rest", "api", "json", "endpoint", "controller"},
        "webapp": {"jsp", "web", "war", "servlet"},
        "java": {"java", "service", "dao", "business", "batch"},
    }

    for indicator, words in semantic_map.items():
        if indicator in indicators and tokens.intersection(words):
            score += 6

    if module.name in {"Sicer", "sicer-lib", "PSGLib"} and score == 0:
        score += 1

    return score


def _inspect_workspace(state: PlannerState) -> PlannerState:
    return {"profile": profile_workspace(state["workspace_path"])}


def _select_modules(state: PlannerState) -> PlannerState:
    profile = state["profile"]
    tokens = _tokenize(state["request"])

    ranked = sorted(
        ((module, _score_module(module, tokens)) for module in profile.modules),
        key=lambda item: item[1],
        reverse=True,
    )

    if not ranked:
        return {
            "primary_module": ".",
            "secondary_modules": [],
            "rationale": "No Maven modules were detected, so the workspace root is the safest starting point.",
        }

    primary_module = ranked[0][0]
    secondary = [module.name for module, score in ranked[1:4] if score > 0]

    for dependency in primary_module.dependencies:
        if dependency not in secondary and any(module.name == dependency for module in profile.modules):
            secondary.append(dependency)

    rationale = (
        f"`{primary_module.name}` scored highest from request keywords and repository signals "
        f"({', '.join(primary_module.indicators) or 'generic module'})."
    )
    return {
        "primary_module": primary_module.name,
        "secondary_modules": secondary[:4],
        "rationale": rationale,
    }


def _find_module(profile: WorkspaceProfile, module_name: str) -> ModuleInfo | None:
    for module in profile.modules:
        if module.name == module_name:
            return module
    return None


def _candidate_paths(module: ModuleInfo, tokens: set[str]) -> list[str]:
    module_path = Path(module.path)
    candidates = [module_path / "pom.xml"]
    conventional_paths = [
        module_path / "src/main/java",
        module_path / "src/main/resources",
        module_path / "src/main/webapp",
    ]
    for path in conventional_paths:
        if path.exists():
            candidates.append(path)

    search_extensions = {".java", ".xml", ".jrxml", ".jsp", ".properties", ".yml", ".yaml", ".ts", ".js"}
    for file_path in module_path.rglob("*"):
        if len(candidates) >= 10:
            break
        if not file_path.is_file() or file_path.suffix.lower() not in search_extensions:
            continue
        lowered = file_path.name.lower()
        if any(token in lowered for token in tokens):
            candidates.append(file_path)

    unique_candidates: list[str] = []
    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate_str not in unique_candidates:
            unique_candidates.append(candidate_str)
    return unique_candidates[:10]


def _build_plan(state: PlannerState) -> PlannerState:
    profile = state["profile"]
    primary_name = state["primary_module"]
    primary_module = _find_module(profile, primary_name)
    tokens = _tokenize(state["request"])

    if primary_module is None:
        return {
            "entry_points": [],
            "files_to_read": [],
            "risks": ["The selected primary module was not found during plan generation."],
            "steps": ["Re-run module discovery before editing code."],
        }

    entry_points = []
    for indicator in primary_module.indicators:
        if indicator == "rest":
            entry_points.append(f"{primary_module.path}/src/main/java/**/*Controller.java")
        elif indicator == "webapp":
            entry_points.append(f"{primary_module.path}/src/main/webapp")
        elif indicator == "reporting":
            entry_points.append(f"{primary_module.path}/src/main/resources/**/*.jrxml")
        elif indicator == "java":
            entry_points.append(f"{primary_module.path}/src/main/java")

    files_to_read = _candidate_paths(primary_module, tokens)
    risks = [
        "Shared-library changes can propagate across multiple Maven modules.",
        "Legacy XML, JSP, or report assets may hide coupling outside Java packages.",
    ]
    if state.get("secondary_modules"):
        risks.append("Cross-module changes should be validated in dependency order to avoid partial regressions.")

    steps = [
        f"Inspect `{primary_module.name}` first and confirm the entry point against the requested change.",
        "Read the candidate files and identify the narrowest business boundary to update.",
        "Review secondary modules before editing shared contracts, resources, or packaging descriptors.",
        "Apply the change in dependency-safe order, starting from shared/core modules and ending at delivery modules.",
        "Run targeted validation for the touched modules before broad workspace verification.",
    ]

    return {
        "entry_points": entry_points or [f"{primary_module.path}/src/main"],
        "files_to_read": files_to_read,
        "risks": risks,
        "steps": steps,
    }


def build_change_planner():
    graph = StateGraph(PlannerState)
    graph.add_node("inspect_workspace", _inspect_workspace)
    graph.add_node("select_modules", _select_modules)
    graph.add_node("build_plan", _build_plan)
    graph.add_edge(START, "inspect_workspace")
    graph.add_edge("inspect_workspace", "select_modules")
    graph.add_edge("select_modules", "build_plan")
    graph.add_edge("build_plan", END)
    return graph.compile()


def plan_multimodule_change(workspace_path: str, request: str) -> ChangePlan:
    planner = build_change_planner()
    result = planner.invoke({"workspace_path": workspace_path, "request": request})
    return ChangePlan(
        request=request,
        primary_module=result["primary_module"],
        secondary_modules=result.get("secondary_modules", []),
        entry_points=result.get("entry_points", []),
        files_to_read=result.get("files_to_read", []),
        risks=result.get("risks", []),
        steps=result.get("steps", []),
        rationale=result.get("rationale", ""),
    )
