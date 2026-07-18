#!/usr/bin/env python3
"""Synthesize one coupon per product.

Reads ``DATA/s03_primary/product.tsv`` and gives every product exactly one coupon:
a usage period (start weekday + duration), one of five fixed discount options
chosen to suit that product's price, and a unique alphanumeric code.

The discount options are fixed by the spec:

    rate   :  5%  |  8%
    amount : ¥30  | ¥50  | ¥80

Picking one "appropriately" is the whole problem, because prices span ¥100 to
¥320,000. A flat draw would put ¥80 off a ¥100 shop item (80% off) and 5% off a
¥150 ice cream (worth ¥7). So an option is **eligible** only if its effective rate
lands inside [min_effective_rate, max_effective_rate] *and* the yen it removes is
at least min_discount_amount. One eligible option is then drawn uniformly.

That single rule sorts itself out by price band without any hand-written mapping:

    ¥100    -> only ¥30 (30%); rates would be worth ¥5-8, the other amounts 50-80%
    ¥2,350  -> 5%, 8%, ¥50, ¥80; ¥30 is only 1.3%, below the floor
    ¥320,000-> only 5% / 8%; every amount option is under 0.03%

Inputs
  * ``DATA/s03_primary/product.tsv`` - produced by `synthesize-products`
  * ``pipeline/config/config.yaml``  - ``synthetics/random_seed``,
                                       ``synthetics/coupons/*``

Output (overwritten each run)
  * ``DATA/s03_primary/coupon.tsv`` with columns:
    coupon_id, shop_id, shop_name, shop_name_en, category, category_en,
    subcategory, subcategory_en, product_id, product_name, product_name_en,
    price, coupon_start_weekday, coupon_duration_days, coupon_discount_display,
    coupon_discount_amount, coupon_discount_rate, coupon_code

The ``*_en`` columns are denormalised straight from product.tsv.

All prices and discount amounts are tax-exclusive (税抜) JPY, inherited from
product.tsv.

Dependencies: PyYAML -- see ``requirements.txt``.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import string
import sys
from pathlib import Path

import yaml

# (display, kind, value) -- the five options the spec allows.
DISCOUNT_OPTIONS = [
    ("rate", "rate", 0.05),
    ("rate", "rate", 0.08),
    ("amount", "amount", 30),
    ("amount", "amount", 50),
    ("amount", "amount", 80),
]
CODE_ALPHABET = string.ascii_uppercase + string.digits

# English columns carried over verbatim from product.tsv.
PRODUCT_EN_COLS = ("shop_name_en", "category_en", "subcategory_en", "product_name_en")


def effective(kind: str, value: float, price: int) -> tuple[float, float]:
    """(amount_off_yen, effective_rate) for one option against one price.

    Rate discounts floor to whole yen — a discount is money off a till, and 切り捨て
    is the merchant-conservative convention. The stored rate stays the exact 0.05 /
    0.08 the coupon advertises; the yen figure is what it actually removes.
    """
    if kind == "rate":
        return float(math.floor(price * value)), float(value)
    return float(value), value / price


def choose_discount(rng: random.Random, price: int, min_rate: float,
                    max_rate: float, min_amount: float):
    """Pick one option suited to `price`. Returns (display, amount, rate)."""
    eligible = []
    for display, kind, value in DISCOUNT_OPTIONS:
        amount, rate = effective(kind, value, price)
        if min_rate <= rate <= max_rate and amount >= min_amount:
            eligible.append((display, amount, rate))
    if eligible:
        return rng.choice(eligible)
    # No option fits the bands (only reachable for prices outside the generated
    # range). Fall back to whichever sits closest to the middle of the rate band.
    target = (min_rate + max_rate) / 2
    scored = [(abs(effective(k, v, price)[1] - target), d, *effective(k, v, price))
              for d, k, v in DISCOUNT_OPTIONS]
    _, display, amount, rate = min(scored, key=lambda t: t[0])
    return display, amount, rate


def make_code(rng: random.Random, used: set[str], lo: int, hi: int) -> str:
    while True:
        code = "".join(rng.choices(CODE_ALPHABET, k=rng.randint(lo, hi)))
        if code not in used:
            used.add(code)
            return code


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
    opts = syn["coupons"]
    rng = random.Random(syn["random_seed"])

    min_rate = float(opts["min_effective_rate"])
    max_rate = float(opts["max_effective_rate"])
    min_amount = float(opts["min_discount_amount"])
    max_dur = int(opts["max_duration_days"])
    clo, chi = int(opts["code_length_min"]), int(opts["code_length_max"])

    product_tsv = root / "DATA" / "s03_primary" / "product.tsv"
    if not product_tsv.exists():
        raise SystemExit("No product.tsv — run synthesize-products first.")
    with product_tsv.open(encoding="utf-8") as fh:
        products = list(csv.DictReader(fh, delimiter="\t"))
    if not products:
        raise SystemExit("product.tsv is empty.")
    if absent := [c for c in PRODUCT_EN_COLS if c not in products[0]]:
        raise SystemExit(f"product.tsv lacks columns {absent} — re-run synthesize-products.")

    used_codes: set[str] = set()
    out = root / "DATA" / "s03_primary" / "coupon.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fallbacks = 0
    with out.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t", lineterminator="\n")
        wr.writerow(["coupon_id", "shop_id", "shop_name", "shop_name_en",
                     "category", "category_en", "subcategory", "subcategory_en",
                     "product_id", "product_name", "product_name_en", "price",
                     "coupon_start_weekday", "coupon_duration_days",
                     "coupon_discount_display", "coupon_discount_amount",
                     "coupon_discount_rate", "coupon_code"])
        for cid, p in enumerate(products, 1):
            price = int(p["price"])
            display, amount, rate = choose_discount(rng, price, min_rate, max_rate,
                                                    min_amount)
            if not (min_rate <= rate <= max_rate and amount >= min_amount):
                fallbacks += 1
            wr.writerow([
                cid, p["shop_id"], p["shop_name"], p["shop_name_en"],
                p["category"], p["category_en"], p["subcategory"], p["subcategory_en"],
                p["product_id"], p["product_name"], p["product_name_en"], price,
                rng.randint(1, 7),                 # coupon_start_weekday (Mon-Sun)
                rng.randint(1, max_dur),           # coupon_duration_days
                display, round(amount, 1), round(rate, 4),
                make_code(rng, used_codes, clo, chi),
            ])

    print(f"  [OK]   {len(products):,} coupons (1 per product) -> {out.relative_to(root)}")
    print(f"         seed={syn['random_seed']}  eligible band "
          f"{min_rate:.0%}-{max_rate:.0%} & >=¥{min_amount:.0f}  "
          f"fallbacks={fallbacks}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
