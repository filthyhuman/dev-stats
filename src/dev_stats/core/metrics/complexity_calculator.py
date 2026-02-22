"""Complexity metrics calculator for code analysis."""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport

# Tokens that increase cyclomatic complexity (language-agnostic heuristic).
_CC_KEYWORDS = re.compile(
    r"\b(?:if|else\s+if|elif|for|foreach|while|case|catch|except)\b"
    r"|&&|\|\|"
)

# Tokens that increase cognitive complexity with extra weight for nesting.
_COGNITIVE_KEYWORDS = re.compile(r"\b(?:if|elif|else\s+if|for|foreach|while|catch|except)\b")

_NESTING_OPENERS = re.compile(r"\b(?:if|for|foreach|while|try|switch|match)\b")

# Halstead operator / operand approximation tokens.
_OPERATORS = re.compile(
    r"(?:[+\-*/%]=?|==|!=|<=?|>=?|&&|\|\||!|~|\^|&|\|"
    r"|<<|>>|\.|\->|::|=>|\?|:|\bas\b|\bin\b|\bnot\b|\band\b|\bor\b)"
)
_OPERANDS = re.compile(r"\b(?:[a-zA-Z_]\w*|\d+(?:\.\d+)?)\b")


class ComplexityCalculator:
    """Computes complexity metrics for source code.

    Provides cyclomatic, cognitive, Halstead, and nesting-depth metrics
    using language-agnostic heuristics on source text.
    """

    def cyclomatic(self, source: str) -> int:
        """Compute approximate McCabe cyclomatic complexity.

        Args:
            source: Source code text (single function or whole file).

        Returns:
            Cyclomatic complexity (minimum 1).
        """
        return 1 + len(_CC_KEYWORDS.findall(source))

    def cognitive(self, source: str) -> int:
        """Compute approximate cognitive complexity.

        Increments for each control-flow break, with extra weight for
        nesting depth at the point of the break.

        Args:
            source: Source code text.

        Returns:
            Cognitive complexity score.
        """
        score = 0
        nesting = 0
        for line in source.splitlines():
            stripped = line.strip()
            # Track nesting via braces / indentation heuristic
            nesting += stripped.count("{") - stripped.count("}")
            nesting = max(0, nesting)

            for _match in _COGNITIVE_KEYWORDS.finditer(stripped):
                score += 1 + nesting
        return score

    def nesting_depth(self, source: str) -> int:
        """Compute maximum nesting depth via brace counting.

        Args:
            source: Source code text.

        Returns:
            Maximum nesting depth observed.
        """
        max_depth = 0
        current = 0
        for char in source:
            if char == "{":
                current += 1
                max_depth = max(max_depth, current)
            elif char == "}":
                current = max(0, current - 1)
        return max_depth

    def halstead(self, source: str) -> dict[str, float]:
        """Compute Halstead complexity metrics.

        Args:
            source: Source code text.

        Returns:
            Dictionary with keys: ``n1`` (unique operators), ``n2`` (unique
            operands), ``N1`` (total operators), ``N2`` (total operands),
            ``vocabulary``, ``length``, ``volume``, ``difficulty``, ``effort``.
        """
        operators = _OPERATORS.findall(source)
        operands = _OPERANDS.findall(source)

        n1 = len(set(operators))
        n2 = len(set(operands))
        big_n1 = len(operators)
        big_n2 = len(operands)

        vocabulary = n1 + n2
        length = big_n1 + big_n2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0.0
        difficulty = (n1 / 2.0) * (big_n2 / n2) if n2 > 0 else 0.0
        effort = volume * difficulty

        return {
            "n1": float(n1),
            "n2": float(n2),
            "N1": float(big_n1),
            "N2": float(big_n2),
            "vocabulary": float(vocabulary),
            "length": float(length),
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort,
        }

    def file_average_cc(self, report: FileReport) -> float:
        """Compute average cyclomatic complexity across all methods in a file.

        Args:
            report: A file report with extracted methods.

        Returns:
            Average CC, or 0.0 if no methods.
        """
        all_methods = list(report.functions)
        for cls in report.classes:
            all_methods.extend(cls.methods)
        if not all_methods:
            return 0.0
        return sum(m.cyclomatic_complexity for m in all_methods) / len(all_methods)
