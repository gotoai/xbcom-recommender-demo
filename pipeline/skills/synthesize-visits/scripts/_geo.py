"""Polygon helpers for placing points inside 町丁・字 boundaries.

Reads the e-stat 小地域 shapefile straight out of the geoshape ZIP in
DATA/s01_raw, so no extract step is needed.

Kept local to this skill: the pipeline's skills are self-contained and
individually runnable, matching the reference project's layout. `synthesize-shops`
carries an equivalent copy.
"""
from __future__ import annotations

import io
import random
import zipfile
from pathlib import Path

import shapefile  # pyshp

NORMAL_HCODE = 8101      # 通常の町丁・字。8154 は水面調査区 (Tokyo Bay, rivers) -> excluded
MAX_POINT_TRIES = 400    # rejection-sampling attempts before falling back
COORD_DIGITS = 6         # output precision; ~0.11 m at Tokyo latitudes


def load_areas(zip_path: Path, wards: set[str]) -> dict[str, list]:
    """{ward: [(S_NAME, bbox, rings), ...]} for the normal 町丁・字 of each ward.

    A 町丁・字 may appear as several polygons (新宿区四谷, 港区台場一丁目 and others
    are discontiguous), so this returns a list per ward and never keys on S_NAME.
    """
    with zipfile.ZipFile(zip_path) as z:
        base = next(n[:-4] for n in z.namelist() if n.endswith(".shp"))
        r = shapefile.Reader(
            shp=io.BytesIO(z.read(base + ".shp")), dbf=io.BytesIO(z.read(base + ".dbf")),
            shx=io.BytesIO(z.read(base + ".shx")), encoding="cp932")
        fi = {f[0]: i for i, f in enumerate(r.fields[1:])}
        out: dict[str, list] = {w: [] for w in wards}
        for sr in r.iterShapeRecords():
            rec, shp = sr.record, sr.shape
            if rec[fi["CITY_NAME"]] not in wards or rec[fi["HCODE"]] != NORMAL_HCODE:
                continue
            pts = shp.points
            bounds = list(shp.parts) + [len(pts)]
            rings = [pts[bounds[i]:bounds[i + 1]] for i in range(len(shp.parts))]
            out[rec[fi["CITY_NAME"]]].append((rec[fi["S_NAME"]], shp.bbox, rings))
    return out


def in_polygon(x: float, y: float, rings: list[list[tuple[float, float]]]) -> bool:
    """Even-odd ray casting across every ring, so holes and multi-part shapes work."""
    inside = False
    for ring in rings:
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                if x < x1 + (y - y1) / (y2 - y1) * (x2 - x1):
                    inside = not inside
    return inside


def random_point(rng: random.Random, bbox, rings, ndigits: int = COORD_DIGITS):
    """Uniform random point inside the polygon (rejection sampling within bbox).

    The candidate is rounded to `ndigits` *before* the inside test, so the value
    returned — and therefore the value written out — is itself guaranteed inside.
    Rounding after the test can nudge a point across a nearby edge: 6 dp is ~0.11 m,
    so a draw landing within ~5 cm of a boundary would otherwise round outside it.
    """
    x0, y0, x1, y1 = bbox
    for _ in range(MAX_POINT_TRIES):
        x = round(rng.uniform(x0, x1), ndigits)
        y = round(rng.uniform(y0, y1), ndigits)
        if in_polygon(x, y, rings):
            return x, y
    # Degenerate sliver. Prefer the centre if it is inside; otherwise fall back to
    # a vertex, which is at least on the polygon rather than possibly far outside.
    cx, cy = round((x0 + x1) / 2, ndigits), round((y0 + y1) / 2, ndigits)
    if in_polygon(cx, cy, rings):
        return cx, cy
    vx, vy = rings[0][0]
    return round(vx, ndigits), round(vy, ndigits)
