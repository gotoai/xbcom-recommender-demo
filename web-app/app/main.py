"""FastAPI app for the XB.com recommender demo — a mobile-style shell.

Initial scope: the active-user list entry page, plus a stub user-detail overlay.
  * Entry page  — active inbound travelers, filterable by nationality / age band,
                  shuffled with a fixed seed, 20 per page.
  * User detail — stub overlay: profile + this week's aligned visit schedule.

Content comes from the primary TSVs via the data layer; the weekday-keyed rows are
aligned to the current JST week (see data.py / dates.py).
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config, data, dates

COUPON_PAGE_SIZE = 5  # coupons per page in the reco list panel

app = FastAPI(title="XB.com recommender web-app", version="0.1.0")

templates = Jinja2Templates(directory=str(config.BASE_DIR / "app" / "templates"))
app.mount("/static", StaticFiles(directory=str(config.BASE_DIR / "app" / "static")), name="static")
# Shop category thumbnails live in the repo's assets/images (served read-only). If
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


@app.get("/ui/user/{traveler_id}", response_class=HTMLResponse)
async def ui_user_reco(request: Request, traveler_id: int, page: int = 1) -> HTMLResponse:
    """The traveler's coupon-recommendation screen (user mode): a map centred on
    their current location, the active coupons within 5 km (paginated list), and a
    concierge-chat placeholder."""
    reco = _reco_or_404(traveler_id)
    if reco is None:
        return HTMLResponse("<p class='error'>不明なユーザーです。</p>", status_code=404)
    coupons = reco["coupons"]
    page_items, page, total_pages = data.paginate(coupons, page, COUPON_PAGE_SIZE)
    return templates.TemplateResponse(request, "_user_reco.html", {
        "u": reco["user"],
        "loc": reco["location"],
        "radius_km": reco["radius_km"],
        "total": len(coupons),
        "markers": data.reco_map_markers(coupons),
        "marker_cap": data.MAP_MARKER_CAP,
        "coupons": page_items,
        "page": page,
        "total_pages": total_pages,
    })


@app.get("/ui/user/{traveler_id}/coupons", response_class=HTMLResponse)
async def ui_user_coupons(request: Request, traveler_id: int, page: int = 1) -> HTMLResponse:
    """Just the coupon-list panel (list + pager) for a given page — swapped in place
    by the reco screen's pager without reloading the map."""
    reco = _reco_or_404(traveler_id)
    if reco is None:
        return HTMLResponse("<p class='error'>不明なユーザーです。</p>", status_code=404)
    coupons = reco["coupons"]
    page_items, page, total_pages = data.paginate(coupons, page, COUPON_PAGE_SIZE)
    return templates.TemplateResponse(request, "_coupon_list.html", {
        "u": reco["user"],
        "total": len(coupons),
        "coupons": page_items,
        "page": page,
        "total_pages": total_pages,
    })


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
