from __future__ import annotations

from pathlib import Path

from sicer_architet_agent.analyzers.maven import gather_maven_modules
from sicer_architet_agent.models import ModuleInfo, WorkspaceProfile


def _module_indicators(module_path: Path) -> list[str]:
    indicators: list[str] = []
    if (module_path / "src/main/java").exists():
        indicators.append("java")
    if (module_path / "src/main/resources").exists():
        indicators.append("resources")
    if (module_path / "src/main/webapp").exists():
        indicators.append("webapp")
    if (module_path / "src/test").exists():
        indicators.append("tests")
    if any(module_path.rglob("*.jrxml")):
        indicators.append("reporting")
    if any(module_path.rglob("*.jsp")):
        indicators.append("jsp")
    if (module_path / "package.json").exists() or (module_path / "angular.json").exists():
        indicators.append("frontend")
    if any(module_path.rglob("*Controller.java")) or any(module_path.rglob("*RC.java")):
        indicators.append("rest")
    return indicators


def _workspace_indicators(workspace_path: Path) -> tuple[str, list[str], list[str]]:
    build_files: list[str] = []
    indicators: list[str] = []

    if (workspace_path / "pom.xml").exists():
        build_files.append("pom.xml")
        indicators.append("maven")
    if any(workspace_path.glob("**/package.json")):
        build_files.append("package.json")
        indicators.append("node")
    if any(workspace_path.glob("**/*.jsp")):
        indicators.append("jsp")
    if any(workspace_path.glob("**/*.jrxml")):
        indicators.append("reporting")
    if any(workspace_path.glob("**/*Controller.java")) or any(workspace_path.glob("**/*RC.java")):
        indicators.append("spring-like-rest")

    indicators = sorted(set(indicators))
    build_files = sorted(set(build_files))

    if "maven" in indicators and len(list(workspace_path.glob("*/pom.xml"))) > 1:
        project_type = "maven-multi-module"
    elif "maven" in indicators:
        project_type = "maven-single-module"
    elif "node" in indicators:
        project_type = "node-workspace"
    else:
        project_type = "generic-codebase"

    return project_type, build_files, indicators


def profile_workspace(workspace_path: str | Path) -> WorkspaceProfile:
    workspace = Path(workspace_path).resolve()
    project_type, build_files, indicators = _workspace_indicators(workspace)
    modules = gather_maven_modules(workspace)

    enriched_modules: list[ModuleInfo] = []
    for module in modules:
        module_path = Path(module.path)
        enriched_modules.append(
            ModuleInfo(
                name=module.name,
                path=module.path,
                packaging=module.packaging,
                dependencies=module.dependencies,
                indicators=_module_indicators(module_path),
            )
        )

    return WorkspaceProfile(
        workspace_path=str(workspace),
        project_type=project_type,
        build_files=build_files,
        indicators=indicators,
        modules=enriched_modules,
    )
