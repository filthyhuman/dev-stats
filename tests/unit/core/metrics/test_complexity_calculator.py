"""Unit tests for ComplexityCalculator."""

from __future__ import annotations

from pathlib import Path

from dev_stats.core.metrics.complexity_calculator import ComplexityCalculator
from dev_stats.core.models import ClassReport, FileReport, MethodReport


class TestCyclomaticComplexity:
    """Tests for cyclomatic complexity computation."""

    def test_simple_function_cc_one(self) -> None:
        """Straight-line code has CC=1."""
        calc = ComplexityCalculator()
        src = "def foo():\n    return 1\n"
        assert calc.cyclomatic(src) == 1

    def test_single_if_cc_two(self) -> None:
        """A single if branch adds 1."""
        calc = ComplexityCalculator()
        src = "if x > 0:\n    return 1\nreturn 0\n"
        assert calc.cyclomatic(src) == 2

    def test_if_elif_else_cc_three(self) -> None:
        """If/elif adds 2 branches."""
        calc = ComplexityCalculator()
        src = "if x > 0:\n    pass\nelif x < 0:\n    pass\nelse:\n    pass\n"
        assert calc.cyclomatic(src) == 3

    def test_for_loop_adds_one(self) -> None:
        """A for loop adds 1."""
        calc = ComplexityCalculator()
        src = "for i in range(10):\n    pass\n"
        assert calc.cyclomatic(src) == 2

    def test_logical_operators(self) -> None:
        """&& and || add to CC."""
        calc = ComplexityCalculator()
        src = "if (a && b || c) {\n}\n"
        # if + && + || = 3 branches + 1 base = 4
        assert calc.cyclomatic(src) >= 4


class TestCognitiveComplexity:
    """Tests for cognitive complexity computation."""

    def test_simple_code_zero(self) -> None:
        """Code without control flow has cognitive=0."""
        calc = ComplexityCalculator()
        src = "int x = 1;\nreturn x;\n"
        assert calc.cognitive(src) == 0

    def test_nested_increases_weight(self) -> None:
        """Nested control flow has higher cognitive complexity."""
        calc = ComplexityCalculator()
        flat_src = "if (x) {\n    return 1;\n}\nif (y) {\n    return 2;\n}\n"
        nested_src = "if (x) {\n    if (y) {\n        return 1;\n    }\n}\n"
        flat_score = calc.cognitive(flat_src)
        nested_score = calc.cognitive(nested_src)
        assert nested_score > flat_score


class TestNestingDepth:
    """Tests for nesting depth computation."""

    def test_flat_code_depth_zero(self) -> None:
        """No braces means depth 0."""
        calc = ComplexityCalculator()
        assert calc.nesting_depth("x = 1\nreturn x\n") == 0

    def test_single_block(self) -> None:
        """Single brace pair is depth 1."""
        calc = ComplexityCalculator()
        assert calc.nesting_depth("if (x) {\n    return 1;\n}\n") == 1

    def test_nested_blocks(self) -> None:
        """Nested braces give higher depth."""
        calc = ComplexityCalculator()
        src = "if (x) {\n    if (y) {\n        if (z) {\n        }\n    }\n}\n"
        assert calc.nesting_depth(src) == 3


class TestHalstead:
    """Tests for Halstead metrics."""

    def test_basic_halstead(self) -> None:
        """Halstead returns expected keys."""
        calc = ComplexityCalculator()
        result = calc.halstead("x = a + b * c")
        assert "volume" in result
        assert "difficulty" in result
        assert "effort" in result
        assert result["volume"] > 0

    def test_empty_source(self) -> None:
        """Empty source returns zero volume."""
        calc = ComplexityCalculator()
        result = calc.halstead("")
        assert result["volume"] == 0.0


class TestFileAverageCC:
    """Tests for file_average_cc."""

    def test_average_cc(self) -> None:
        """Average CC across multiple methods."""
        calc = ComplexityCalculator()
        m1 = MethodReport(name="a", line=1, end_line=5, lines=5, cyclomatic_complexity=2)
        m2 = MethodReport(name="b", line=6, end_line=10, lines=5, cyclomatic_complexity=4)
        report = FileReport(
            path=Path("test.py"),
            language="python",
            total_lines=10,
            code_lines=10,
            blank_lines=0,
            comment_lines=0,
            functions=(m1, m2),
        )
        assert calc.file_average_cc(report) == 3.0

    def test_no_methods_returns_zero(self) -> None:
        """No methods returns 0.0."""
        calc = ComplexityCalculator()
        report = FileReport(
            path=Path("test.py"),
            language="python",
            total_lines=0,
            code_lines=0,
            blank_lines=0,
            comment_lines=0,
        )
        assert calc.file_average_cc(report) == 0.0

    def test_includes_class_methods(self) -> None:
        """Class methods are included in the average."""
        calc = ComplexityCalculator()
        m1 = MethodReport(name="foo", line=1, end_line=5, lines=5, cyclomatic_complexity=3)
        cls = ClassReport(name="Foo", line=1, end_line=10, lines=10, methods=(m1,))
        report = FileReport(
            path=Path("test.py"),
            language="python",
            total_lines=10,
            code_lines=10,
            blank_lines=0,
            comment_lines=0,
            classes=(cls,),
        )
        assert calc.file_average_cc(report) == 3.0
