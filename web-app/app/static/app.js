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
  let recoMap = null;

  function destroyRecoMap() {
    if (recoMap) { recoMap.remove(); recoMap = null; }
  }

  function initRecoMap() {
    destroyRecoMap();
    const el = document.getElementById("reco-map");
    const dataEl = document.getElementById("reco-data");
    if (!el || !dataEl || !window.L) return;
    let data;
    try { data = JSON.parse(dataEl.textContent); } catch { return; }
    if (!data.center) { el.innerHTML = "<p class='detail-loading' style='padding:16px'>Your current location is unavailable.</p>"; return; }

    const center = [data.center.lat, data.center.lon];
    recoMap = L.map(el, { zoomControl: true }).setView(center, 14);
    // Esri World Street Map — renders Latin/English labels for Japan (the OSM
    // default shows local Japanese names). English user view.
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19, attribution: "Tiles &copy; Esri",
    }).addTo(recoMap);

    // 5 km search radius + the traveler's current location at the centre.
    L.circle(center, { radius: data.radius_km * 1000, color: "#0a6cff", weight: 1, fillOpacity: 0.05 }).addTo(recoMap);
    const you = L.circleMarker(center, { radius: 8, color: "#fff", weight: 2, fillColor: "#0a6cff", fillOpacity: 1 })
      .addTo(recoMap).bindPopup("You are here");

    // Coupon pins (circleMarkers avoid needing external icon images).
    const pins = [you];
    (data.markers || []).forEach((m) => {
      const pin = L.circleMarker([m.lat, m.lon], {
        radius: 3, color: "#e8590c", weight: 1, fillColor: "#e8590c", fillOpacity: 0.85,
      }).addTo(recoMap);
      pin.bindPopup(`<b>${m.shop_name}</b><br>${m.discount} · ${m.distance_km} km`);
      pin._couponId = m.coupon_id;
      pins.push(pin);
    });

    try { recoMap.fitBounds(L.featureGroup(pins).getBounds().pad(0.15)); } catch { /* single point */ }
    // The container was hidden / mid slide-in transition; recompute tile layout
    // once it has settled.
    setTimeout(() => recoMap && recoMap.invalidateSize(), 350);
  }

  async function openUser(id) {
    open(overlay);
    await fetchInto(content, `/ui/user/${encodeURIComponent(id)}`);
    initRecoMap();
  }

  // Swap just the coupon-list panel for another page (map untouched).
  async function loadCouponPage(userId, page) {
    const list = document.getElementById("reco-list");
    if (!list) return;
    list.style.opacity = "0.5";
    try {
      const r = await fetch(`/ui/user/${encodeURIComponent(userId)}/coupons?page=${encodeURIComponent(page)}`);
      if (r.ok) list.innerHTML = await r.text();
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
      if (list) loadCouponPage(list.dataset.userId, pageBtn.dataset.page);
      return;
    }
    const card = e.target.closest(".user-card[data-user-id]");
    if (card) { openUser(card.dataset.userId); return; }
  });

  // Keyboard: Enter/Space activates a focused card; Esc closes the overlay.
  document.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && e.target.matches("[data-user-id]")) {
      e.preventDefault(); e.target.click();
    }
    if (e.key === "Escape" && !overlay.hidden) { destroyRecoMap(); close(overlay); }
  });
})();
