# XB.com recommender — web-app

A mobile-style demo front-end for the XB.com inbound-traveler coupon recommender.
Server-rendered with **FastAPI + Jinja2** (vanilla CSS/JS, no build step),
mirroring the OneNeo Bank concierge reference stack.

## Initialization data processing
The Tokyo visit/coupon data is authored against an abstract **Mon–Sun week**
(weekday `1–7`, no calendar dates — see `docs/scenarios/travelers.md`). On startup
the app anchors that week to the **real calendar week (JST) containing today**:

```
week_monday = today − (isoweekday − 1)      # Monday of the current week
weekday n   → week_monday + (n − 1) days
```

so every weekday-keyed row gains an aligned **date** column:

- `visit.tsv`  → `date` (the calendar date of its `weekday`).
- `coupon.tsv` → `coupon_start_date` (from `coupon_start_weekday`) and
  `coupon_end_date` (= start + `coupon_duration_days − 1`), giving each coupon its
  active date span in the current week.

Because the anchor depends on today, enrichment is computed **in memory at load**
(and cached for the JST day) — never written back to the TSVs, so it can't go stale.

## Entry page — active user list
The landing page lists the **active users** (the inbound travelers who appear in
`visit.tsv`).

- Two filter dropdowns at the top — **nationality** and **age band** — both
  default to the unset `-`.
- Selected filters are applied, the result is **shuffled with a fixed seed**
  (stable across pages/reloads), and shown **20 per page** with prev/next paging.
- Tapping a user opens their **user-mode reco screen** (below).

## User-mode reco screen
Tapping a traveler opens a full-screen overlay that mimics what *that* user sees in
their own mobile app right now. The **chrome is rendered in the traveler's own
language** — derived from their nationality via the country→language table in
`docs/profiles/users.md` (`app/i18n.py`). The 16 languages listed there are
supported (English, Korean, Simplified/Traditional Chinese, Thai, Vietnamese,
Filipino, Hindi, Spanish, Portuguese, French, German, Italian, Dutch, Hebrew — RTL
— and Turkish); any other nationality falls back to English. A **language switcher**
floats over the top of the map so the viewer can override the language for the
current view (the whole screen re-renders, filters + page preserved). The **coupon
data itself stays English** (shop / product names, discount, price) with one
exception: the **category / subcategory taxonomy is translated** to the display
language — all 20 categories (`app/labels.py`) and all 117 subcategories
(`app/labels_subcategory.py`) are covered for every one of the 16 languages, with
English as the fallback. Filter *values* stay the English canonical (that's what the
data is filtered on); only the displayed labels are localised. Three stacked panels:

1. **Map** (Leaflet) centred on the traveler's **current location** — the
   `visit.tsv` row for today's weekday and the current JST daypart (`06:00-11:59` /
   `12:00-17:59` / `18:00-23:59`; the 00–06 gap falls back to the evening bucket).
   The caption reads *"You are here: {ward} · {date} ({weekday}) {HH:MM}"* — the
   actual current clock time — followed by a **red-dot "Coupon" legend**. A 5 km
   search ring is drawn, and the active coupons in range are dropped as pins (nearest
   ~200, to stay readable). **The pins track the coupon-list filter** — narrowing by
   category / subcategory re-draws the map. Tiles are **Esri World Street Map**, which
   renders Latin/English place labels for Japan (the raw OSM basemap shows local
   Japanese names).
2. **Coupon list** — every active coupon within 5 km (joined `coupon.tsv` →
   `shop.tsv` for coordinates, filtered to those whose date span includes today),
   nearest first, paginated **5 per page**. Thumbnails come from `assets/images`.
   Two dropdowns at the top of the panel filter by **category** and **subcategory**
   (localised labels; the subcategory options depend on the chosen category).
   Changing a filter re-fetches this panel (page resets to 1) **and re-draws the map
   pins** to match.
3. **Concierge chat** — a placeholder (backend to come).

> Because shops populate only the 6 central wards (港/渋谷/新宿/台東/千代田/中央)
> while travelers move across all 23, a traveler currently in an outer ward may see
> **no** coupons within 5 km — an expected outcome, shown as an empty state. The
> same user's result changes through the day as their location moves.

Leaflet (CDN) and the Esri tiles both need **internet at runtime**; the rest of the
app works offline.

## Run
```bash
cd web-app
make install         # creates .venv, installs requirements
make dev             # autoreload on http://localhost:8091
# or: make serve
```

Open http://localhost:8091 (best viewed narrow, like a phone).

## Layout
```
web-app/
  app/
    config.py     # paths (→ ../DATA/s03_primary) + env
    dates.py      # JST today + weekday→date alignment
    data.py       # load TSVs, enrich w/ dates, filter/shuffle/paginate, coupon facets
    i18n.py       # nationality→language map + reco-screen chrome translations
    labels.py     # category taxonomy translations (+ subcategory helper)
    labels_subcategory.py  # subcategory taxonomy translations (all 16 languages)
    main.py       # FastAPI: entry page + /ui/user (+ filters, lang) + /api/* + /healthz
    templates/{index.html,_user_reco.html,_coupon_list.html}
    static/{styles.css,app.js}
  requirements.txt  Makefile  .env.example  README.md  BACKLOG.md
  tests/
```

The app owns no model and computes no recommendations yet — it reads the primary
TSVs and presents the aligned data.
