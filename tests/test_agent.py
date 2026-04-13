from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from sicer_architet_agent.analyzers.repository import profile_workspace
from sicer_architet_agent.graph import plan_multimodule_change


ROOT_POM = """\
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>demo</groupId>
  <artifactId>root</artifactId>
  <packaging>pom</packaging>
  <modules>
    <module>Sicer</module>
    <module>JBFReporting</module>
  </modules>
</project>
"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


class AgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        write_file(self.root / "pom.xml", ROOT_POM)
        write_file(
            self.root / "Sicer/pom.xml",
            """\
            <project xmlns="http://maven.apache.org/POM/4.0.0"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
              <modelVersion>4.0.0</modelVersion>
              <artifactId>Sicer</artifactId>
              <packaging>jar</packaging>
            </project>
            """,
        )
        write_file(
            self.root / "Sicer/src/main/java/demo/CompensazioneService.java",
            "class CompensazioneService {}\n",
        )
        write_file(
            self.root / "JBFReporting/pom.xml",
            """\
            <project xmlns="http://maven.apache.org/POM/4.0.0"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
              <modelVersion>4.0.0</modelVersion>
              <artifactId>JBFReporting</artifactId>
              <packaging>jar</packaging>
            </project>
            """,
        )
        write_file(
            self.root / "JBFReporting/src/main/resources/reports/bilancio.jrxml",
            "<jasperReport/>\n",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_profiles_maven_workspace(self) -> None:
        profile = profile_workspace(self.root)
        self.assertEqual(profile.project_type, "maven-multi-module")
        self.assertEqual([module.name for module in profile.modules], ["Sicer", "JBFReporting"])

    def test_plan_prefers_reporting_module_for_report_request(self) -> None:
        plan = plan_multimodule_change(str(self.root), "aggiungi un report pdf di bilancio")
        self.assertEqual(plan.primary_module, "JBFReporting")
        self.assertTrue(any(item.endswith(".jrxml") for item in plan.files_to_read))


if __name__ == "__main__":
    unittest.main()
