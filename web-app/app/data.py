"""In-memory data layer for the XB.com recommender web-app.

Loads the primary TSVs (DATA/s03_primary) and enriches the weekday-keyed rows with
the calendar dates of the current JST week (see ``dates.py``):

  * active users   — inbound travelers that appear in visit.tsv, with derived
                     age / age band / nationality flag, plus this week's visits.
  * visits         — each row gains a ``date`` (from its ``weekday``).
  * shops          — id -> coordinates / names / category (for the coupon join).
  * coupons        — each row gains ``coupon_start_date`` / ``coupon_end_date``,
                     an ``active`` flag (date range includes today), a human
                     ``discount_label``, and its shop's coordinates.

On top of that the layer answers a per-user "what does this traveler see right now"
query (``build_reco``): their current location (the visit row for today's weekday
and the current JST timespan) and the active coupons within 5 km, nearest first.

The active-user list is shuffled once with a fixed seed at load, so filtering and
pagination are stable across pages and reloads. Reloaded automatically when the JST
day changes (the date anchor moves), otherwise cached.
"""
from __future__ import annotations

import csv
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime

from . import config, dates

# The three daypart timespans the visit data is bucketed into.
TIMESPANS = ("06:00-11:59", "12:00-17:59", "18:00-23:59")
# Coupon search radius around the traveler's current location.
RECO_RADIUS_KM = 5.0
# Cap on how many coupons are drawn as pins on the map (nearest first). The list
# panel still paginates the full result set.
MAP_MARKER_CAP = 200

# Nationality (Japanese label in the data) -> flag emoji, for the user cards and the
# dropdown. Covers every value present in inbound_traveler.tsv.
NATIONALITY_FLAG = {
    "韓国": "🇰🇷", "台湾": "🇹🇼", "米国": "🇺🇸", "中国": "🇨🇳", "香港": "🇭🇰",
    "豪州": "🇦🇺", "タイ": "🇹🇭", "フィリピン": "🇵🇭", "カナダ": "🇨🇦", "ベトナム": "🇻🇳",
    "インドネシア": "🇮🇩", "英国": "🇬🇧", "フランス": "🇫🇷", "マレーシア": "🇲🇾",
    "ドイツ": "🇩🇪", "シンガポール": "🇸🇬", "インド": "🇮🇳", "イタリア": "🇮🇹",
    "メキシコ": "🇲🇽", "スペイン": "🇪🇸", "オランダ": "🇳🇱", "ニュージーランド": "🇳🇿",
    "トルコ": "🇹🇷", "スイス": "🇨🇭", "スウェーデン": "🇸🇪", "ベルギー": "🇧🇪",
    "イスラエル": "🇮🇱", "デンマーク": "🇩🇰", "ノルウェー": "🇳🇴", "フィンランド": "🇫🇮",
    "サウジアラビア": "🇸🇦", "アラブ首長国連邦": "🇦🇪", "クウェート": "🇰🇼",
    "カタール": "🇶🇦", "バーレーン": "🇧🇭", "オマーン": "🇴🇲",
}


def nationality_flag(nat: str) -> str:
    return NATIONALITY_FLAG.get(nat, "🏳️")


# Gender code (F/M/-) -> an emoji face. '-' (unknown / not disclosed) gets the
# gender-neutral face.
GENDER_FACE = {"F": "👩", "M": "👨", "-": "🧑"}
GENDER_LABEL = {"F": "女性", "M": "男性", "-": "不明"}
GENDER_EN = {"F": "Female", "M": "Male", "-": "Unknown"}


def gender_face(gender: str) -> str:
    return GENDER_FACE.get(gender, "🧑")


def age_band(age: int) -> int:
    """Decade band an age falls in, e.g. 39 -> 30. Ages < 10 clamp to 10."""
    return max(10, (age // 10) * 10)


# Fallback emoji per shop category, shown if the asset thumbnail fails to load.
CATEGORY_EMOJI = {
    "レストラン": "🍽️", "バー": "🍺", "コンビニエンスストア": "🏪", "コーヒーショップ": "☕",
    "衣料品店": "👕", "ファストフード": "🍔", "スイーツショップ": "🍰", "美容院": "💇",
    "ドラッグストア": "💊", "マッサージ店": "💆", "ディスカウントストア": "🏷️",
    "音楽・映像・ゲーム店": "🎮", "カラオケボックス": "🎤", "書店": "📚", "映画館": "🎬",
    "家電量販店": "🔌", "スパ": "♨️", "スポーツジム・プール": "🏋️", "レンタカー": "🚗",
    "荷物預かりサービス": "🧳",
}


def category_emoji(category: str) -> str:
    return CATEGORY_EMOJI.get(category, "🎟️")


def discount_label(display: str, amount: float, rate: float) -> str:
    """Human coupon-discount label: rate -> 'NN%OFF', amount -> 'NNN円OFF'."""
    if display == "rate":
        return f"{round(rate * 100)}%OFF"
    return f"{int(round(amount)):,}円OFF"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon points."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def current_timespan(now: datetime) -> str:
    """The visit timespan bucket for the current JST clock time.

    The data only covers 06:00-23:59; the 00:00-05:59 gap falls back to the
    previous evening bucket (the traveler's last known location for the night).
    """
    h = now.hour
    if 6 <= h < 12:
        return "06:00-11:59"
    if 12 <= h < 18:
        return "12:00-17:59"
    return "18:00-23:59"


@dataclass
class Data:
    today: date
    week_monday: date
    # Active users in stable shuffled order (already enriched).
    users: list[dict]
    # Filter dropdown options.
    nationalities: list[str]  # ordered by frequency (most common first)
    age_bands: list[int]      # ascending, e.g. [10, 20, 30, ...]
    # traveler_id -> this week's visits (enriched with date), ordered by weekday/span.
    visits_by_user: dict[int, list[dict]]
    coupons: list[dict]       # enriched with dates / active / discount / shop coords
    active_coupons: list[dict]  # subset of coupons active today (has coordinates)

    users_by_id: dict[int, dict]
    shops_by_id: dict[str, dict]


def _read_tsv(path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _load_visits(today: date) -> dict[int, list[dict]]:
    """visit.tsv grouped by traveler_id, each row enriched with its calendar date."""
    by_user: dict[int, list[dict]] = defaultdict(list)
    for row in _read_tsv(config.VISIT_TSV):
        weekday = int(row["weekday"])
        tid = int(row["traveler_id"])
        by_user[tid].append({
            "weekday": weekday,
            "weekday_label": dates.weekday_label_ja(weekday),
            "date": dates.weekday_to_date(weekday, today).isoformat(),
            "timespan": row["timespan"],
            "ward": row["ward"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
        })
    for visits in by_user.values():
        visits.sort(key=lambda v: (v["weekday"], v["timespan"]))
    return by_user


def _load_shops() -> dict[str, dict]:
    """shop.tsv indexed by shop_id, with coordinates and names for the coupon join."""
    shops: dict[str, dict] = {}
    for row in _read_tsv(config.SHOP_TSV):
        shops[row["shop_id"]] = {
            "shop_id": row["shop_id"],
            "shop_name": row["shop_name"],
            "shop_name_en": row["shop_name_en"],
            "category": row["category"],
            "subcategory": row["subcategory"],
            "address": row["address"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
        }
    return shops


def _load_coupons(today: date, shops: dict[str, dict]) -> list[dict]:
    """coupon.tsv, each row enriched with aligned dates, an ``active`` flag, a
    human discount label, and its shop's coordinates (joined by shop_id)."""
    from datetime import timedelta

    out: list[dict] = []
    for row in _read_tsv(config.COUPON_TSV):
        start_wd = int(row["coupon_start_weekday"])
        duration = int(row["coupon_duration_days"])
        start = dates.weekday_to_date(start_wd, today)
        end = start + timedelta(days=duration - 1)
        shop = shops.get(row["shop_id"], {})
        c = dict(row)
        c["price"] = int(row["price"])
        c["coupon_start_weekday"] = start_wd
        c["coupon_duration_days"] = duration
        c["coupon_start_date"] = start.isoformat()
        c["coupon_end_date"] = end.isoformat()
        c["active"] = start <= today <= end
        c["discount_label"] = discount_label(
            row["coupon_discount_display"],
            float(row["coupon_discount_amount"]),
            float(row["coupon_discount_rate"]),
        )
        c["shop_name_en"] = shop.get("shop_name_en", "")
        c["address"] = shop.get("address", "")
        c["latitude"] = shop.get("latitude")
        c["longitude"] = shop.get("longitude")
        c["emoji"] = category_emoji(row["category"])
        c["image"] = f"{row['category']}_{row['subcategory']}.png"
        out.append(c)
    return out


def _load(today: date) -> Data:
    visits_by_user = _load_visits(today)
    shops = _load_shops()
    coupons = _load_coupons(today, shops)
    active_coupons = [c for c in coupons
                      if c["active"] and c["latitude"] is not None]

    # Active users = inbound travelers that actually appear in the visit data.
    travelers = _read_tsv(config.INBOUND_TSV)
    year = today.year
    users: list[dict] = []
    for t in travelers:
        tid = int(t["traveler_id"])
        if tid not in visits_by_user:
            continue
        birthyear = int(t["birthyear"])
        age = year - birthyear
        nat = t["nationality"]
        gender = t.get("gender", "-") or "-"
        users.append({
            "id": tid,
            "nationality": nat,
            "flag": nationality_flag(nat),
            "gender": gender,
            "face": gender_face(gender),
            "gender_label": GENDER_LABEL.get(gender, "不明"),
            "gender_en": GENDER_EN.get(gender, "Unknown"),
            "birthyear": birthyear,
            "age": age,
            "age_band": age_band(age),
            "repeating_times": int(t["repeating_times"]),
            "visit_count": len(visits_by_user[tid]),
        })

    # Stable shuffle: fixed seed so page N is the same set every reload.
    random.Random(config.USER_SHUFFLE_SEED).shuffle(users)

    # Dropdown options.
    nat_counts = Counter(u["nationality"] for u in users)
    nationalities = [n for n, _ in nat_counts.most_common()]
    age_bands = sorted({u["age_band"] for u in users})

    return Data(
        today=today,
        week_monday=dates.week_monday(today),
        users=users,
        nationalities=nationalities,
        age_bands=age_bands,
        visits_by_user=visits_by_user,
        coupons=coupons,
        active_coupons=active_coupons,
        users_by_id={u["id"]: u for u in users},
        shops_by_id=shops,
    )


# --- cache, keyed by the JST day so the date anchor stays current ----------------
_cache: Data | None = None


def get_data() -> Data:
    global _cache
    today = dates.jst_today()
    if _cache is None or _cache.today != today:
        _cache = _load(today)
    return _cache


def filter_users(d: Data, nationality: str | None, age_band_sel: int | None) -> list[dict]:
    """Active users matching the (optional) nationality and age-band filters, in the
    stable shuffled order. ``None``/empty means 'unset' (no constraint)."""
    users = d.users
    if nationality:
        users = [u for u in users if u["nationality"] == nationality]
    if age_band_sel:
        users = [u for u in users if u["age_band"] == age_band_sel]
    return users


def paginate(items: list, page: int, page_size: int) -> tuple[list, int, int]:
    """Return (page_items, page_clamped, total_pages) for a 1-based ``page``."""
    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    return items[start:start + page_size], page, total_pages


def user_by_id(tid: int) -> dict | None:
    return get_data().users_by_id.get(tid)
