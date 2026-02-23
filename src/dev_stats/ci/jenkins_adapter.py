"""Jenkins CI adapter producing JUnit XML reports."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from dev_stats.ci.abstract_ci_adapter import AbstractCIAdapter
from dev_stats.ci.violation import ViolationSeverity

if TYPE_CHECKING:
    from pathlib import Path


class JenkinsAdapter(AbstractCIAdapter):
    """Produces JUnit XML compatible with Jenkins test result ingestion.

    Each violation becomes a ``<testcase>`` with a ``<failure>`` element
    inside a ``<testsuite>`` named ``dev-stats``.
    """

    def emit(self) -> str:
        """Emit violations as JUnit XML string.

        Returns:
            JUnit XML string with testsuites/testsuite/testcase elements.
        """
        violations = self._violations
        root = ET.Element("testsuites")

        suite = ET.SubElement(root, "testsuite")
        suite.set("name", "dev-stats")
        suite.set("tests", str(len(violations)))
        suite.set(
            "failures",
            str(sum(1 for v in violations if v.severity == ViolationSeverity.ERROR)),
        )
        suite.set(
            "warnings",
            str(sum(1 for v in violations if v.severity == ViolationSeverity.WARNING)),
        )

        for v in violations:
            tc = ET.SubElement(suite, "testcase")
            tc.set("classname", v.file_path or "repo")
            tc.set("name", v.rule)

            if v.severity in (ViolationSeverity.ERROR, ViolationSeverity.WARNING):
                fail = ET.SubElement(tc, "failure")
                fail.set("message", v.message)
                fail.set("type", v.severity.value)
                fail.text = (
                    f"Rule: {v.rule}\n"
                    f"Value: {v.value}\n"
                    f"Threshold: {v.threshold}\n"
                    f"File: {v.file_path}\n"
                    f"Line: {v.line}"
                )

        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def write_report(self, output_dir: Path) -> list[Path]:
        """Write JUnit XML report to *output_dir*.

        Args:
            output_dir: Directory to write into.

        Returns:
            Single-element list with the path to the XML file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "dev-stats-junit.xml"
        out_path.write_text(self.emit(), encoding="utf-8")
        return [out_path]
