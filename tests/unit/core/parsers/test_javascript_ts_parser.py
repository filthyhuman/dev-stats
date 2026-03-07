"""Unit tests for JavaScriptTreeSitterParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from dev_stats.core.parsers.tree_sitter_base import _tree_sitter_available

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport

pytestmark = pytest.mark.skipif(
    not _tree_sitter_available(),
    reason="tree-sitter-languages not installed",
)


def _parse_source(source: str, filename: str = "test.js") -> FileReport:
    """Parse a source string with JavaScriptTreeSitterParser.

    Args:
        source: JavaScript source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    from dev_stats.core.parsers.javascript_ts_parser import JavaScriptTreeSitterParser

    tmp = Path("/tmp/_dev_stats_test_js_ts")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = JavaScriptTreeSitterParser()
    return parser.parse(test_file, tmp)


class TestJSTSClasses:
    """Tests for class extraction."""

    def test_simple_class(self) -> None:
        """Finds an ES6 class."""
        report = _parse_source("class Foo {}")
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_class_with_extends(self) -> None:
        """Detects extends clause."""
        report = _parse_source("class Foo extends Bar {}")
        assert "Bar" in report.classes[0].base_classes

    def test_class_methods(self) -> None:
        """Finds methods inside a class."""
        src = "class Foo { bar() {} baz(x) {} }"
        report = _parse_source(src)
        assert report.classes[0].num_methods == 2

    def test_constructor_detected(self) -> None:
        """Constructor is marked as is_constructor."""
        src = "class Foo { constructor(x) { this.x = x; } }"
        report = _parse_source(src)
        ctor = report.classes[0].methods[0]
        assert ctor.is_constructor is True
        assert ctor.name == "constructor"

    def test_getter_method(self) -> None:
        """Getter methods are found."""
        src = "class Foo { get value() { return 1; } }"
        report = _parse_source(src)
        assert report.classes[0].num_methods == 1


class TestJSTSFunctions:
    """Tests for function extraction."""

    def test_function_declaration(self) -> None:
        """Finds top-level function declarations."""
        src = "function greet(name) { return 'hi ' + name; }"
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "greet"

    def test_arrow_function(self) -> None:
        """Finds arrow function assigned to const."""
        src = "const add = (x, y) => x + y;"
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "add"

    def test_arrow_function_parameters(self) -> None:
        """Arrow function parameters are extracted."""
        src = "const fn = (a, b, c) => a + b + c;"
        report = _parse_source(src)
        assert report.functions[0].num_parameters == 3

    def test_function_complexity(self) -> None:
        """Functions with branches have CC > 1."""
        src = """
function process(x) {
    if (x > 0) {
        return 1;
    } else if (x < 0) {
        return -1;
    }
    return 0;
}
"""
        report = _parse_source(src)
        assert report.functions[0].cyclomatic_complexity >= 3

    def test_exported_function(self) -> None:
        """Exported function declarations are found."""
        src = "export function greet() { return 'hi'; }"
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "greet"


class TestJSTSImports:
    """Tests for import detection."""

    def test_es6_import(self) -> None:
        """ES6 import statements are parsed."""
        src = "import { foo } from 'bar';\nfunction x() {}"
        report = _parse_source(src)
        assert "bar" in report.imports

    def test_require_import(self) -> None:
        """require() calls are parsed."""
        src = "const x = require('lodash');\nfunction y() {}"
        report = _parse_source(src)
        assert "lodash" in report.imports

    def test_scoped_import(self) -> None:
        """Scoped package imports extract the scope."""
        src = "import x from '@scope/pkg';\nfunction y() {}"
        report = _parse_source(src)
        assert "@scope" in report.imports


class TestJSTSEdgeCases:
    """Edge-case tests."""

    def test_empty_file(self) -> None:
        """Empty file returns empty report."""
        report = _parse_source("")
        assert report.num_classes == 0
        assert report.num_functions == 0

    def test_class_not_counted_as_function(self) -> None:
        """Methods inside classes are not counted as top-level functions."""
        src = """
class Foo {
    bar() { return 1; }
}
function standalone() { return 2; }
"""
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.num_functions == 1
        assert report.functions[0].name == "standalone"
