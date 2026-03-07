"""Unit tests for JavaTreeSitterParser."""

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


def _parse_source(source: str, filename: str = "Test.java") -> FileReport:
    """Parse a source string with JavaTreeSitterParser.

    Args:
        source: Java source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    from dev_stats.core.parsers.java_ts_parser import JavaTreeSitterParser

    tmp = Path("/tmp/_dev_stats_test_java_ts")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = JavaTreeSitterParser()
    return parser.parse(test_file, tmp)


class TestJavaTSClasses:
    """Tests for class extraction."""

    def test_simple_class(self) -> None:
        """Finds a simple class."""
        report = _parse_source("public class Foo {}")
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_class_with_extends(self) -> None:
        """Detects extends clause."""
        report = _parse_source("public class Foo extends Bar {}")
        assert "Bar" in report.classes[0].base_classes

    def test_class_with_implements(self) -> None:
        """Detects implements clause."""
        report = _parse_source("public class Foo implements Runnable, Serializable {}")
        bases = report.classes[0].base_classes
        assert "Runnable" in bases
        assert "Serializable" in bases

    def test_nested_class(self) -> None:
        """Finds nested inner classes."""
        src = "public class Outer { class Inner {} }"
        report = _parse_source(src)
        assert report.num_classes == 2
        names = {c.name for c in report.classes}
        assert names == {"Outer", "Inner"}

    def test_interface_detected(self) -> None:
        """Finds interfaces."""
        src = "public interface Callback { void onResult(int code); }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Callback"

    def test_enum_detected(self) -> None:
        """Finds enums."""
        src = "public enum Color { RED, GREEN, BLUE }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Color"


class TestJavaTSMethods:
    """Tests for method extraction."""

    def test_method_found(self) -> None:
        """Finds methods inside a class."""
        src = "public class Foo { public void bar() {} }"
        report = _parse_source(src)
        assert report.classes[0].num_methods == 1
        assert report.classes[0].methods[0].name == "bar"

    def test_constructor_detected(self) -> None:
        """Constructors are marked as is_constructor."""
        src = "public class Foo { public Foo(int x) { } }"
        report = _parse_source(src)
        methods = report.classes[0].methods
        assert len(methods) == 1
        assert methods[0].is_constructor is True

    def test_method_parameters(self) -> None:
        """Method parameters are extracted."""
        src = "public class Foo { public void bar(int x, String name) {} }"
        report = _parse_source(src)
        params = report.classes[0].methods[0].parameters
        assert len(params) == 2

    def test_method_cyclomatic_complexity(self) -> None:
        """CC increases with branches."""
        src = """
public class Foo {
    public int bar(int x) {
        if (x > 0) {
            return 1;
        } else if (x < 0) {
            return -1;
        }
        return 0;
    }
}
"""
        report = _parse_source(src)
        method = report.classes[0].methods[0]
        assert method.cyclomatic_complexity >= 3

    def test_method_cognitive_complexity(self) -> None:
        """Cognitive complexity is non-zero for complex methods."""
        src = """
public class Foo {
    public void process(int[] items) {
        for (int item : items) {
            if (item > 0) {
                System.out.println(item);
            }
        }
    }
}
"""
        report = _parse_source(src)
        method = report.classes[0].methods[0]
        assert method.cognitive_complexity > 0


class TestJavaTSImports:
    """Tests for import detection."""

    def test_imports_detected(self) -> None:
        """Import statements are parsed."""
        src = "import java.util.List;\nimport java.io.File;\nclass Foo {}"
        report = _parse_source(src)
        assert "java" in report.imports

    def test_no_functions(self) -> None:
        """Java has no top-level functions."""
        src = "class Foo { void bar() {} }"
        report = _parse_source(src)
        assert report.num_functions == 0


class TestJavaTSEdgeCases:
    """Edge-case tests."""

    def test_empty_file(self) -> None:
        """Empty file returns empty report."""
        report = _parse_source("")
        assert report.num_classes == 0
        assert report.num_functions == 0

    def test_generics(self) -> None:
        """Classes with generics are handled."""
        src = "public class Container<T extends Comparable<T>> { public T get() { return null; } }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Container"
        assert report.classes[0].num_methods == 1
