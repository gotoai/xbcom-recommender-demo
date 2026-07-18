---
name: synthesize-coupons
description: >-
  Synthesize one coupon per product. Reads DATA/s03_primary/product.tsv and gives
  every product a usage period (start weekday 1-7 + duration 1-7 days), one of
  five fixed discount options (5%, 8%, ¥30, ¥50, ¥80) chosen to suit that
  product's price, and a unique 6-10 char alphanumeric code. Writes
  DATA/s03_primary/coupon.tsv. Reproducible via synthetics/random_seed in
  pipeline/config/config.yaml. Use when asked to synthesize, generate, sample,
  refresh, or bootstrap the demo's coupons / discounts / offers.
---

# Synthesize coupons

The offers XBCOM's recommender ranks. One coupon per product, so a coupon, a
product, and a shop are 1:1:1 throughout the demo.

> **Prices and discount amounts are tax-exclusive (税抜) JPY**, inherited from
> `product.tsv`. Consumption tax is not modelled — see `synthesize-products`.

## What it produces

`DATA/s03_primary/coupon.tsv` — a UTF-8, tab-separated table (header + **6,000**
rows), **overwritten** on each run:

| column | meaning |
| --- | --- |
| `coupon_id` | 1-based unique integer |
| `shop_id` | joins to `shop.tsv` |
| `shop_name` | denormalised (Japanese) |
| `shop_name_en` | denormalised (English) |
| `category` | denormalised |
| `category_en` | denormalised (English) |
| `subcategory` | denormalised |
| `subcategory_en` | denormalised (English) |
| `product_id` | joins to `product.tsv` |
| `product_name` | denormalised (Japanese) |
| `product_name_en` | denormalised (English) |
| `price` | non-discounted, tax-exclusive JPY |
| `coupon_start_weekday` | 1-7, Monday to Sunday |
| `coupon_duration_days` | 1-7, inclusive |
| `coupon_discount_display` | `rate` or `amount` — which form the coupon shows |
| `coupon_discount_amount` | yen off (float) |
| `coupon_discount_rate` | 0-1 (float) |
| `coupon_code` | unique 6-10 char `[A-Z0-9]` string |

The four `*_en` columns are copied verbatim from `product.tsv` (which sources
`shop_name_en` / `category_en` / `subcategory_en` from `shop.tsv`), so a consumer
has the English labels without re-joining. The run fails fast if `product.tsv`
lacks them — re-run `synthesize-products` (and `synthesize-shops` before it) if so.

Row order follows `product.tsv`, which follows the shuffled `shop.tsv`.

## How to run it

Requires `synthesize-products` to have run.

```bash
.venv/bin/pip install -r pipeline/requirements.txt   # first time only (PyYAML)
.venv/bin/python pipeline/skills/synthesize-coupons/scripts/synthesize_coupons.py
```

Reproducible via `synthetics/random_seed` in `pipeline/config/config.yaml`.

Options: `--repo-root <path>` and `--config <path>` (both auto-detected).

## Usage period

`coupon_start_weekday` (1-7) and `coupon_duration_days` (1-7) are each drawn
uniformly and independently.

**The end weekday is deliberately not stored.** A Saturday start with a 7-day run
leaves the Mon-Sun week, and every way of forcing an end weekday into 1-7 loses
information: clamping truncates late-starting coupons (a Sunday start would always
be 1 day, and mean observed duration would fall to ~2.7); wrapping makes `end <
start` and needs modular logic downstream. Storing the duration keeps both fields
uniform and unbiased, and lets each consumer derive the end under whatever
boundary rule it needs:

```python
end_clamped = min(start + duration - 1, 7)        # fixed Mon-Sun window
end_wrapped = (start - 1 + duration - 1) % 7 + 1  # recurring weekly cycle
```

## Choosing a discount

The five options are fixed by spec — **5%**, **8%**, **¥30**, **¥50**, **¥80** —
and exactly one is assigned per coupon. Choosing well is the whole problem, since
prices span ¥100 to ¥320,000: a flat draw would put ¥80 off a ¥100 shop item (80%
off) and 5% off a ¥150 ice cream (worth ¥7).

Rather than hand-map price bands to options, one rule decides eligibility:

> An option is eligible iff its **effective rate** falls in
> `[min_effective_rate, max_effective_rate]` **and** the yen it removes is at
> least `min_discount_amount`.

Defaults: rate in **[2%, 30%]**, amount **≥ ¥20**. One eligible option is then
drawn uniformly. The price gradient falls out on its own:

| price band | n | options actually chosen |
| --- | ---: | --- |
| ¥0-200 | 37 | ¥30 (26), ¥50 (11) — rates would be worth under ¥20 |
| ¥200-500 | 311 | all five |
| ¥500-1,500 | 1,709 | all five, roughly evenly |
| ¥1,500-5,000 | 2,437 | 5% / 8% / ¥80 dominate; ¥30 nearly gone (6) |
| ¥5,000-50,000 | 1,466 | 5% / 8% only — every amount is under 2% |
| ¥50,000+ | 40 | 5% / 8% only |

Resulting mix: 3,880 `rate` / 2,120 `amount`. Effective rates span exactly
2.0%-30.0% with a 5.0% median; discounts run ¥20 to ¥18,080 (median ¥100). No
coupon discounts more than its price.

### Both discount columns are always populated

`coupon_discount_display` says which form is **canonical** — the one the coupon
advertises. The other is derived:

- `display = rate`: `coupon_discount_rate` is the exact advertised 0.05 / 0.08;
  `coupon_discount_amount` is the yen it removes, **floored** to whole yen (切り捨て,
  the merchant-conservative convention). 5% of ¥1,050 → rate `0.05`, amount `52.0`.
- `display = amount`: `coupon_discount_amount` is the exact ¥30 / ¥50 / ¥80;
  `coupon_discount_rate` is the derived ratio, rounded to 4 dp. ¥50 off ¥1,110 →
  amount `50.0`, rate `0.045`.

So a consumer can always sort or filter on either column, but should render the
one `display` names.

## Notes & maintenance

- **The eligibility bands are the tuning knob**, not a price→option table. If the
  mix looks wrong, move `min_effective_rate` / `max_effective_rate` /
  `min_discount_amount` in `config.yaml`; the gradient re-derives itself.
- **A fallback exists but never fires** (0/6,000 with the current price range). If
  no option fits the bands — reachable only if `product.tsv` gains prices below
  ~¥100 — the option whose effective rate sits closest to the middle of the band
  is used, and the run reports a non-zero `fallbacks` count. Treat that count as a
  signal the bands need revisiting.
- **Eligible options are drawn uniformly**, so within a band every suitable option
  is equally likely. Real coupon programmes skew (round-yen offers are commoner
  at convenience stores); weight `eligible` in `choose_discount` if that matters.
- **Every product has exactly one coupon, always active for some part of the
  week.** There is no "no coupon available" state at the product level — that
  only arises geographically, from the 17 wards with no shops (see
  `synthesize-visits`).
- `coupon_code` is uniform over `[A-Z0-9]` with length 6-10, uniqueness enforced
  against a set. Ambiguous glyphs (`0`/`O`, `1`/`I`) are **not** excluded; add a
  reduced alphabet if the codes are ever meant to be read aloud or typed.
