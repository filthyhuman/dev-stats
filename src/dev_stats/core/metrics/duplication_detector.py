"""Duplication detector using Rabin-Karp rolling hash."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dev_stats.core.models import DuplicateBlock, DuplicationReport

if TYPE_CHECKING:
    from dev_stats.core.models import FileReport

logger = logging.getLogger(__name__)

# Rolling hash constants.
_BASE = 257
_MOD = 1_000_000_007


class DuplicationDetector:
    """Detects duplicated code blocks across files using Rabin-Karp hashing.

    Compares normalized (stripped, lowered) lines to find blocks of
    ``min_lines`` or more identical consecutive lines.
    """

    def __init__(self, min_lines: int = 6) -> None:
        """Initialise with the minimum block size.

        Args:
            min_lines: Minimum number of consecutive identical lines to
                       count as a duplicate.
        """
        self._min_lines = min_lines

    def detect(self, files: list[FileReport]) -> DuplicationReport:
        """Scan all files for duplicated code blocks.

        Args:
            files: File reports with path information.

        Returns:
            A ``DuplicationReport`` with detected duplicates and ratio.
        """
        # Build a map of file path -> normalized lines
        file_lines: dict[str, list[str]] = {}
        total_code_lines = 0

        for f in files:
            try:
                from pathlib import Path

                path = Path(f.path)
                if not path.is_absolute():
                    # Skip files we can't read directly
                    continue
                source = path.read_text(errors="replace")
            except OSError:
                continue

            lines = self._normalize(source)
            if len(lines) >= self._min_lines:
                file_lines[str(f.path)] = lines
            total_code_lines += f.code_lines

        # Find duplicates using rolling hash
        duplicates = self._find_duplicates(file_lines)
        total_dup_lines = sum(d.length for d in duplicates)
        ratio = total_dup_lines / total_code_lines if total_code_lines > 0 else 0.0

        return DuplicationReport(
            duplicates=tuple(duplicates),
            total_duplicated_lines=total_dup_lines,
            duplication_ratio=ratio,
        )

    def detect_from_sources(self, sources: dict[str, str]) -> DuplicationReport:
        """Detect duplicates from in-memory source strings.

        Args:
            sources: Mapping of file path to source code.

        Returns:
            A ``DuplicationReport``.
        """
        file_lines: dict[str, list[str]] = {}
        total_lines = 0

        for path, source in sources.items():
            lines = self._normalize(source)
            if len(lines) >= self._min_lines:
                file_lines[path] = lines
            total_lines += len([ln for ln in source.splitlines() if ln.strip()])

        duplicates = self._find_duplicates(file_lines)
        total_dup = sum(d.length for d in duplicates)
        ratio = total_dup / total_lines if total_lines > 0 else 0.0

        return DuplicationReport(
            duplicates=tuple(duplicates),
            total_duplicated_lines=total_dup,
            duplication_ratio=ratio,
        )

    @staticmethod
    def _normalize(source: str) -> list[str]:
        """Normalize source lines for comparison.

        Args:
            source: Raw source text.

        Returns:
            List of stripped, lowered, non-empty lines.
        """
        return [line.strip().lower() for line in source.splitlines() if line.strip()]

    def _find_duplicates(self, file_lines: dict[str, list[str]]) -> list[DuplicateBlock]:
        """Find duplicate blocks across all file pairs.

        Args:
            file_lines: Mapping of file path to normalized lines.

        Returns:
            List of ``DuplicateBlock`` objects.
        """
        # Build hash index: hash -> list of (file, start_line)
        hash_index: dict[int, list[tuple[str, int]]] = {}
        window = self._min_lines

        for path, lines in file_lines.items():
            if len(lines) < window:
                continue
            for start in range(len(lines) - window + 1):
                block = lines[start : start + window]
                h = self._hash_block(block)
                hash_index.setdefault(h, []).append((path, start + 1))

        # Find collisions that are actual duplicates
        duplicates: list[DuplicateBlock] = []
        seen: set[tuple[str, int, str, int]] = set()

        for locations in hash_index.values():
            if len(locations) < 2:
                continue
            for i in range(len(locations)):
                for j in range(i + 1, len(locations)):
                    fa, la = locations[i]
                    fb, lb = locations[j]
                    if fa == fb and abs(la - lb) < window:
                        continue
                    key = (fa, la, fb, lb)
                    if key in seen:
                        continue
                    seen.add(key)

                    # Verify the blocks actually match
                    block_a = file_lines[fa][la - 1 : la - 1 + window]
                    block_b = file_lines[fb][lb - 1 : lb - 1 + window]
                    if block_a == block_b:
                        duplicates.append(
                            DuplicateBlock(
                                file_a=fa,
                                file_b=fb,
                                line_a=la,
                                line_b=lb,
                                length=window,
                            )
                        )

        return duplicates

    @staticmethod
    def _hash_block(block: list[str]) -> int:
        """Compute a rolling hash for a block of lines.

        Args:
            block: Normalized lines.

        Returns:
            Hash value.
        """
        h = 0
        for line in block:
            for ch in line:
                h = (h * _BASE + ord(ch)) % _MOD
        return h
