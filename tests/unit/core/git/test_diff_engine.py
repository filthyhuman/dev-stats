"""Unit tests for DiffEngine."""

from __future__ import annotations

from dev_stats.core.git.diff_engine import DiffEngine

_SAMPLE_DIFF = """\
diff --git a/src/main.py b/src/main.py
index abc1234..def5678 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,5 +10,8 @@ def greet():
     print("hello")
-    print("old")
+    print("new")
+    print("extra1")
+    print("extra2")
     return True
"""


class TestDiffEngineParsing:
    """Tests for parse_diff method."""

    def test_parse_single_hunk(self) -> None:
        """Single hunk is parsed correctly."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(_SAMPLE_DIFF)

        assert len(hunks) == 1
        hunk = hunks[0]
        assert hunk.old_start == 10
        assert hunk.old_count == 5
        assert hunk.new_start == 10
        assert hunk.new_count == 8

    def test_hunk_header_preserved(self) -> None:
        """The full @@ header line is preserved."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(_SAMPLE_DIFF)

        assert hunks[0].header.startswith("@@")
        assert "def greet()" in hunks[0].header

    def test_hunk_lines(self) -> None:
        """Diff lines are categorised correctly."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(_SAMPLE_DIFF)

        lines = hunks[0].lines
        types = [ln.line_type for ln in lines]
        assert "context" in types
        assert "add" in types
        assert "delete" in types

    def test_additions_count(self) -> None:
        """Correct number of additions."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(_SAMPLE_DIFF)

        adds = [ln for ln in hunks[0].lines if ln.line_type == "add"]
        assert len(adds) == 3

    def test_deletions_count(self) -> None:
        """Correct number of deletions."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(_SAMPLE_DIFF)

        deletes = [ln for ln in hunks[0].lines if ln.line_type == "delete"]
        assert len(deletes) == 1

    def test_context_lines_count(self) -> None:
        """Correct number of context lines."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(_SAMPLE_DIFF)

        ctx = [ln for ln in hunks[0].lines if ln.line_type == "context"]
        assert len(ctx) == 2

    def test_line_numbers(self) -> None:
        """Line numbers are tracked correctly."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(_SAMPLE_DIFF)

        first_line = hunks[0].lines[0]
        assert first_line.line_type == "context"
        assert first_line.old_lineno == 10
        assert first_line.new_lineno == 10

    def test_add_line_has_no_old_lineno(self) -> None:
        """Added lines have no old line number."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(_SAMPLE_DIFF)

        adds = [ln for ln in hunks[0].lines if ln.line_type == "add"]
        for ln in adds:
            assert ln.old_lineno is None
            assert ln.new_lineno is not None

    def test_delete_line_has_no_new_lineno(self) -> None:
        """Deleted lines have no new line number."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(_SAMPLE_DIFF)

        deletes = [ln for ln in hunks[0].lines if ln.line_type == "delete"]
        for ln in deletes:
            assert ln.new_lineno is None
            assert ln.old_lineno is not None

    def test_empty_diff(self) -> None:
        """Empty diff returns no hunks."""
        engine = DiffEngine.__new__(DiffEngine)
        assert engine.parse_diff("") == []


class TestDiffEngineMultiHunk:
    """Tests for multi-hunk diffs."""

    _MULTI_HUNK = """\
diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 line1
+inserted
 line2
 line3
@@ -20,3 +21,3 @@
 line20
-old
+new
 line22
"""

    def test_two_hunks(self) -> None:
        """Two hunks are parsed separately."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(self._MULTI_HUNK)
        assert len(hunks) == 2

    def test_second_hunk_start(self) -> None:
        """Second hunk has correct start lines."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(self._MULTI_HUNK)
        assert hunks[1].old_start == 20
        assert hunks[1].new_start == 21


class TestDiffEngineHunkNoCount:
    """Tests for hunk headers without explicit counts."""

    _SINGLE_LINE = """\
@@ -5 +5 @@
-old
+new
"""

    def test_missing_count_defaults_to_one(self) -> None:
        """Missing count defaults to 1."""
        engine = DiffEngine.__new__(DiffEngine)
        hunks = engine.parse_diff(self._SINGLE_LINE)
        assert len(hunks) == 1
        assert hunks[0].old_count == 1
        assert hunks[0].new_count == 1
