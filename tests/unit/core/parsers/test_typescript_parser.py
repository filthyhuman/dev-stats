"""Unit tests for TypeScriptParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.core.parsers.typescript_parser import TypeScriptParser

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


def _parse_source(source: str, filename: str = "test.ts") -> FileReport:
    """Parse a source string and return the FileReport.

    Args:
        source: TypeScript source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    tmp = Path("/tmp/_dev_stats_test_ts")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = TypeScriptParser()
    return parser.parse(test_file, tmp)


class TestTSParserClasses:
    """Tests for class extraction."""

    def test_class_found(self) -> None:
        """TypeScriptParser finds a class definition."""
        src = "class Foo {\n}\n"
        report = _parse_source(src)
        class_names = {c.name for c in report.classes}
        assert "Foo" in class_names

    def test_interface_found(self) -> None:
        """TypeScriptParser finds an interface definition."""
        src = "interface Bar {\n    doStuff(): void;\n}\n"
        report = _parse_source(src)
        bar = next(c for c in report.classes if c.name == "Bar")
        assert "interface" in bar.decorators

    def test_enum_found(self) -> None:
        """TypeScriptParser finds an enum definition."""
        src = 'enum Color {\n    Red = "red",\n    Blue = "blue",\n}\n'
        report = _parse_source(src)
        color = next(c for c in report.classes if c.name == "Color")
        assert "enum" in color.decorators

    def test_exported_interface(self) -> None:
        """TypeScriptParser finds exported interface."""
        src = "export interface Foo {\n    bar(): number;\n}\n"
        report = _parse_source(src)
        assert any(c.name == "Foo" for c in report.classes)


class TestTSParserMethods:
    """Tests for method extraction (inherited from JS)."""

    def test_method_found(self) -> None:
        """TypeScriptParser finds methods inside a class."""
        src = "class Foo {\n    bar(x: number): number {\n        return x;\n    }\n}\n"
        report = _parse_source(src)
        names = [m.name for m in report.classes[0].methods]
        assert "bar" in names


class TestTSParserFunctions:
    """Tests for top-level function extraction."""

    def test_function_found(self) -> None:
        """TypeScriptParser finds top-level functions."""
        src = "function helper(a: number, b: number): number {\n    return a + b;\n}\n"
        report = _parse_source(src)
        assert report.num_functions == 1

    def test_exported_function(self) -> None:
        """TypeScriptParser finds exported functions."""
        src = "export function foo(): void {\n    return;\n}\n"
        report = _parse_source(src)
        assert report.num_functions == 1


class TestTSParserImports:
    """Tests for import detection."""

    def test_import_detected(self) -> None:
        """TypeScriptParser detects import statements."""
        src = 'import * as path from "path";\n'
        report = _parse_source(src)
        assert "path" in report.imports


class TestTSParserFixture:
    """Tests against the hand-verified sample fixture."""

    def test_sample_fixture(self) -> None:
        """Parse the sample fixture and verify expected values."""
        fixtures = Path(__file__).resolve().parents[3] / "fixtures"
        sample = fixtures / "sample_files" / "typescript" / "sample.ts"
        if not sample.exists():
            return
        parser = TypeScriptParser()
        report = parser.parse(sample, sample.parent.parent.parent.parent)
        assert report.num_classes >= 3
        class_names = {c.name for c in report.classes}
        assert "Calculator" in class_names
        assert "Computable" in class_names
        assert "Operation" in class_names
        assert "path" in report.imports
