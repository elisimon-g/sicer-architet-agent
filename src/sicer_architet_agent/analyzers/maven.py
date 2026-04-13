from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from sicer_architet_agent.models import ModuleInfo

MAVEN_NS = {"m": "http://maven.apache.org/POM/4.0.0"}


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def parse_xml(path: Path) -> ElementTree.Element:
    return ElementTree.fromstring(_read_text(path))


def _find_text(root: ElementTree.Element, query: str) -> str | None:
    element = root.find(query, MAVEN_NS)
    if element is None or element.text is None:
        return None
    return element.text.strip()


def _find_all_text(root: ElementTree.Element, query: str) -> list[str]:
    return [
        element.text.strip()
        for element in root.findall(query, MAVEN_NS)
        if element.text and element.text.strip()
    ]


def parse_pom(path: Path) -> dict[str, object]:
    root = parse_xml(path)
    artifact_id = _find_text(root, "m:artifactId") or path.parent.name
    packaging = _find_text(root, "m:packaging") or "jar"
    modules = _find_all_text(root, "m:modules/m:module")
    dependencies = _find_all_text(root, "m:dependencies/m:dependency/m:artifactId")
    return {
        "artifact_id": artifact_id,
        "packaging": packaging,
        "modules": modules,
        "dependencies": dependencies,
    }


def gather_maven_modules(workspace_path: Path) -> list[ModuleInfo]:
    root_pom = workspace_path / "pom.xml"
    if not root_pom.exists():
        return []

    root_data = parse_pom(root_pom)
    modules: list[ModuleInfo] = []

    for module_name in root_data["modules"]:
        module_path = workspace_path / module_name
        module_pom = module_path / "pom.xml"
        if not module_pom.exists():
            modules.append(
                ModuleInfo(name=module_name, path=str(module_path), packaging="unknown", dependencies=[])
            )
            continue

        module_data = parse_pom(module_pom)
        modules.append(
            ModuleInfo(
                name=str(module_data["artifact_id"]),
                path=str(module_path),
                packaging=str(module_data["packaging"]),
                dependencies=[str(item) for item in module_data["dependencies"]],
            )
        )

    return modules
