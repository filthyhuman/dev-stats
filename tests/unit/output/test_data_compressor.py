"""Unit tests for DataCompressor."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from pathlib import Path

from dev_stats.core.models import (
    FileReport,
    LanguageSummary,
    RepoReport,
)
from dev_stats.output.dashboard.data_compressor import DataCompressor


def _make_report() -> RepoReport:
    """Create a minimal RepoReport for testing."""
    return RepoReport(
        root=Path("/tmp/repo"),
        files=(
            FileReport(
                path=Path("main.py"),
                language="python",
                total_lines=100,
                code_lines=80,
                blank_lines=10,
                comment_lines=10,
            ),
        ),
        languages=(
            LanguageSummary(
                language="python",
                file_count=1,
                total_lines=100,
                code_lines=80,
                blank_lines=10,
                comment_lines=10,
            ),
        ),
    )


class TestDataCompressorCompress:
    """Tests for compression."""

    def test_compress_produces_valid_base64(self) -> None:
        """Compressed output is valid base64."""
        compressor = DataCompressor()
        result = compressor.compress_json({"hello": "world"})

        # Should not raise
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_compress_decompresses_to_json(self) -> None:
        """Compressed output decompresses back to original JSON."""
        compressor = DataCompressor()
        data = {"key": "value", "numbers": [1, 2, 3]}
        compressed = compressor.compress_json(data)

        json_str = compressor.decompress(compressed)
        restored = json.loads(json_str)

        assert restored == data

    def test_compress_report_has_meta(self) -> None:
        """compress_report produces a meta chunk."""
        compressor = DataCompressor()
        report = _make_report()
        chunks = compressor.compress_report(report)

        assert "meta" in chunks
        meta_json = compressor.decompress(chunks["meta"])
        meta = json.loads(meta_json)
        assert meta["file_count"] == 1

    def test_compress_report_has_files(self) -> None:
        """compress_report produces a files chunk."""
        compressor = DataCompressor()
        report = _make_report()
        chunks = compressor.compress_report(report)

        assert "files" in chunks
        files_json = compressor.decompress(chunks["files"])
        files = json.loads(files_json)
        assert len(files) == 1
        assert files[0]["language"] == "python"

    def test_compress_report_has_languages(self) -> None:
        """compress_report produces a languages chunk."""
        compressor = DataCompressor()
        report = _make_report()
        chunks = compressor.compress_report(report)

        assert "languages" in chunks

    def test_compress_report_skips_none_fields(self) -> None:
        """None fields are not included as chunks."""
        compressor = DataCompressor()
        report = _make_report()
        chunks = compressor.compress_report(report)

        # These are None on the minimal report
        assert "commits" not in chunks
        assert "branches" not in chunks
        assert "contributors" not in chunks


class TestDataCompressorDecompress:
    """Tests for decompression."""

    def test_decompress_round_trip(self) -> None:
        """Compress then decompress returns original data."""
        compressor = DataCompressor()
        original = {"nested": {"a": 1}, "list": [1, 2, 3]}
        compressed = compressor.compress_json(original)
        result = json.loads(compressor.decompress(compressed))

        assert result == original

    def test_decompress_handles_unicode(self) -> None:
        """Unicode data survives round-trip."""
        compressor = DataCompressor()
        original = {"name": "Müller", "emoji": "✨"}
        compressed = compressor.compress_json(original)
        result = json.loads(compressor.decompress(compressed))

        assert result == original

    def test_decompress_handles_datetime(self) -> None:
        """Datetime values are serialised as ISO strings."""
        compressor = DataCompressor()
        dt = datetime(2024, 6, 15, 10, 30, 0, tzinfo=UTC)
        compressed = compressor.compress_json(compressor._convert_value(dt))
        result = json.loads(compressor.decompress(compressed))

        assert "2024-06-15" in result


class TestDataCompressorSize:
    """Tests for compression effectiveness."""

    def test_compressed_smaller_than_json(self) -> None:
        """Compressed output is smaller than raw JSON."""
        compressor = DataCompressor()
        data = [{"path": f"file_{i}.py", "lines": i * 10} for i in range(100)]
        json_str = json.dumps(data)
        compressed = compressor.compress_json(data)

        # base64 adds ~33% overhead, but zlib should still win on
        # repetitive data
        assert len(compressed) < len(json_str)
