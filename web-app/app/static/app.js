// Entry-page interactions for the active-user list.
//   * Changing a filter dropdown auto-submits the form (page resets to 1).
//   * Tapping a user card opens a slide-in detail overlay, fetched as a fragment.
(function () {
  const form = document.getElementById("filter-form");

  // Auto-submit on filter change. Reset to page 1 whenever a filter changes so the
  // user isn't stranded on a page number that no longer exists for the new result.
  if (form) {
    form.querySelectorAll("[data-autosubmit]").forEach((sel) => {
      sel.addEventListener("change", () => {
        const page = form.querySelector('input[name="page"]');
        if (page) page.value = "1";
        form.submit();
      });
    });
  }

  // --- user detail overlay ---
  const overlay = document.getElementById("user-overlay");
  const content = document.getElementById("user-content");
  // --- coupon detail overlay (layers above the user/reco overlay) ---
  const couponOverlay = document.getElementById("coupon-overlay");
  const couponContent = document.getElementById("coupon-content");

  // --- favorites (persisted per-traveler in this browser via localStorage) ---
  // The browser is the source of truth; the server is told the current favorites on
  // each list request (to render the hearts and to filter "My favorites").
  const favKey = (userId) => `xb:favorites:${userId}`;
  function getFavs(userId) {
    try { return new Set(JSON.parse(localStorage.getItem(favKey(userId)) || "[]")); }
    catch { return new Set(); }
  }
  function toggleFav(userId, couponId) {
    const s = getFavs(userId);
    if (s.has(couponId)) s.delete(couponId); else s.add(couponId);
    try { localStorage.setItem(favKey(userId), JSON.stringify([...s])); } catch { /* quota/denied */ }
    return s.has(couponId);
  }
  const favCsv = (userId) => [...getFavs(userId)].join(",");

  const open = (ov) => { ov.hidden = false; requestAnimationFrame(() => ov.classList.add("open")); };
  const close = (ov) => {
    ov.classList.remove("open");
    const done = () => { ov.hidden = true; ov.removeEventListener("transitionend", done); };
    ov.addEventListener("transitionend", done);
  };

  async function fetchInto(el, url) {
    el.innerHTML = "<p class='detail-loading'>Loading…</p>";
    try {
      const r = await fetch(url);
      el.innerHTML = r.ok ? await r.text() : "<p class='error'>Could not load.</p>";
    } catch { el.innerHTML = "<p class='error'>A network error occurred.</p>"; }
    el.scrollTop = 0;
  }

  // --- Leaflet reco map ---
  let recoMap = null;      // the map instance
  let recoYou = null;      // "you are here" marker (kept across filter changes)
  let recoPins = null;     // layer group holding the coupon pins (re-rendered on filter)

  function destroyRecoMap() {
    if (recoMap) { recoMap.remove(); recoMap = null; recoYou = null; recoPins = null; }
  }

  // Draw the coupon pins from the current `#reco-markers` payload (the filtered set),
  // then fit the view to the pins + "you". Called on init and after every list swap,
  // so the map stays in sync with the filtered coupon list.
  function renderPins() {
    if (!recoMap || !recoPins) return;
    const el = document.getElementById("reco-markers");
    let markers = [];
    if (el) { try { markers = JSON.parse(el.textContent); } catch { /* keep [] */ } }
    recoPins.clearLayers();
    const group = recoYou ? [recoYou] : [];
    markers.forEach((m) => {
      const pin = L.circleMarker([m.lat, m.lon], {
        radius: 3, color: "#e8590c", weight: 1, fillColor: "#e8590c", fillOpacity: 0.85,
      });
      pin.bindPopup(`<b>${m.shop_name}</b><br>${m.discount} · ${m.distance_km} km`);
      pin._couponId = m.coupon_id;
      recoPins.addLayer(pin);
      group.push(pin);
    });
    try { recoMap.fitBounds(L.featureGroup(group).getBounds().pad(0.15)); } catch { /* single point */ }
  }

  function initRecoMap() {
    destroyRecoMap();
    const el = document.getElementById("reco-map");
    const dataEl = document.getElementById("reco-data");
    if (!el || !dataEl || !window.L) return;
    let data;
    try { data = JSON.parse(dataEl.textContent); } catch { return; }
    const i18n = data.i18n || {};
    if (!data.center) { el.innerHTML = `<p class='detail-loading' style='padding:16px'>${i18n.loc_unavailable || "Your current location is unavailable."}</p>`; return; }

    const center = [data.center.lat, data.center.lon];
    recoMap = L.map(el, { zoomControl: true }).setView(center, 14);
    // Esri World Street Map — renders Latin/English labels for Japan (the OSM
    // default shows local Japanese names).
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19, attribution: "Tiles &copy; Esri",
    }).addTo(recoMap);

    // 5 km search radius + the traveler's current location at the centre.
    L.circle(center, { radius: data.radius_km * 1000, color: "#0a6cff", weight: 1, fillOpacity: 0.05 }).addTo(recoMap);
    recoYou = L.circleMarker(center, { radius: 8, color: "#fff", weight: 2, fillColor: "#0a6cff", fillOpacity: 1 })
      .addTo(recoMap).bindPopup(i18n.you_are_here || "You are here");

    // Coupon pins (circleMarkers avoid needing external icon images), from the
    // fragment's `#reco-markers` payload.
    recoPins = L.layerGroup().addTo(recoMap);
    renderPins();

    // The container was hidden / mid slide-in transition; recompute tile layout
    // once it has settled.
    setTimeout(() => recoMap && recoMap.invalidateSize(), 350);
  }

  async function openUser(id) {
    open(overlay);
    const params = new URLSearchParams();
    const csv = favCsv(id);
    if (csv) params.set("favorites", csv);
    await fetchInto(content, `/ui/user/${encodeURIComponent(id)}?${params.toString()}`);
    initRecoMap();
  }

  // Rebuild the whole reco screen in a different UI language, preserving the current
  // filters + page. Re-inits the map (chrome strings are baked server-side).
  async function reloadReco(userId, lang, filters, page) {
    const params = new URLSearchParams();
    params.set("lang", lang);
    if (filters.category) params.set("category", filters.category);
    if (filters.subcategory) params.set("subcategory", filters.subcategory);
    const csv = favCsv(userId);
    if (csv) params.set("favorites", csv);
    if (filters.favOnly) params.set("fav_only", "1");
    params.set("page", page);
    await fetchInto(content, `/ui/user/${encodeURIComponent(userId)}?${params.toString()}`);
    initRecoMap();
  }

  // Current category / subcategory / favorites-only filter selection (read from the
  // live controls, which the fragment re-renders with their state on every swap).
  function currentFilters() {
    const cat = document.querySelector('.cf-select[data-filter="category"]');
    const sub = document.querySelector('.cf-select[data-filter="subcategory"]');
    const fav = document.querySelector('[data-filter="favorites"]');
    return {
      category: cat ? cat.value : "",
      subcategory: sub ? sub.value : "",
      favOnly: !!(fav && fav.checked),
    };
  }
  // Current UI language (the language switcher's value).
  function currentLang() {
    const sel = document.querySelector(".lang-select");
    return sel ? sel.value : "";
  }
  // The reco screen's current language (scoped, so it's read even while the coupon
  // overlay holds its own language switcher).
  function recoLang() {
    const sel = document.querySelector("#user-content .lang-select");
    return sel ? sel.value : "";
  }

  // --- coupon detail overlay ---
  async function openCoupon(userId, couponId) {
    open(couponOverlay);
    const params = new URLSearchParams();
    if (recoLang()) params.set("lang", recoLang());
    const csv = favCsv(userId);
    if (csv) params.set("favorites", csv);
    await fetchInto(couponContent, `/ui/user/${encodeURIComponent(userId)}/coupon/${encodeURIComponent(couponId)}?${params.toString()}`);
  }
  // Re-render the coupon detail in another language (from its own switcher).
  async function reloadCoupon(userId, couponId, lang) {
    const params = new URLSearchParams();
    params.set("lang", lang);
    const csv = favCsv(userId);
    if (csv) params.set("favorites", csv);
    await fetchInto(couponContent, `/ui/user/${encodeURIComponent(userId)}/coupon/${encodeURIComponent(couponId)}?${params.toString()}`);
  }
  // --- concierge chat (shared by the reco-list and coupon-detail panels) ---
  // Append a message bubble to the chat body and keep it scrolled to the newest.
  function appendMsg(body, cls, text) {
    const div = document.createElement("div");
    div.className = `msg ${cls}`;
    div.textContent = text;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
    return div;
  }

  // --- HTML sanitizer for the model's replies (it is instructed to answer in HTML) ---
  // DOMParser parses into an INERT document (no scripts run), then we rebuild the tree
  // from an allowlist: unknown tags are unwrapped (text kept), <script>/<style> dropped
  // whole, <a href> survives with a scheme check, and <img> only with a src on the
  // Mapillary CDN (the street-photo tool's images). No attribute the model sends is
  // trusted (no style/on*), so this is XSS-safe.
  const OK_TAGS = new Set(["P", "BR", "STRONG", "B", "EM", "I", "U", "S", "UL", "OL",
    "LI", "CODE", "PRE", "A", "H3", "H4", "H5", "BLOCKQUOTE", "SPAN", "SUP", "SUB", "IMG"]);
  const OK_ATTR = { A: new Set(["href"]), IMG: new Set(["src", "alt"]) };

  // <img src> is restricted to the Mapillary CDN host so a prompt-injected reply can't
  // load an arbitrary external image (tracking pixel / data exfil). Mapillary thumbs are
  // served from *.fbcdn.net over https.
  function isAllowedImgSrc(value) {
    try {
      const u = new URL(String(value).trim());
      return u.protocol === "https:" && /(^|\.)fbcdn\.net$/i.test(u.hostname);
    } catch { return false; }
  }

  function sanitizeInto(src, dst) {
    src.childNodes.forEach((node) => {
      if (node.nodeType === 3) {  // text
        dst.appendChild(document.createTextNode(node.nodeValue));
        return;
      }
      if (node.nodeType !== 1) return;  // drop comments / others
      const tag = node.tagName;
      if (tag === "SCRIPT" || tag === "STYLE" || tag === "TEMPLATE") return;  // + content
      if (!OK_TAGS.has(tag)) { sanitizeInto(node, dst); return; }  // unwrap unknown
      const el = document.createElement(tag);
      const allow = OK_ATTR[tag];
      if (allow) {
        for (const a of node.attributes) {
          const name = a.name.toLowerCase();
          if (!allow.has(name)) continue;
          if (name === "href" && !/^(https?:|mailto:)/i.test(a.value.trim())) continue;
          if (name === "src" && !isAllowedImgSrc(a.value)) continue;
          el.setAttribute(name, a.value);
        }
      }
      if (tag === "A") { el.setAttribute("target", "_blank"); el.setAttribute("rel", "noopener noreferrer"); }
      if (tag === "IMG") {
        if (!el.getAttribute("src")) return;  // drop an <img> with no allowed src
        el.setAttribute("referrerpolicy", "no-referrer");
        el.setAttribute("loading", "lazy");
      }
      sanitizeInto(node, el);
      dst.appendChild(el);
    });
    return dst;
  }
  function sanitizeHtml(html) {
    const doc = new DOMParser().parseFromString(String(html), "text/html");
    return sanitizeInto(doc.body, document.createElement("div")).innerHTML;
  }

  // Post one chat turn to the backend and render the reply. Naive: the server holds
  // the history (keyed per traveler, or per traveler+coupon); the browser sends only
  // the message text. Endpoint + strings come from the form's data-* attributes, so
  // the same handler drives both the reco-list and coupon-detail chats.
  async function sendChat(form) {
    const input = form.querySelector(".js-chat-text");
    const body = form.closest("section").querySelector(".reco-chat-body");
    if (!input || !body) return;
    const msg = input.value.trim();
    if (!msg) return;
    const btn = form.querySelector('button[type="submit"]');

    input.value = "";
    input.disabled = true;
    if (btn) btn.disabled = true;
    appendMsg(body, "user", msg);
    const pending = appendMsg(body, "assistant muted", form.dataset.thinking || "…");

    try {
      const r = await fetch(form.dataset.endpoint,
        { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: msg }) });
      const data = r.ok ? await r.json() : null;
      if (data && data.reply) {
        pending.className = "msg assistant";
        pending.innerHTML = sanitizeHtml(data.reply);  // model replies in (sanitized) HTML
      } else {
        pending.className = "msg assistant error-msg";
        pending.textContent = form.dataset.error || "Something went wrong.";
      }
    } catch {
      pending.className = "msg assistant error-msg";
      pending.textContent = form.dataset.error || "A network error occurred.";
    } finally {
      input.disabled = false;
      if (btn) btn.disabled = false;
      input.focus();
    }
  }

  // Redeem QR popup (pre-rendered hidden inside the coupon detail fragment).
  function qrModal() { return couponContent.querySelector("#qr-modal"); }
  function openQr() { const m = qrModal(); if (m) m.hidden = false; }
  function closeQr() { const m = qrModal(); if (m) m.hidden = true; }

  // Swap the coupon-list panel — a given page with the given filters applied — and
  // re-draw the map pins from the fragment's markers, so the map tracks the filter.
  async function loadCouponList(userId, page, filters) {
    const list = document.getElementById("reco-list");
    if (!list) return;
    list.style.opacity = "0.5";
    const params = new URLSearchParams();
    if (filters.category) params.set("category", filters.category);
    if (filters.subcategory) params.set("subcategory", filters.subcategory);
    if (currentLang()) params.set("lang", currentLang());
    const csv = favCsv(userId);
    if (csv) params.set("favorites", csv);
    if (filters.favOnly) params.set("fav_only", "1");
    params.set("page", page);
    try {
      const r = await fetch(`/ui/user/${encodeURIComponent(userId)}/coupons?${params.toString()}`);
      if (r.ok) { list.innerHTML = await r.text(); list.dataset.page = page; renderPins(); }
    } catch { /* leave current page in place */ }
    list.style.opacity = "";
    const panel = list.closest(".reco-list-panel");
    if (panel) panel.scrollTop = 0;
  }

  // Delegated clicks: open a user/coupon card, page the coupon list, redeem, or close.
  document.addEventListener("click", (e) => {
    // QR popup: close on the × button or a tap on the dim backdrop.
    if (e.target.closest("#qr-close") || e.target.classList.contains("qr-modal")) { closeQr(); return; }
    if (e.target.closest(".cd-use-btn")) { openQr(); return; }
    if (e.target.closest("#coupon-back")) { close(couponOverlay); return; }
    if (e.target.closest("#user-back")) { destroyRecoMap(); close(overlay); return; }
    // Favorite heart — toggle localStorage + icon; works from the list card or the
    // detail header, and never opens the card detail.
    const favBtn = e.target.closest(".cpn-fav[data-coupon-id]");
    if (favBtn) {
      const ctx = favBtn.closest("[data-user-id]");  // reco-list or coupon-detail
      if (!ctx) return;
      const userId = ctx.dataset.userId;
      const cid = favBtn.dataset.couponId;
      const nowFav = toggleFav(userId, cid);
      // Sync every heart for this coupon (list card + detail header stay in step).
      document.querySelectorAll(`.cpn-fav[data-coupon-id="${cid}"]`).forEach((b) => {
        b.classList.toggle("is-fav", nowFav);
        b.setAttribute("aria-pressed", nowFav ? "true" : "false");
      });
      // In "My favorites" view, un-favoriting removes the item — reload the list.
      const favChk = document.querySelector('[data-filter="favorites"]');
      const list = document.getElementById("reco-list");
      if (favChk && favChk.checked && !nowFav && list) {
        loadCouponList(userId, list.dataset.page || 1, currentFilters());
      }
      return;
    }
    const pageBtn = e.target.closest(".reco-pager [data-page]");
    if (pageBtn) {
      const list = document.getElementById("reco-list");
      if (list) loadCouponList(list.dataset.userId, pageBtn.dataset.page, currentFilters());
      return;
    }
    const coupon = e.target.closest(".coupon-card[data-coupon-id]");
    if (coupon) {
      const list = document.getElementById("reco-list");
      if (list) openCoupon(list.dataset.userId, coupon.dataset.couponId);
      return;
    }
    const card = e.target.closest(".user-card[data-user-id]");
    if (card) { openUser(card.dataset.userId); return; }
  });

  // Delegated change: category/subcategory filters, or a language switcher.
  document.addEventListener("change", (e) => {
    // Coupon detail's own switcher — checked first (it also carries .lang-select).
    const cLangSel = e.target.closest(".coupon-lang-select");
    if (cLangSel) {
      reloadCoupon(cLangSel.dataset.userId, cLangSel.dataset.couponId, cLangSel.value);
      return;
    }
    const langSel = e.target.closest(".lang-select");
    if (langSel) {
      const list = document.getElementById("reco-list");
      const page = list ? (list.dataset.page || 1) : 1;
      reloadReco(langSel.dataset.userId, langSel.value, currentFilters(), page);
      return;
    }
    // Coupon-list filters: category / subcategory selects or the "My favorites" checkbox.
    const filterEl = e.target.closest("[data-filter]");
    if (!filterEl) return;
    const list = document.getElementById("reco-list");
    if (!list) return;
    // Changing the category resets the subcategory (its options depend on it).
    const filters = currentFilters();
    if (filterEl.dataset.filter === "category") filters.subcategory = "";
    loadCouponList(list.dataset.userId, 1, filters);
  });

  // Delegated submit: either concierge chat form (reco-list or coupon-detail).
  document.addEventListener("submit", (e) => {
    const chatForm = e.target.closest(".js-chat-form");
    if (chatForm) { e.preventDefault(); sendChat(chatForm); }
  });

  // Keyboard: Enter/Space activates a focused card; Esc closes the top-most overlay.
  document.addEventListener("keydown", (e) => {
    // Chat composer (multi-line): Ctrl+Enter (or ⌘+Enter) sends; plain Enter is a
    // newline. Works in both the reco-list and coupon-detail chat inputs.
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey) &&
        e.target.classList.contains("js-chat-text")) {
      const form = e.target.closest(".js-chat-form");
      if (form) { e.preventDefault(); sendChat(form); return; }
    }
    if ((e.key === "Enter" || e.key === " ") &&
        e.target.matches(".user-card[data-user-id], .coupon-card[data-coupon-id]")) {
      e.preventDefault(); e.target.click();
    }
    if (e.key === "Escape") {
      const qm = qrModal();
      if (qm && !qm.hidden) { closeQr(); }
      else if (!couponOverlay.hidden) { close(couponOverlay); }
      else if (!overlay.hidden) { destroyRecoMap(); close(overlay); }
    }
  });
})();
