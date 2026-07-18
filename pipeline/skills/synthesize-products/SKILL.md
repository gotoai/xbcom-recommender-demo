---
name: synthesize-products
description: >-
  Synthesize one product per shop, aligned to that shop's category. Reads
  DATA/s03_primary/shop.tsv and gives every shop a compositional Japanese/English
  product name ({modifier}{item}, e.g. 野菜たっぷり醤油ラーメン) plus a non-discounted,
  tax-exclusive JPY price drawn from that sub-category's band, where the modifier
  also scales the price. Writes DATA/s03_primary/product.tsv. Reproducible via
  synthetics/random_seed in pipeline/config/config.yaml. Use when asked to
  synthesize, generate, sample, refresh, or bootstrap the demo's products /
  menu items / shop offerings.
---

# Synthesize products

Gives every shop something to actually sell. This is the table a coupon's
discount will apply to.

> **All prices in `product.tsv` are tax-exclusive (税抜) JPY.** Consumption tax is
> not included and is not modelled. Any display price, discount, or settlement
> figure downstream must add 消費税 itself (10% standard; 8% 軽減税率 applies to
> takeaway food and non-alcoholic drinks — the reduced rate is **not** flagged in
> this table).

## What it produces

`DATA/s03_primary/product.tsv` — a UTF-8, tab-separated table (header + **6,000**
rows, one per shop), **overwritten** on each run:

| column | meaning |
| --- | --- |
| `shop_id` | joins to `shop.tsv` |
| `shop_name` | denormalised from `shop.tsv` (Japanese) |
| `category` | denormalised from `shop.tsv` |
| `subcategory` | denormalised from `shop.tsv` |
| `product_id` | 1-based unique integer |
| `product_name` | Japanese, e.g. `野菜たっぷり豚骨ラーメン` |
| `product_name_en` | English, e.g. `Veggie-Loaded Tonkotsu Ramen` |
| `price` | non-discounted, **tax-exclusive (税抜)** price in JPY (int) |

Row order follows `shop.tsv`, which is itself shuffled.

## How to run it

Requires `synthesize-shops` to have run.

```bash
.venv/bin/pip install -r pipeline/requirements.txt   # first time only (PyYAML)
.venv/bin/python pipeline/skills/synthesize-products/scripts/synthesize_products.py
```

Reproducible via `synthetics/random_seed` in `pipeline/config/config.yaml`.

Options: `--repo-root <path>` and `--config <path>` (both auto-detected).

## Compositional names

[scripts/product_names.py](scripts/product_names.py) holds a **paired** JA/EN
vocabulary — same design as `synthesize-shops/scripts/shop_names.py`, so the
English name is a parallel name rather than a transliteration.

Names are built as `{modifier}{item}`, which is what makes 6,000 shops
distinguishable from only 117 sub-categories:

```
醤油ラーメン + 野菜たっぷり -> 野菜たっぷり醤油ラーメン / Veggie-Loaded Shoyu Ramen
             + 魚介         -> 魚介醤油ラーメン         / Seafood Shoyu Ramen
             + 煮干し       -> 煮干し醤油ラーメン       / Niboshi Shoyu Ramen
```

- `PRODUCTS[(category, subcategory)]` = (items, modifier-pool key, price band).
  Keyed by the **pair**, because 「日用品・雑貨」 appears under both ドラッグストア and
  コンビニエンスストア.
- `MOD_POOLS` — 19 pools (`ramen`, `sushi`, `yakiniku`, `retail`, `beauty`,
  `ticket`, `spa`, …) so modifiers stay category-appropriate: 特上 belongs on
  sushi, not on a coin locker.
- Modifiers are chosen to work as an adjectival **prefix in both languages**, so
  the two names stay structurally parallel. This rules out 「味玉入り」-style
  modifiers that would need to become a postfix in English ("Shoyu Ramen with
  Ajitama").
- `modifier_probability` (config, default 0.75) — the rest stay plain, so both
  `醤油ラーメン` and `野菜たっぷり醤油ラーメン` occur.

Yield: **2,287 distinct Japanese names** and 2,277 English across 6,000 products,
from a theoretical space of 2,944. So ~2.6 shops share a product name — realistic,
since plenty of ramen shops do sell a plain 醤油ラーメン.

The script fails fast if `shop.tsv` contains a (category, subcategory) with no
`PRODUCTS` entry.

## Prices

All prices are **tax-exclusive (税抜)**.

Each sub-category has its own band (ラーメン ¥800-1,600; カメラ・レンズ
¥30,000-250,000; スイーツ・アイス ¥150-600). Within the band the draw is
**log-uniform, not uniform** — the wide bands would otherwise produce absurd
central values. A uniform draw makes the median camera ¥140,000; log-uniform puts
it at ¥94,650, which is what a camera shop's typical stock actually looks like.

The modifier then applies its **price multiplier**, so the name and the price
agree with each other:

| modifier | ×    | effect |
| --- | ---: | --- |
| 極上 (sushi) | 1.8 | 極上寿司盛り合わせ lands near the top |
| 全部のせ (ramen) | 1.5 | 全部のせ豚骨ラーメン ¥2,350 |
| あっさり (ramen) | 1.0 | あっさり醤油ラーメン ¥980 |
| 初回 (beauty) | 0.8 | first-visit discount |
| 初回体験 (gym) | 0.6 | trial pass is cheap |

Prices are then rounded to a step that matches the magnitude (¥10 under ¥2,000;
¥50 under ¥10,000; ¥100 under ¥100,000; ¥1,000 above), the way real menu prices
are.

**Multipliers may push a price past its band ceiling**, and this is intended: a
¥2,350 全部のせ ramen or a ¥13,300 極上 sushi platter are correct outcomes, not
overflow. The band describes the ordinary range, not a hard cap.

### Hard caps

Where the ceiling is part of what the shop *is*, `PRICE_CAP` in
[scripts/product_names.py](scripts/product_names.py) clamps the final price after
the multiplier:

| category / subcategory | cap (税抜) |
| --- | ---: |
| ディスカウントストア / 100円ショップ | ¥500 |

A 100円ショップ sells items above ¥100 — ¥200, ¥300, ¥500 lines are normal — but
never at a ¥1,300 「日本限定」 price, which is what an uncapped multiplier would
produce. Band ¥100-500 plus the cap yields: median ¥270, max ¥500, nothing above
it (15 items at the ¥100 line, 3 clamped at ¥500 out of 42).

## Notes & maintenance

- **One product per shop is a demo simplification.** Real shops carry many items;
  this table exists so a coupon has a single unambiguous thing to discount. If
  the recommender should rank *within* a shop, this is the skill to extend.
- **Prices are hypothetical, and tax-exclusive.** They are set to be plausible
  for central Tokyo in the 2020s, but nothing in the repo sources them.
  消費税 is out of scope: no 10%/8% rate is stored, so a downstream consumer cannot
  tell a 軽減税率 item (takeaway food, non-alcoholic drinks) from a standard-rate
  one without inferring it from the category. The 東京都 survey's
  per-nationality 支出額 (図表26: 全体 ¥182,390 per Tokyo stay, of which ¥39,560
  飲食費 and ¥53,200 土産買物費) would be the input if these should reconcile with
  real spending.
- **No discount is modelled here** — `price` is explicitly the non-discounted
  price. Coupon rates belong in a later skill.
- If shops.md gains a sub-category, add a matching `PRODUCTS` entry (items +
  modifier pool + price band) or the run fails with the missing pairs listed.
