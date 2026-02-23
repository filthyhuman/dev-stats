/**
 * dev-stats dashboard — app.js
 *
 * Client-side JavaScript for the self-contained HTML dashboard.
 * Provides:
 * - TableSorter: click-to-sort on any data table
 * - FilterBar: live search/filter for table rows
 * - TabManager: tab switching with URL hash state
 * - DataLoader: decompresses embedded zlib/base64 data chunks
 * - LazyRenderer: populates tab content on first activation
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
   * Initialise TableSorter and FilterBar widgets inside a panel
   * after its content has been rendered.
   * @param {HTMLElement} panel
   */
  static _initWidgets(panel) {
    panel.querySelectorAll(".data-table").forEach((table) => {
      new TableSorter(table);
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
});
