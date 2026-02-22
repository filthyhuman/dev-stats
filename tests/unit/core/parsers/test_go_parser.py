"""Unit tests for GoParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.core.parsers.go_parser import GoParser

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


def _parse_source(source: str, filename: str = "test.go") -> FileReport:
    """Parse a source string and return the FileReport.

    Args:
        source: Go source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    tmp = Path("/tmp/_dev_stats_test_go")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = GoParser()
    return parser.parse(test_file, tmp)


class TestGoParserStructs:
    """Tests for struct extraction."""

    def test_struct_found(self) -> None:
        """GoParser finds a struct definition."""
        src = "package main\n\ntype Foo struct {\n    X int\n}\n"
        report = _parse_source(src)
        assert report.num_classes >= 1
        names = {c.name for c in report.classes}
        assert "Foo" in names

    def test_interface_found(self) -> None:
        """GoParser finds an interface definition."""
        src = "package main\n\ntype Reader interface {\n    Read() error\n}\n"
        report = _parse_source(src)
        reader = next(c for c in report.classes if c.name == "Reader")
        assert "interface" in reader.decorators


class TestGoParserMethods:
    """Tests for method extraction."""

    def test_method_found(self) -> None:
        """GoParser finds methods with receivers."""
        src = (
            "package main\n\n"
            "type Foo struct {\n    X int\n}\n\n"
            "func (f *Foo) Bar(x int) int {\n"
            "    return x\n"
            "}\n"
        )
        report = _parse_source(src)
        foo = next(c for c in report.classes if c.name == "Foo")
        names = [m.name for m in foo.methods]
        assert "Bar" in names

    def test_method_parameters(self) -> None:
        """GoParser extracts method parameters."""
        src = (
            "package main\n\n"
            "type Foo struct{}\n\n"
            "func (f *Foo) Add(a int, b int) int {\n"
            "    return a + b\n"
            "}\n"
        )
        report = _parse_source(src)
        foo = next(c for c in report.classes if c.name == "Foo")
        add = next(m for m in foo.methods if m.name == "Add")
        assert len(add.parameters) == 2


class TestGoParserFunctions:
    """Tests for top-level function extraction."""

    def test_function_found(self) -> None:
        """GoParser finds top-level functions."""
        src = "package main\n\nfunc Helper(a int, b int) int {\n    return a + b\n}\n"
        report = _parse_source(src)
        assert report.num_functions >= 1
        names = [f.name for f in report.functions]
        assert "Helper" in names


class TestGoParserImports:
    """Tests for import detection."""

    def test_single_import(self) -> None:
        """GoParser detects single import statements."""
        src = 'package main\n\nimport "fmt"\n'
        report = _parse_source(src)
        assert "fmt" in report.imports

    def test_grouped_imports(self) -> None:
        """GoParser detects grouped import blocks."""
        src = 'package main\n\nimport (\n    "fmt"\n    "os"\n)\n'
        report = _parse_source(src)
        assert "fmt" in report.imports
        assert "os" in report.imports


class TestGoParserCC:
    """Tests for cyclomatic complexity."""

    def test_simple_function_cc_one(self) -> None:
        """Simple function has CC=1."""
        src = "package main\n\nfunc Simple() int {\n    return 1\n}\n"
        report = _parse_source(src)
        simple = next(f for f in report.functions if f.name == "Simple")
        assert simple.cyclomatic_complexity == 1

    def test_if_increases_cc(self) -> None:
        """If/else if increases CC."""
        src = (
            "package main\n\n"
            "func Branch(x int) int {\n"
            "    if x > 0 {\n"
            "        return 1\n"
            "    } else if x < 0 {\n"
            "        return -1\n"
            "    }\n"
            "    return 0\n"
            "}\n"
        )
        report = _parse_source(src)
        branch = next(f for f in report.functions if f.name == "Branch")
        assert branch.cyclomatic_complexity >= 3


class TestGoParserFixture:
    """Tests against the hand-verified sample fixture."""

    def test_sample_fixture(self) -> None:
        """Parse the sample fixture and verify expected values."""
        fixtures = Path(__file__).resolve().parents[3] / "fixtures"
        sample = fixtures / "sample_files" / "go" / "sample.go"
        if not sample.exists():
            return
        parser = GoParser()
        report = parser.parse(sample, sample.parent.parent.parent.parent)
        class_names = {c.name for c in report.classes}
        assert "Calculator" in class_names
        assert "Computable" in class_names
        assert report.num_functions >= 1
        assert "fmt" in report.imports
