"""Unit tests for CSharpTreeSitterParser."""

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


def _parse_source(source: str, filename: str = "Test.cs") -> FileReport:
    """Parse a source string with CSharpTreeSitterParser.

    Args:
        source: C# source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    from dev_stats.core.parsers.csharp_ts_parser import CSharpTreeSitterParser

    tmp = Path("/tmp/_dev_stats_test_csharp_ts")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = CSharpTreeSitterParser()
    return parser.parse(test_file, tmp)


class TestCSharpTSClasses:
    """Tests for class extraction."""

    def test_simple_class(self) -> None:
        """Finds a simple class."""
        report = _parse_source("public class Foo {}")
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_class_with_inheritance(self) -> None:
        """Detects base class in inheritance."""
        report = _parse_source("public class Foo : Bar {}")
        assert "Bar" in report.classes[0].base_classes

    def test_class_with_interface(self) -> None:
        """Detects interface implementations."""
        report = _parse_source("public class Foo : IDisposable, IComparable {}")
        bases = report.classes[0].base_classes
        assert "IDisposable" in bases
        assert "IComparable" in bases

    def test_interface_detected(self) -> None:
        """Finds interfaces."""
        src = "public interface ICallback { void OnResult(int code); }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "ICallback"

    def test_struct_detected(self) -> None:
        """Finds structs (reported as classes)."""
        src = "public struct Point { public int X; public int Y; }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Point"

    def test_enum_detected(self) -> None:
        """Finds enums."""
        src = "public enum Color { Red, Green, Blue }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Color"

    def test_record_detected(self) -> None:
        """Finds record types."""
        src = "public record Person(string Name, int Age);"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Person"


class TestCSharpTSMethods:
    """Tests for method extraction."""

    def test_method_found(self) -> None:
        """Finds methods inside a class."""
        src = "public class Foo { public void Bar() {} }"
        report = _parse_source(src)
        assert report.classes[0].num_methods >= 1
        method_names = {m.name for m in report.classes[0].methods}
        assert "Bar" in method_names

    def test_constructor_detected(self) -> None:
        """Constructors are marked as is_constructor."""
        src = "public class Foo { public Foo(int x) { } }"
        report = _parse_source(src)
        constructors = [m for m in report.classes[0].methods if m.is_constructor]
        assert len(constructors) == 1
        assert constructors[0].name == "Foo"

    def test_method_parameters(self) -> None:
        """Method parameters are extracted."""
        src = "public class Foo { public void Bar(int x, string name) {} }"
        report = _parse_source(src)
        bar_methods = [m for m in report.classes[0].methods if m.name == "Bar"]
        assert len(bar_methods) == 1
        assert len(bar_methods[0].parameters) == 2

    def test_property_detected(self) -> None:
        """Properties are extracted as methods."""
        src = "public class Foo { public int Value { get; set; } }"
        report = _parse_source(src)
        prop_names = {m.name for m in report.classes[0].methods}
        assert "Value" in prop_names

    def test_method_cyclomatic_complexity(self) -> None:
        """CC increases with branches."""
        src = """
public class Foo {
    public int Bar(int x) {
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
        bar_methods = [m for m in report.classes[0].methods if m.name == "Bar"]
        assert len(bar_methods) == 1
        assert bar_methods[0].cyclomatic_complexity >= 3

    def test_method_cognitive_complexity(self) -> None:
        """Cognitive complexity is non-zero for complex methods."""
        src = """
public class Foo {
    public void Process(int[] items) {
        foreach (var item in items) {
            if (item > 0) {
                Console.WriteLine(item);
            }
        }
    }
}
"""
        report = _parse_source(src)
        proc_methods = [m for m in report.classes[0].methods if m.name == "Process"]
        assert len(proc_methods) == 1
        assert proc_methods[0].cognitive_complexity > 0


class TestCSharpTSImports:
    """Tests for import detection."""

    def test_using_directives_detected(self) -> None:
        """Using directives are parsed as imports."""
        src = "using System;\nusing System.Collections.Generic;\nclass Foo {}"
        report = _parse_source(src)
        assert "System" in report.imports

    def test_no_functions(self) -> None:
        """C# has no top-level functions."""
        src = "class Foo { void Bar() {} }"
        report = _parse_source(src)
        assert report.num_functions == 0


class TestCSharpTSEdgeCases:
    """Edge-case tests."""

    def test_empty_file(self) -> None:
        """Empty file returns empty report."""
        report = _parse_source("")
        assert report.num_classes == 0
        assert report.num_functions == 0

    def test_generics(self) -> None:
        """Classes with generics are handled."""
        src = "public class Container<T> { public T Get() { return default; } }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Container"
        method_names = {m.name for m in report.classes[0].methods}
        assert "Get" in method_names

    def test_namespace_with_classes(self) -> None:
        """Classes inside namespaces are found."""
        src = "namespace MyApp { public class Service {} }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Service"
