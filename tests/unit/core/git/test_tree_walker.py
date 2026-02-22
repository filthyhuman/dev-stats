"""Unit tests for TreeWalker."""

from __future__ import annotations

from dev_stats.core.git.tree_walker import TreeWalker

_SAMPLE_LS_TREE = """\
100644 blob abc123def456abc123def456abc123def456abc1     150\tsrc/main.py
100644 blob abc123def456abc123def456abc123def456abc2     200\tsrc/utils.py
100644 blob abc123def456abc123def456abc123def456abc3      50\tREADME.md
100755 blob abc123def456abc123def456abc123def456abc4     100\tscripts/deploy.sh
160000 commit abc123def456abc123def456abc123def456abc5       -\tvendor/lib
"""


class TestTreeWalkerParsing:
    """Tests for _parse_ls_tree static method."""

    def test_parse_entries(self) -> None:
        """All entries are parsed."""
        entries = TreeWalker._parse_ls_tree(_SAMPLE_LS_TREE)
        assert len(entries) == 5

    def test_blob_entry(self) -> None:
        """Blob entries have correct type and size."""
        entries = TreeWalker._parse_ls_tree(_SAMPLE_LS_TREE)
        main = entries[0]
        assert main.entry_type == "blob"
        assert main.path == "src/main.py"
        assert main.size == 150
        assert main.mode == "100644"

    def test_submodule_entry(self) -> None:
        """Submodule (commit) entries have type 'commit' and size -1."""
        entries = TreeWalker._parse_ls_tree(_SAMPLE_LS_TREE)
        submod = entries[4]
        assert submod.entry_type == "commit"
        assert submod.path == "vendor/lib"
        assert submod.size == -1

    def test_executable_mode(self) -> None:
        """Executable file mode is preserved."""
        entries = TreeWalker._parse_ls_tree(_SAMPLE_LS_TREE)
        script = entries[3]
        assert script.mode == "100755"

    def test_empty_output(self) -> None:
        """Empty output returns empty list."""
        assert TreeWalker._parse_ls_tree("") == []


class TestTreeWalkerDirectorySizes:
    """Tests for directory_sizes method."""

    def test_directory_sizes(self) -> None:
        """Sizes are aggregated per directory."""
        entries = TreeWalker._parse_ls_tree(_SAMPLE_LS_TREE)

        sizes: dict[str, int] = {}
        for entry in entries:
            if entry.size < 0:
                continue
            parts = entry.path.rsplit("/", 1)
            directory = parts[0] if len(parts) > 1 else "(root)"
            sizes[directory] = sizes.get(directory, 0) + entry.size

        assert sizes["src"] == 350  # 150 + 200
        assert sizes["(root)"] == 50  # README.md
        assert sizes["scripts"] == 100


class TestTreeWalkerSubmodules:
    """Tests for submodule detection."""

    def test_submodules_detected(self) -> None:
        """Submodule entries are filtered correctly."""
        entries = TreeWalker._parse_ls_tree(_SAMPLE_LS_TREE)
        submodules = [e for e in entries if e.entry_type == "commit"]
        assert len(submodules) == 1
        assert submodules[0].path == "vendor/lib"
