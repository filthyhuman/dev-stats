"""Data compressor for embedding analysis data in the HTML dashboard."""

from __future__ import annotations

import base64
import dataclasses
import enum
import json
import zlib
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dev_stats.core.models import RepoReport


class DataCompressor:
    """Compresses ``RepoReport`` data into base64-encoded zlib chunks.

    Produces thematic data chunks (files, commits, branches, etc.) that
    can be embedded as ``<script>`` tags in the dashboard HTML and
    decompressed in the browser via ``DecompressionStream``.
    """

    def compress_report(self, report: RepoReport) -> dict[str, str]:
        """Compress a full report into named base64 chunks.

        Each chunk is a JSON string → zlib-compressed → base64-encoded.

        Args:
            report: The analysis report to compress.

        Returns:
            Mapping of chunk name to base64-encoded compressed data.
        """
        chunks: dict[str, str] = {}

        chunks["meta"] = self._compress_json(
            {
                "root": str(report.root),
                "file_count": len(report.files),
                "language_count": len(report.languages),
                "module_count": len(report.modules),
            }
        )

        chunks["files"] = self._compress_json([self._convert_value(f) for f in report.files])

        chunks["languages"] = self._compress_json(
            [self._convert_value(lang) for lang in report.languages]
        )

        chunks["modules"] = self._compress_json([self._convert_value(m) for m in report.modules])

        if report.duplication is not None:
            chunks["duplication"] = self._compress_json(self._convert_value(report.duplication))

        if report.coupling is not None:
            chunks["coupling"] = self._compress_json(self._convert_value(report.coupling))

        if report.coverage is not None:
            chunks["coverage"] = self._compress_json(self._convert_value(report.coverage))

        if report.file_churn is not None:
            chunks["churn"] = self._compress_json(
                [self._convert_value(c) for c in report.file_churn]
            )

        if report.commits is not None:
            chunks["commits"] = self._compress_json(
                [self._convert_value(c) for c in report.commits]
            )

        if report.enriched_commits is not None:
            chunks["enriched_commits"] = self._compress_json(
                [self._convert_value(ec) for ec in report.enriched_commits]
            )

        if report.branches_report is not None:
            chunks["branches"] = self._compress_json(self._convert_value(report.branches_report))

        if report.contributors is not None:
            chunks["contributors"] = self._compress_json(
                [self._convert_value(c) for c in report.contributors]
            )

        if report.tags is not None:
            chunks["tags"] = self._compress_json([self._convert_value(t) for t in report.tags])

        if report.patterns is not None:
            chunks["patterns"] = self._compress_json(
                [self._convert_value(p) for p in report.patterns]
            )

        if report.timeline is not None:
            chunks["timeline"] = self._compress_json(
                [self._convert_value(t) for t in report.timeline]
            )

        return chunks

    def compress_json(self, data: object) -> str:
        """Compress arbitrary JSON-serialisable data.

        Args:
            data: JSON-serialisable object.

        Returns:
            Base64-encoded zlib-compressed string.
        """
        return self._compress_json(data)

    @staticmethod
    def decompress(compressed: str) -> str:
        """Decompress a base64-encoded zlib string back to JSON.

        Args:
            compressed: Base64-encoded zlib data.

        Returns:
            The original JSON string.
        """
        raw_bytes = base64.b64decode(compressed)
        return zlib.decompress(raw_bytes).decode("utf-8")

    @staticmethod
    def _compress_json(data: object) -> str:
        """Serialise to JSON, compress with zlib, encode as base64.

        Args:
            data: JSON-serialisable object.

        Returns:
            Base64-encoded compressed string.
        """
        json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        compressed = zlib.compress(json_str.encode("utf-8"), level=9)
        return base64.b64encode(compressed).decode("ascii")

    @classmethod
    def _convert_value(cls, value: object) -> object:
        """Convert a value for JSON serialisation.

        Args:
            value: Any dataclass, enum, datetime, Path, or primitive.

        Returns:
            JSON-compatible value.
        """
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, enum.Enum):
            return value.value
        if isinstance(value, (list, tuple)):
            return [cls._convert_value(item) for item in value]
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            result: dict[str, object] = {}
            for fld in dataclasses.fields(value):
                result[fld.name] = cls._convert_value(getattr(value, fld.name))
            return result
        return str(value)
