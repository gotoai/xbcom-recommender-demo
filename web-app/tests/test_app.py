"""Data-layer + endpoint smoke tests for the XB.com recommender web-app."""
from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

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


def test_user_detail_fragment():
    d = data.get_data()
    uid = d.users[0]["id"]
    r = client.get(f"/ui/user/{uid}")
    assert r.status_code == 200
    assert f"Traveler #{uid}" in r.text
    assert client.get("/ui/user/999999").status_code == 404


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["status"] == "ok"
