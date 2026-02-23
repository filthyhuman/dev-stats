"""Asset embedder producing base64 data URIs for dashboard assets."""

from __future__ import annotations

import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Directory containing the dashboard template assets.
_ASSETS_DIR = Path(__file__).parent / "templates" / "assets"

# MIME types for asset file extensions.
_MIME_TYPES: dict[str, str] = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".html": "text/html",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".gif": "image/gif",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
}


class AssetEmbedder:
    """Embeds dashboard assets as base64 data URIs.

    Reads static asset files (CSS, JS, images) from the templates/assets
    directory and produces ``data:`` URIs suitable for embedding in a
    self-contained HTML file.
    """

    def __init__(self, assets_dir: Path | None = None) -> None:
        """Initialise the asset embedder.

        Args:
            assets_dir: Path to the assets directory.
                Defaults to the built-in ``templates/assets``.
        """
        self._assets_dir = assets_dir or _ASSETS_DIR

    def embed_all(self) -> dict[str, str]:
        """Embed all known dashboard assets.

        Returns:
            Mapping of asset key to data URI string.
            Keys: ``chart_js_uri``, ``css_uri``, ``app_js_uri``.
        """
        result: dict[str, str] = {}

        chart_path = self._assets_dir / "chart.min.js"
        if chart_path.exists():
            result["chart_js_uri"] = self.file_to_data_uri(chart_path)

        css_path = self._assets_dir / "styles.css"
        if css_path.exists():
            result["css_uri"] = self.file_to_data_uri(css_path)

        app_path = self._assets_dir / "app.js"
        if app_path.exists():
            result["app_js_uri"] = self.file_to_data_uri(app_path)

        return result

    def embed_file(self, filename: str) -> str | None:
        """Embed a single file from the assets directory.

        Args:
            filename: Name of the file within the assets directory.

        Returns:
            Data URI string, or ``None`` if the file does not exist.
        """
        path = self._assets_dir / filename
        if not path.exists():
            logger.debug("Asset file not found: %s", path)
            return None
        return self.file_to_data_uri(path)

    @staticmethod
    def file_to_data_uri(path: Path) -> str:
        """Convert a file to a base64 data URI.

        Args:
            path: Absolute or relative path to the file.

        Returns:
            A ``data:<mime>;base64,<encoded>`` string.
        """
        suffix = path.suffix.lower()
        mime = _MIME_TYPES.get(suffix, "application/octet-stream")

        content = path.read_bytes()
        encoded = base64.b64encode(content).decode("ascii")

        return f"data:{mime};base64,{encoded}"

    @staticmethod
    def inline_css(path: Path) -> str:
        """Read a CSS file and return its contents for inline embedding.

        Args:
            path: Path to the CSS file.

        Returns:
            CSS text content.
        """
        return path.read_text(encoding="utf-8")

    @staticmethod
    def inline_js(path: Path) -> str:
        """Read a JS file and return its contents for inline embedding.

        Args:
            path: Path to the JavaScript file.

        Returns:
            JavaScript text content.
        """
        return path.read_text(encoding="utf-8")
