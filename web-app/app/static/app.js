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
    await fetchInto(content, `/ui/user/${encodeURIComponent(id)}`);
    initRecoMap();
  }

  // Rebuild the whole reco screen in a different UI language, preserving the current
  // filters + page. Re-inits the map (chrome strings are baked server-side).
  async function reloadReco(userId, lang, filters, page) {
    const params = new URLSearchParams();
    params.set("lang", lang);
    if (filters.category) params.set("category", filters.category);
    if (filters.subcategory) params.set("subcategory", filters.subcategory);
    params.set("page", page);
    await fetchInto(content, `/ui/user/${encodeURIComponent(userId)}?${params.toString()}`);
    initRecoMap();
  }

  // Current category / subcategory filter selection (read from the live selects,
  // which the fragment re-renders with their selected state on every swap).
  function currentFilters() {
    const cat = document.querySelector('.cf-select[data-filter="category"]');
    const sub = document.querySelector('.cf-select[data-filter="subcategory"]');
    return { category: cat ? cat.value : "", subcategory: sub ? sub.value : "" };
  }
  // Current UI language (the language switcher's value).
  function currentLang() {
    const sel = document.querySelector(".lang-select");
    return sel ? sel.value : "";
  }

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
    params.set("page", page);
    try {
      const r = await fetch(`/ui/user/${encodeURIComponent(userId)}/coupons?${params.toString()}`);
      if (r.ok) { list.innerHTML = await r.text(); list.dataset.page = page; renderPins(); }
    } catch { /* leave current page in place */ }
    list.style.opacity = "";
    const panel = list.closest(".reco-list-panel");
    if (panel) panel.scrollTop = 0;
  }

  // Delegated clicks: open a user card, page the coupon list, or close the screen.
  document.addEventListener("click", (e) => {
    if (e.target.closest("#user-back")) { destroyRecoMap(); close(overlay); return; }
    const pageBtn = e.target.closest(".reco-pager [data-page]");
    if (pageBtn) {
      const list = document.getElementById("reco-list");
      if (list) loadCouponList(list.dataset.userId, pageBtn.dataset.page, currentFilters());
      return;
    }
    const card = e.target.closest(".user-card[data-user-id]");
    if (card) { openUser(card.dataset.userId); return; }
  });

  // Delegated change: category/subcategory filters, or the language switcher.
  document.addEventListener("change", (e) => {
    const langSel = e.target.closest(".lang-select");
    if (langSel) {
      const list = document.getElementById("reco-list");
      const page = list ? (list.dataset.page || 1) : 1;
      reloadReco(langSel.dataset.userId, langSel.value, currentFilters(), page);
      return;
    }
    const sel = e.target.closest(".cf-select[data-filter]");
    if (!sel) return;
    const list = document.getElementById("reco-list");
    if (!list) return;
    // Changing the category resets the subcategory (its options depend on it).
    const filters = currentFilters();
    if (sel.dataset.filter === "category") filters.subcategory = "";
    loadCouponList(list.dataset.userId, 1, filters);
  });

  // Keyboard: Enter/Space activates a focused card; Esc closes the overlay.
  document.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && e.target.matches("[data-user-id]")) {
      e.preventDefault(); e.target.click();
    }
    if (e.key === "Escape" && !overlay.hidden) { destroyRecoMap(); close(overlay); }
  });
})();
