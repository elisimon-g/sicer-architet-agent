from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ModuleInfo:
    name: str
    path: str
    packaging: str = "jar"
    dependencies: list[str] = field(default_factory=list)
    indicators: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkspaceProfile:
    workspace_path: str
    project_type: str
    build_files: list[str] = field(default_factory=list)
    indicators: list[str] = field(default_factory=list)
    modules: list[ModuleInfo] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            f"**Workspace:** `{self.workspace_path}`",
            f"**Project type:** {self.project_type}",
        ]
        if self.build_files:
            lines.append(f"**Build files:** {', '.join(f'`{item}`' for item in self.build_files)}")
        if self.indicators:
            lines.append(f"**Signals:** {', '.join(self.indicators)}")
        if self.modules:
            lines.append("")
            lines.append("**Modules**")
            for module in self.modules:
                deps = ", ".join(module.dependencies) if module.dependencies else "-"
                indicators = ", ".join(module.indicators) if module.indicators else "-"
                lines.append(
                    f"- `{module.name}` ({module.packaging}) at `{module.path}` | deps: {deps} | signals: {indicators}"
                )
        return "\n".join(lines)


@dataclass(slots=True)
class ChangePlan:
    request: str
    primary_module: str
    secondary_modules: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    files_to_read: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    rationale: str = ""

    def to_markdown(self) -> str:
        lines = [
            f"**Request:** {self.request}",
            f"**Primary module:** `{self.primary_module}`",
        ]
        if self.secondary_modules:
            lines.append(
                f"**Secondary modules:** {', '.join(f'`{item}`' for item in self.secondary_modules)}"
            )
        if self.rationale:
            lines.append(f"**Why this module first:** {self.rationale}")
        if self.entry_points:
            lines.append("")
            lines.append("**Entry points**")
            for item in self.entry_points:
                lines.append(f"- `{item}`")
        if self.files_to_read:
            lines.append("")
            lines.append("**Candidate files to inspect**")
            for item in self.files_to_read:
                lines.append(f"- `{item}`")
        if self.risks:
            lines.append("")
            lines.append("**Risks**")
            for item in self.risks:
                lines.append(f"- {item}")
        if self.steps:
            lines.append("")
            lines.append("**Recommended order**")
            for index, item in enumerate(self.steps, start=1):
                lines.append(f"{index}. {item}")
        return "\n".join(lines)

