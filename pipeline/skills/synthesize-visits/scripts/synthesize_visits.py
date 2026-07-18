#!/usr/bin/env python3
"""Synthesize where each inbound traveler is, in each 6-hour interval of the week.

The demo week (docs/scenarios/travelers.md 「滞在期間」) is split into 7 days x 3
time spans = 21 intervals. For every interval, each of the 2,000 travelers is
given a **central location**: a ward sampled from the 23-ward distribution in
travelers.md, and a uniformly random point inside a 町丁・字 of that ward.

Two modelling notes, both consequences of the spec rather than of the source data:

* travelers.md's 「1日あたり滞在確率」 are **per-day** and non-MECE (they sum to
  94.2%, and a traveller may touch several wards in a day). A single central
  location per interval is MECE by construction, so the 23 values are
  **normalised** to a categorical distribution. Relative ward weights are
  preserved exactly; the absolute daily rate is not (see SKILL.md).
* Intervals are sampled **independently**, so a traveller may jump between
  distant wards between spans. See SKILL.md for why this is less wrong than it
  looks, and how to add persistence.

Inputs
  * ``docs/scenarios/travelers.md``          - 「### 東京都23区別 1日あたり滞在確率」
  * ``DATA/s03_primary/inbound_traveler.tsv`` - traveler_id -> nationality
  * ``pipeline/config/config.yaml``          - ``synthetics/random_seed``,
                                               ``synthetics/visits/*``
  * ``DATA/s01_raw/geoshape_*13.zip``        - read directly from the ZIP

Output (overwritten each run)
  * ``DATA/s03_primary/visit.tsv`` with columns:
    weekday, timespan, traveler_id, nationality, ward, latitude, longitude

Dependencies: pyshp, PyYAML -- see ``requirements.txt``.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _geo import load_areas, random_point  # noqa: E402

WARD_TABLE_HEADING = "### 東京都23区別 1日あたり滞在確率"


def parse_ward_probs(md: str) -> dict[str, float]:
    """Read the 23-ward table -> {ward: daily probability}. The ※ mark on the 11
    interpolated wards is ignored; they are drawn like any other."""
    i = md.find(WARD_TABLE_HEADING)
    if i < 0:
        raise SystemExit(f"Heading not found in travelers.md: {WARD_TABLE_HEADING}")
    start = i + len(WARD_TABLE_HEADING)
    nxt = re.search(r"^#{1,3}\s", md[start:], re.M)
    section = md[start:start + nxt.start()] if nxt else md[start:]
    rows = re.findall(r"^\|\s*(\S+区)\s*(?:※)?\s*\|\s*([\d.]+)%\s*\|", section, re.M)
    if len(rows) != 23:
        raise SystemExit(f"Expected 23 wards in travelers.md, parsed {len(rows)}")
    return {w: float(p) for w, p in rows}


def load_travelers(path: Path) -> list[tuple[int, str]]:
    with path.open(encoding="utf-8") as fh:
        return [(int(r["traveler_id"]), r["nationality"])
                for r in csv.DictReader(fh, delimiter="\t")]


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "docs" / "scenarios").is_dir() and (p / "pipeline").is_dir():
            return p
    raise SystemExit("Could not locate repo root (docs/scenarios + pipeline not found).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args()

    root = args.repo_root or find_repo_root(Path(__file__).resolve())
    cfg = yaml.safe_load((args.config or root / "pipeline" / "config" / "config.yaml")
                         .read_text(encoding="utf-8"))
    syn = cfg["synthetics"]
    opts = syn["visits"]
    import random
    rng = random.Random(syn["random_seed"])

    probs = parse_ward_probs((root / "docs" / "scenarios" / "travelers.md")
                            .read_text(encoding="utf-8"))
    wards = list(probs)
    weights = [probs[w] for w in wards]        # rng.choices normalises internally

    travelers = load_travelers(root / "DATA" / "s03_primary" / "inbound_traveler.tsv")
    if not travelers:
        raise SystemExit("inbound_traveler.tsv is empty — run "
                         "synthesize-inbound-travelers first.")

    zips = sorted((root / "DATA" / "s01_raw").glob("geoshape_*13.zip"))
    if not zips:
        raise SystemExit("No Tokyo geoshape ZIP in DATA/s01_raw — run "
                         "retrieve-tokyo-geoshapes first.")
    areas = load_areas(zips[0], set(wards))
    for w in wards:
        if not areas.get(w):
            raise SystemExit(f"No 町丁・字 polygons found for {w}")

    spans = list(opts["timespans"])
    days = int(opts["days"])

    out = root / "DATA" / "s03_primary" / "visit.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t", lineterminator="\n")
        wr.writerow(["weekday", "timespan", "traveler_id", "nationality",
                     "ward", "latitude", "longitude"])
        for weekday in range(1, days + 1):
            for span in spans:
                # One ward draw per traveller per interval, then a point inside it.
                picks = rng.choices(wards, weights=weights, k=len(travelers))
                for (tid, nat), ward in zip(travelers, picks):
                    _s_name, bbox, rings = rng.choice(areas[ward])
                    lon, lat = random_point(rng, bbox, rings)
                    wr.writerow([weekday, span, tid, nat, ward, lat, lon])
                    n += 1

    total = sum(weights)
    print(f"  [OK]   {n:,} visits ({len(travelers):,} travelers x {days} days "
          f"x {len(spans)} spans) -> {out.relative_to(root)}")
    print(f"         seed={syn['random_seed']}  wards={len(wards)}  "
          f"daily probs summed to {total:.1f}% before normalisation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
