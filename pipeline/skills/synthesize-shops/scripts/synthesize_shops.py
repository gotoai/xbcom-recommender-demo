#!/usr/bin/env python3
"""Synthesize the demo's coupon-providing shops.

For each of the 6 PoC wards in ``docs/profiles/shops.md`` this script samples
``per_ward`` shops: it draws a category / sub-category from the configured mix,
picks a 町丁・字 in that ward, places the shop at a uniformly random point inside
that 町丁・字's polygon, builds a Japanese address from the polygon's own
``S_NAME`` plus a synthetic 番地, and generates paired JA/EN names.

Because the coordinate is drawn *inside* the polygon whose ``S_NAME`` supplies the
address, address and coordinates always agree.

Inputs
  * ``docs/profiles/shops.md``      - the 6 対象地域 wards and the category tree
  * ``pipeline/config/config.yaml`` - ``synthetics/random_seed`` and
                                      ``synthetics/shops/*``
  * ``DATA/s01_raw/geoshape_*13.zip`` - read directly from the ZIP; no extract step

Output (overwritten each run)
  * ``DATA/s03_primary/shop.tsv`` with columns:
    shop_id, shop_name, shop_name_en, category, category_en, subcategory,
    subcategory_en, description_en, address, address_en, latitude, longitude

Dependencies: pyshp, PyYAML -- see ``requirements.txt``.
"""
from __future__ import annotations

import argparse
import csv
import io
import random
import re
import sys
import zipfile
from pathlib import Path

import shapefile  # pyshp
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shop_names import SHOP_WORD, make_name  # noqa: E402
from shop_i18n import (  # noqa: E402
    CATEGORY_EN, CHO_EN, SUBCATEGORY_EN, make_description, romanise_address,
    split_chome,
)

NORMAL_HCODE = 8101      # 通常の町丁・字。8154 は水面調査区 (Tokyo Bay etc.) -> excluded
MAX_POINT_TRIES = 400    # rejection-sampling attempts before falling back
COORD_DIGITS = 6         # output precision; ~0.11 m at Tokyo latitudes


def parse_shops_md(md: str) -> tuple[list[str], dict[str, list[str]]]:
    """Return (wards, {category: [subcategory, ...]}) from docs/profiles/shops.md."""
    wards = re.findall(r"^-\s*(\S+区)\s*$", _section(md, "## 対象地域"), re.M)
    cats: dict[str, list[str]] = {}
    cur = None
    for line in _section(md, "## 対象店舗カテゴリ").splitlines():
        if m := re.match(r"^-\s+(\S.*?)\s*$", line):
            cur = m.group(1)
            cats[cur] = []
        elif (m := re.match(r"^\s{2,}-\s+(\S.*?)\s*$", line)) and cur:
            cats[cur].append(m.group(1))
    cats = {k: v for k, v in cats.items() if v}
    if not wards or not cats:
        raise SystemExit("Failed to parse wards/categories from shops.md")
    return wards, cats


def _section(md: str, heading: str) -> str:
    i = md.find(heading)
    if i < 0:
        raise SystemExit(f"Heading not found in shops.md: {heading}")
    start = i + len(heading)
    depth = len(heading) - len(heading.lstrip("#"))
    nxt = re.search(rf"^#{{1,{depth}}}\s", md[start:], re.M)
    return md[start:start + nxt.start()] if nxt else md[start:]


def load_areas(zip_path: Path, wards: set[str]) -> dict[str, list]:
    """{ward: [(S_NAME, bbox, rings), ...]} for the normal 町丁・字 of each ward."""
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
    """Even-odd ray casting across every ring, so holes are handled correctly."""
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


def weighted(rng: random.Random, items: list[str], weights: dict[str, float]) -> str:
    return rng.choices(items, weights=[weights.get(i, 1.0) for i in items], k=1)[0]


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "docs" / "profiles").is_dir() and (p / "pipeline").is_dir():
            return p
    raise SystemExit("Could not locate repo root (docs/profiles + pipeline not found).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args()

    root = args.repo_root or find_repo_root(Path(__file__).resolve())
    cfg = yaml.safe_load((args.config or root / "pipeline" / "config" / "config.yaml")
                         .read_text(encoding="utf-8"))
    syn = cfg["synthetics"]
    opts = syn["shops"]
    rng = random.Random(syn["random_seed"])

    wards, cats = parse_shops_md((root / "docs" / "profiles" / "shops.md")
                                 .read_text(encoding="utf-8"))
    # Every (category, subcategory) must have a name vocabulary entry and an
    # English label; every category must have an English label.
    pairs = [(c, s) for c, subs in cats.items() for s in subs]
    for label, table in (("shop_names.SHOP_WORD", SHOP_WORD),
                         ("shop_i18n.SUBCATEGORY_EN", SUBCATEGORY_EN)):
        missing = [p for p in pairs if p not in table]
        if missing:
            raise SystemExit(f"{label} is missing {len(missing)} entries: "
                             f"{missing[:5]}")
    if missing_cat := [c for c in cats if c not in CATEGORY_EN]:
        raise SystemExit(f"shop_i18n.CATEGORY_EN is missing: {missing_cat}")

    zips = sorted((root / "DATA" / "s01_raw").glob("geoshape_*13.zip"))
    if not zips:
        raise SystemExit("No Tokyo geoshape ZIP in DATA/s01_raw — run "
                         "retrieve-tokyo-geoshapes first.")
    areas = load_areas(zips[0], set(wards))

    # Every 町丁 (chome stripped) must have a romaji entry for address_en.
    missing_cho = sorted({split_chome(s)[0] for polys in areas.values()
                          for s, _, _ in polys} - set(CHO_EN))
    if missing_cho:
        raise SystemExit(f"shop_i18n.CHO_EN is missing {len(missing_cho)} 町丁: "
                         f"{missing_cho[:5]}")

    # A separate stream for descriptions, so name/geo columns are unaffected.
    desc_rng = random.Random(syn["random_seed"] ^ 0x5CE5D)

    cat_w = opts["category_weights"]
    ward_mult = opts.get("ward_category_multipliers") or {}
    sub_w = opts.get("subcategory_weights") or {}
    cat_names = list(cats)

    rows = []
    for ward in wards:
        if not areas.get(ward):
            raise SystemExit(f"No 町丁・字 polygons found for {ward}")
        mult = ward_mult.get(ward) or {}
        w = {c: cat_w[c] * mult.get(c, 1.0) for c in cat_names}
        for _ in range(int(opts["per_ward"])):
            cat = weighted(rng, cat_names, w)
            sub = weighted(rng, cats[cat], sub_w.get(cat) or {})
            s_name, bbox, rings = rng.choice(areas[ward])
            lon, lat = random_point(rng, bbox, rings)
            ja, en = make_name(rng, cat, sub, ward)
            banchi = rng.randint(1, int(opts["banchi_max"]))
            go = rng.randint(1, int(opts["go_max"]))
            addr = f"東京都{ward}{s_name}{banchi}番{go}号"
            addr_en = romanise_address(ward, s_name, banchi, go)
            desc = make_description(desc_rng, cat, sub)
            rows.append([ja, en, cat, CATEGORY_EN[cat], sub, SUBCATEGORY_EN[(cat, sub)],
                         desc, addr, addr_en, lat, lon])

    rng.shuffle(rows)
    out = root / "DATA" / "s03_primary" / "shop.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t", lineterminator="\n")
        wr.writerow(["shop_id", "shop_name", "shop_name_en",
                     "category", "category_en", "subcategory", "subcategory_en",
                     "description_en", "address", "address_en",
                     "latitude", "longitude"])
        for i, r in enumerate(rows, 1):
            wr.writerow([i, *r])

    print(f"  [OK]   {len(rows):,} shops across {len(wards)} wards "
          f"-> {out.relative_to(root)}")
    print(f"         seed={syn['random_seed']}  per_ward={opts['per_ward']}  "
          f"categories={len(cat_names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
