"""Unit tests for JavaScriptParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.core.parsers.javascript_parser import JavaScriptParser

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


def _parse_source(source: str, filename: str = "test.js") -> FileReport:
    """Parse a source string and return the FileReport.

    Args:
        source: JavaScript source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    tmp = Path("/tmp/_dev_stats_test_js")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = JavaScriptParser()
    return parser.parse(test_file, tmp)


class TestJSParserClasses:
    """Tests for class extraction."""

    def test_class_found(self) -> None:
        """JavaScriptParser finds a class definition."""
        src = "class Foo {\n}\n"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_extends_detected(self) -> None:
        """JavaScriptParser detects extends clause."""
        src = "class Foo extends Bar {\n}\n"
        report = _parse_source(src)
        assert "Bar" in report.classes[0].base_classes

    def test_exported_class(self) -> None:
        """JavaScriptParser finds exported class."""
        src = "export class Foo {\n}\n"
        report = _parse_source(src)
        assert report.num_classes == 1


class TestJSParserMethods:
    """Tests for method extraction."""

    def test_method_found(self) -> None:
        """JavaScriptParser finds methods inside a class."""
        src = "class Foo {\n    bar() {\n        return 1;\n    }\n}\n"
        report = _parse_source(src)
        names = [m.name for m in report.classes[0].methods]
        assert "bar" in names

    def test_constructor_detected(self) -> None:
        """JavaScriptParser detects constructors."""
        src = "class Foo {\n    constructor(x) {\n        this.x = x;\n    }\n}\n"
        report = _parse_source(src)
        ctors = [m for m in report.classes[0].methods if m.is_constructor]
        assert len(ctors) == 1

    def test_method_parameters(self) -> None:
        """JavaScriptParser extracts method parameters."""
        src = "class Foo {\n    add(a, b) {\n        return a + b;\n    }\n}\n"
        report = _parse_source(src)
        add = next(m for m in report.classes[0].methods if m.name == "add")
        assert len(add.parameters) == 2


class TestJSParserFunctions:
    """Tests for top-level function extraction."""

    def test_function_found(self) -> None:
        """JavaScriptParser finds top-level functions."""
        src = "function helper(a, b) {\n    return a + b;\n}\n"
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "helper"

    def test_default_parameter(self) -> None:
        """JavaScriptParser detects default parameters."""
        src = "function greet(name = 'world') {\n    return name;\n}\n"
        report = _parse_source(src)
        assert report.functions[0].parameters[0].has_default is True


class TestJSParserImports:
    """Tests for import detection."""

    def test_require_detected(self) -> None:
        """JavaScriptParser detects require() calls."""
        src = 'const fs = require("fs");\n'
        report = _parse_source(src)
        assert "fs" in report.imports

    def test_es6_import_detected(self) -> None:
        """JavaScriptParser detects ES6 import statements."""
        src = 'import path from "path";\n'
        report = _parse_source(src)
        assert "path" in report.imports


class TestJSParserCC:
    """Tests for cyclomatic complexity."""

    def test_simple_function_cc_one(self) -> None:
        """Simple function has CC=1."""
        src = "function simple() {\n    return 1;\n}\n"
        report = _parse_source(src)
        assert report.functions[0].cyclomatic_complexity == 1

    def test_if_increases_cc(self) -> None:
        """If/else if increases CC."""
        src = (
            "function branch(x) {\n"
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


class TestJSParserFixture:
    """Tests against the hand-verified sample fixture."""

    def test_sample_fixture(self) -> None:
        """Parse the sample fixture and verify expected values."""
        fixtures = Path(__file__).resolve().parents[3] / "fixtures"
        sample = fixtures / "sample_files" / "javascript" / "sample.js"
        if not sample.exists():
            return
        parser = JavaScriptParser()
        report = parser.parse(sample, sample.parent.parent.parent.parent)
        assert report.num_classes == 1
        assert report.classes[0].name == "Calculator"
        assert report.num_functions >= 1
        assert "path" in report.imports
