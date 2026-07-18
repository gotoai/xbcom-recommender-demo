"""JST 'today' and the weekday -> calendar-date alignment.

The visit/coupon data is authored against an abstract Mon-Sun week: weekday is an
integer 1-7 (1 = Monday .. 7 = Sunday) with no calendar dates. To give those rows
real dates we anchor that abstract week to the actual calendar week (Japan time)
that contains today:

    week_monday = today - (isoweekday - 1) days     # Monday of the current week
    weekday n   -> week_monday + (n - 1) days

So for a Saturday today, weekday 6 maps to today, weekday 1 to the preceding
Monday, weekday 7 to the following Sunday. Everything here is pure and date-only.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

# Japan Standard Time is a fixed UTC+9 offset (no DST), so a fixed-offset tz is
# exact and avoids a zoneinfo/tzdata dependency.
JST = timezone(timedelta(hours=9))

# Weekday 1-7 -> Japanese single-character label (月..日).
_WEEKDAY_JA = {1: "月", 2: "火", 3: "水", 4: "木", 5: "金", 6: "土", 7: "日"}


def jst_today() -> date:
    """The current calendar date in Japan Standard Time."""
    return datetime.now(JST).date()


def week_monday(today: date) -> date:
    """Monday of the calendar week containing ``today`` (ISO: Monday = weekday 1)."""
    return today - timedelta(days=today.isoweekday() - 1)


def weekday_to_date(weekday: int, today: date) -> date:
    """Calendar date of abstract ``weekday`` (1-7) in the week containing ``today``.

    Raises ValueError for a weekday outside 1-7.
    """
    if not 1 <= weekday <= 7:
        raise ValueError(f"weekday must be 1-7, got {weekday!r}")
    return week_monday(today) + timedelta(days=weekday - 1)


def weekday_label_ja(weekday: int) -> str:
    """Japanese single-character weekday label, e.g. 1 -> '月'. '' if out of range."""
    return _WEEKDAY_JA.get(weekday, "")
