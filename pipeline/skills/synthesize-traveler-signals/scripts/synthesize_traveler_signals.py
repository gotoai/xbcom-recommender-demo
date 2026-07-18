#!/usr/bin/env python3
"""Synthesize per-traveler feature signals in a long (tidy) table.

For every inbound traveler in ``DATA/s03_primary/inbound_traveler.tsv`` this
script emits several **signal rows**:

  * ``nationality``      - the traveler's nationality in English
  * ``gender``           - F / M / - (as stored)
  * ``age``              - computed from birthyear and the **system current date**
  * ``repeating_times``  - prior visits to Japan (as stored)
  * ``propensity`` x N   - 5-10 distinct (category, subcategory) interests, each
                           with a taste score in [-1, 0.99]

Propensity scores are drawn from Beta distributions (not uniform): a selected
item is a *dislike* (negative score in [-1, 0)) with probability
``negative_fraction``, otherwise a *like* (0.99 * Beta), where the Beta shape is
tuned so the mean of the non-negative scores is ~0.3. A score < 0 is a rejection,
0 is neutral, > 0 is preference.

Every propensity row also carries a ``score_type``: 1 = derived from historical
behaviour, 2 = inferred. It is assigned per row (``historical_fraction``); in this
synthetic demo it is a label only, not a different computation.

Long format — one row per (traveler, signal), columns:
    traveler_id, signal_name, signal_value1, signal_value2, signal_value3,
    signal_value4

Only ``propensity`` uses value2-4 (category_en, subcategory_en, score_type,
score); the scalar signals put their value in ``signal_value1`` and leave the rest
empty.

Inputs
  * ``DATA/s03_primary/inbound_traveler.tsv`` - produced by
                                                `synthesize-inbound-travelers`
  * ``DATA/s03_primary/product.tsv``          - source of the (category_en,
                                                subcategory_en) interest space
  * ``pipeline/config/config.yaml``           - ``synthetics/random_seed`` and
                                                ``synthetics/traveler_signals/*``

Output (overwritten each run)
  * ``DATA/s04_feature/traveler_signal.tsv``

Note: ``age`` depends on today's date, so it is the one column that is not
reproducible from the seed alone across calendar time.

Dependencies: PyYAML -- see ``requirements.txt``.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from datetime import date
from pathlib import Path

import yaml

# Scalar signals whose single value goes in signal_value1 (value2-4 empty).
SCALAR_SIGNALS = ("nationality", "gender", "age", "repeating_times")


def load_interest_space(product_tsv: Path) -> list[tuple[str, str]]:
    """Sorted unique (category_en, subcategory_en) pairs from product.tsv."""
    with product_tsv.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows:
        raise SystemExit("product.tsv is empty — run synthesize-products first.")
    for col in ("category_en", "subcategory_en"):
        if col not in rows[0]:
            raise SystemExit(f"product.tsv lacks column {col} — re-run synthesize-products.")
    pairs = {(r["category_en"], r["subcategory_en"]) for r in rows}
    return sorted(pairs)


def draw_propensity(rng: random.Random, o: dict) -> float:
    """One taste score in [-1, 0.99], rounded to 2 dp.

    Dislike with probability ``negative_fraction`` (negative, from -Beta), else a
    like (0.99 * Beta). Beta rather than uniform so the shape is realistic and the
    like-mean can be pinned near 0.3.
    """
    if rng.random() < float(o["negative_fraction"]):
        mag = rng.betavariate(float(o["neg_beta_a"]), float(o["neg_beta_b"]))
        return min(-0.01, round(-mag, 2))          # keep it strictly negative
    like = 0.99 * rng.betavariate(float(o["pos_beta_a"]), float(o["pos_beta_b"]))
    return round(like, 2)                          # in [0.00, 0.99]


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "DATA").is_dir() and (p / "pipeline").is_dir():
            return p
    raise SystemExit("Could not locate repo root (DATA + pipeline not found).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args()

    root = args.repo_root or find_repo_root(Path(__file__).resolve())
    cfg = yaml.safe_load((args.config or root / "pipeline" / "config" / "config.yaml")
                         .read_text(encoding="utf-8"))
    syn = cfg["synthetics"]
    o = syn["traveler_signals"]
    rng = random.Random(syn["random_seed"])

    imin, imax = int(o["items_min"]), int(o["items_max"])
    hist_frac = float(o["historical_fraction"])
    this_year = date.today().year

    primary = root / "DATA" / "s03_primary"
    interests = load_interest_space(primary / "product.tsv")
    if imax > len(interests):
        raise SystemExit(f"items_max={imax} exceeds {len(interests)} available interests")

    traveler_tsv = primary / "inbound_traveler.tsv"
    if not traveler_tsv.exists():
        raise SystemExit("No inbound_traveler.tsv — run synthesize-inbound-travelers first.")
    with traveler_tsv.open(encoding="utf-8") as fh:
        travelers = list(csv.DictReader(fh, delimiter="\t"))
    if not travelers:
        raise SystemExit("inbound_traveler.tsv is empty.")
    if "nationality_en" not in travelers[0]:
        raise SystemExit("inbound_traveler.tsv lacks nationality_en — "
                         "re-run synthesize-inbound-travelers.")

    out = root / "DATA" / "s04_feature" / "traveler_signal.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)

    n_signals = n_prop = 0
    pos_sum = pos_n = neg_n = 0.0
    with out.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t", lineterminator="\n")
        wr.writerow(["traveler_id", "signal_name", "signal_value1",
                     "signal_value2", "signal_value3", "signal_value4"])
        for t in travelers:
            tid = t["traveler_id"]
            age = this_year - int(t["birthyear"])
            scalars = {
                "nationality": t["nationality_en"],
                "gender": t["gender"],
                "age": str(age),
                "repeating_times": t["repeating_times"],
            }
            for name in SCALAR_SIGNALS:
                wr.writerow([tid, name, scalars[name], "", "", ""])
                n_signals += 1

            k = rng.randint(imin, imax)
            for cat_en, sub_en in rng.sample(interests, k):
                score = draw_propensity(rng, o)
                score_type = "1" if rng.random() < hist_frac else "2"
                wr.writerow([tid, "propensity", cat_en, sub_en, score_type,
                             f"{score:.2f}"])
                n_signals += 1
                n_prop += 1
                if score >= 0:
                    pos_sum += score
                    pos_n += 1
                else:
                    neg_n += 1

    pos_mean = pos_sum / pos_n if pos_n else 0.0
    print(f"  [OK]   {n_signals:,} signal rows for {len(travelers):,} travelers "
          f"-> {out.relative_to(root)}")
    print(f"         seed={syn['random_seed']}  propensity rows={n_prop:,} "
          f"({neg_n / n_prop * 100:.1f}% negative)  "
          f"non-negative mean={pos_mean:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
