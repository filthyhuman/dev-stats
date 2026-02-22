"""XML exporter producing JUnit-format XML for CI integration."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from dev_stats.output.exporters.abstract_exporter import AbstractExporter

if TYPE_CHECKING:
    from pathlib import Path

    from dev_stats.config.analysis_config import AnalysisConfig
    from dev_stats.core.models import RepoReport


class XmlExporter(AbstractExporter):
    """Exports the analysis report as JUnit-style XML.

    Each file is represented as a ``<testsuite>`` and each quality check
    (complexity threshold, line-count threshold, etc.) is a ``<testcase>``.
    Violations appear as ``<failure>`` elements, making the output compatible
    with CI tools that parse JUnit XML (Jenkins, GitLab, GitHub Actions).
    """

    def __init__(
        self,
        report: RepoReport,
        config: AnalysisConfig,
    ) -> None:
        """Initialise the XML exporter.

        Args:
            report: The analysis report to export.
            config: Analysis configuration.
        """
        super().__init__(report, config)

    def export(self, output_dir: Path) -> list[Path]:
        """Write JUnit XML report to *output_dir*.

        Args:
            output_dir: Directory to write the XML file into.

        Returns:
            Single-element list with the path to the generated file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        root = ET.Element("testsuites")
        root.set("name", "dev-stats")

        total_tests = 0
        total_failures = 0

        for f in self._report.files:
            suite = ET.SubElement(root, "testsuite")
            suite.set("name", str(f.path))
            suite.set("package", f.language)

            tests = 0
            failures = 0

            # Test case: file size
            tc_size = ET.SubElement(suite, "testcase")
            tc_size.set("name", "file_size")
            tc_size.set("classname", str(f.path))
            tests += 1
            max_lines = self._config.thresholds.max_file_lines
            if f.total_lines > max_lines:
                fail = ET.SubElement(tc_size, "failure")
                fail.set("type", "FileTooLarge")
                fail.set(
                    "message",
                    f"File has {f.total_lines} lines (threshold: {max_lines})",
                )
                failures += 1

            # Test cases for method complexity
            all_methods = list(f.functions)
            for cls in f.classes:
                all_methods.extend(cls.methods)

            for m in all_methods:
                tc_cc = ET.SubElement(suite, "testcase")
                tc_cc.set("name", f"complexity:{m.name}")
                tc_cc.set("classname", str(f.path))
                tests += 1
                max_cc = self._config.thresholds.max_cyclomatic_complexity
                if m.cyclomatic_complexity > max_cc:
                    fail = ET.SubElement(tc_cc, "failure")
                    fail.set("type", "CyclomaticComplexity")
                    fail.set(
                        "message",
                        f"{m.name} has CC={m.cyclomatic_complexity} (threshold: {max_cc})",
                    )
                    failures += 1

            # Test cases for method length
            for m in all_methods:
                tc_len = ET.SubElement(suite, "testcase")
                tc_len.set("name", f"method_length:{m.name}")
                tc_len.set("classname", str(f.path))
                tests += 1
                max_method = self._config.thresholds.max_function_lines
                if m.lines > max_method:
                    fail = ET.SubElement(tc_len, "failure")
                    fail.set("type", "MethodTooLong")
                    fail.set(
                        "message",
                        f"{m.name} has {m.lines} lines (threshold: {max_method})",
                    )
                    failures += 1

            suite.set("tests", str(tests))
            suite.set("failures", str(failures))
            suite.set("errors", "0")
            total_tests += tests
            total_failures += failures

        root.set("tests", str(total_tests))
        root.set("failures", str(total_failures))
        root.set("errors", "0")

        tree = ET.ElementTree(root)
        out_path = output_dir / "dev-stats.xml"
        ET.indent(tree, space="  ")
        tree.write(str(out_path), encoding="unicode", xml_declaration=True)
        # Ensure trailing newline
        content = out_path.read_text()
        if not content.endswith("\n"):
            out_path.write_text(content + "\n")
        return [out_path]
