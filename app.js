const state = {
  items: [],
  filter: "all",
  query: "",
  sort: "curated",
  style: localStorage.getItem("retro-whisper-style") || "win98",
};

const visualGlyphs = {
  sprite: "✚",
  rct: "▦",
  transport: "◆",
  xcom: "⌁",
  doom: "☠",
  rpg: "✦",
  scumm: "◈",
  dos: "▣",
  pc: "▤",
  terminal: "▰",
  default: "✧",
};

const elements = {
  body: document.body,
  feedGrid: document.querySelector("#feedGrid"),
  emptyState: document.querySelector("#emptyState"),
  resultSummary: document.querySelector("#resultSummary"),
  lastSync: document.querySelector("#lastSync"),
  searchInput: document.querySelector("#searchInput"),
  sortSelect: document.querySelector("#sortSelect"),
};

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatStars(value) {
  const stars = Number(value) || 0;
  if (stars >= 1000) {
    return `${(stars / 1000).toFixed(stars >= 10000 ? 0 : 1)}k`;
  }
  return String(stars);
}

function formatDate(value) {
  if (!value) return "未记录";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未记录";
  const diffDays = Math.max(0, Math.floor((Date.now() - date.getTime()) / 86400000));
  if (diffDays === 0) return "今天更新";
  if (diffDays === 1) return "昨天更新";
  if (diffDays < 30) return `${diffDays} 天前`;
  return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, "0")}.${String(date.getDate()).padStart(2, "0")}`;
}

function formatSync(value) {
  if (!value) return "等待数据";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "等待数据";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date).replace("/", ".").replace("/", ".");
}

function normalizeItem(item, index) {
  const fullName = item.full_name || item.id || item.name || "unknown/project";
  const pieces = fullName.split("/");
  return {
    ...item,
    id: item.id || fullName,
    full_name: fullName,
    name: item.name || pieces.at(-1),
    owner: item.owner || pieces[0] || "unknown",
    description: item.description || item.editor_note || "一个值得被重新发现的开源项目。",
    category: item.category || "工具",
    tags: Array.isArray(item.tags) ? item.tags : [],
    visual: item.visual || "default",
    cover: item.cover || `https://opengraph.githubassets.com/1/${fullName}`,
    curated_index: Number.isFinite(Number(item.curated_index)) ? Number(item.curated_index) : index,
  };
}

function getFilteredItems() {
  const query = state.query.trim().toLowerCase();
  const filtered = state.items.filter((item) => {
    const matchesFilter = state.filter === "all" || item.category === state.filter;
    if (!matchesFilter) return false;
    if (!query) return true;
    const haystack = [item.name, item.full_name, item.description, item.editor_note, item.language, ...(item.tags || []), ...(item.topics || [])]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });

  return filtered.sort((a, b) => {
    if (state.sort === "stars") return (b.stars || 0) - (a.stars || 0);
    if (state.sort === "updated") return new Date(b.updated_at || 0) - new Date(a.updated_at || 0);
    return (a.curated_index ?? 0) - (b.curated_index ?? 0);
  });
}

function cardTemplate(item, index) {
  const safeName = escapeHtml(item.name);
  const safeOwner = escapeHtml(item.owner);
  const safeDescription = escapeHtml(item.editor_note || item.description);
  const safeCategory = escapeHtml(item.category);
  const visualName = String(item.visual || "default").replace(/[^a-z0-9_-]/gi, "") || "default";
  const visual = escapeHtml(visualName);
  const glyph = escapeHtml(visualGlyphs[item.visual] || visualGlyphs.default);
  const tags = (item.tags || []).slice(0, 4).map((tag) => `<span class="repo-tag">${escapeHtml(tag)}</span>`).join("");
  const language = item.language ? escapeHtml(item.language) : "多语言";
  const license = item.license && item.license !== "NOASSERTION" ? escapeHtml(item.license) : "许可证未标注";
  const cover = escapeHtml(item.cover);
  const href = escapeHtml(item.html_url || item.url || `https://github.com/${item.full_name}`);

  return `
    <article class="repo-card" data-repo-id="${escapeHtml(item.full_name)}">
      <a class="card-cover visual-${visual}" href="${href}" target="_blank" rel="noreferrer" aria-label="打开 ${safeName} 的 GitHub 仓库">
        <div class="cover-fallback" aria-hidden="true">
          <span class="cover-fallback__glyph">${glyph}</span>
          <span class="cover-fallback__grid"></span>
          <span class="cover-fallback__label">${escapeHtml(item.full_name)}</span>
        </div>
        <img class="card-cover-image" src="${cover}" alt="" loading="lazy" />
        <span class="card-cover-shade" aria-hidden="true"></span>
        <span class="card-cover-meta">
          <span class="card-index">#${String(index + 1).padStart(2, "0")}</span>
          <span class="card-signal">GITHUB</span>
        </span>
      </a>
      <div class="card-body">
        <div class="card-kicker">
          <span class="category-badge">${safeCategory}</span>
          <span class="card-stars">★ <strong>${formatStars(item.stars)}</strong></span>
        </div>
        <h3 class="repo-title">${safeName}</h3>
        <p class="repo-owner">${safeOwner} / ${safeName}</p>
        <p class="repo-description">${safeDescription}</p>
        <div class="repo-tags">${tags}</div>
        <div class="repo-footer">
          <div class="repo-meta">
            <span>${language}</span>
            <span>${license}</span>
            <span>${formatDate(item.updated_at)}</span>
          </div>
          <a class="repo-open" href="${href}" target="_blank" rel="noreferrer">打开仓库 <span aria-hidden="true">↗</span></a>
        </div>
      </div>
    </article>
  `;
}

function renderCards() {
  const items = getFilteredItems();
  elements.feedGrid.innerHTML = items.map(cardTemplate).join("");
  elements.emptyState.hidden = items.length > 0;

  if (state.items.length === 0) {
    elements.resultSummary.textContent = "暂时没有收到数据";
  } else if (items.length === state.items.length && !state.query && state.filter === "all") {
    elements.resultSummary.textContent = `${items.length} 个项目`;
  } else {
    elements.resultSummary.textContent = `当前显示 ${items.length} / ${state.items.length} 个项目`;
  }

  elements.feedGrid.querySelectorAll(".card-cover-image").forEach((image) => {
    image.addEventListener("error", () => {
      image.closest(".card-cover")?.classList.add("image-missing");
    }, { once: true });
  });
}

function setStyle(style) {
  const nextStyle = ["pixel", "win98", "vista"].includes(style) ? style : "win98";
  state.style = nextStyle;
  document.documentElement.dataset.style = nextStyle;
  elements.body.dataset.style = nextStyle;
  localStorage.setItem("retro-whisper-style", nextStyle);
  document.querySelectorAll("[data-style-option]").forEach((button) => {
    const isSelected = button.dataset.styleOption === nextStyle;
    button.classList.toggle("is-selected", isSelected);
    button.setAttribute("aria-pressed", String(isSelected));
  });
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", nextStyle === "win98" ? "#008080" : nextStyle === "vista" ? "#bdeeff" : "#13152f");
}

function updateFilterButtons() {
  document.querySelectorAll("[data-filter]").forEach((button) => {
    const isActive = button.dataset.filter === state.filter;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
}

function updateAllCount() {
  const allTab = document.querySelector('[data-filter="all"] span');
  if (allTab) allTab.textContent = state.items.length;
}

function attachInteractions() {
  document.querySelectorAll("[data-style-option]").forEach((button) => {
    button.addEventListener("click", () => setStyle(button.dataset.styleOption));
  });

  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.filter = button.dataset.filter;
      updateFilterButtons();
      renderCards();
    });
  });

  elements.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value;
    renderCards();
  });

  elements.sortSelect.addEventListener("change", (event) => {
    state.sort = event.target.value;
    renderCards();
  });

  document.querySelector("#resetFilters").addEventListener("click", () => {
    state.filter = "all";
    state.query = "";
    elements.searchInput.value = "";
    updateFilterButtons();
    renderCards();
  });

}

async function loadData() {
  const response = await fetch(`data/repositories.json?cache=${Date.now()}`);
  if (!response.ok) throw new Error(`Data request failed: ${response.status}`);
  return response.json();
}

async function init() {
  setStyle(state.style);
  attachInteractions();
  try {
    const payload = await loadData();
    state.items = (payload.items || []).map(normalizeItem);
    updateAllCount();
    elements.lastSync.textContent = formatSync(payload.updated_at);
    renderCards();
  } catch (error) {
    elements.resultSummary.textContent = "数据暂时无法接入，请稍后刷新";
    elements.emptyState.hidden = false;
    console.error(error);
  }
}

init();
