/**
 * dev-stats dashboard — app.js
 *
 * Client-side JavaScript for the self-contained HTML dashboard.
 * Provides:
 * - TableSorter: click-to-sort on any data table with URL hash state
 * - FilterBar: live search/filter for table rows
 * - TabManager: tab switching with URL hash state
 * - DataLoader: decompresses embedded zlib/base64 data chunks
 * - LazyRenderer: populates tab content on first activation
 * - VirtualScroller: renders only visible rows for large tables
 * - ThemeToggle: dark/light mode with localStorage persistence
 * - CopyDeleteScript: copies git branch -d commands to clipboard
 * - BlameHeatMap: age-based colour scale for blame lines
 * - CommitGraph: canvas-based commit graph with zoom/pan
 * - ActivityHeatmap: 52-week contribution calendar
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
    this.tableId = table.id || "";

    this.headers.forEach((th, index) => {
      th.addEventListener("click", () => this.sort(index));
    });

    // Restore sort from URL hash
    this._restoreFromHash();
  }

  /**
   * Sort the table by the given column index.
   * @param {number} colIndex
   * @param {boolean} [updateHash=true]  Whether to update the URL hash
   */
  sort(colIndex, updateHash = true) {
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

    // Persist sort state in URL hash
    if (updateHash && this.tableId) {
      this._saveToHash(colIndex, this.ascending);
    }
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

  /**
   * Save sort state to URL hash.
   * @param {number} colIndex
   * @param {boolean} ascending
   */
  _saveToHash(colIndex, ascending) {
    const params = new URLSearchParams(location.hash.slice(1));
    params.set("sort", `${this.tableId}:${colIndex}:${ascending ? "asc" : "desc"}`);
    history.replaceState(null, "", `#${params.toString()}`);
  }

  /** Restore sort state from URL hash. */
  _restoreFromHash() {
    if (!this.tableId) return;
    const params = new URLSearchParams(location.hash.slice(1));
    const sort = params.get("sort");
    if (!sort) return;

    const parts = sort.split(":");
    if (parts.length >= 3 && parts[0] === this.tableId) {
      const colIndex = parseInt(parts[1], 10);
      const dir = parts[2];
      if (colIndex >= 0 && colIndex < this.headers.length) {
        this.ascending = dir !== "desc";
        this.currentCol = colIndex;
        // Invert so sort() flips it back
        this.ascending = !this.ascending;
        this.sort(colIndex, false);
      }
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

    // Trigger lazy rendering for the activated panel
    LazyRenderer.renderIfNeeded(tabId);
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
   *
   * Fallback chain:
   * 1. DecompressionStream (modern browsers)
   * 2. pako (if bundled)
   * 3. Uncompressed JSON (if data is not compressed)
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
      const raw = script.textContent.trim();

      // Try parsing as raw JSON first (uncompressed fallback)
      if (raw.startsWith("{") || raw.startsWith("[")) {
        return JSON.parse(raw);
      }

      const binary = atob(raw);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }

      // Use DecompressionStream if available
      if (typeof DecompressionStream !== "undefined") {
        // "deflate" = zlib format (RFC 1950): header + deflate + adler32
        // Pass the full zlib bytes — do NOT strip header/checksum.
        const ds = new DecompressionStream("deflate");
        const writer = ds.writable.getWriter();
        const reader = ds.readable.getReader();

        writer.write(bytes);
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

      // Last resort: try decoding as UTF-8 text directly
      try {
        const text = new TextDecoder().decode(bytes);
        return JSON.parse(text);
      } catch (_e) {
        // Not valid JSON either
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
/* VirtualScroller                                                    */
/* ------------------------------------------------------------------ */

class VirtualScroller {
  /**
   * Virtual scroll for tables with > 500 rows.
   * Only renders visible rows + a buffer above/below the viewport.
   *
   * @param {HTMLTableElement} table  The table to virtualise
   * @param {number} [rowHeight=28]   Estimated row height in px
   * @param {number} [buffer=20]      Buffer rows above/below viewport
   * @param {number} [threshold=500]  Min rows before enabling virtual scroll
   */
  constructor(table, rowHeight = 28, buffer = 20, threshold = 500) {
    this.table = table;
    this.tbody = table.querySelector("tbody");
    if (!this.tbody) return;

    this.allRows = Array.from(this.tbody.querySelectorAll("tr"));
    if (this.allRows.length < threshold) return;

    this.rowHeight = rowHeight;
    this.buffer = buffer;
    this.visibleStart = 0;
    this.visibleEnd = 0;

    this._setup();
  }

  /** Wrap the table in a scroll container and virtualise. */
  _setup() {
    // Wrap table in a scroll container
    this.container = document.createElement("div");
    this.container.className = "virtual-scroll";
    this.table.parentNode.insertBefore(this.container, this.table);
    this.container.appendChild(this.table);

    // Create a spacer element for total height
    this.spacer = document.createElement("div");
    this.spacer.className = "virtual-scroll__spacer";
    this.spacer.style.height = `${this.allRows.length * this.rowHeight}px`;
    this.tbody.appendChild(this.spacer);

    // Hide all rows initially
    this.allRows.forEach((row) => { row.style.display = "none"; });

    // Listen for scroll events
    this.container.addEventListener("scroll", () => this._onScroll());

    // Initial render
    this._onScroll();
  }

  /** Handle scroll events — show/hide rows as needed. */
  _onScroll() {
    const scrollTop = this.container.scrollTop;
    const viewportHeight = this.container.clientHeight;

    const start = Math.max(0, Math.floor(scrollTop / this.rowHeight) - this.buffer);
    const end = Math.min(
      this.allRows.length,
      Math.ceil((scrollTop + viewportHeight) / this.rowHeight) + this.buffer
    );

    if (start === this.visibleStart && end === this.visibleEnd) return;

    // Hide previously visible rows outside new range
    for (let i = this.visibleStart; i < this.visibleEnd; i++) {
      if (i < start || i >= end) {
        this.allRows[i].style.display = "none";
      }
    }

    // Show new visible rows
    for (let i = start; i < end; i++) {
      this.allRows[i].style.display = "";
    }

    this.visibleStart = start;
    this.visibleEnd = end;

    // Position rows using padding on tbody
    this.tbody.style.paddingTop = `${start * this.rowHeight}px`;
  }
}

/* ------------------------------------------------------------------ */
/* LazyRenderer                                                       */
/* ------------------------------------------------------------------ */

class LazyRenderer {
  /** Track which panels have been rendered. */
  static _rendered = new Set();

  /** Cached data chunks, loaded on demand. */
  static _data = null;

  /**
   * Render a tab panel's dynamic content on first activation.
   * Subsequent activations are no-ops.
   * @param {string} panelId  The tab panel ID
   */
  static async renderIfNeeded(panelId) {
    if (LazyRenderer._rendered.has(panelId)) return;

    const panel = document.getElementById(panelId);
    if (!panel) return;

    // Only process panels marked as lazy
    if (panel.dataset.lazy !== "true") return;

    LazyRenderer._rendered.add(panelId);

    // Load data on first render
    if (!LazyRenderer._data) {
      LazyRenderer._data = await DataLoader.loadAll();
    }
    const data = LazyRenderer._data;

    // Dispatch to the correct renderer
    const renderers = {
      "tab-languages": () => LazyRenderer._renderLanguages(data),
      "tab-files": () => LazyRenderer._renderFiles(data),
      "tab-classes": () => LazyRenderer._renderClasses(data),
      "tab-methods": () => LazyRenderer._renderMethods(data),
      "tab-hotspots": () => LazyRenderer._renderHotspots(data),
      "tab-dependencies": () => LazyRenderer._renderDependencies(data),
      "tab-branches": () => LazyRenderer._renderBranches(data),
      "tab-git": () => LazyRenderer._renderGit(data),
      "tab-quality": () => LazyRenderer._renderQuality(data),
    };

    const renderer = renderers[panelId];
    if (renderer) {
      try {
        await renderer();
        LazyRenderer._initWidgets(panel);
      } catch (e) {
        console.error("Lazy render failed for", panelId, e);
      }
    }
  }

  /**
   * Initialise TableSorter, FilterBar, and VirtualScroller widgets
   * inside a panel after its content has been rendered.
   * @param {HTMLElement} panel
   */
  static _initWidgets(panel) {
    panel.querySelectorAll(".data-table").forEach((table) => {
      new TableSorter(table);
      new VirtualScroller(table);
    });

    panel.querySelectorAll("[data-filter-table]").forEach((input) => {
      const tableId = input.dataset.filterTable;
      const table = document.getElementById(tableId);
      const countEl = document.querySelector(
        `[data-filter-count="${tableId}"]`
      );
      if (table) {
        new FilterBar(input, table, countEl);
      }
    });
  }

  /**
   * Helper to create a table row from cell values.
   * @param {Array} cells  Cell values
   * @param {Array} [classes]  CSS classes per cell (optional)
   * @returns {HTMLTableRowElement}
   */
  static _makeRow(cells, classes) {
    const tr = document.createElement("tr");
    cells.forEach((val, i) => {
      const td = document.createElement("td");
      td.textContent = val != null ? String(val) : "";
      if (classes && classes[i]) td.className = classes[i];
      tr.appendChild(td);
    });
    return tr;
  }

  /** Render the Languages tab charts from data chunks. */
  static _renderLanguages(data) {
    const languages = data.languages;
    if (!languages) return;

    // Filter out non-language types for the bar chart
    const nonLangTypes = (window.__devstats_non_lang_types || []).map((t) => t.name || t);
    const nonLangSet = new Set(nonLangTypes);
    const realLangs = languages.filter((l) => !nonLangSet.has(l.name || l.language || ""));
    ChartRenderer.langBar("chart-lang-bar", realLangs);

    // Render non-language extension donut in the Languages tab
    const nonLangExts = window.__devstats_non_lang_exts || [];
    ChartRenderer.nonLangDonut("chart-nonlang-ext-donut", nonLangExts);
  }

  /** Render the Files tab from data chunks. */
  static _renderFiles(data) {
    const files = data.files;
    if (!files) return;
    const tbody = document.getElementById("table-files-body");
    if (!tbody) return;

    const cls = [null, null, "num", "num", "num", "num"];
    files.forEach((f) => {
      const numClasses = f.classes ? f.classes.length : 0;
      const numFuncs = f.functions ? f.functions.length : 0;
      tbody.appendChild(
        LazyRenderer._makeRow(
          [f.path, f.language, f.total_lines, f.code_lines, numClasses, numFuncs],
          cls
        )
      );
    });
  }

  /** Render the Classes tab from data chunks. */
  static _renderClasses(data) {
    const files = data.files;
    if (!files) return;
    const tbody = document.getElementById("table-classes-body");
    if (!tbody) return;

    const cls = [null, null, "num", "num", "num"];
    files.forEach((f) => {
      if (!f.classes) return;
      f.classes.forEach((c) => {
        const numAttrs = c.attributes ? c.attributes.length : 0;
        const numMethods = c.methods ? c.methods.length : 0;
        tbody.appendChild(
          LazyRenderer._makeRow(
            [c.name, f.path, c.lines, numMethods, numAttrs],
            cls
          )
        );
      });
    });
  }

  /** Render the Methods tab from data chunks. */
  static _renderMethods(data) {
    const files = data.files;
    if (!files) return;
    const tbody = document.getElementById("table-methods-body");
    if (!tbody) return;

    const cls = [null, null, "num", "num", "num"];
    files.forEach((f) => {
      const methods = [];
      if (f.functions) {
        f.functions.forEach((fn) => methods.push(fn));
      }
      if (f.classes) {
        f.classes.forEach((c) => {
          if (c.methods) c.methods.forEach((m) => methods.push(m));
        });
      }
      methods.forEach((m) => {
        const params = m.parameters ? m.parameters.length : 0;
        tbody.appendChild(
          LazyRenderer._makeRow(
            [m.name, f.path, m.lines, m.cyclomatic_complexity, params],
            cls
          )
        );
      });
    });
  }

  /** Render the Hotspots tab from data chunks. */
  static _renderHotspots(data) {
    const churn = data.churn;
    if (!churn) return;
    const tbody = document.getElementById("table-hotspots-body");
    if (!tbody) return;

    const cls = [null, "num", "num", "num", "num"];
    churn.forEach((c) => {
      tbody.appendChild(
        LazyRenderer._makeRow(
          [c.path, c.commit_count, c.churn_score, c.insertions, c.deletions],
          cls
        )
      );
    });

    ChartRenderer.hotspotScatter("chart-hotspots", churn, data.files);
  }

  /** Render the Dependencies tab from data chunks. */
  static _renderDependencies(data) {
    const coupling = data.coupling;
    if (!coupling || !coupling.modules) return;
    const tbody = document.getElementById("table-coupling-body");
    if (!tbody) return;

    const cls = [null, "num", "num", "num", "num", "num"];
    coupling.modules.forEach((m) => {
      tbody.appendChild(
        LazyRenderer._makeRow(
          [
            m.name,
            m.afferent,
            m.efferent,
            m.instability.toFixed(2),
            m.abstractness.toFixed(2),
            m.distance.toFixed(2),
          ],
          cls
        )
      );
    });

    ChartRenderer.instabilityBar("chart-instability", coupling);
  }

  /** Render the Branches tab from data chunks. */
  static _renderBranches(data) {
    const branches = data.branches;
    if (!branches || !branches.branches) return;

    const allBody = document.getElementById("table-branches-body");
    const mergedBody = document.getElementById("table-branches-merged-body");
    const unmergedBody = document.getElementById("table-branches-unmerged-body");

    branches.branches.forEach((b) => {
      const merged = b.merge_status && b.merge_status.is_merged;

      if (allBody) {
        allBody.appendChild(
          LazyRenderer._makeRow([
            b.name,
            b.status,
            b.author_name,
            b.last_commit_date,
            b.commits_ahead,
            b.commits_behind,
            b.deletability_category,
          ])
        );
      }

      if (merged && mergedBody) {
        const mergeType = b.merge_status.merge_type || "merge_commit";
        mergedBody.appendChild(
          LazyRenderer._makeRow([b.name, b.author_name, b.last_commit_date, mergeType])
        );
      }

      if (!merged && unmergedBody) {
        unmergedBody.appendChild(
          LazyRenderer._makeRow([
            b.name,
            b.status,
            b.author_name,
            b.last_commit_date,
            b.commits_ahead,
          ])
        );
      }
    });

    // Initialise copy-safe-deletes button
    CopyDeleteScript.init(branches.branches);
  }

  /** Render the Git tab (commits, contributors, tags, patterns). */
  static _renderGit(data) {
    // Commits
    const commits = data.commits;
    const commitsBody = document.getElementById("table-commits-body");
    if (commits && commitsBody) {
      commits.forEach((c) => {
        const sha = c.sha ? c.sha.substring(0, 8) : "";
        const msg = c.message ? c.message.split("\n")[0] : "";
        commitsBody.appendChild(
          LazyRenderer._makeRow(
            [sha, c.author_name, c.authored_date, msg, c.insertions, c.deletions],
            [null, null, null, null, "num", "num"]
          )
        );
      });
    }

    // Contributors
    const contributors = data.contributors;
    const contribBody = document.getElementById("table-contributors-body");
    if (contributors && contribBody) {
      const cls = [null, null, "num", "num", "num", "num"];
      contributors.forEach((c) => {
        contribBody.appendChild(
          LazyRenderer._makeRow(
            [c.name, c.email, c.commit_count, c.insertions, c.deletions, c.files_touched],
            cls
          )
        );
      });
    }

    // Tags
    const tags = data.tags;
    const tagsBody = document.getElementById("table-tags-body");
    if (tags && tagsBody) {
      tags.forEach((t) => {
        const sha = t.sha ? t.sha.substring(0, 8) : "";
        tagsBody.appendChild(
          LazyRenderer._makeRow([t.name, sha, t.date, t.message || ""])
        );
      });
    }

    // Patterns
    const patterns = data.patterns;
    const patternsBody = document.getElementById("table-patterns-body");
    if (patterns && patternsBody) {
      patterns.forEach((p) => {
        patternsBody.appendChild(
          LazyRenderer._makeRow([p.name, p.severity, p.description, p.evidence])
        );
      });
    }
  }

  /** Render the Quality Gates tab from data chunks. */
  static _renderQuality(data) {
    // Duplication
    const dup = data.duplication;
    const dupBody = document.getElementById("table-duplication-body");
    if (dup && dup.duplicates && dupBody) {
      const cls = [null, null, "num", "num", "num"];
      dup.duplicates.forEach((d) => {
        dupBody.appendChild(
          LazyRenderer._makeRow(
            [d.file_a, d.file_b, d.line_a, d.line_b, d.length],
            cls
          )
        );
      });
    }

    ChartRenderer.coverageBar("chart-coverage", data.coverage);
  }
}

/* ------------------------------------------------------------------ */
/* ThemeToggle                                                        */
/* ------------------------------------------------------------------ */

class ThemeToggle {
  /** Storage key for persisted theme preference. */
  static STORAGE_KEY = "devstats-theme";

  /**
   * Initialise the theme toggle button.
   * @param {string} buttonId  ID of the toggle button element
   */
  constructor(buttonId) {
    this.button = document.getElementById(buttonId);
    if (!this.button) return;

    // Restore saved preference
    const saved = ThemeToggle._getSaved();
    if (saved === "light") {
      document.documentElement.classList.add("light");
    }
    this._updateIcon();

    this.button.addEventListener("click", () => this.toggle());
  }

  /** Toggle between dark and light mode. */
  toggle() {
    document.documentElement.classList.toggle("light");
    const isLight = document.documentElement.classList.contains("light");
    ThemeToggle._save(isLight ? "light" : "dark");
    this._updateIcon();
  }

  /** Update the button icon to reflect current theme. */
  _updateIcon() {
    if (!this.button) return;
    const isLight = document.documentElement.classList.contains("light");
    this.button.textContent = isLight ? "\u2600" : "\u263E";
    this.button.title = isLight ? "Switch to dark mode" : "Switch to light mode";
  }

  /**
   * Get saved theme preference.
   * @returns {string|null}
   */
  static _getSaved() {
    try {
      return localStorage.getItem(ThemeToggle.STORAGE_KEY);
    } catch (_e) {
      return null;
    }
  }

  /**
   * Save theme preference.
   * @param {string} theme  "dark" or "light"
   */
  static _save(theme) {
    try {
      localStorage.setItem(ThemeToggle.STORAGE_KEY, theme);
    } catch (_e) {
      // localStorage may be unavailable
    }
  }
}

/* ------------------------------------------------------------------ */
/* CopyDeleteScript                                                   */
/* ------------------------------------------------------------------ */

class CopyDeleteScript {
  /**
   * Build a multi-line shell script of `git branch -d` commands
   * for safe-to-delete branches and copy to clipboard.
   *
   * @param {Array} branches  Branch data objects from the data chunk
   */
  static init(branches) {
    const btn = document.getElementById("copy-safe-deletes");
    if (!btn || !branches) return;

    btn.addEventListener("click", () => {
      const safeBranches = branches.filter(
        (b) => b.deletability_category === "safe" && !b.is_remote
      );

      if (safeBranches.length === 0) {
        btn.textContent = "No safe deletes";
        btn.classList.add("btn--success");
        setTimeout(() => {
          btn.textContent = "Copy safe deletes";
          btn.classList.remove("btn--success");
        }, 2000);
        return;
      }

      const script = safeBranches
        .map((b) => `git branch -d '${b.name.replace(/'/g, "'\\''")}'`)
        .join("\n");

      navigator.clipboard.writeText(script).then(() => {
        btn.textContent = `Copied ${safeBranches.length} commands`;
        btn.classList.add("btn--success");
        setTimeout(() => {
          btn.textContent = "Copy safe deletes";
          btn.classList.remove("btn--success");
        }, 2000);
      }).catch(() => {
        btn.textContent = "Copy failed";
        setTimeout(() => { btn.textContent = "Copy safe deletes"; }, 2000);
      });
    });
  }
}

/* ------------------------------------------------------------------ */
/* BlameHeatMap                                                       */
/* ------------------------------------------------------------------ */

class BlameHeatMap {
  /**
   * Assign age-based CSS classes to blame line elements.
   *
   * Thresholds (days since authoring):
   * - fresh:   < 30 days
   * - recent:  30–180 days
   * - old:     180–365 days
   * - ancient: > 365 days
   *
   * @param {HTMLElement} container  Element containing blame lines
   * @param {Array} lines  Blame line data from data chunks
   */
  static apply(container, lines) {
    if (!container || !lines) return;

    const now = Date.now();
    const DAY_MS = 86400000;

    const lineEls = container.querySelectorAll("[data-blame-date]");
    lineEls.forEach((el) => {
      const dateStr = el.dataset.blameDate;
      if (!dateStr) return;

      const age = (now - new Date(dateStr).getTime()) / DAY_MS;
      el.classList.remove(
        "blame-age-fresh", "blame-age-recent", "blame-age-old", "blame-age-ancient"
      );

      if (age < 30) {
        el.classList.add("blame-age-fresh");
      } else if (age < 180) {
        el.classList.add("blame-age-recent");
      } else if (age < 365) {
        el.classList.add("blame-age-old");
      } else {
        el.classList.add("blame-age-ancient");
      }
    });
  }
}

/* ------------------------------------------------------------------ */
/* CommitGraph                                                        */
/* ------------------------------------------------------------------ */

class CommitGraph {
  /**
   * Canvas-based commit graph with zoom and pan.
   *
   * @param {string} canvasId   ID of the canvas element
   * @param {Array} commits     Commit data objects
   */
  constructor(canvasId, commits) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas || !commits || commits.length === 0) return;

    this.ctx = this.canvas.getContext("2d");
    this.commits = commits;

    // View state
    this.offsetX = 0;
    this.offsetY = 0;
    this.scale = 1;

    // Layout constants
    this.nodeRadius = 4;
    this.colWidth = 20;
    this.rowHeight = 24;

    // Setup canvas size
    this.canvas.width = this.canvas.parentElement.clientWidth || 800;
    this.canvas.height = 300;

    // Event listeners for pan/zoom
    this._dragging = false;
    this._lastX = 0;
    this._lastY = 0;

    this.canvas.addEventListener("mousedown", (e) => this._onMouseDown(e));
    this.canvas.addEventListener("mousemove", (e) => this._onMouseMove(e));
    this.canvas.addEventListener("mouseup", () => this._onMouseUp());
    this.canvas.addEventListener("mouseleave", () => this._onMouseUp());
    this.canvas.addEventListener("wheel", (e) => this._onWheel(e), { passive: false });

    this._render();
  }

  /** Render the commit graph onto the canvas. */
  _render() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.save();
    ctx.translate(this.offsetX, this.offsetY);
    ctx.scale(this.scale, this.scale);

    const nodeColor = getComputedStyle(document.documentElement)
      .getPropertyValue("--color-primary").trim() || "#58a6ff";
    const lineColor = getComputedStyle(document.documentElement)
      .getPropertyValue("--color-border").trim() || "#30363d";

    // Draw connecting lines
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 1.5;
    for (let i = 1; i < this.commits.length; i++) {
      const x = this.colWidth;
      const y1 = (i - 1) * this.rowHeight + this.rowHeight / 2;
      const y2 = i * this.rowHeight + this.rowHeight / 2;
      ctx.beginPath();
      ctx.moveTo(x, y1);
      ctx.lineTo(x, y2);
      ctx.stroke();
    }

    // Draw commit nodes
    ctx.fillStyle = nodeColor;
    for (let i = 0; i < this.commits.length; i++) {
      const x = this.colWidth;
      const y = i * this.rowHeight + this.rowHeight / 2;
      ctx.beginPath();
      ctx.arc(x, y, this.nodeRadius, 0, Math.PI * 2);
      ctx.fill();

      // Draw SHA + message label
      const c = this.commits[i];
      const sha = c.sha ? c.sha.substring(0, 7) : "";
      const msg = c.message ? c.message.split("\n")[0].substring(0, 60) : "";
      ctx.fillStyle = getComputedStyle(document.documentElement)
        .getPropertyValue("--color-text").trim() || "#c9d1d9";
      ctx.font = "11px monospace";
      ctx.fillText(`${sha} ${msg}`, x + this.nodeRadius + 6, y + 4);
      ctx.fillStyle = nodeColor;
    }

    ctx.restore();
  }

  /** @param {MouseEvent} e */
  _onMouseDown(e) {
    this._dragging = true;
    this._lastX = e.clientX;
    this._lastY = e.clientY;
  }

  /** @param {MouseEvent} e */
  _onMouseMove(e) {
    if (!this._dragging) return;
    this.offsetX += e.clientX - this._lastX;
    this.offsetY += e.clientY - this._lastY;
    this._lastX = e.clientX;
    this._lastY = e.clientY;
    this._render();
  }

  _onMouseUp() {
    this._dragging = false;
  }

  /** @param {WheelEvent} e */
  _onWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    this.scale = Math.max(0.2, Math.min(5, this.scale * delta));
    this._render();
  }
}

/* ------------------------------------------------------------------ */
/* ActivityHeatmap                                                     */
/* ------------------------------------------------------------------ */

class ActivityHeatmap {
  /**
   * Render a 52-week activity heatmap (GitHub-style contribution calendar).
   *
   * @param {HTMLElement} container  Element to render the heatmap into
   * @param {Array} commits         Commit data with authored_date fields
   */
  static render(container, commits) {
    if (!container || !commits || commits.length === 0) return;

    // Count commits per day for the last 52 weeks
    const now = new Date();
    const weekMs = 7 * 86400000;
    const startDate = new Date(now.getTime() - 52 * weekMs);

    const dayCounts = {};
    commits.forEach((c) => {
      const dateStr = (c.authored_date || "").substring(0, 10);
      if (dateStr) {
        dayCounts[dateStr] = (dayCounts[dateStr] || 0) + 1;
      }
    });

    // Find max for scaling
    const maxCount = Math.max(1, ...Object.values(dayCounts));

    // Build grid
    const grid = document.createElement("div");
    grid.className = "heatmap";

    for (let week = 0; week < 52; week++) {
      for (let day = 0; day < 7; day++) {
        const date = new Date(startDate.getTime() + (week * 7 + day) * 86400000);
        const dateStr = date.toISOString().substring(0, 10);
        const count = dayCounts[dateStr] || 0;

        const cell = document.createElement("div");
        cell.className = "heatmap__cell";
        cell.title = `${dateStr}: ${count} commit${count !== 1 ? "s" : ""}`;

        if (count > 0) {
          const level = Math.min(4, Math.ceil((count / maxCount) * 4));
          cell.classList.add(`heatmap__cell--l${level}`);
        }

        grid.appendChild(cell);
      }
    }

    container.appendChild(grid);
  }
}

/* ------------------------------------------------------------------ */
/* ChartRenderer                                                      */
/* ------------------------------------------------------------------ */

class ChartRenderer {
  /** 10-colour palette matching the dashboard theme. */
  static PALETTE = [
    "#58a6ff", "#3fb950", "#d29922", "#f85149", "#bc8cff",
    "#79c0ff", "#56d364", "#e3b341", "#ff7b72", "#d2a8ff",
  ];

  /**
   * Get a colour from the palette (wrapping for > 10 items).
   * @param {number} index
   * @returns {string}
   */
  static _color(index) {
    return ChartRenderer.PALETTE[index % ChartRenderer.PALETTE.length];
  }

  /**
   * Read a CSS custom property from the document root.
   * @param {string} prop  Property name (e.g. "--color-text")
   * @returns {string}
   */
  static _css(prop) {
    return getComputedStyle(document.documentElement).getPropertyValue(prop).trim();
  }

  /**
   * Shared defaults for Chart.js (dark-/light-aware).
   * @returns {Object}
   */
  static _defaults() {
    const text = ChartRenderer._css("--color-text") || "#c9d1d9";
    const muted = ChartRenderer._css("--color-text-muted") || "#8b949e";
    const border = ChartRenderer._css("--color-border") || "#30363d";
    return { text, muted, border };
  }

  /**
   * Format a number with locale-aware thousand separators.
   * @param {number} n
   * @returns {string}
   */
  static _fmtNum(n) {
    return n.toLocaleString("en-US");
  }

  /**
   * Render a doughnut chart with percentage labels in the legend.
   * @param {string} canvasId
   * @param {Array} labels
   * @param {Array} data
   * @param {string} [unit=""]  Unit label for the total header (e.g. "lines", "files")
   * @param {number} [colorOffset=0]  Offset into the palette for colour cycling
   */
  /**
   * Build an HTML legend element with a single-column layout.
   * @param {Array} labels
   * @param {Array} data
   * @param {Array} colors
   * @param {string} unit
   * @param {function} fmtValue  Formatter for individual values
   * @param {function} fmtTotal  Formatter for the total (defaults to fmtValue)
   * @returns {HTMLDivElement}
   */
  static _buildHtmlLegend(labels, data, colors, unit, fmtValue, fmtTotal) {
    const total = data.reduce((s, v) => s + v, 0);
    const fmtT = fmtTotal || fmtValue;
    const legend = document.createElement("div");
    legend.className = "donut-legend";

    const totalLabel = unit ? `All ${unit}` : "All";
    const header = document.createElement("div");
    header.className = "donut-legend__item donut-legend__item--header";
    header.textContent = `${totalLabel} 100% (${fmtT(total)})`;
    legend.appendChild(header);

    labels.forEach((label, i) => {
      const pct = total > 0 ? ((data[i] / total) * 100).toFixed(1) : "0.0";
      const row = document.createElement("div");
      row.className = "donut-legend__item";
      const swatch = document.createElement("span");
      swatch.className = "donut-legend__swatch";
      swatch.style.backgroundColor = colors[i];
      row.appendChild(swatch);
      row.appendChild(document.createTextNode(`${label}  ${pct}% (${fmtValue(data[i])})`));
      legend.appendChild(row);
    });
    return legend;
  }

  static _donutWithPercent(canvasId, labels, data, unit = "", colorOffset = 0) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !labels || labels.length === 0) return;

    const colors = labels.map((_, i) => ChartRenderer._color(i + colorOffset));
    const fmt = ChartRenderer._fmtNum;

    // Replace the chart-container with a flex wrapper holding canvas + HTML legend
    const container = canvas.parentElement;
    ChartRenderer._setupDonutLayout(container, canvas, labels, data, colors, unit, fmt);

    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{ data, backgroundColor: colors, borderWidth: 0 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
      },
    });
  }

  /**
   * Set up a flex layout for a donut chart: canvas on the left, HTML legend on the right.
   * @param {HTMLElement} container  The .chart-container element
   * @param {HTMLCanvasElement} canvas
   * @param {Array} labels
   * @param {Array} data
   * @param {Array} colors
   * @param {string} unit
   * @param {function} fmtValue
   * @param {function} [fmtTotal]
   */
  static _setupDonutLayout(container, canvas, labels, data, colors, unit, fmtValue, fmtTotal) {
    if (!container) return;
    container.style.display = "flex";
    container.style.flexDirection = "row";
    container.style.alignItems = "flex-start";
    container.style.justifyContent = "center";
    container.style.maxHeight = "none";

    // Canvas wrapper takes fixed width for the donut
    const canvasWrap = document.createElement("div");
    canvasWrap.style.width = "260px";
    canvasWrap.style.minWidth = "200px";
    canvasWrap.style.height = "260px";
    canvasWrap.style.flexShrink = "0";
    container.insertBefore(canvasWrap, canvas);
    canvasWrap.appendChild(canvas);

    const legend = ChartRenderer._buildHtmlLegend(labels, data, colors, unit, fmtValue, fmtTotal);
    container.appendChild(legend);

    // Height: 2-column legend needs ~half the rows; ensure at least donut height
    const legendRows = Math.ceil(labels.length / 2);
    const minHeight = Math.max(260, (legendRows + 1) * 24 + 20);
    container.style.height = minHeight + "px";
  }

  /**
   * Render a doughnut chart of language distribution.
   * @param {string} canvasId
   * @param {Array} languages  [{name, file_count, total_lines, code_lines}]
   */
  static langDonut(canvasId, languages) {
    if (!languages || languages.length === 0) return;
    const labels = languages.map((l) => l.name || l.language || "Unknown");
    const data = languages.map((l) => l.code_lines || l.total_lines || 0);
    ChartRenderer._donutWithPercent(canvasId, labels, data, "code lines");
  }

  /**
   * Render a doughnut chart of language file types by extension+language.
   * @param {string} canvasId
   * @param {Array} fileTypes  [{label, count}]
   */
  static langFileTypesDonut(canvasId, fileTypes) {
    if (!fileTypes || fileTypes.length === 0) return;
    const labels = fileTypes.map((ft) => ft.label || "other");
    const data = fileTypes.map((ft) => ft.count || 0);
    ChartRenderer._donutWithPercent(canvasId, labels, data, "files");
  }

  /**
   * Render a doughnut chart of non-language file types by extension.
   * @param {string} canvasId
   * @param {Array} extensions  [{ext, count}]
   */
  static nonLangDonut(canvasId, extensions) {
    if (!extensions || extensions.length === 0) return;
    const labels = extensions.map((e) => e.ext || "other");
    const data = extensions.map((e) => e.count || 0);
    ChartRenderer._donutWithPercent(canvasId, labels, data, "files", 5);
  }

  /**
   * Format a byte count into a human-readable string.
   * @param {number} bytes
   * @returns {string}
   */
  static _fmtBytes(bytes) {
    if (bytes === 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    const k = 1024;
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), units.length - 1);
    const value = bytes / Math.pow(k, i);
    return (i === 0 ? value.toString() : value.toFixed(1)) + " " + units[i];
  }

  /**
   * Render a doughnut chart of non-language file sizes by extension.
   * @param {string} canvasId
   * @param {Array} sizes  [{ext, size}]  size in bytes
   */
  static nonLangSizesDonut(canvasId, sizes) {
    if (!sizes || sizes.length === 0) return;
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const labels = sizes.map((e) => e.ext || "other");
    const data = sizes.map((e) => e.size || 0);
    const colors = labels.map((_, i) => ChartRenderer._color(i + 5));
    const fmtB = ChartRenderer._fmtBytes;

    const container = canvas.parentElement;
    ChartRenderer._setupDonutLayout(container, canvas, labels, data, colors, "files", fmtB, fmtB);

    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{ data, backgroundColor: colors, borderWidth: 0 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
      },
    });
  }

  /** @type {Chart|null} Active LOC timeline chart instance. */
  static _locChart = null;

  /** @type {string|null} Canvas ID for the LOC chart. */
  static _locCanvasId = null;

  /** @type {Array|null} Full timeline data for range filtering. */
  static _locTimeline = null;

  /**
   * Render a line chart of LOC over time with range filtering.
   *
   * Range is computed relative to the **last data point** (not "now"),
   * so historical projects with no recent commits still produce
   * meaningful sub-ranges.
   *
   * @param {string} canvasId
   * @param {Array} timeline  [{date, value, label}]
   * @param {number} [rangeMonths=0]  0 = show all data
   */
  static locTimeline(canvasId, timeline, rangeMonths = 0) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !timeline || timeline.length === 0) return;

    // Store full data and canvas ID for re-rendering with different ranges
    if (!ChartRenderer._locTimeline) {
      ChartRenderer._locTimeline = timeline;
      ChartRenderer._locCanvasId = canvasId;
    }

    // Filter by range relative to the latest data point
    let filtered = timeline;
    if (rangeMonths > 0) {
      const lastDate = new Date(timeline[timeline.length - 1].date);
      const cutoff = new Date(lastDate);
      cutoff.setMonth(cutoff.getMonth() - rangeMonths);
      filtered = timeline.filter((t) => new Date(t.date) >= cutoff);
      if (filtered.length === 0) filtered = timeline;
    }

    // Aggregate by week/month when there are too many points
    const aggregated = ChartRenderer._aggregateTimeline(filtered);
    const labels = aggregated.map((t) => t.label);
    const values = aggregated.map((t) => t.value);

    // Update existing chart or create a new one
    if (ChartRenderer._locChart) {
      ChartRenderer._locChart.data.labels = labels;
      ChartRenderer._locChart.data.datasets[0].data = values;
      ChartRenderer._locChart.data.datasets[0].pointRadius = aggregated.length > 60 ? 0 : 3;
      ChartRenderer._locChart.update();
      return;
    }

    const { text, muted, border } = ChartRenderer._defaults();

    ChartRenderer._locChart = new Chart(canvas, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Lines of Code",
          data: values,
          borderColor: ChartRenderer.PALETTE[0],
          backgroundColor: ChartRenderer.PALETTE[0] + "33",
          fill: true,
          tension: 0.3,
          pointRadius: aggregated.length > 60 ? 0 : 3,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        scales: {
          x: { ticks: { color: muted, maxTicksLimit: 14 }, grid: { color: border } },
          y: { ticks: { color: muted }, grid: { color: border } },
        },
        plugins: { legend: { labels: { color: text } } },
      },
    });

    // Wire range buttons (once)
    ChartRenderer._initRangeButtons();
  }

  /**
   * Aggregate timeline data to keep charts readable.
   * - <= 90 points: keep as-is (daily labels)
   * - <= 365 points: aggregate by week
   * - > 365 points: aggregate by month
   * @param {Array} timeline
   * @returns {Array} [{label, value}]
   */
  static _aggregateTimeline(timeline) {
    if (timeline.length <= 90) {
      return timeline.map((t) => {
        const d = new Date(t.date);
        return {
          label: d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "2-digit" }),
          value: t.value,
        };
      });
    }

    const byMonth = timeline.length > 365;
    const buckets = new Map();

    timeline.forEach((t) => {
      const d = new Date(t.date);
      const key = byMonth
        ? `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`
        : (() => {
            const start = new Date(d);
            start.setDate(start.getDate() - start.getDay());
            return start.toISOString().substring(0, 10);
          })();
      buckets.set(key, { date: d, value: t.value });
    });

    const result = [];
    for (const [, entry] of buckets) {
      const d = entry.date;
      const label = byMonth
        ? d.toLocaleDateString(undefined, { month: "short", year: "numeric" })
        : d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "2-digit" });
      result.push({ label, value: entry.value });
    }
    return result;
  }

  /** @type {boolean} Whether range buttons have been wired. */
  static _rangeWired = false;

  /**
   * Wire the LOC range buttons to update the chart.
   */
  static _initRangeButtons() {
    if (ChartRenderer._rangeWired) return;
    ChartRenderer._rangeWired = true;

    const bar = document.getElementById("loc-range-bar");
    if (!bar) return;

    bar.addEventListener("click", (e) => {
      const btn = e.target.closest(".chart-range-btn");
      if (!btn) return;

      bar.querySelectorAll(".chart-range-btn").forEach((b) =>
        b.classList.toggle("chart-range-btn--active", b === btn)
      );

      const months = parseInt(btn.dataset.range, 10) || 0;
      ChartRenderer.locTimeline(
        ChartRenderer._locCanvasId,
        ChartRenderer._locTimeline,
        months
      );
    });
  }

  /**
   * Render a horizontal bar chart of lines by language.
   * @param {string} canvasId
   * @param {Array} languages
   */
  static langBar(canvasId, languages) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !languages || languages.length === 0) return;
    const { text, muted, border } = ChartRenderer._defaults();

    const sorted = [...languages].sort(
      (a, b) => (b.code_lines || b.total_lines || 0) - (a.code_lines || a.total_lines || 0)
    );
    const labels = sorted.map((l) => l.name || l.language || "Unknown");
    const data = sorted.map((l) => l.code_lines || l.total_lines || 0);
    const colors = labels.map((_, i) => ChartRenderer._color(i));

    new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [{ label: "Code Lines", data, backgroundColor: colors }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: muted }, grid: { color: border } },
          y: { ticks: { color: text } },
        },
        plugins: { legend: { display: false } },
      },
    });
  }

  /**
   * Render a scatter chart of churn vs complexity hotspots.
   * @param {string} canvasId
   * @param {Array} churn   [{path, commit_count, churn_score, insertions, deletions}]
   * @param {Array} files   [{path, …}]  (used for complexity lookup)
   */
  static hotspotScatter(canvasId, churn, files) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !churn || churn.length === 0) return;
    const { text, muted, border } = ChartRenderer._defaults();

    // Build a complexity map from files if available
    const complexityMap = {};
    if (files) {
      files.forEach((f) => {
        let maxCC = 0;
        if (f.functions) f.functions.forEach((fn) => { maxCC = Math.max(maxCC, fn.cyclomatic_complexity || 0); });
        if (f.classes) f.classes.forEach((c) => {
          if (c.methods) c.methods.forEach((m) => { maxCC = Math.max(maxCC, m.cyclomatic_complexity || 0); });
        });
        complexityMap[f.path] = maxCC;
      });
    }

    const points = churn.map((c) => ({
      x: c.commit_count || 0,
      y: complexityMap[c.path] || c.churn_score || 0,
      label: c.path,
    }));

    new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: [{
          label: "Files",
          data: points,
          backgroundColor: ChartRenderer.PALETTE[3] + "99",
          pointRadius: 5,
          pointHoverRadius: 7,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { title: { display: true, text: "Commits", color: text }, ticks: { color: muted }, grid: { color: border } },
          y: { title: { display: true, text: "Complexity / Churn", color: text }, ticks: { color: muted }, grid: { color: border } },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const p = ctx.raw;
                const name = p.label ? p.label.split("/").pop() : "";
                return `${name} (commits: ${p.x}, score: ${p.y})`;
              },
            },
          },
        },
      },
    });
  }

  /**
   * Render a bar chart of module instability.
   * @param {string} canvasId
   * @param {Object} coupling  {modules: [{name, instability, distance, …}]}
   */
  static instabilityBar(canvasId, coupling) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !coupling || !coupling.modules || coupling.modules.length === 0) return;
    const { text, muted, border } = ChartRenderer._defaults();

    const modules = coupling.modules;
    const labels = modules.map((m) => m.name);
    const instData = modules.map((m) => m.instability);
    const distData = modules.map((m) => m.distance);

    new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [
          { label: "Instability", data: instData, backgroundColor: ChartRenderer.PALETTE[0] + "cc" },
          { label: "Distance", data: distData, backgroundColor: ChartRenderer.PALETTE[2] + "cc" },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: muted }, grid: { color: border } },
          y: { min: 0, max: 1, ticks: { color: muted }, grid: { color: border } },
        },
        plugins: { legend: { labels: { color: text } } },
      },
    });
  }

  /**
   * Render a bar chart of test coverage per file.
   * @param {string} canvasId
   * @param {Object} coverage  {files: [{path, coverage_ratio}], overall_ratio}
   */
  static coverageBar(canvasId, coverage) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !coverage) return;

    const { text, muted, border } = ChartRenderer._defaults();
    const files = coverage.files || [];
    if (files.length === 0) return;

    // Sort by coverage ratio ascending so worst files are visible first
    const sorted = [...files].sort((a, b) => a.coverage_ratio - b.coverage_ratio);
    // Limit to top 30 files for readability
    const shown = sorted.slice(0, 30);

    const labels = shown.map((f) => f.path.split("/").pop());
    const data = shown.map((f) => Math.round(f.coverage_ratio * 100));
    const colors = shown.map((f) => {
      if (f.coverage_ratio >= 0.9) return ChartRenderer.PALETTE[1];
      if (f.coverage_ratio >= 0.7) return ChartRenderer.PALETTE[2];
      return ChartRenderer.PALETTE[3];
    });

    new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [{ label: "Coverage %", data, backgroundColor: colors }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { min: 0, max: 100, ticks: { color: muted }, grid: { color: border } },
          y: { ticks: { color: text, font: { size: 10 } } },
        },
        plugins: { legend: { display: false } },
      },
    });
  }
}

/* ------------------------------------------------------------------ */
/* Sidebar navigation                                                 */
/* ------------------------------------------------------------------ */

class SidebarNav {
  /**
   * Wire sidebar links to tab panel activation.
   * Syncs the active sidebar link with the visible panel.
   */
  constructor() {
    this.links = Array.from(document.querySelectorAll(".sidebar__link[data-tab]"));
    this.panels = Array.from(document.querySelectorAll(".tab-panel"));

    this.links.forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        this.activate(link.dataset.tab);
      });
    });

    // Activate from hash on load
    const hash = location.hash.slice(1);
    if (hash && this.links.some((l) => l.dataset.tab === hash)) {
      this.activate(hash);
    }

    // Listen for hash changes
    window.addEventListener("hashchange", () => {
      const h = location.hash.slice(1);
      if (h) this.activate(h);
    });
  }

  /**
   * Activate a panel and update the sidebar.
   * @param {string} panelId
   */
  activate(panelId) {
    // Update sidebar links
    this.links.forEach((l) =>
      l.classList.toggle("sidebar__link--active", l.dataset.tab === panelId)
    );

    // Show/hide panels
    this.panels.forEach((p) =>
      p.classList.toggle("tab-panel--active", p.id === panelId)
    );

    // Update URL hash
    history.replaceState(null, "", `#${panelId}`);

    // Trigger lazy rendering
    LazyRenderer.renderIfNeeded(panelId);
  }
}

/* ------------------------------------------------------------------ */
/* Initialisation                                                     */
/* ------------------------------------------------------------------ */

document.addEventListener("DOMContentLoaded", () => {
  // Auto-initialise TableSorters for statically-rendered tables
  document.querySelectorAll(".data-table").forEach((table) => {
    new TableSorter(table);
  });

  // Auto-initialise FilterBars for statically-rendered tables
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

  // Auto-initialise TabManagers (for sub-tabs like branch, git)
  document.querySelectorAll(".tabs").forEach((container) => {
    new TabManager(`#${container.id}`);
  });

  // Initialise sidebar navigation
  new SidebarNav();

  // Initialise theme toggle
  new ThemeToggle("theme-toggle");

  // Render overview charts (non-lazy, visible on load)
  (async () => {
    const data = await DataLoader.loadAll();
    LazyRenderer._data = data;

    // Filter out non-language types from the language donut
    const nonLangTypes = (window.__devstats_non_lang_types || []).map((t) => t.name || t);
    const nonLangSet = new Set(nonLangTypes);
    const realLangs = (data.languages || []).filter(
      (l) => !nonLangSet.has(l.name || l.language || "")
    );
    ChartRenderer.langDonut("chart-lang-donut", realLangs);

    // Render language file types chart (by extension + language)
    const langFileTypes = window.__devstats_lang_file_types || [];
    ChartRenderer.langFileTypesDonut("chart-lang-filetypes", langFileTypes);

    // Render non-language file types chart
    const nonLangExts = window.__devstats_non_lang_exts || [];
    ChartRenderer.nonLangDonut("chart-nonlang-donut", nonLangExts);

    // Render non-language file sizes chart
    const nonLangSizes = window.__devstats_non_lang_sizes || [];
    ChartRenderer.nonLangSizesDonut("chart-nonlang-sizes", nonLangSizes);

    ChartRenderer.locTimeline("chart-loc-timeline", data.timeline);
  })();
});
