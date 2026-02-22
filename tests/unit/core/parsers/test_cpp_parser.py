"""Unit tests for CppParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.core.parsers.cpp_parser import CppParser

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


def _parse_source(source: str, filename: str = "test.cpp") -> FileReport:
    """Parse a source string and return the FileReport.

    Args:
        source: C++ source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    tmp = Path("/tmp/_dev_stats_test_cpp")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = CppParser()
    return parser.parse(test_file, tmp)


class TestCppParserClasses:
    """Tests for class and struct extraction."""

    def test_class_found(self) -> None:
        """CppParser finds a class definition."""
        src = "class Foo {\npublic:\n    void bar() {}\n};\n"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_struct_found(self) -> None:
        """CppParser finds a struct definition."""
        src = "struct Point {\n    int x;\n    int y;\n};\n"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Point"

    def test_inheritance_detected(self) -> None:
        """CppParser detects inheritance."""
        src = "class Foo : public Bar {\n};\n"
        report = _parse_source(src)
        base = report.classes[0].base_classes
        assert any("Bar" in b for b in base)


class TestCppParserMethods:
    """Tests for method extraction."""

    def test_method_found(self) -> None:
        """CppParser finds methods inside a class."""
        src = "class Foo {\npublic:\n    int bar(int x) {\n        return x;\n    }\n};\n"
        report = _parse_source(src)
        names = [m.name for m in report.classes[0].methods]
        assert "bar" in names

    def test_method_parameters(self) -> None:
        """CppParser extracts method parameters."""
        src = (
            "class Foo {\npublic:\n    int add(int a, int b) {\n        return a + b;\n    }\n};\n"
        )
        report = _parse_source(src)
        add = next(m for m in report.classes[0].methods if m.name == "add")
        assert len(add.parameters) == 2


class TestCppParserFunctions:
    """Tests for top-level function extraction."""

    def test_function_found(self) -> None:
        """CppParser finds top-level functions."""
        src = "int helper(int a, int b) {\n    return a + b;\n}\n"
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "helper"

    def test_default_parameter(self) -> None:
        """CppParser detects default parameters."""
        src = "int greet(int x = 0) {\n    return x;\n}\n"
        report = _parse_source(src)
        assert report.functions[0].parameters[0].has_default is True


class TestCppParserIncludes:
    """Tests for include detection."""

    def test_includes_detected(self) -> None:
        """CppParser detects #include directives."""
        src = '#include <vector>\n#include "utils.h"\n'
        report = _parse_source(src)
        assert "vector" in report.imports
        assert "utils" in report.imports


class TestCppParserCC:
    """Tests for cyclomatic complexity."""

    def test_simple_function_cc_one(self) -> None:
        """Simple function has CC=1."""
        src = "int simple() {\n    return 1;\n}\n"
        report = _parse_source(src)
        assert report.functions[0].cyclomatic_complexity == 1

    def test_if_increases_cc(self) -> None:
        """If/else if increases CC."""
        src = (
            "int branch(int x) {\n"
            "    if (x > 0) {\n"
            "        return 1;\n"
            "    } else if (x < 0) {\n"
            "        return -1;\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        )
        report = _parse_source(src)
        assert report.functions[0].cyclomatic_complexity >= 3


class TestCppParserFixture:
    """Tests against the hand-verified sample fixture."""

    def test_sample_fixture(self) -> None:
        """Parse the sample fixture and verify expected values."""
        fixtures = Path(__file__).resolve().parents[3] / "fixtures"
        sample = fixtures / "sample_files" / "cpp" / "sample.cpp"
        if not sample.exists():
            return
        parser = CppParser()
        report = parser.parse(sample, sample.parent.parent.parent.parent)
        class_names = {c.name for c in report.classes}
        assert "Calculator" in class_names
        assert "Result" in class_names
        assert "vector" in report.imports
        assert "string" in report.imports
        assert report.num_functions >= 1
