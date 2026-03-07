"""Unit tests for TypeScriptTreeSitterParser."""

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


def _parse_source(source: str, filename: str = "test.ts") -> FileReport:
    """Parse a source string with TypeScriptTreeSitterParser.

    Args:
        source: TypeScript source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    from dev_stats.core.parsers.typescript_ts_parser import TypeScriptTreeSitterParser

    tmp = Path("/tmp/_dev_stats_test_ts_ts")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = TypeScriptTreeSitterParser()
    return parser.parse(test_file, tmp)


class TestTSTSClasses:
    """Tests for class extraction."""

    def test_simple_class(self) -> None:
        """Finds a simple class."""
        report = _parse_source("class Foo {}")
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_class_with_extends(self) -> None:
        """Detects extends clause."""
        report = _parse_source("class Foo extends Bar {}")
        assert "Bar" in report.classes[0].base_classes

    def test_class_with_implements(self) -> None:
        """Detects implements clause."""
        report = _parse_source("class Foo implements Runnable, Serializable {}")
        bases = report.classes[0].base_classes
        assert "Runnable" in bases
        assert "Serializable" in bases

    def test_interface_detected(self) -> None:
        """Finds interfaces and marks them with decorator."""
        src = "interface Callback { onResult(code: number): void; }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Callback"
        assert "interface" in report.classes[0].decorators

    def test_interface_with_extends(self) -> None:
        """Detects interface extends clause."""
        src = "interface Foo extends Bar {}"
        report = _parse_source(src)
        assert "Bar" in report.classes[0].base_classes

    def test_enum_detected(self) -> None:
        """Finds enums and marks them with decorator."""
        src = "enum Color { Red, Green, Blue }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Color"
        assert "enum" in report.classes[0].decorators

    def test_exported_class(self) -> None:
        """Finds exported classes."""
        src = "export class Service {}"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Service"

    def test_generics(self) -> None:
        """Classes with generics are handled."""
        src = "class Container<T> { get(): T { return {} as T; } }"
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Container"


class TestTSTSMethods:
    """Tests for method extraction."""

    def test_method_found(self) -> None:
        """Finds methods inside a class."""
        src = "class Foo { bar(): void {} }"
        report = _parse_source(src)
        assert report.classes[0].num_methods == 1
        assert report.classes[0].methods[0].name == "bar"

    def test_constructor_detected(self) -> None:
        """Constructors are marked as is_constructor."""
        src = "class Foo { constructor(private x: number) {} }"
        report = _parse_source(src)
        methods = report.classes[0].methods
        assert len(methods) == 1
        assert methods[0].is_constructor is True
        assert methods[0].name == "constructor"

    def test_method_parameters(self) -> None:
        """Method parameters are extracted."""
        src = "class Foo { bar(x: number, name: string): void {} }"
        report = _parse_source(src)
        params = report.classes[0].methods[0].parameters
        assert len(params) == 2

    def test_method_cyclomatic_complexity(self) -> None:
        """CC increases with branches."""
        src = """
class Foo {
    bar(x: number): number {
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
class Foo {
    process(items: number[]): void {
        for (const item of items) {
            if (item > 0) {
                console.log(item);
            }
        }
    }
}
"""
        report = _parse_source(src)
        method = report.classes[0].methods[0]
        assert method.cognitive_complexity > 0


class TestTSTSFunctions:
    """Tests for function extraction."""

    def test_function_declaration(self) -> None:
        """Finds top-level function declarations."""
        src = "function greet(name: string): string { return 'hi ' + name; }"
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "greet"

    def test_arrow_function(self) -> None:
        """Finds arrow function assigned to const."""
        src = "const add = (x: number, y: number): number => x + y;"
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "add"

    def test_arrow_function_parameters(self) -> None:
        """Arrow function parameters are extracted."""
        src = "const fn = (a: number, b: number, c: number) => a + b + c;"
        report = _parse_source(src)
        assert report.functions[0].num_parameters == 3

    def test_exported_function(self) -> None:
        """Exported function declarations are found."""
        src = "export function greet(): string { return 'hi'; }"
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "greet"

    def test_function_complexity(self) -> None:
        """Functions with branches have CC > 1."""
        src = """
function process(x: number): number {
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

    def test_class_not_counted_as_function(self) -> None:
        """Methods inside classes are not counted as top-level functions."""
        src = """
class Foo {
    bar(): number { return 1; }
}
function standalone(): number { return 2; }
"""
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.num_functions == 1
        assert report.functions[0].name == "standalone"


class TestTSTSImports:
    """Tests for import detection."""

    def test_es6_import(self) -> None:
        """ES6 import statements are parsed."""
        src = "import { foo } from 'bar';\nfunction x(): void {}"
        report = _parse_source(src)
        assert "bar" in report.imports

    def test_scoped_import(self) -> None:
        """Scoped package imports extract the scope."""
        src = "import x from '@scope/pkg';\nfunction y(): void {}"
        report = _parse_source(src)
        assert "@scope" in report.imports

    def test_multiple_imports(self) -> None:
        """Multiple imports are all detected."""
        src = "import { a } from 'alpha';\nimport { b } from 'beta';\nfunction x(): void {}"
        report = _parse_source(src)
        assert "alpha" in report.imports
        assert "beta" in report.imports


class TestTSTSEdgeCases:
    """Edge-case tests."""

    def test_empty_file(self) -> None:
        """Empty file returns empty report."""
        report = _parse_source("")
        assert report.num_classes == 0
        assert report.num_functions == 0

    def test_exported_arrow_function(self) -> None:
        """Exported arrow functions are found."""
        src = "export const add = (x: number, y: number): number => x + y;"
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "add"
