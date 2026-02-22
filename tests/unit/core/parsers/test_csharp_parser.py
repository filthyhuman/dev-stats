"""Unit tests for CSharpParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.core.parsers.csharp_parser import CSharpParser

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


def _parse_source(source: str, filename: str = "Test.cs") -> FileReport:
    """Parse a source string and return the FileReport.

    Args:
        source: C# source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    tmp = Path("/tmp/_dev_stats_test_cs")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = CSharpParser()
    return parser.parse(test_file, tmp)


class TestCSharpParserClasses:
    """Tests for class and interface extraction."""

    def test_class_found(self) -> None:
        """CSharpParser finds a class definition."""
        src = "public class Foo {\n}\n"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_interface_found(self) -> None:
        """CSharpParser finds an interface definition."""
        src = "public interface IFoo {\n    void Bar();\n}\n"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "IFoo"

    def test_inheritance_detected(self) -> None:
        """CSharpParser detects base class."""
        src = "public class Foo : Bar, IDisposable {\n}\n"
        report = _parse_source(src)
        assert "Bar" in report.classes[0].base_classes
        assert "IDisposable" in report.classes[0].base_classes


class TestCSharpParserMethods:
    """Tests for method extraction."""

    def test_method_found(self) -> None:
        """CSharpParser finds methods inside a class."""
        src = "public class Foo {\n    public void Bar() {\n        return;\n    }\n}\n"
        report = _parse_source(src)
        names = [m.name for m in report.classes[0].methods]
        assert "Bar" in names

    def test_constructor_detected(self) -> None:
        """CSharpParser detects constructors."""
        src = "public class Foo {\n    public Foo(int x) {\n        this.x = x;\n    }\n}\n"
        report = _parse_source(src)
        ctors = [m for m in report.classes[0].methods if m.is_constructor]
        assert len(ctors) >= 1

    def test_method_parameters(self) -> None:
        """CSharpParser extracts method parameters."""
        src = (
            "public class Foo {\n"
            "    public int Add(int a, int b) {\n"
            "        return a + b;\n"
            "    }\n"
            "}\n"
        )
        report = _parse_source(src)
        add = next(m for m in report.classes[0].methods if m.name == "Add")
        assert len(add.parameters) == 2
        assert add.parameters[0].name == "a"

    def test_default_parameter(self) -> None:
        """CSharpParser detects default parameters."""
        src = "public class Foo {\n    public void Bar(int x = 0) {\n        return;\n    }\n}\n"
        report = _parse_source(src)
        bar = next(m for m in report.classes[0].methods if m.name == "Bar")
        assert bar.parameters[0].has_default is True


class TestCSharpParserCC:
    """Tests for cyclomatic complexity."""

    def test_simple_method_cc_one(self) -> None:
        """Simple method has CC=1."""
        src = "public class Foo {\n    public void Bar() {\n        return;\n    }\n}\n"
        report = _parse_source(src)
        bar = next(m for m in report.classes[0].methods if m.name == "Bar")
        assert bar.cyclomatic_complexity == 1

    def test_if_increases_cc(self) -> None:
        """If/else if increases CC."""
        src = (
            "public class Foo {\n"
            "    public int Branch(int x) {\n"
            "        if (x > 0) {\n"
            "            return 1;\n"
            "        } else if (x < 0) {\n"
            "            return -1;\n"
            "        }\n"
            "        return 0;\n"
            "    }\n"
            "}\n"
        )
        report = _parse_source(src)
        branch = next(m for m in report.classes[0].methods if m.name == "Branch")
        assert branch.cyclomatic_complexity >= 3


class TestCSharpParserUsings:
    """Tests for using detection."""

    def test_usings_detected(self) -> None:
        """CSharpParser detects using statements."""
        src = "using System;\nusing System.Collections.Generic;\npublic class Foo {\n}\n"
        report = _parse_source(src)
        assert "System" in report.imports

    def test_no_top_level_functions(self) -> None:
        """C# has no top-level functions (pre-C#9)."""
        src = "public class Foo {\n}\n"
        report = _parse_source(src)
        assert report.num_functions == 0


class TestCSharpParserFixture:
    """Tests against the hand-verified sample fixture."""

    def test_sample_fixture(self) -> None:
        """Parse the sample fixture and verify expected values."""
        fixtures = Path(__file__).resolve().parents[3] / "fixtures"
        sample = fixtures / "sample_files" / "csharp" / "Sample.cs"
        if not sample.exists():
            return
        parser = CSharpParser()
        report = parser.parse(sample, sample.parent.parent.parent.parent)
        class_names = {c.name for c in report.classes}
        assert "Calculator" in class_names
        assert "IComputable" in class_names
        assert "System" in report.imports
