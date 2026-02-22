"""Unit tests for PythonParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from dev_stats.core.parsers.python_parser import PythonParser

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport


def _parse_source(source: str, filename: str = "test.py") -> FileReport:
    """Parse a source string and return the FileReport.

    Args:
        source: Python source code.
        filename: Filename to use.

    Returns:
        A ``FileReport``.
    """
    tmp = Path("/tmp/_dev_stats_test")
    tmp.mkdir(parents=True, exist_ok=True)
    test_file = tmp / filename
    test_file.write_text(source)
    parser = PythonParser()
    return parser.parse(test_file, tmp)


class TestPythonParserClasses:
    """Tests for class extraction."""

    def test_class_found(self) -> None:
        """PythonParser finds a class definition."""
        report = _parse_source("class Foo:\n    pass\n")
        assert report.num_classes == 1
        assert report.classes[0].name == "Foo"

    def test_method_count(self) -> None:
        """PythonParser counts methods inside a class."""
        src = "class Foo:\n    def a(self) -> None: pass\n    def b(self) -> None: pass\n"
        report = _parse_source(src)
        assert report.classes[0].num_methods == 2

    def test_nested_class_found(self) -> None:
        """PythonParser finds nested classes."""
        src = "class Outer:\n    class Inner:\n        pass\n"
        report = _parse_source(src)
        assert report.num_classes == 2

    def test_abstract_class_detected(self) -> None:
        """PythonParser detects ABC base class."""
        src = "import abc\nclass Foo(abc.ABC):\n    pass\n"
        report = _parse_source(src)
        assert "abc.ABC" in report.classes[0].base_classes

    def test_decorated_class(self) -> None:
        """PythonParser captures class decorators."""
        src = "from dataclasses import dataclass\n@dataclass\nclass Foo:\n    x: int = 0\n"
        report = _parse_source(src)
        assert "dataclass" in report.classes[0].decorators


class TestPythonParserMethods:
    """Tests for method and function extraction."""

    def test_simple_cc_is_one(self) -> None:
        """A simple function has CC=1."""
        src = "def simple() -> None:\n    return None\n"
        report = _parse_source(src)
        assert report.functions[0].cyclomatic_complexity == 1

    def test_if_elif_cc_is_three(self) -> None:
        """if/elif/else yields CC=3."""
        src = (
            "def branch(x: int) -> int:\n"
            "    if x > 0:\n"
            "        return 1\n"
            "    elif x < 0:\n"
            "        return -1\n"
            "    else:\n"
            "        return 0\n"
        )
        report = _parse_source(src)
        assert report.functions[0].cyclomatic_complexity == 3

    def test_loop_cc_is_two(self) -> None:
        """A for-loop adds 1 to complexity."""
        src = (
            "def loop() -> int:\n    s = 0\n    for i in range(10):\n        s += i\n    return s\n"
        )
        report = _parse_source(src)
        assert report.functions[0].cyclomatic_complexity == 2

    def test_constructor_detected(self) -> None:
        """__init__ is marked as constructor."""
        src = "class Foo:\n    def __init__(self) -> None:\n        self.x = 1\n"
        report = _parse_source(src)
        init = report.classes[0].methods[0]
        assert init.is_constructor is True

    def test_static_method_decorator(self) -> None:
        """@staticmethod is captured as a decorator."""
        src = "class Foo:\n    @staticmethod\n    def bar() -> None:\n        pass\n"
        report = _parse_source(src)
        assert "staticmethod" in report.classes[0].methods[0].decorators

    def test_property_decorator(self) -> None:
        """@property is captured as a decorator."""
        src = "class Foo:\n    @property\n    def val(self) -> int:\n        return 0\n"
        report = _parse_source(src)
        assert "property" in report.classes[0].methods[0].decorators

    def test_async_function_found(self) -> None:
        """Async functions are extracted."""
        src = "async def fetch() -> None:\n    pass\n"
        report = _parse_source(src)
        assert len(report.functions) == 1
        assert report.functions[0].name == "fetch"


class TestPythonParserParameters:
    """Tests for parameter extraction."""

    def test_parameters_extracted(self) -> None:
        """Parameters are extracted with names."""
        src = "def add(a: int, b: int) -> int:\n    return a + b\n"
        report = _parse_source(src)
        params = report.functions[0].parameters
        assert len(params) == 2
        assert params[0].name == "a"

    def test_default_detected(self) -> None:
        """Default values are detected."""
        src = "def greet(name: str = 'world') -> str:\n    return name\n"
        report = _parse_source(src)
        assert report.functions[0].parameters[0].has_default is True

    def test_self_excluded(self) -> None:
        """The ``self`` parameter is not included in parameter list."""
        src = "class Foo:\n    def bar(self, x: int) -> None:\n        pass\n"
        report = _parse_source(src)
        params = report.classes[0].methods[0].parameters
        assert all(p.name != "self" for p in params)
        assert len(params) == 1


class TestPythonParserAttributes:
    """Tests for attribute extraction."""

    def test_self_x_as_attribute(self) -> None:
        """Attribute ``self.x`` in __init__ is extracted."""
        src = (
            "class Foo:\n    def __init__(self) -> None:\n"
            "        self.x = 1\n        self.y: int = 2\n"
        )
        report = _parse_source(src)
        attrs = report.classes[0].attributes
        assert "x" in attrs
        assert "y" in attrs


class TestPythonParserImports:
    """Tests for import detection."""

    def test_import_detection(self) -> None:
        """Imports are detected."""
        src = "import os\nfrom pathlib import Path\nimport sys\n"
        report = _parse_source(src)
        assert "os" in report.imports
        assert "pathlib" in report.imports
        assert "sys" in report.imports

    def test_no_duplicate_imports(self) -> None:
        """Duplicate imports are deduplicated."""
        src = "import os\nimport os.path\n"
        report = _parse_source(src)
        assert report.imports.count("os") == 1


class TestPythonParserEdgeCases:
    """Tests for error handling and edge cases."""

    def test_syntax_error_returns_empty(self) -> None:
        """Syntax errors produce a report with no classes/functions."""
        src = "def broken(\n"
        report = _parse_source(src)
        assert report.num_classes == 0
        assert report.num_functions == 0

    def test_empty_file_zero_counts(self) -> None:
        """Empty files have zero counts."""
        report = _parse_source("")
        assert report.total_lines == 0
        assert report.num_classes == 0


class TestPythonParserSampleFixture:
    """Tests against the hand-verified sample fixture."""

    def test_sample_fixture(self) -> None:
        """Parse the sample fixture and verify expected values."""
        fixtures = Path(__file__).resolve().parents[3] / "fixtures"
        sample = fixtures / "sample_files" / "python" / "sample.py"
        if not sample.exists():
            return
        parser = PythonParser()
        report = parser.parse(sample, sample.parent.parent.parent.parent)
        assert report.num_classes == 1
        assert report.classes[0].name == "Calculator"
        assert report.classes[0].num_methods == 3
        assert report.num_functions == 1
        # CC for add (if/elif/else) = 3
        add_method = next(m for m in report.classes[0].methods if m.name == "add")
        assert add_method.cyclomatic_complexity == 3
        # Attributes: value, history
        assert "value" in report.classes[0].attributes
        assert "history" in report.classes[0].attributes
