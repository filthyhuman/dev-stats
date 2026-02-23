/**
 * dev-stats dashboard — app.js
 *
 * Client-side JavaScript for the self-contained HTML dashboard.
 * Provides:
 * - TableSorter: click-to-sort on any data table
 * - FilterBar: live search/filter for table rows
 * - TabManager: tab switching with URL hash state
 * - DataLoader: decompresses embedded zlib/base64 data chunks
 */

/* ------------------------------------------------------------------ */
/* TableSorter                                                        */
/* ------------------------------------------------------------------ */

class TableSorter {
  /**
   * Attach click-to-sort behaviour to a table element.
   * @param {HTMLTableElement} table
   */
  constructor(table) {
    this.table = table;
    this.tbody = table.querySelector("tbody");
    this.headers = Array.from(table.querySelectorAll("thead th"));
    this.currentCol = -1;
    this.ascending = true;

    this.headers.forEach((th, index) => {
      th.addEventListener("click", () => this.sort(index));
    });
  }

  /**
   * Sort the table by the given column index.
   * @param {number} colIndex
   */
  sort(colIndex) {
    if (this.currentCol === colIndex) {
      this.ascending = !this.ascending;
    } else {
      this.currentCol = colIndex;
      const defaultDesc = this.headers[colIndex].dataset.defaultDesc === "true";
      this.ascending = !defaultDesc;
    }

    // Update header indicators
    this.headers.forEach((th) => th.removeAttribute("data-sort-dir"));
    this.headers[colIndex].setAttribute(
      "data-sort-dir",
      this.ascending ? "asc" : "desc"
    );

    const rows = Array.from(this.tbody.querySelectorAll("tr"));
    const sortType = this.headers[colIndex].dataset.sortType || "string";

    rows.sort((a, b) => {
      const aVal = this._cellValue(a, colIndex, sortType);
      const bVal = this._cellValue(b, colIndex, sortType);
      let cmp = 0;

      if (sortType === "integer" || sortType === "float") {
        cmp = aVal - bVal;
      } else if (sortType === "date") {
        cmp = new Date(aVal) - new Date(bVal);
      } else {
        cmp = String(aVal).localeCompare(String(bVal));
      }

      return this.ascending ? cmp : -cmp;
    });

    // Re-append rows in sorted order
    rows.forEach((row) => this.tbody.appendChild(row));
  }

  /**
   * Extract and coerce the cell value for sorting.
   * @param {HTMLTableRowElement} row
   * @param {number} colIndex
   * @param {string} sortType
   * @returns {*}
   */
  _cellValue(row, colIndex, sortType) {
    const cell = row.cells[colIndex];
    if (!cell) return "";
    const text = cell.textContent.trim();

    switch (sortType) {
      case "integer":
        return parseInt(text, 10) || 0;
      case "float":
        return parseFloat(text) || 0;
      case "date":
        return text;
      case "boolean":
        return text.toLowerCase() === "true" ? 1 : 0;
      default:
        return text.toLowerCase();
    }
  }
}

/* ------------------------------------------------------------------ */
/* FilterBar                                                          */
/* ------------------------------------------------------------------ */

class FilterBar {
  /**
   * Attach live search filtering to a table.
   * @param {HTMLInputElement} input
   * @param {HTMLTableElement} table
   * @param {HTMLElement} [countEl]  Element to show match count
   */
  constructor(input, table, countEl) {
    this.input = input;
    this.table = table;
    this.countEl = countEl || null;
    this.tbody = table.querySelector("tbody");

    this.input.addEventListener("input", () => this.filter());
  }

  /** Run the filter based on current input value. */
  filter() {
    const query = this.input.value.toLowerCase().trim();
    const rows = Array.from(this.tbody.querySelectorAll("tr"));
    let visible = 0;

    rows.forEach((row) => {
      const text = row.textContent.toLowerCase();
      const match = !query || text.includes(query);
      row.style.display = match ? "" : "none";
      if (match) visible++;
    });

    if (this.countEl) {
      this.countEl.textContent = `${visible} / ${rows.length}`;
    }
  }
}

/* ------------------------------------------------------------------ */
/* TabManager                                                         */
/* ------------------------------------------------------------------ */

class TabManager {
  /**
   * Manage tab switching with URL hash state persistence.
   * @param {string} containerSelector  CSS selector for the tab container
   */
  constructor(containerSelector) {
    this.container = document.querySelector(containerSelector);
    if (!this.container) return;

    this.tabs = Array.from(this.container.querySelectorAll(".tab"));
    this.panels = Array.from(
      this.container.parentElement.querySelectorAll(".tab-panel")
    );

    this.tabs.forEach((tab) => {
      tab.addEventListener("click", () => this.activate(tab.dataset.tab));
    });

    // Restore from URL hash
    window.addEventListener("hashchange", () => this._onHash());
    this._onHash();
  }

  /**
   * Activate a tab by its ID.
   * @param {string} tabId
   */
  activate(tabId) {
    this.tabs.forEach((t) => t.classList.toggle("tab--active", t.dataset.tab === tabId));
    this.panels.forEach((p) =>
      p.classList.toggle("tab-panel--active", p.id === tabId)
    );

    // Update URL hash without scrolling
    history.replaceState(null, "", `#${tabId}`);
  }

  /** Handle hash changes. */
  _onHash() {
    const hash = location.hash.slice(1);
    if (hash && this.tabs.some((t) => t.dataset.tab === hash)) {
      this.activate(hash);
    } else if (this.tabs.length > 0) {
      this.activate(this.tabs[0].dataset.tab);
    }
  }
}

/* ------------------------------------------------------------------ */
/* DataLoader                                                         */
/* ------------------------------------------------------------------ */

class DataLoader {
  /**
   * Decompress base64-encoded zlib data embedded in script tags.
   *
   * Looks for <script type="application/x-devstats-data"> elements
   * whose data-chunk attribute names the chunk.
   */

  /**
   * Load and decompress a named data chunk.
   * @param {string} chunkName
   * @returns {Promise<Object|null>}
   */
  static async load(chunkName) {
    const script = document.querySelector(
      `script[data-chunk="${chunkName}"]`
    );
    if (!script) return null;

    try {
      const base64 = script.textContent.trim();
      const binary = atob(base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }

      // Use DecompressionStream if available, else fallback
      if (typeof DecompressionStream !== "undefined") {
        const ds = new DecompressionStream("deflate");
        const writer = ds.writable.getWriter();
        const reader = ds.readable.getReader();

        // zlib = 2-byte header + deflate + adler32
        // DecompressionStream("deflate") handles raw deflate
        // Strip zlib header (2 bytes) and checksum (4 bytes)
        const rawDeflate = bytes.slice(2, -4);
        writer.write(rawDeflate);
        writer.close();

        const chunks = [];
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
        }

        const totalLength = chunks.reduce((acc, c) => acc + c.length, 0);
        const result = new Uint8Array(totalLength);
        let offset = 0;
        for (const chunk of chunks) {
          result.set(chunk, offset);
          offset += chunk.length;
        }

        const text = new TextDecoder().decode(result);
        return JSON.parse(text);
      }

      // Fallback: try pako if available
      if (typeof pako !== "undefined") {
        const text = pako.inflate(bytes, { to: "string" });
        return JSON.parse(text);
      }

      console.warn("No decompression method available for chunk:", chunkName);
      return null;
    } catch (e) {
      console.error("Failed to decompress chunk:", chunkName, e);
      return null;
    }
  }

  /**
   * Load all available data chunks.
   * @returns {Promise<Object>} Map of chunk name to parsed data
   */
  static async loadAll() {
    const scripts = document.querySelectorAll(
      'script[type="application/x-devstats-data"]'
    );
    const data = {};

    for (const script of scripts) {
      const name = script.dataset.chunk;
      if (name) {
        data[name] = await DataLoader.load(name);
      }
    }

    return data;
  }
}

/* ------------------------------------------------------------------ */
/* Initialisation                                                     */
/* ------------------------------------------------------------------ */

document.addEventListener("DOMContentLoaded", () => {
  // Auto-initialise TableSorters
  document.querySelectorAll(".data-table").forEach((table) => {
    new TableSorter(table);
  });

  // Auto-initialise FilterBars
  document.querySelectorAll("[data-filter-table]").forEach((input) => {
    const tableId = input.dataset.filterTable;
    const table = document.getElementById(tableId);
    const countEl = document.querySelector(
      `[data-filter-count="${tableId}"]`
    );
    if (table) {
      new FilterBar(input, table, countEl);
    }
  });

  // Auto-initialise TabManagers
  document.querySelectorAll(".tabs").forEach((container) => {
    new TabManager(`#${container.id}`);
  });
});
