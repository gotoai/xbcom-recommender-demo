"""FastAPI app for the XB.com recommender demo — a mobile-style shell.

Initial scope: the active-user list entry page, plus a stub user-detail overlay.
  * Entry page  — active inbound travelers, filterable by nationality / age band,
                  shuffled with a fixed seed, 20 per page.
  * User detail — stub overlay: profile + this week's aligned visit schedule.

Content comes from the primary TSVs via the data layer; the weekday-keyed rows are
aligned to the current JST week (see data.py / dates.py).
"""
from __future__ import annotations

import io
import logging

import segno
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import agent
from config import config

from . import data, dates, i18n, labels

log = logging.getLogger(__name__)

COUPON_PAGE_SIZE = 5  # coupons per page in the reco list panel

app = FastAPI(title="XB.com recommender web-app", version="0.1.0")

templates = Jinja2Templates(directory=str(config.BASE_DIR / "app" / "templates"))
app.mount("/static", StaticFiles(directory=str(config.BASE_DIR / "app" / "static")), name="static")
# Subcategory coupon images live in the repo's assets/images (served read-only). If
# the folder is absent the app still runs; the templates fall back to an emoji.
_assets = config.REPO_ROOT / "assets"
if _assets.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")


def _page_context(nationality: str | None, age: str | None, page: int) -> dict:
    """Shared context: filtered + paginated active users and the filter state."""
    d = data.get_data()
    age_band = int(age) if (age and age.isdigit()) else None
    matched = data.filter_users(d, nationality or None, age_band)
    page_users, page, total_pages = data.paginate(matched, page, config.PAGE_SIZE)
    return {
        "d": d,
        "users": page_users,
        "total": len(matched),
        "page": page,
        "total_pages": total_pages,
        "sel_nationality": nationality or "",
        "sel_age": age or "",
        "page_size": config.PAGE_SIZE,
    }


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    nationality: str | None = None,
    age: str | None = None,
    page: int = 1,
) -> HTMLResponse:
    from datetime import timedelta

    ctx = _page_context(nationality, age, page)
    d = ctx["d"]
    week_sunday = d.week_monday + timedelta(days=6)
    ctx["request"] = request
    ctx["ui_language"] = config.UI_LANGUAGE
    ctx["today_label"] = d.today.strftime("%Y/%m/%d")
    ctx["week_range"] = f"{d.week_monday.strftime('%m/%d')}（月）〜{week_sunday.strftime('%m/%d')}（日）"
    return templates.TemplateResponse(request, "index.html", ctx)


def _reco_or_404(traveler_id: int) -> dict | None:
    d = data.get_data()
    return data.build_reco(d, traveler_id, dates.jst_now())


def _parse_fav_ids(favorites: str | None) -> set[str]:
    """The client (localStorage) sends its favorite coupon ids as a CSV; parse to a
    set. The browser is the source of truth — the server keeps no favorites state."""
    if not favorites:
        return set()
    return {part for part in (p.strip() for p in favorites.split(",")) if part}


def _coupon_list_ctx(reco: dict, category: str | None, subcategory: str | None,
                     page: int, lang: str, t: dict, fav_ids: set[str],
                     favorites_only: bool = False) -> dict:
    """Context for the swap-in coupon-list fragment: the category/subcategory filter
    facets, the filtered + paginated coupons, and the current selection — plus the
    map markers for the *filtered* set, so the map stays in sync with the list.

    Filter option **values** and the selection stay English (the canonical
    ``category_en`` / ``subcategory_en`` the data filters on); the displayed
    **labels** — and the category on each coupon card — are translated to ``lang``.
    The subcategory dropdown depends on the chosen category; a stale subcategory (one
    not offered under the selected category) is dropped rather than empty-filtering.

    ``fav_ids`` are the coupon ids the browser has favorited (from localStorage);
    each card is marked ``is_favorite`` so the heart renders solid/hollow, and
    ``favorites_only`` narrows the list to them (ANDed with category/subcategory).
    """
    all_coupons = reco["coupons"]
    category = category or None
    subcategory = subcategory or None
    categories, subcats = data.coupon_facets(all_coupons)
    if category not in categories:
        category = None
    sub_values = subcats.get(category, []) if category else []
    if subcategory not in sub_values:
        subcategory = None
    filtered = data.filter_coupons(all_coupons, category, subcategory)
    if favorites_only:
        filtered = [c for c in filtered if str(c["coupon_id"]) in fav_ids]
    page_items, page, total_pages = data.paginate(filtered, page, COUPON_PAGE_SIZE)
    for c in page_items:
        c["category_label"] = labels.category_label(lang, c["category_en"])
        c["is_favorite"] = str(c["coupon_id"]) in fav_ids
    return {
        "u": reco["user"],
        "coupons": page_items,
        "total": len(filtered),
        "grand_total": len(all_coupons),
        "page": page,
        "total_pages": total_pages,
        "categories": [{"value": c, "label": labels.category_label(lang, c)}
                       for c in categories],
        "sub_options": [{"value": s, "label": labels.subcategory_label(lang, s)}
                        for s in sub_values],
        "sel_category": category or "",
        "sel_subcategory": subcategory or "",
        "favorites_only": favorites_only,
        "markers": data.reco_map_markers(filtered),
        "marker_cap": data.MAP_MARKER_CAP,
        "lang": lang,
        "t": t,
    }


@app.get("/ui/user/{traveler_id}", response_class=HTMLResponse)
async def ui_user_reco(request: Request, traveler_id: int, page: int = 1,
                       category: str | None = None,
                       subcategory: str | None = None,
                       lang: str | None = None,
                       favorites: str | None = None,
                       fav_only: bool = False) -> HTMLResponse:
    """The traveler's coupon-recommendation screen (user mode): a map centred on
    their current location, the active coupons within 5 km (filterable by category /
    subcategory, paginated), and a concierge-chat placeholder. Chrome is rendered in
    the traveler's own language by default; ``lang`` lets the viewer switch it. The
    coupon data itself stays English (its taxonomy labels excepted)."""
    reco = _reco_or_404(traveler_id)
    if reco is None:
        return HTMLResponse("<p class='error'>Unknown user.</p>", status_code=404)
    lang = i18n.resolve_lang(lang, reco["user"]["lang"])
    t = i18n.translations(lang)
    ctx = _coupon_list_ctx(reco, category, subcategory, page, lang, t,
                           _parse_fav_ids(favorites), fav_only)
    ctx.update({
        "loc": reco["location"],
        "radius_km": reco["radius_km"],
        "now_hm": dates.jst_now().strftime("%H:%M"),
        "dir": i18n.direction(lang),
        "language_options": i18n.LANGUAGE_OPTIONS,
    })
    return templates.TemplateResponse(request, "_user_reco.html", ctx)


@app.get("/ui/user/{traveler_id}/coupons", response_class=HTMLResponse)
async def ui_user_coupons(request: Request, traveler_id: int, page: int = 1,
                          category: str | None = None,
                          subcategory: str | None = None,
                          lang: str | None = None,
                          favorites: str | None = None,
                          fav_only: bool = False) -> HTMLResponse:
    """Just the coupon-list panel (filter bar + list + pager, plus the filtered map
    markers) — swapped in place by the reco screen's filters and pager without
    reloading the map."""
    reco = _reco_or_404(traveler_id)
    if reco is None:
        return HTMLResponse("<p class='error'>Unknown user.</p>", status_code=404)
    lang = i18n.resolve_lang(lang, reco["user"]["lang"])
    t = i18n.translations(lang)
    return templates.TemplateResponse(
        request, "_coupon_list.html",
        _coupon_list_ctx(reco, category, subcategory, page, lang, t,
                         _parse_fav_ids(favorites), fav_only))


@app.get("/ui/user/{traveler_id}/coupon/{coupon_id}", response_class=HTMLResponse)
async def ui_coupon_detail(request: Request, traveler_id: int, coupon_id: str,
                           lang: str | None = None,
                           favorites: str | None = None) -> HTMLResponse:
    """The coupon detail screen for one coupon in the traveler's reco set: a hero
    image with a redeem CTA, the product / coupon conditions, and an agent
    placeholder. Rendered in the traveler's language (``lang`` overrides). The coupon
    is resolved from the traveler's own reco list so it carries ``distance_km``."""
    reco = _reco_or_404(traveler_id)
    if reco is None:
        return HTMLResponse("<p class='error'>Unknown user.</p>", status_code=404)
    coupon = next((c for c in reco["coupons"]
                   if str(c["coupon_id"]) == str(coupon_id)), None)
    if coupon is None:
        return HTMLResponse("<p class='error'>Unknown coupon.</p>", status_code=404)
    lang = i18n.resolve_lang(lang, reco["user"]["lang"])
    t = i18n.translations(lang)
    coupon = dict(coupon)
    coupon["category_label"] = labels.category_label(lang, coupon["category_en"])
    coupon["subcategory_label"] = labels.subcategory_label(lang, coupon["subcategory_en"])
    coupon["is_favorite"] = str(coupon["coupon_id"]) in _parse_fav_ids(favorites)
    return templates.TemplateResponse(request, "_coupon_detail.html", {
        "u": reco["user"], "c": coupon, "t": t, "lang": lang,
        "dir": i18n.direction(lang), "language_options": i18n.LANGUAGE_OPTIONS,
    })


class ChatIn(BaseModel):
    message: str


def _latlon(rec: dict | None) -> tuple[float, float] | None:
    """(lat, lon) from a reco location / coupon dict, or None if unavailable."""
    if not rec:
        return None
    lat, lon = rec.get("latitude"), rec.get("longitude")
    return (lat, lon) if lat is not None and lon is not None else None


@app.post("/ui/user/{traveler_id}/chat")
async def reco_chat(traveler_id: int, body: ChatIn) -> JSONResponse:
    """One turn of the reco-screen (coupon-list) concierge chat — the traveler asking
    about their coupon set as a whole. Same naive relay as the coupon-detail chat, but
    a **per-traveler** history thread (``reco:<id>``), kept separate from the
    per-coupon threads. The traveler's current location is passed through so the agent
    can answer directions questions via the railway tool."""
    message = (body.message or "").strip()
    if not message:
        return JSONResponse({"error": "empty message"}, status_code=400)
    reco = _reco_or_404(traveler_id)
    origin = _latlon(reco["location"]) if reco else None
    session_key = f"reco:{traveler_id}"
    try:
        answer = await run_in_threadpool(
            agent.reply, session_key, traveler_id, message, origin=origin)
    except Exception:  # noqa: BLE001 — surface a generic failure; the panel shows a retry hint
        log.exception("reco-chat agent call failed (session=%s)", session_key)
        return JSONResponse({"error": "agent unavailable"}, status_code=502)
    return JSONResponse({"reply": answer})


@app.post("/ui/user/{traveler_id}/coupon/{coupon_id}/chat")
async def coupon_chat(traveler_id: int, coupon_id: str, body: ChatIn) -> JSONResponse:
    """One turn of the coupon-detail concierge chat. Naive first cut: the user's text
    is relayed to the data plane via ``agent.reply`` and the model's answer returned.
    History is server-held, keyed per (traveler, coupon) — the browser sends only the
    message. The traveler's current location and the coupon shop's location are passed
    through so the agent can answer "how do I get there?" via the railway tool. The
    blocking oumigo call runs in a threadpool so the event loop stays free."""
    message = (body.message or "").strip()
    if not message:
        return JSONResponse({"error": "empty message"}, status_code=400)
    reco = _reco_or_404(traveler_id)
    origin = _latlon(reco["location"]) if reco else None
    coupon = next((c for c in reco["coupons"] if str(c["coupon_id"]) == str(coupon_id)),
                  None) if reco else None
    destination = _latlon(coupon)
    session_key = f"{traveler_id}:{coupon_id}"
    try:
        answer = await run_in_threadpool(
            agent.reply, session_key, traveler_id, message,
            origin=origin, destination=destination, coupon=coupon)
    except Exception:  # noqa: BLE001 — surface a generic failure; the panel shows a retry hint
        log.exception("coupon-chat agent call failed (session=%s)", session_key)
        return JSONResponse({"error": "agent unavailable"}, status_code=502)
    return JSONResponse({"reply": answer})


@app.get("/api/coupon-qr/{code}")
async def coupon_qr(code: str) -> Response:
    """A 2D QR code (SVG) encoding the coupon code, shown in the redeem popup. Error
    correction level H (~30%) so the centred "XB eSIM" logo overlaid by the UI does
    not stop it from scanning. Pure-Python (segno) — no network or PIL needed."""
    qr = segno.make(code, error="h")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=10, border=2, dark="#1b2733", light="#ffffff")
    return Response(content=buf.getvalue(), media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/users")
async def api_users(
    nationality: str | None = None,
    age: str | None = None,
    page: int = 1,
) -> JSONResponse:
    ctx = _page_context(nationality, age, page)
    return JSONResponse({
        "today": ctx["d"].today.isoformat(),
        "week_monday": ctx["d"].week_monday.isoformat(),
        "total": ctx["total"],
        "page": ctx["page"],
        "total_pages": ctx["total_pages"],
        "page_size": ctx["page_size"],
        "users": ctx["users"],
    })


@app.get("/api/user/{traveler_id}/reco")
async def api_user_reco(traveler_id: int) -> JSONResponse:
    reco = _reco_or_404(traveler_id)
    if reco is None:
        return JSONResponse({"error": "unknown user"}, status_code=404)
    return JSONResponse({
        "user_id": traveler_id,
        "location": reco["location"],
        "radius_km": reco["radius_km"],
        "coupon_count": len(reco["coupons"]),
        "map_markers": len(data.reco_map_markers(reco["coupons"])),
        "coupons": reco["coupons"][:COUPON_PAGE_SIZE],
    })


@app.get("/api/nationalities")
async def api_nationalities() -> JSONResponse:
    d = data.get_data()
    return JSONResponse({"nationalities": d.nationalities, "age_bands": d.age_bands})


@app.get("/healthz")
async def healthz() -> dict:
    d = data.get_data()
    return {
        "status": "ok",
        "today": d.today.isoformat(),
        "active_users": len(d.users),
        "coupons": len(d.coupons),
        "active_coupons": len(d.active_coupons),
    }


def main() -> None:
    import uvicorn
    uvicorn.run(app, host=config.WEB_HOST, port=config.WEB_PORT, workers=1)


if __name__ == "__main__":
    main()
