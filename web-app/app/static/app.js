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
    el.innerHTML = "<p class='detail-loading'>読み込み中…</p>";
    try {
      const r = await fetch(url);
      el.innerHTML = r.ok ? await r.text() : "<p class='error'>読み込めませんでした。</p>";
    } catch { el.innerHTML = "<p class='error'>通信エラーが発生しました。</p>"; }
    el.scrollTop = 0;
  }

  async function openUser(id) {
    open(overlay);
    await fetchInto(content, `/ui/user/${encodeURIComponent(id)}`);
  }

  // Delegated clicks: open a user card, or the back button inside the fragment.
  document.addEventListener("click", (e) => {
    if (e.target.closest("#user-back")) { close(overlay); return; }
    const card = e.target.closest("[data-user-id]");
    if (card) { openUser(card.dataset.userId); return; }
  });

  // Keyboard: Enter/Space activates a focused card; Esc closes the overlay.
  document.addEventListener("keydown", (e) => {
    if ((e.key === "Enter" || e.key === " ") && e.target.matches("[data-user-id]")) {
      e.preventDefault(); e.target.click();
    }
    if (e.key === "Escape" && !overlay.hidden) close(overlay);
  });
})();
