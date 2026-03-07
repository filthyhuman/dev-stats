"""Unit tests for GoTreeSitterParser."""

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


def _parse_source(source: str, filename: str = "main.go") -> FileReport:
    """Parse a source string with GoTreeSitterParser.

    Args:
        source: Go source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    from dev_stats.core.parsers.go_ts_parser import GoTreeSitterParser

    tmp = Path("/tmp/_dev_stats_test_go_ts")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = GoTreeSitterParser()
    return parser.parse(test_file, tmp)


class TestGoTSStructs:
    """Tests for struct and interface extraction."""

    def test_simple_struct(self) -> None:
        """Finds a simple struct."""
        src = """\
package main

type Server struct {
    Host string
    Port int
}
"""
        report = _parse_source(src)
        assert report.num_classes == 1
        assert report.classes[0].name == "Server"

    def test_struct_with_methods(self) -> None:
        """Methods with receivers are associated with their struct."""
        src = """\
package main

type Server struct {
    Host string
}

func (s Server) Start() {
}

func (s *Server) Stop() {
}
"""
        report = _parse_source(src)
        assert report.num_classes == 1
        cls = report.classes[0]
        assert cls.name == "Server"
        assert cls.num_methods == 2
        method_names = {m.name for m in cls.methods}
        assert method_names == {"Start", "Stop"}

    def test_interface(self) -> None:
        """Finds interfaces with the interface decorator marker."""
        src = """\
package main

type Reader interface {
    Read(p []byte) (int, error)
}
"""
        report = _parse_source(src)
        assert report.num_classes == 1
        cls = report.classes[0]
        assert cls.name == "Reader"
        assert "interface" in cls.decorators

    def test_struct_and_interface(self) -> None:
        """Finds both structs and interfaces in the same file."""
        src = """\
package main

type MyStruct struct {
    Value int
}

type MyInterface interface {
    DoSomething()
}
"""
        report = _parse_source(src)
        assert report.num_classes == 2
        names = {c.name for c in report.classes}
        assert names == {"MyStruct", "MyInterface"}


class TestGoTSFunctions:
    """Tests for top-level function extraction."""

    def test_simple_function(self) -> None:
        """Finds a top-level function."""
        src = """\
package main

func main() {
}
"""
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "main"

    def test_function_with_parameters(self) -> None:
        """Extracts function parameters."""
        src = """\
package main

func add(a int, b int) int {
    return a + b
}
"""
        report = _parse_source(src)
        assert report.num_functions == 1
        params = report.functions[0].parameters
        assert len(params) == 2
        assert params[0].name == "a"
        assert params[0].type_annotation == "int"
        assert params[1].name == "b"

    def test_function_grouped_params(self) -> None:
        """Handles grouped Go parameters like ``(a, b int)``."""
        src = """\
package main

func sum(a, b int) int {
    return a + b
}
"""
        report = _parse_source(src)
        params = report.functions[0].parameters
        assert len(params) == 2
        assert params[0].name == "a"
        assert params[1].name == "b"

    def test_methods_not_in_functions(self) -> None:
        """Methods with receivers are not listed as top-level functions."""
        src = """\
package main

type Foo struct{}

func (f Foo) Bar() {}

func standalone() {}
"""
        report = _parse_source(src)
        assert report.num_functions == 1
        assert report.functions[0].name == "standalone"


class TestGoTSImports:
    """Tests for import detection."""

    def test_single_import(self) -> None:
        """Single import statement is parsed."""
        src = """\
package main

import "fmt"

func main() {}
"""
        report = _parse_source(src)
        assert "fmt" in report.imports

    def test_grouped_imports(self) -> None:
        """Grouped import block is parsed."""
        src = """\
package main

import (
    "fmt"
    "net/http"
    "encoding/json"
)

func main() {}
"""
        report = _parse_source(src)
        assert "fmt" in report.imports
        assert "http" in report.imports
        assert "json" in report.imports

    def test_no_imports(self) -> None:
        """File without imports has empty import list."""
        src = """\
package main

func main() {}
"""
        report = _parse_source(src)
        assert report.imports == ()


class TestGoTSEdgeCases:
    """Edge-case tests."""

    def test_empty_file(self) -> None:
        """Empty file returns empty report."""
        report = _parse_source("")
        assert report.num_classes == 0
        assert report.num_functions == 0

    def test_complexity_with_branches(self) -> None:
        """CC increases with branches in a function."""
        src = """\
package main

func classify(x int) string {
    if x > 0 {
        return "positive"
    } else if x < 0 {
        return "negative"
    }
    return "zero"
}
"""
        report = _parse_source(src)
        func = report.functions[0]
        assert func.cyclomatic_complexity >= 3

    def test_complexity_with_loop_and_condition(self) -> None:
        """Cognitive complexity is non-zero for nested structures."""
        src = """\
package main

func process(items []int) int {
    total := 0
    for _, v := range items {
        if v > 0 {
            total += v
        }
    }
    return total
}
"""
        report = _parse_source(src)
        func = report.functions[0]
        assert func.cognitive_complexity > 0

    def test_method_complexity(self) -> None:
        """Methods on structs also have complexity computed."""
        src = """\
package main

type Calc struct{}

func (c Calc) Decide(x int) int {
    if x > 10 {
        return 1
    } else if x > 5 {
        return 2
    }
    return 0
}
"""
        report = _parse_source(src)
        method = report.classes[0].methods[0]
        assert method.cyclomatic_complexity >= 3
