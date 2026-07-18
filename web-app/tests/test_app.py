"""Data-layer + endpoint smoke tests for the XB.com recommender web-app."""
from __future__ import annotations

from datetime import date, datetime, timezone, timedelta

from fastapi.testclient import TestClient

JST = timezone(timedelta(hours=9))

from app import config, data, dates
from app.main import app

client = TestClient(app)


# --- weekday -> date alignment ------------------------------------------------
def test_week_monday_is_monday():
    # 2026-07-18 is a Saturday (isoweekday 6).
    today = date(2026, 7, 18)
    mon = dates.week_monday(today)
    assert mon == date(2026, 7, 13)
    assert mon.isoweekday() == 1


def test_weekday_to_date_spans_the_current_week():
    today = date(2026, 7, 18)
    assert dates.weekday_to_date(1, today) == date(2026, 7, 13)  # Mon
    assert dates.weekday_to_date(6, today) == today               # Sat = today
    assert dates.weekday_to_date(7, today) == date(2026, 7, 19)  # Sun


def test_weekday_to_date_boundaries():
    # A Sunday today: weekday 7 maps to today, weekday 1 to the same week's Monday.
    sunday = date(2026, 7, 19)
    assert dates.weekday_to_date(7, sunday) == sunday
    assert dates.weekday_to_date(1, sunday) == date(2026, 7, 13)
    for bad in (0, 8, -1):
        try:
            dates.weekday_to_date(bad, sunday)
            assert False, "expected ValueError"
        except ValueError:
            pass


# --- data layer ---------------------------------------------------------------
def test_active_users_and_enrichment():
    d = data.get_data()
    assert d.users, "expected active users"
    assert len(d.users) == len(d.users_by_id)
    u = d.users[0]
    assert u["age"] == d.today.year - u["birthyear"]
    assert u["age_band"] % 10 == 0
    assert u["flag"]  # every nationality maps to a flag
    assert u["gender"] in ("F", "M", "-")
    assert u["face"] in ("👩", "👨", "🧑")  # gender-neutral face for unknown
    # Visits are enriched with an aligned ISO date.
    visits = d.visits_by_user[u["id"]]
    assert visits and all("date" in v for v in visits)


def test_coupons_have_aligned_dates():
    d = data.get_data()
    assert d.coupons
    c = d.coupons[0]
    assert c["coupon_start_date"] <= c["coupon_end_date"]
    # end = start + (duration - 1) days
    start = date.fromisoformat(c["coupon_start_date"])
    end = date.fromisoformat(c["coupon_end_date"])
    assert (end - start).days == c["coupon_duration_days"] - 1


def test_seeded_shuffle_is_stable():
    order1 = [u["id"] for u in data._load(date(2026, 7, 18)).users]
    order2 = [u["id"] for u in data._load(date(2026, 7, 18)).users]
    assert order1 == order2  # same seed -> same order


def test_filter_and_paginate():
    d = data.get_data()
    nat = d.nationalities[0]
    matched = data.filter_users(d, nat, None)
    assert matched and all(u["nationality"] == nat for u in matched)
    page1, p, total = data.paginate(matched, 1, config.PAGE_SIZE)
    assert p == 1 and len(page1) <= config.PAGE_SIZE
    # Out-of-range page clamps to the last page.
    _, p_clamped, total_pages = data.paginate(matched, 9999, config.PAGE_SIZE)
    assert p_clamped == total_pages


# --- endpoints ----------------------------------------------------------------
def test_index_ok():
    r = client.get("/")
    assert r.status_code == 200
    assert "国籍" in r.text and "年代" in r.text


def test_index_pagination_stable():
    a = client.get("/?page=1").text
    b = client.get("/?page=1").text
    assert a == b


def test_api_users_filtered():
    d = data.get_data()
    nat = d.nationalities[0]
    r = client.get(f"/api/users?nationality={nat}")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert all(u["nationality"] == nat for u in body["users"])


# --- reco (user-mode) ---------------------------------------------------------
def test_current_timespan_buckets():
    def span(h):
        return data.current_timespan(datetime(2026, 7, 18, h, 0, tzinfo=JST))
    assert span(9) == "06:00-11:59"
    assert span(14) == "12:00-17:59"
    assert span(20) == "18:00-23:59"
    assert span(3) == "18:00-23:59"   # 00:00-05:59 falls back to the evening bucket


def test_coupons_within_search():
    # Shops populate the 6 central wards, so a central point has active coupons
    # within 5 km; results are all active, in range, and nearest-first.
    d = data.get_data()
    near = data.coupons_within(d, 35.6595, 139.7005, data.RECO_RADIUS_KM)  # 渋谷
    assert near, "central Tokyo should have active coupons within 5 km"
    assert all(c["active"] and c["distance_km"] <= data.RECO_RADIUS_KM for c in near)
    assert near == sorted(near, key=lambda c: c["distance_km"])
    # English fields present for the user-mode view.
    c = near[0]
    assert c["product_name_en"] and c["shop_name_en"] and c["category_en"]
    assert c["discount_label"].endswith("OFF") and ("%" in c["discount_label"] or "¥" in c["discount_label"])
    # Marker cap: nearest N, with only the fields the pins need.
    markers = data.reco_map_markers(near)
    assert len(markers) == min(len(near), data.MAP_MARKER_CAP)
    assert {"coupon_id", "lat", "lon", "shop_name", "discount", "distance_km"} <= markers[0].keys()


def test_build_reco_location():
    d = data.get_data()
    uid = d.users[0]["id"]
    now = datetime(2026, 7, 18, 14, 0, tzinfo=JST)  # Sat afternoon -> 12:00-17:59
    reco = data.build_reco(d, uid, now)
    assert reco is not None
    loc = reco["location"]
    assert loc and loc["timespan"] == "12:00-17:59"
    # Location matches the user's visit row for that weekday/timespan.
    v = next(x for x in d.visits_by_user[uid]
             if x["weekday"] == 6 and x["timespan"] == "12:00-17:59")
    assert (loc["latitude"], loc["longitude"]) == (v["latitude"], v["longitude"])
    # Coupons (possibly empty for an outer-ward location) obey the invariants.
    assert all(c["active"] and c["distance_km"] <= data.RECO_RADIUS_KM
               for c in reco["coupons"])
    assert reco["coupons"] == sorted(reco["coupons"], key=lambda c: c["distance_km"])


def test_reco_screen_and_paging():
    d = data.get_data()
    uid = d.users[0]["id"]
    r = client.get(f"/ui/user/{uid}")
    assert r.status_code == 200
    assert f"Traveler #{uid}" in r.text
    assert 'id="reco-map"' in r.text and 'id="reco-data"' in r.text
    # User-mode view is English.
    for token in ("‹ Back", "You are here", "Coupons", "within 5"):
        assert token in r.text
    assert "現在地" not in r.text and "戻る" not in r.text
    # coupon-list fragment paginates 5/page
    r2 = client.get(f"/ui/user/{uid}/coupons?page=2")
    assert r2.status_code == 200
    assert r2.text.count("coupon-card") <= 5
    assert client.get("/ui/user/999999").status_code == 404


def test_api_user_reco():
    d = data.get_data()
    uid = d.users[0]["id"]
    r = client.get(f"/api/user/{uid}/reco")
    assert r.status_code == 200
    body = r.json()
    assert body["radius_km"] == data.RECO_RADIUS_KM
    assert body["map_markers"] <= data.MAP_MARKER_CAP
    assert body["location"]["ward"]


def test_healthz():
    r = client.get("/healthz")
    body = r.json()
    assert r.status_code == 200 and body["status"] == "ok"
    assert body["active_coupons"] >= 1
