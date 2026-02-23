"""Unit tests for AssetEmbedder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dev_stats.output.dashboard.asset_embedder import AssetEmbedder

if TYPE_CHECKING:
    from pathlib import Path


class TestAssetEmbedderDataUri:
    """Tests for data URI generation."""

    def test_file_to_data_uri_js(self, tmp_path: Path) -> None:
        """JS file produces data:application/javascript URI."""
        js_file = tmp_path / "test.js"
        js_file.write_text("console.log('hello');")

        uri = AssetEmbedder.file_to_data_uri(js_file)

        assert uri.startswith("data:application/javascript;base64,")

    def test_file_to_data_uri_css(self, tmp_path: Path) -> None:
        """CSS file produces data:text/css URI."""
        css_file = tmp_path / "test.css"
        css_file.write_text("body { color: red; }")

        uri = AssetEmbedder.file_to_data_uri(css_file)

        assert uri.startswith("data:text/css;base64,")

    def test_file_to_data_uri_contains_base64(self, tmp_path: Path) -> None:
        """Data URI contains base64-encoded content."""
        js_file = tmp_path / "test.js"
        js_file.write_text("var x = 1;")

        uri = AssetEmbedder.file_to_data_uri(js_file)

        # After the base64, prefix there should be actual base64 data
        base64_part = uri.split(",", 1)[1]
        assert len(base64_part) > 0

    def test_unknown_extension(self, tmp_path: Path) -> None:
        """Unknown file extension uses octet-stream MIME type."""
        file = tmp_path / "data.xyz"
        file.write_bytes(b"\x00\x01\x02")

        uri = AssetEmbedder.file_to_data_uri(file)

        assert uri.startswith("data:application/octet-stream;base64,")


class TestAssetEmbedderEmbedAll:
    """Tests for embed_all with real assets."""

    def test_embed_all_with_assets(self, tmp_path: Path) -> None:
        """embed_all returns URIs for all known assets."""
        (tmp_path / "chart.min.js").write_text("// chart")
        (tmp_path / "styles.css").write_text("body {}")
        (tmp_path / "app.js").write_text("// app")

        embedder = AssetEmbedder(assets_dir=tmp_path)
        result = embedder.embed_all()

        assert "chart_js_uri" in result
        assert "css_uri" in result
        assert "app_js_uri" in result
        assert result["chart_js_uri"].startswith("data:")
        assert result["css_uri"].startswith("data:")
        assert result["app_js_uri"].startswith("data:")

    def test_embed_all_missing_files(self, tmp_path: Path) -> None:
        """embed_all skips missing asset files."""
        embedder = AssetEmbedder(assets_dir=tmp_path)
        result = embedder.embed_all()

        assert result == {}

    def test_embed_all_partial(self, tmp_path: Path) -> None:
        """embed_all handles partially available assets."""
        (tmp_path / "styles.css").write_text("body {}")

        embedder = AssetEmbedder(assets_dir=tmp_path)
        result = embedder.embed_all()

        assert "css_uri" in result
        assert "chart_js_uri" not in result
        assert "app_js_uri" not in result


class TestAssetEmbedderEmbedFile:
    """Tests for single file embedding."""

    def test_embed_existing_file(self, tmp_path: Path) -> None:
        """Existing file returns data URI."""
        (tmp_path / "test.js").write_text("// test")

        embedder = AssetEmbedder(assets_dir=tmp_path)
        result = embedder.embed_file("test.js")

        assert result is not None
        assert result.startswith("data:")

    def test_embed_missing_file(self, tmp_path: Path) -> None:
        """Missing file returns None."""
        embedder = AssetEmbedder(assets_dir=tmp_path)
        result = embedder.embed_file("nonexistent.js")

        assert result is None


class TestAssetEmbedderInline:
    """Tests for inline CSS/JS reading."""

    def test_inline_css(self, tmp_path: Path) -> None:
        """inline_css reads CSS file contents."""
        css_file = tmp_path / "styles.css"
        css_file.write_text("body { margin: 0; }")

        content = AssetEmbedder.inline_css(css_file)

        assert content == "body { margin: 0; }"

    def test_inline_js(self, tmp_path: Path) -> None:
        """inline_js reads JS file contents."""
        js_file = tmp_path / "app.js"
        js_file.write_text("const x = 42;")

        content = AssetEmbedder.inline_js(js_file)

        assert content == "const x = 42;"


class TestAssetEmbedderBuiltInAssets:
    """Tests with the actual built-in assets."""

    def test_builtin_assets_exist(self) -> None:
        """Built-in asset files exist and can be embedded."""
        embedder = AssetEmbedder()
        result = embedder.embed_all()

        # All three should be present since we created them
        assert "chart_js_uri" in result
        assert "css_uri" in result
        assert "app_js_uri" in result

    def test_builtin_chart_js_has_content(self) -> None:
        """Chart.js placeholder has meaningful content."""
        embedder = AssetEmbedder()
        result = embedder.embed_file("chart.min.js")

        assert result is not None
        assert len(result) > 100

    def test_builtin_css_has_content(self) -> None:
        """CSS file has meaningful content."""
        embedder = AssetEmbedder()
        result = embedder.embed_file("styles.css")

        assert result is not None
        assert len(result) > 100

    def test_builtin_app_js_has_content(self) -> None:
        """App.js has meaningful content."""
        embedder = AssetEmbedder()
        result = embedder.embed_file("app.js")

        assert result is not None
        assert len(result) > 100
