"""Unit tests for JavaParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.core.parsers.java_parser import JavaParser

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


def _parse_source(source: str, filename: str = "Test.java") -> FileReport:
    """Parse a source string and return the FileReport.

    Args:
        source: Java source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    tmp = Path("/tmp/_dev_stats_test_java")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = JavaParser()
    return parser.parse(test_file, tmp)


class TestJavaParserClasses:
    """Tests for class extraction."""

    def test_class_found(self) -> None:
        """JavaParser finds a class definition."""
        src = "public class Foo {\n}\n"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_interface_found(self) -> None:
        """JavaParser finds an interface definition."""
        src = "public interface Bar {\n    void doStuff();\n}\n"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Bar"

    def test_extends_detected(self) -> None:
        """JavaParser detects base class from extends."""
        src = "public class Foo extends Bar {\n}\n"
        report = _parse_source(src)
        assert "Bar" in report.classes[0].base_classes

    def test_implements_detected(self) -> None:
        """JavaParser detects implemented interfaces."""
        src = "public class Foo implements Runnable, Serializable {\n}\n"
        report = _parse_source(src)
        assert "Runnable" in report.classes[0].base_classes
        assert "Serializable" in report.classes[0].base_classes


class TestJavaParserMethods:
    """Tests for method extraction."""

    def test_method_found(self) -> None:
        """JavaParser finds methods inside a class."""
        src = "public class Foo {\n    public void bar() {\n        return;\n    }\n}\n"
        report = _parse_source(src)
        assert len(report.classes[0].methods) >= 1
        names = [m.name for m in report.classes[0].methods]
        assert "bar" in names

    def test_constructor_detected(self) -> None:
        """JavaParser detects constructors."""
        src = "public class Foo {\n    public Foo(int x) {\n        this.x = x;\n    }\n}\n"
        report = _parse_source(src)
        constructors = [m for m in report.classes[0].methods if m.is_constructor]
        assert len(constructors) >= 1

    def test_method_parameters(self) -> None:
        """JavaParser extracts method parameters."""
        src = (
            "public class Foo {\n"
            "    public int add(int a, int b) {\n"
            "        return a + b;\n"
            "    }\n"
            "}\n"
        )
        report = _parse_source(src)
        add = next(m for m in report.classes[0].methods if m.name == "add")
        assert len(add.parameters) == 2
        assert add.parameters[0].name == "a"


class TestJavaParserCC:
    """Tests for cyclomatic complexity."""

    def test_simple_method_cc_one(self) -> None:
        """Simple method has CC=1."""
        src = "public class Foo {\n    public void bar() {\n        return;\n    }\n}\n"
        report = _parse_source(src)
        bar = next(m for m in report.classes[0].methods if m.name == "bar")
        assert bar.cyclomatic_complexity == 1

    def test_if_else_cc(self) -> None:
        """If/else if/else increases CC."""
        src = (
            "public class Foo {\n"
            "    public int branch(int x) {\n"
            "        if (x > 0) {\n"
            "            return 1;\n"
            "        } else if (x < 0) {\n"
            "            return -1;\n"
            "        } else {\n"
            "            return 0;\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        report = _parse_source(src)
        branch = next(m for m in report.classes[0].methods if m.name == "branch")
        assert branch.cyclomatic_complexity >= 3


class TestJavaParserImports:
    """Tests for import detection."""

    def test_imports_detected(self) -> None:
        """JavaParser detects import statements."""
        src = "import java.util.List;\nimport java.io.File;\npublic class Foo {\n}\n"
        report = _parse_source(src)
        assert "java" in report.imports

    def test_no_top_level_functions(self) -> None:
        """Java has no top-level functions."""
        src = "public class Foo {\n}\n"
        report = _parse_source(src)
        assert report.num_functions == 0


class TestJavaParserFixture:
    """Tests against the hand-verified sample fixture."""

    def test_sample_fixture(self) -> None:
        """Parse the sample fixture and verify expected values."""
        fixtures = Path(__file__).resolve().parents[3] / "fixtures"
        sample = fixtures / "sample_files" / "java" / "Sample.java"
        if not sample.exists():
            return
        parser = JavaParser()
        report = parser.parse(sample, sample.parent.parent.parent.parent)
        assert report.num_classes == 2
        class_names = {c.name for c in report.classes}
        assert "Calculator" in class_names
        assert "MathUtils" in class_names
        assert "java" in report.imports
