#!/usr/bin/env python3
"""Synthesize one product per shop, aligned to the shop's category.

Reads ``DATA/s03_primary/shop.tsv`` and gives every shop exactly one product:
a compositional Japanese/English name drawn from the vocabulary for that shop's
(category, subcategory), and a non-discounted, **tax-exclusive (税抜)** JPY price
drawn from that sub-category's band.

Names are `{modifier}{item}` (野菜たっぷり + 醤油ラーメン), and the modifier also
carries a price multiplier, so the name and the price stay consistent with each
other — a 特上 item costs more than an あっさり one.

Inputs
  * ``DATA/s03_primary/shop.tsv``   - produced by `synthesize-shops`
  * ``pipeline/config/config.yaml`` - ``synthetics/random_seed``,
                                      ``synthetics/products/*``

Output (overwritten each run)
  * ``DATA/s03_primary/product.tsv`` with columns:
    shop_id, shop_name, shop_name_en, category, category_en, subcategory,
    subcategory_en, product_id, product_name, product_name_en, description_en,
    price

``shop_name_en`` / ``category_en`` / ``subcategory_en`` are copied straight from
shop.tsv; ``description_en`` is a short traveler-facing product blurb.

Dependencies: PyYAML -- see ``requirements.txt``.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from product_names import PRODUCTS, make_product, price_band, price_cap  # noqa: E402
from product_i18n import DESC_TEMPLATE, make_description  # noqa: E402

# Columns copied verbatim from shop.tsv onto every product of that shop.
SHOP_EN_COLS = ("shop_name_en", "category_en", "subcategory_en")


def round_price(p: float) -> int:
    """Round to a step that suits the magnitude, the way real menu prices do."""
    if p < 2000:
        step = 10
    elif p < 10000:
        step = 50
    elif p < 100000:
        step = 100
    else:
        step = 1000
    return max(step, int(round(p / step) * step))


def sample_price(rng: random.Random, lo: int, hi: int, mult: float,
                 cap: int | None = None) -> int:
    """Log-uniform within the band, scaled by the modifier's multiplier.

    Log-uniform (not uniform) because the bands span wide ranges — カメラ is
    30,000-250,000 — and cheap items genuinely outnumber expensive ones. Uniform
    would make the median camera 140,000 yen; log-uniform puts it near 86,000.

    A multiplier may normally carry the result past `hi` (a 全部のせ ramen costs
    more than the ordinary range). `cap`, where set, is a hard ceiling applied
    after the multiplier — see product_names.PRICE_CAP.

    All prices are tax-exclusive (税抜) JPY.
    """
    p = math.exp(rng.uniform(math.log(lo), math.log(hi))) * mult
    price = round_price(p)
    return min(price, cap) if cap else price


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
    opts = syn.get("products") or {}
    rng = random.Random(syn["random_seed"])
    mod_p = float(opts.get("modifier_probability", 0.75))

    shop_tsv = root / "DATA" / "s03_primary" / "shop.tsv"
    if not shop_tsv.exists():
        raise SystemExit("No shop.tsv — run synthesize-shops first.")
    with shop_tsv.open(encoding="utf-8") as fh:
        shops = list(csv.DictReader(fh, delimiter="\t"))
    if not shops:
        raise SystemExit("shop.tsv is empty.")
    if absent := [c for c in SHOP_EN_COLS if c not in shops[0]]:
        raise SystemExit(f"shop.tsv lacks columns {absent} — re-run synthesize-shops.")

    # Every (category, subcategory) in shop.tsv must have a product vocabulary
    # and a description template.
    for label, table in (("product_names.PRODUCTS", PRODUCTS),
                         ("product_i18n.DESC_TEMPLATE", DESC_TEMPLATE)):
        missing = sorted({(s["category"], s["subcategory"]) for s in shops
                          if (s["category"], s["subcategory"]) not in table})
        if missing:
            raise SystemExit(f"{label} is missing {len(missing)} entries: "
                             f"{missing[:5]}")

    # A separate stream for descriptions, so name/price columns are unaffected.
    desc_rng = random.Random(syn["random_seed"] ^ 0x5CE5D)

    out = root / "DATA" / "s03_primary" / "product.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t", lineterminator="\n")
        wr.writerow(["shop_id", "shop_name", "shop_name_en",
                     "category", "category_en", "subcategory", "subcategory_en",
                     "product_id", "product_name", "product_name_en",
                     "description_en", "price"])
        for pid, s in enumerate(shops, 1):
            cat, sub = s["category"], s["subcategory"]
            ja, en, mult = make_product(rng, cat, sub, mod_p)
            lo, hi = price_band(cat, sub)
            price = sample_price(rng, lo, hi, mult, price_cap(cat, sub))
            desc = make_description(desc_rng, cat, sub, en)
            wr.writerow([s["shop_id"], s["shop_name"], s["shop_name_en"],
                         cat, s["category_en"], sub, s["subcategory_en"],
                         pid, ja, en, desc, price])

    print(f"  [OK]   {len(shops):,} products (1 per shop) -> {out.relative_to(root)}")
    print(f"         seed={syn['random_seed']}  modifier_probability={mod_p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
