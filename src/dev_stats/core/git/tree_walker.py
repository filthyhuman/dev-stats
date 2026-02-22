"""Tree walker for git ls-tree with directory sizes and submodule detection."""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

from dev_stats.core.models import TreeEntry

if TYPE_CHECKING:
    from pathlib import Path

# ls-tree -r -l output: mode<SP>type<SP>sha<SP>size<TAB>path
# Size is "-" for trees/submodules.
_LS_TREE_RE = re.compile(r"^(\d{6})\s+(blob|tree|commit)\s+([0-9a-f]{40})\s+(-|\d+)\t(.+)$")


class TreeWalker:
    """Walks the git object tree to list files, sizes, and detect submodules.

    Uses ``git ls-tree -r -l`` for efficient recursive listing with sizes.
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialise the tree walker.

        Args:
            repo_path: Absolute path to the repository root.
        """
        self._repo_path = repo_path

    def walk(self, ref: str = "HEAD") -> list[TreeEntry]:
        """Walk the tree at the given ref.

        Args:
            ref: Git ref to walk (default ``HEAD``).

        Returns:
            List of ``TreeEntry`` objects for all entries.
        """
        raw = self._run_git("git", "ls-tree", "-r", "-l", ref)
        return self._parse_ls_tree(raw)

    def directory_sizes(self, ref: str = "HEAD") -> dict[str, int]:
        """Compute total size per directory.

        Args:
            ref: Git ref to walk.

        Returns:
            Mapping of directory path to total size in bytes.
        """
        entries = self.walk(ref)
        sizes: dict[str, int] = {}
        for entry in entries:
            if entry.size < 0:
                continue
            parts = entry.path.rsplit("/", 1)
            directory = parts[0] if len(parts) > 1 else "(root)"
            sizes[directory] = sizes.get(directory, 0) + entry.size
        return sizes

    def submodules(self, ref: str = "HEAD") -> list[TreeEntry]:
        """Detect submodules (entries with type ``commit``).

        Args:
            ref: Git ref to walk.

        Returns:
            List of ``TreeEntry`` objects for submodules.
        """
        return [e for e in self.walk(ref) if e.entry_type == "commit"]

    def _run_git(self, *args: str) -> str:
        """Execute a git command and return stdout.

        Args:
            *args: Full command arguments.

        Returns:
            Standard output as a string.
        """
        result = subprocess.run(
            list(args),
            cwd=self._repo_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout

    @staticmethod
    def _parse_ls_tree(raw: str) -> list[TreeEntry]:
        """Parse ``git ls-tree -r -l`` output.

        Args:
            raw: Raw ls-tree output.

        Returns:
            List of ``TreeEntry`` objects.
        """
        entries: list[TreeEntry] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            m = _LS_TREE_RE.match(line)
            if m:
                mode = m.group(1)
                entry_type = m.group(2)
                sha = m.group(3)
                size_str = m.group(4)
                path = m.group(5)
                size = int(size_str) if size_str != "-" else -1
                entries.append(
                    TreeEntry(
                        mode=mode,
                        entry_type=entry_type,
                        sha=sha,
                        path=path,
                        size=size,
                    )
                )
        return entries
