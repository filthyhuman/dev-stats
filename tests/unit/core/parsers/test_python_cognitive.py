"""Unit tests for cognitive complexity computation in PythonParser."""

from __future__ import annotations

import ast

from dev_stats.core.parsers.python_parser import _cognitive_complexity


def _cc(source: str) -> int:
    """Parse *source* as a single function and return its cognitive complexity.

    Args:
        source: Python source code containing exactly one function.

    Returns:
        The cognitive complexity score.
    """
    tree = ast.parse(source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return _cognitive_complexity(node)
    msg = "No function found in source"
    raise ValueError(msg)


class TestCognitiveSimple:
    """Simple functions with low or zero cognitive complexity."""

    def test_empty_function(self) -> None:
        """An empty function has cognitive complexity 0."""
        assert _cc("def f():\n    pass\n") == 0

    def test_assignment_only(self) -> None:
        """A function with only assignments has CC 0."""
        assert _cc("def f():\n    x = 1\n    y = 2\n    return x + y\n") == 0

    def test_single_return(self) -> None:
        """A function that just returns a value has CC 0."""
        assert _cc("def f():\n    return 42\n") == 0


class TestCognitiveIfElse:
    """If/elif/else branching."""

    def test_single_if(self) -> None:
        """A single if adds +1."""
        src = "def f(x):\n    if x:\n        return 1\n    return 0\n"
        assert _cc(src) == 1

    def test_if_else(self) -> None:
        """if/else adds +1 (if) +1 (else) = 2."""
        src = "def f(x):\n    if x:\n        return 1\n    else:\n        return 0\n"
        assert _cc(src) == 2

    def test_if_elif_else(self) -> None:
        """if/elif/else: +1 (if) +1 (elif) +1 (else) = 3."""
        src = (
            "def f(x):\n"
            "    if x > 0:\n"
            "        return 1\n"
            "    elif x < 0:\n"
            "        return -1\n"
            "    else:\n"
            "        return 0\n"
        )
        assert _cc(src) == 3

    def test_nested_if(self) -> None:
        """Nested if: outer +1, inner +1 +1(nesting) = 3."""
        src = "def f(x, y):\n    if x:\n        if y:\n            return 1\n    return 0\n"
        assert _cc(src) == 3


class TestCognitiveLoops:
    """For and while loops."""

    def test_single_for(self) -> None:
        """A for loop adds +1."""
        src = "def f():\n    for i in range(10):\n        pass\n"
        assert _cc(src) == 1

    def test_single_while(self) -> None:
        """A while loop adds +1."""
        src = "def f():\n    while True:\n        break\n"
        assert _cc(src) == 1

    def test_for_with_else(self) -> None:
        """for/else: +1 (for) +1 (else) = 2."""
        src = "def f():\n    for i in range(10):\n        pass\n    else:\n        pass\n"
        assert _cc(src) == 2

    def test_nested_loops(self) -> None:
        """Nested loops: outer +1, inner +1 +1(nesting) = 3."""
        src = "def f():\n    for i in range(10):\n        for j in range(10):\n            pass\n"
        assert _cc(src) == 3


class TestCognitiveExceptions:
    """Try/except/finally."""

    def test_single_except(self) -> None:
        """Except adds +1 (try is nesting-only, except is +1)."""
        src = "def f():\n    try:\n        pass\n    except ValueError:\n        pass\n"
        assert _cc(src) == 1

    def test_except_with_finally(self) -> None:
        """Except + finally: +1 (except) +1 (finally) = 2."""
        src = (
            "def f():\n"
            "    try:\n"
            "        pass\n"
            "    except ValueError:\n"
            "        pass\n"
            "    finally:\n"
            "        pass\n"
        )
        assert _cc(src) == 2

    def test_try_else(self) -> None:
        """try/except/else: +1 (except) +1 (else) = 2."""
        src = (
            "def f():\n"
            "    try:\n"
            "        pass\n"
            "    except ValueError:\n"
            "        pass\n"
            "    else:\n"
            "        pass\n"
        )
        assert _cc(src) == 2


class TestCognitiveBooleanOps:
    """Boolean operator chains."""

    def test_single_and(self) -> None:
        """``a and b`` in an if: +1 (if) +1 (and) = 2."""
        src = "def f(a, b):\n    if a and b:\n        return 1\n"
        assert _cc(src) == 2

    def test_single_or(self) -> None:
        """``a or b`` in an if: +1 (if) +1 (or) = 2."""
        src = "def f(a, b):\n    if a or b:\n        return 1\n"
        assert _cc(src) == 2

    def test_chained_same_op(self) -> None:
        """``a and b and c``: still +1 for the single BoolOp sequence."""
        src = "def f(a, b, c):\n    if a and b and c:\n        return 1\n"
        assert _cc(src) == 2  # +1 if, +1 and-chain

    def test_mixed_ops(self) -> None:
        """``a and b or c``: Python nests this as BoolOp(or, [BoolOp(and, ..), c])."""
        src = "def f(a, b, c):\n    if a and b or c:\n        return 1\n"
        assert _cc(src) == 3  # +1 if, +1 outer or, +1 inner and


class TestCognitiveRecursion:
    """Recursive function calls."""

    def test_simple_recursion(self) -> None:
        """Direct recursion adds +1."""
        src = (
            "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n"
        )
        assert _cc(src) == 2  # +1 if, +1 recursion

    def test_no_false_recursion(self) -> None:
        """Calling a different function is not recursion."""
        src = "def f(x):\n    return g(x)\n"
        assert _cc(src) == 0


class TestCognitiveNesting:
    """Deep nesting scenarios."""

    def test_deeply_nested(self) -> None:
        """Three levels of nesting produce high scores."""
        src = (
            "def f(a, b, c, d):\n"
            "    if a:\n"  # +1
            "        for x in b:\n"  # +1 + 1(nesting) = +2
            "            if c:\n"  # +1 + 2(nesting) = +3
            "                while d:\n"  # +1 + 3(nesting) = +4
            "                    pass\n"
        )
        assert _cc(src) == 10

    def test_lambda_adds_nesting(self) -> None:
        """A lambda inside a function adds nesting for inner structures."""
        src = "def f(items):\n    return sorted(items, key=lambda x: x if x > 0 else -x)\n"
        # lambda adds nesting, the ternary if/else inside it: +1 + 1(nesting) + 1(else) = 3
        assert _cc(src) == 3

    def test_nested_function_adds_nesting(self) -> None:
        """A nested function definition adds nesting depth."""
        src = (
            "def outer():\n"
            "    def inner():\n"
            "        if True:\n"  # +1 + 1(nesting from inner) = +2
            "            pass\n"
            "    inner()\n"
        )
        assert _cc(src) == 2


class TestCognitiveComplex:
    """More complex real-world-like scenarios."""

    def test_moderate_function(self) -> None:
        """A moderately complex function."""
        src = (
            "def process(items, threshold):\n"
            "    result = []\n"
            "    for item in items:\n"  # +1
            "        if item.valid:\n"  # +1 + 1(nesting) = +2
            "            if item.value > threshold:\n"  # +1 + 2(nesting) = +3
            "                result.append(item)\n"
            "            else:\n"  # +1 (else)
            "                pass\n"
            "        else:\n"  # +1 (else)
            "            pass\n"
            "    return result\n"
        )
        assert _cc(src) == 8
