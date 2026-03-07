"""Unit tests for CppTreeSitterParser."""

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


def _parse_source(source: str, filename: str = "test.cpp") -> FileReport:
    """Parse a source string with CppTreeSitterParser.

    Args:
        source: C/C++ source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    from dev_stats.core.parsers.cpp_ts_parser import CppTreeSitterParser

    tmp = Path("/tmp/_dev_stats_test_cpp_ts")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = CppTreeSitterParser()
    return parser.parse(test_file, tmp)


class TestCppTSClasses:
    """Tests for class and struct extraction."""

    def test_simple_class(self) -> None:
        """Finds a simple class."""
        src = "class Foo {};"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_class_with_inheritance(self) -> None:
        """Detects base class in inheritance."""
        src = "class Derived : public Base {};"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert "Base" in report.classes[0].base_classes

    def test_struct_as_class(self) -> None:
        """Structs are reported as classes."""
        src = "struct Point { int x; int y; };"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Point"


class TestCppTSMethods:
    """Tests for method and constructor extraction."""

    def test_method_found(self) -> None:
        """Finds methods inside a class."""
        src = """
class Foo {
    void bar() {}
};
"""
        report = _parse_source(src)
        assert report.classes[0].num_methods == 1
        assert report.classes[0].methods[0].name == "bar"

    def test_constructor_detected(self) -> None:
        """Constructors are marked as is_constructor."""
        src = """
class Foo {
    Foo(int x) {}
};
"""
        report = _parse_source(src)
        methods = report.classes[0].methods
        assert len(methods) == 1
        assert methods[0].is_constructor is True

    def test_method_parameters(self) -> None:
        """Method parameters are extracted."""
        src = """
class Foo {
    void bar(int x, float y) {}
};
"""
        report = _parse_source(src)
        params = report.classes[0].methods[0].parameters
        assert len(params) == 2


class TestCppTSFunctions:
    """Tests for top-level function extraction."""

    def test_top_level_function(self) -> None:
        """Top-level functions are extracted."""
        src = """
int add(int a, int b) {
    return a + b;
}
"""
        report = _parse_source(src)
        assert report.num_functions >= 1
        names = {f.name for f in report.functions}
        assert "add" in names

    def test_function_not_inside_class(self) -> None:
        """Functions inside classes are not reported as top-level."""
        src = """
class Foo {
    void bar() {}
};

int standalone() { return 0; }
"""
        report = _parse_source(src)
        func_names = {f.name for f in report.functions}
        assert "standalone" in func_names
        assert "bar" not in func_names


class TestCppTSImports:
    """Tests for #include detection."""

    def test_includes_detected(self) -> None:
        """Include directives are parsed as imports."""
        src = '#include <iostream>\n#include "myheader.h"\nint main() { return 0; }'
        report = _parse_source(src)
        assert "iostream" in report.imports
        assert "myheader" in report.imports


class TestCppTSEdgeCases:
    """Edge-case tests."""

    def test_empty_file(self) -> None:
        """Empty file returns empty report."""
        report = _parse_source("")
        assert report.num_classes == 0
        assert report.num_functions == 0

    def test_complexity_with_branches(self) -> None:
        """CC increases with branches."""
        src = """
class Foo {
    int decide(int x) {
        if (x > 0) {
            return 1;
        } else if (x < 0) {
            return -1;
        }
        return 0;
    }
};
"""
        report = _parse_source(src)
        method = report.classes[0].methods[0]
        assert method.cyclomatic_complexity >= 3
