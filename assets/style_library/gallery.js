// ## 核心功能
// 把原生 registry 与 Remotion 配方快照合并为统一浏览模型，并负责筛选、按需预览、选择和复制。
// ## 输入
// window.__EFFECTS_REGISTRY__、window.__REMOTION_RECIPE_LIBRARY__ 与用户的筛选交互。
// ## 输出
// 配方卡 DOM、统计数字、预览弹窗和可复制给 Agent 的双引擎调用指令。
// ## 定位
// Gallery 客户端控制器；不写回 registry、recipe 快照或 snippet。
// ## 依赖
// 浏览器原生 IntersectionObserver、dialog、Clipboard API 与 localStorage。
// ## 维护规则
// 配方 schema、状态或交互变化时同步更新 gallery.html、gallery.css 和 EffectsLibrary_style_library_README.md。

(() => {
  "use strict";

  const nativePayload = window.__EFFECTS_REGISTRY__ || {effects: []};
  const remotionPayload = window.__REMOTION_RECIPE_LIBRARY__ || {recipes: [], stats: {}};

  const CATEGORY_LABELS = {
    all: "全部配方",
    skeleton: "骨架与常驻",
    container: "容器与画中画",
    beat: "内容与节拍",
    product: "产品卡片",
    opening: "开场与品牌",
    typography: "文字表现",
    "ui-entrance": "界面入场",
    camera: "镜头运动",
    data: "数据表达",
    interaction: "交互反馈",
    transition: "转场",
    rhythm: "节奏剪辑",
    effects: "光效与强调",
    util: "工具层",
    outro: "片尾",
    uncategorized: "未分类",
  };

  const ENGINE_LABELS = {
    native: "HTML / GSAP · Hyperframes",
    remotion: "Remotion · Frame Driven",
  };

  const state = {
    query: "",
    engine: "all",
    category: "all",
    status: "all",
    selected: new Set(),
    selectedStyles: new Map(),
    themeChoice: readStorage("motion-recipe-atlas-theme") || "dark",
  };

  const elements = {
    recipeGrid: document.querySelector("#recipeGrid"),
    emptyState: document.querySelector("#emptyState"),
    resultTitle: document.querySelector("#resultTitle"),
    resultCount: document.querySelector("#resultCount"),
    searchInput: document.querySelector("#searchInput"),
    categoryNav: document.querySelector("#categoryNav"),
    engineNav: document.querySelector("#engineNav"),
    statusFilter: document.querySelector("#statusFilter"),
    selectionBar: document.querySelector("#selectionBar"),
    selectionCount: document.querySelector("#selectionCount"),
    previewDialog: document.querySelector("#previewDialog"),
    dialogTitle: document.querySelector("#dialogTitle"),
    dialogEngine: document.querySelector("#dialogEngine"),
    dialogStage: document.querySelector("#dialogStage"),
    dialogFooter: document.querySelector("#dialogFooter"),
    toast: document.querySelector("#toast"),
  };

  const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#039;", '"': "&quot;",
  })[char]);

  const escapeAttr = escapeHtml;

  function readStorage(key) {
    try { return localStorage.getItem(key); } catch { return null; }
  }

  function writeStorage(key, value) {
    try { localStorage.setItem(key, value); } catch { /* file:// privacy mode */ }
  }

  function normalizeNative(effect) {
    const id = effect.id || "missing-id";
    return {
      uid: `native:${id}`,
      id,
      namespace: "chaojifeng-video-content-creator",
      name: effect.name || id,
      engine: "native",
      runtimeStatus: "local-ready",
      verification: "local-preview",
      category: effect.category || "uncategorized",
      tags: [effect.category || "uncategorized"],
      summary: effect.desc || "",
      intention: effect.desc || "",
      use: effect.desc || "",
      duration: "",
      energy: "",
      path: effect.path || "",
      anim: effect.anim || "",
      params: effect.params || "",
      accent: effect.accent || "#b7f34a",
      styles: [{
        id,
        name: effect.name || id,
        desc: effect.desc || "",
        preview: {type: "iframe", url: `previews/${encodeURIComponent(id)}.html`, availability: "local"},
      }],
    };
  }

  function normalizeRemotion(recipe) {
    return {
      ...recipe,
      uid: `remotion:${recipe.id}`,
      engine: "remotion",
      accent: "#72d9ff",
      styles: Array.isArray(recipe.styles) ? recipe.styles : [],
    };
  }

  const recipes = [
    ...(Array.isArray(nativePayload.effects) ? nativePayload.effects.map(normalizeNative) : []),
    ...(Array.isArray(remotionPayload.recipes) ? remotionPayload.recipes.map(normalizeRemotion) : []),
  ];

  const recipeByUid = new Map(recipes.map((recipe) => [recipe.uid, recipe]));
  let mediaObserver = null;
  let searchTimer = null;
  let toastTimer = null;

  function selectedStyle(recipe) {
    const index = Math.min(state.selectedStyles.get(recipe.uid) || 0, Math.max(recipe.styles.length - 1, 0));
    return {style: recipe.styles[index] || {}, index};
  }

  function searchableText(recipe) {
    return [
      recipe.id, recipe.name, recipe.engine, recipe.category,
      recipe.summary, recipe.intention, recipe.use, recipe.duration,
      recipe.energy, recipe.anim, recipe.params, recipe.path,
      ...(recipe.tags || []),
      ...recipe.styles.flatMap((style) => [style.id, style.name, style.desc]),
    ].filter(Boolean).join(" ").toLowerCase();
  }

  function matchesRecipe(recipe) {
    if (state.engine !== "all" && recipe.engine !== state.engine) return false;
    if (state.category !== "all" && recipe.category !== state.category && !(recipe.tags || []).includes(state.category)) return false;
    if (state.status === "local" && recipe.runtimeStatus !== "local-ready") return false;
    if (state.status === "upstream" && recipe.runtimeStatus !== "upstream-source") return false;
    return !state.query || searchableText(recipe).includes(state.query);
  }

  function visibleRecipes() {
    return recipes.filter(matchesRecipe).sort((a, b) => {
      if (a.engine !== b.engine) return a.engine === "native" ? -1 : 1;
      return a.name.localeCompare(b.name, "zh-CN");
    });
  }

  function categoryCounts() {
    const counts = {all: 0};
    recipes.filter((recipe) => {
      if (state.engine !== "all" && recipe.engine !== state.engine) return false;
      if (state.status === "local" && recipe.runtimeStatus !== "local-ready") return false;
      if (state.status === "upstream" && recipe.runtimeStatus !== "upstream-source") return false;
      return true;
    }).forEach((recipe) => {
      counts.all += 1;
      const keys = new Set([recipe.category, ...(recipe.tags || [])].filter(Boolean));
      keys.forEach((key) => { counts[key] = (counts[key] || 0) + 1; });
    });
    return counts;
  }

  function renderStats() {
    const nativeRecipes = recipes.filter((recipe) => recipe.engine === "native");
    const remotionRecipes = recipes.filter((recipe) => recipe.engine === "remotion");
    const nativeStyles = nativeRecipes.reduce((sum, recipe) => sum + recipe.styles.length, 0);
    const remotionStyles = remotionRecipes.reduce((sum, recipe) => sum + recipe.styles.length, 0);
    document.querySelector("#recipeCount").textContent = recipes.length;
    document.querySelector("#styleCount").textContent = nativeStyles + remotionStyles;
    document.querySelector("#nativeStyleCount").textContent = nativeStyles;
    document.querySelector("#remotionStyleCount").textContent = remotionStyles;
    document.querySelector("#allRecipeCount").textContent = recipes.length;
    document.querySelector("#nativeRecipeCount").textContent = nativeRecipes.length;
    document.querySelector("#remotionRecipeCount").textContent = remotionRecipes.length;
  }

  function renderCategories() {
    const counts = categoryCounts();
    const ordered = Object.keys(CATEGORY_LABELS).filter((key) => key === "all" || counts[key]);
    elements.categoryNav.innerHTML = ordered.map((key) => `
      <button type="button" data-category="${escapeAttr(key)}" class="${state.category === key ? "is-active" : ""}">
        <span class="category-dot"></span><span>${escapeHtml(CATEGORY_LABELS[key] || key)}</span><b>${counts[key] || 0}</b>
      </button>`).join("");
  }

  function mediaMarkup(recipe, style) {
    const preview = style.preview || {};
    const type = preview.type === "mp4" ? "video" : "iframe";
    const availability = preview.availability || "missing";
    if (!preview.url || availability === "missing") {
      return `<div class="media-placeholder"><span>PREVIEW UNAVAILABLE</span></div>`;
    }
    return `
      <div class="media-placeholder" data-media-placeholder data-preview-type="${type}" data-preview-url="${escapeAttr(preview.url)}">
        <span>${recipe.engine === "native" ? "LOCAL LIVE PREVIEW" : "REMOTE MOTION SAMPLE"}</span>
      </div>`;
  }

  function styleSwitcher(recipe, activeIndex) {
    if (recipe.styles.length < 2) return "";
    return `<div class="style-switcher" aria-label="配方变体">${recipe.styles.map((style, index) => `
      <button type="button" data-style-uid="${escapeAttr(recipe.uid)}" data-style-index="${index}" class="${index === activeIndex ? "is-active" : ""}" title="${escapeAttr(style.name || style.id)}">${String(index + 1).padStart(2, "0")}</button>`).join("")}</div>`;
  }

  function cardMarkup(recipe) {
    const {style, index} = selectedStyle(recipe);
    const isSelected = state.selected.has(recipe.uid);
    const engineColor = recipe.engine === "native" ? "var(--native)" : "var(--remotion)";
    const category = CATEGORY_LABELS[recipe.category] || recipe.category;
    const status = recipe.runtimeStatus === "local-ready" ? "本地可用" : "上游源码";
    const title = recipe.engine === "native" ? recipe.name : recipe.id;
    const codeLine = recipe.engine === "native" ? recipe.id : `${recipe.namespace}/${style.id || recipe.id}`;
    const summary = style.desc || recipe.summary || recipe.intention || "暂无配方说明";
    const sourceLink = recipe.engine === "remotion" && recipe.implementationUrl
      ? `<a href="${escapeAttr(recipe.implementationUrl)}" target="_blank" rel="noreferrer">源码</a>`
      : `<a href="previews/${encodeURIComponent(recipe.id)}.html" target="_blank" rel="noreferrer">独立预览</a>`;
    return `
      <article class="recipe-card${isSelected ? " is-selected" : ""}" data-recipe-uid="${escapeAttr(recipe.uid)}" style="--engine-color:${engineColor}">
        <div class="card-media">
          ${mediaMarkup(recipe, style)}
          <span class="engine-badge">${recipe.engine === "native" ? "NATIVE" : "REMOTION"}</span>
          <span class="status-badge">${status}</span>
          ${styleSwitcher(recipe, index)}
          <button type="button" class="media-action" data-preview-uid="${escapeAttr(recipe.uid)}" aria-label="放大预览 ${escapeAttr(title)}"></button>
        </div>
        <div class="card-body">
          <div class="card-heading"><div><h3>${escapeHtml(title)}</h3><code>${escapeHtml(codeLine)}</code></div><button type="button" class="select-toggle${isSelected ? " is-selected" : ""}" data-select-uid="${escapeAttr(recipe.uid)}" aria-label="${isSelected ? "移出" : "加入"}镜头计划" aria-pressed="${isSelected}"></button></div>
          <p class="recipe-summary">${escapeHtml(summary)}</p>
          <div class="meta-row"><span class="engine-meta">${escapeHtml(ENGINE_LABELS[recipe.engine])}</span><span>${escapeHtml(category)}</span>${recipe.duration ? `<span>${escapeHtml(recipe.duration)}</span>` : ""}${recipe.energy ? `<span>${escapeHtml(recipe.energy)}</span>` : ""}</div>
          <div class="card-actions"><button type="button" data-copy-uid="${escapeAttr(recipe.uid)}">复制当前配方</button>${sourceLink}</div>
        </div>
      </article>`;
  }

  function renderRecipes() {
    const visible = visibleRecipes();
    elements.recipeGrid.setAttribute("aria-busy", "true");
    elements.recipeGrid.innerHTML = visible.map(cardMarkup).join("");
    elements.recipeGrid.hidden = visible.length === 0;
    elements.emptyState.hidden = visible.length > 0;
    elements.recipeGrid.setAttribute("aria-busy", "false");
    const engineTitle = state.engine === "native" ? "原生 / Hyperframes 配方" : state.engine === "remotion" ? "Remotion 配方" : (CATEGORY_LABELS[state.category] || "全部配方");
    elements.resultTitle.textContent = engineTitle;
    const styleTotal = visible.reduce((sum, recipe) => sum + recipe.styles.length, 0);
    elements.resultCount.textContent = `${visible.length} 张配方卡 · ${styleTotal} 个动效样式`;
    observeMedia();
  }

  function observeMedia() {
    mediaObserver?.disconnect();
    const placeholders = [...document.querySelectorAll("[data-media-placeholder]")];
    if (!("IntersectionObserver" in window)) {
      placeholders.slice(0, 12).forEach(hydrateMedia);
      return;
    }
    mediaObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        hydrateMedia(entry.target);
        mediaObserver.unobserve(entry.target);
      });
    }, {rootMargin: "280px 0px", threshold: 0.01});
    placeholders.forEach((placeholder) => mediaObserver.observe(placeholder));
  }

  function hydrateMedia(placeholder) {
    if (!placeholder?.isConnected) return;
    const type = placeholder.dataset.previewType;
    const url = placeholder.dataset.previewUrl;
    if (!url) return;
    if (type === "video") {
      const video = document.createElement("video");
      video.src = url;
      video.muted = true;
      video.loop = true;
      video.playsInline = true;
      video.preload = "metadata";
      video.addEventListener("mouseenter", () => video.play().catch(() => {}));
      video.addEventListener("mouseleave", () => video.pause());
      video.addEventListener("error", () => showToast("远程预览暂时不可用，配方和源码仍可使用"), {once: true});
      placeholder.replaceWith(video);
      return;
    }
    const iframe = document.createElement("iframe");
    iframe.src = url;
    iframe.loading = "lazy";
    iframe.title = "本地动效预览";
    iframe.tabIndex = -1;
    placeholder.replaceWith(iframe);
  }

  function renderAll() {
    renderStats();
    renderCategories();
    elements.engineNav.querySelectorAll("[data-engine]").forEach((button) => button.classList.toggle("is-active", button.dataset.engine === state.engine));
    elements.statusFilter.querySelectorAll("[data-status]").forEach((button) => button.classList.toggle("is-active", button.dataset.status === state.status));
    renderRecipes();
    renderSelection();
  }

  function copyTextFor(recipe) {
    const {style} = selectedStyle(recipe);
    if (recipe.engine === "native") {
      return `请在视频里使用原生动效配方「${recipe.id}（${recipe.name}）」。引擎：HTML/GSAP + Hyperframes；snippet：${recipe.path}；动效：${recipe.anim || "按配方默认"}；参数：${recipe.params || "按配方默认"}。`;
    }
    return `请在视频里使用 Remotion 动效配方「${recipe.id}」，当前样式「${style.id || recipe.id}」。引擎：Remotion 帧驱动；配方：${recipe.recipeUrl || "见本地配方库"}；源码实现：${recipe.implementationUrl || recipe.githubSourceUrl || "见上游仓库"}。请按当前视频真实文案和素材改写，不把远程预览当成本地已渲染结果。`;
  }

  async function copyText(text, successMessage) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const area = document.createElement("textarea");
        area.value = text;
        area.style.cssText = "position:fixed;opacity:0;pointer-events:none";
        document.body.append(area);
        area.select();
        document.execCommand("copy");
        area.remove();
      }
      showToast(successMessage);
    } catch {
      showToast("复制失败，请打开配方详情后手动复制");
    }
  }

  function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.classList.toggle("has-selection", state.selected.size > 0);
    elements.toast.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => elements.toast.classList.remove("is-visible"), 2200);
  }

  function renderSelection() {
    elements.selectionBar.hidden = state.selected.size === 0;
    elements.selectionCount.textContent = state.selected.size;
  }

  function openPreview(recipe) {
    const {style} = selectedStyle(recipe);
    const preview = style.preview || {};
    elements.dialogTitle.textContent = recipe.engine === "native" ? recipe.name : `${recipe.id} · ${style.id || recipe.id}`;
    elements.dialogEngine.textContent = ENGINE_LABELS[recipe.engine];
    elements.dialogStage.innerHTML = "";
    if (preview.url) {
      if (preview.type === "mp4") {
        const video = document.createElement("video");
        video.src = preview.url; video.controls = true; video.autoplay = true; video.loop = true; video.muted = true; video.playsInline = true;
        elements.dialogStage.append(video);
      } else {
        const iframe = document.createElement("iframe");
        iframe.src = preview.url; iframe.title = elements.dialogTitle.textContent;
        elements.dialogStage.append(iframe);
      }
    } else {
      elements.dialogStage.innerHTML = '<div class="media-placeholder"><span>PREVIEW UNAVAILABLE</span></div>';
    }
    const links = [];
    if (recipe.recipeUrl) links.push(`<a href="${escapeAttr(recipe.recipeUrl)}" target="_blank" rel="noreferrer">查看配方说明</a>`);
    if (recipe.implementationUrl) links.push(`<a href="${escapeAttr(recipe.implementationUrl)}" target="_blank" rel="noreferrer">查看 Remotion 源码</a>`);
    if (recipe.engine === "native") links.push(`<a href="previews/${encodeURIComponent(recipe.id)}.html" target="_blank">打开独立预览</a>`);
    elements.dialogFooter.innerHTML = links.join("");
    if (typeof elements.previewDialog.showModal === "function") elements.previewDialog.showModal();
    else elements.previewDialog.setAttribute("open", "");
  }

  function closePreview() {
    elements.dialogStage.querySelector("video")?.pause();
    elements.dialogStage.innerHTML = "";
    if (typeof elements.previewDialog.close === "function" && elements.previewDialog.open) elements.previewDialog.close();
    else elements.previewDialog.removeAttribute("open");
  }

  function clearFilters() {
    state.query = ""; state.engine = "all"; state.category = "all"; state.status = "all";
    elements.searchInput.value = "";
    renderAll();
  }

  function resolveTheme(choice) {
    if (choice !== "system") return choice;
    return window.matchMedia?.("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }

  function applyTheme(choice) {
    state.themeChoice = choice;
    document.documentElement.dataset.theme = resolveTheme(choice);
    document.querySelectorAll("[data-theme-choice]").forEach((button) => button.classList.toggle("is-active", button.dataset.themeChoice === choice));
    writeStorage("motion-recipe-atlas-theme", choice);
  }

  elements.engineNav.addEventListener("click", (event) => {
    const button = event.target.closest("[data-engine]");
    if (!button) return;
    state.engine = button.dataset.engine;
    if (state.engine === "native" && state.status === "upstream") state.status = "all";
    if (state.engine === "remotion" && state.status === "local") state.status = "all";
    state.category = "all";
    renderAll();
  });

  elements.categoryNav.addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    state.category = button.dataset.category;
    renderAll();
  });

  elements.statusFilter.addEventListener("click", (event) => {
    const button = event.target.closest("[data-status]");
    if (!button) return;
    state.status = button.dataset.status;
    state.category = "all";
    renderAll();
  });

  elements.searchInput.addEventListener("input", (event) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { state.query = event.target.value.trim().toLowerCase(); renderRecipes(); }, 120);
  });

  elements.recipeGrid.addEventListener("click", (event) => {
    const styleButton = event.target.closest("[data-style-uid]");
    if (styleButton) {
      state.selectedStyles.set(styleButton.dataset.styleUid, Number(styleButton.dataset.styleIndex));
      renderRecipes();
      return;
    }
    const selectButton = event.target.closest("[data-select-uid]");
    if (selectButton) {
      const uid = selectButton.dataset.selectUid;
      state.selected.has(uid) ? state.selected.delete(uid) : state.selected.add(uid);
      renderRecipes(); renderSelection();
      return;
    }
    const copyButton = event.target.closest("[data-copy-uid]");
    if (copyButton) {
      const recipe = recipeByUid.get(copyButton.dataset.copyUid);
      if (recipe) copyText(copyTextFor(recipe), "当前配方已复制");
      return;
    }
    const previewButton = event.target.closest("[data-preview-uid]");
    if (previewButton) {
      const recipe = recipeByUid.get(previewButton.dataset.previewUid);
      if (recipe) openPreview(recipe);
    }
  });

  document.querySelector("#clearSelected").addEventListener("click", () => { state.selected.clear(); renderRecipes(); renderSelection(); });
  document.querySelector("#copySelected").addEventListener("click", () => {
    const text = [...state.selected].map((uid) => recipeByUid.get(uid)).filter(Boolean).map(copyTextFor).join("\n\n");
    copyText(text, `已复制 ${state.selected.size} 张配方`);
  });
  document.querySelector("#clearFilters").addEventListener("click", clearFilters);
  document.querySelector("#closeDialog").addEventListener("click", closePreview);
  elements.previewDialog.addEventListener("click", (event) => { if (event.target === elements.previewDialog) closePreview(); });
  elements.previewDialog.addEventListener("cancel", (event) => { event.preventDefault(); closePreview(); });
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); elements.searchInput.focus(); }
  });
  document.querySelectorAll("[data-theme-choice]").forEach((button) => button.addEventListener("click", () => applyTheme(button.dataset.themeChoice)));
  window.matchMedia?.("(prefers-color-scheme: light)").addEventListener?.("change", () => { if (state.themeChoice === "system") applyTheme("system"); });

  applyTheme(state.themeChoice);
  renderAll();
})();
