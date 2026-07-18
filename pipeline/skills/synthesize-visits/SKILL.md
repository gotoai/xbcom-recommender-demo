---
name: synthesize-visits
description: >-
  Synthesize where each inbound traveler is during every 6-hour interval of the
  demo week. Splits Mon-Sun into 7 days x 3 time spans = 21 intervals, and for
  each interval gives all 2,000 travelers a central location: a ward drawn from
  the 23-ward distribution in docs/scenarios/travelers.md, plus a uniformly
  random point inside a 町丁・字 of that ward. Writes
  DATA/s03_primary/visit.tsv (42,000 rows). Reproducible via
  synthetics/random_seed in pipeline/config/config.yaml. Use when asked to
  synthesize, generate, sample, refresh, or bootstrap traveler visits /
  locations / movement over the demo week.
---

# Synthesize visits

Places every traveler somewhere in Tokyo for every interval of the demo week.
This is the table the recommender's location signal reads from.

## What it produces

`DATA/s03_primary/visit.tsv` — a UTF-8, tab-separated table (header + **42,000**
rows = 2,000 travelers x 7 days x 3 spans), **overwritten** on each run:

| column | meaning |
| --- | --- |
| `weekday` | 1-7, Monday to Sunday |
| `timespan` | `06:00-11:59`, `12:00-17:59`, or `18:00-23:59` |
| `traveler_id` | joins to `inbound_traveler.tsv` |
| `nationality` | denormalised from `inbound_traveler.tsv` |
| `ward` | 23区 name in Japanese |
| `latitude` | WGS84/JGD2000, 6 dp |
| `longitude` | WGS84/JGD2000, 6 dp |

Rows are ordered by weekday, then timespan, then traveler_id. Exactly one row
per (weekday, timespan, traveler_id).

`00:00-05:59` is not modelled — travelers are assumed asleep — so 18 of each
day's 24 hours are covered.

## How to run it

Requires both upstream skills: `retrieve-tokyo-geoshapes` and
`synthesize-inbound-travelers`.

```bash
.venv/bin/pip install -r pipeline/requirements.txt   # first time only (pyshp, PyYAML)
.venv/bin/python pipeline/skills/synthesize-visits/scripts/synthesize_visits.py
```

Runs in well under a second. Reproducible via `synthetics/random_seed`.

Options: `--repo-root <path>` and `--config <path>` (both auto-detected).

## Inputs

- `docs/scenarios/travelers.md` — 「### 東京都23区別 1日あたり滞在確率」. Parsed live;
  the ※ mark on the 11 interpolated wards is ignored (they are drawn like any
  other). The script fails fast if it does not parse exactly 23 wards.
- `DATA/s03_primary/inbound_traveler.tsv` — traveler_id -> nationality.
- `pipeline/config/config.yaml` — `synthetics/random_seed`,
  `synthetics/visits/{days, timespans}`.
- `DATA/s01_raw/geoshape_*13.zip` — read directly from the ZIP.

## The per-day → per-interval conversion

This is the one modelling decision worth understanding.

travelers.md's 「1日あたり滞在確率」 are **per-day** probabilities and deliberately
**non-MECE** — they sum to 94.2%, because a traveler can touch several wards in
one day. But a *central location* for one interval is MECE: you are in exactly
one place at a time. So the 23 values are **normalised** to a categorical
distribution and one ward is drawn per interval (渋谷区 18.3% → 19.43%).

**Relative ward weights are preserved exactly** — verified to within 0.15pp
across all 23 wards. What is *not* preserved is the absolute rate: travelers.md
implies ~0.94 ward-presences per day, whereas this model gives exactly 3 (one per
interval).

That inflation is **less wrong than it looks**, because it cancels a known
conservatism in the source. travelers.md notes that 0.94 wards/day follows
honestly from 図表18 but likely understates reality — the survey offers a coarse
checklist and respondents recall only headline places, and a real Tokyo tourist
plausibly touches 2-3 areas a day. Three ward-presences per day lands in that
range. The two errors run in opposite directions.

If you need the strict source-faithful rate instead, the model must gain an
「圏外」 (outside the 23 wards) outcome carrying ~65% of the interval mass — which
the required schema (`ward`, `latitude`, `longitude` all non-null) does not
allow today.

## Placement within a ward

A 町丁・字 is chosen uniformly among the ward's polygons, then a point is drawn
uniformly inside it by rejection sampling with even-odd ray casting. Only
`HCODE == 8101` polygons are used, so nothing lands in 水面調査区 (Tokyo Bay,
rivers). Verified: 0 of 3,000 sampled points fall outside their own ward.

Note this is *uniform over 町丁・字*, not over area or population — the same choice
`synthesize-shops` makes, and for the same reason (`JINKO` is ~0 in 大手町 and
丸の内, which are among the busiest places in Tokyo).

## Notes & maintenance

- **Intervals are sampled independently**, so a traveler can jump from 渋谷区 to
  足立区 between spans with no travel cost. Real trips are sticky: you stay in an
  area, or move to an adjacent one. Adding a stickiness parameter (repeat the
  previous ward with probability *k*, else redraw) would be a small change and
  would make the action logs read far more plausibly. Not done, because the spec
  asks for per-interval sampling.
- **The distribution is nationality-blind.** Every traveler draws from the same
  23-ward distribution, so a Taiwanese and a Spanish traveler have identical
  location behaviour. The 東京都 survey publishes per-country top-10 places
  (韓国 渋谷 63.9%, 台湾 浅草 46.4%, 中国 銀座 52.2%), so a per-nationality table is
  available if the recommender should act on 「台湾人は台東区に集まる」.
- **Only 6 of the 23 wards have shops.** 新宿・中央・台東・千代田・港・渋谷 carry
  coupons (`synthesize-shops`); the other 17 appear in this table but have nothing
  to recommend. About 88.5% of visit rows fall in the 6 coupon wards.
- `_geo.py` duplicates the polygon helpers in `synthesize-shops`. The pipeline's
  skills are deliberately self-contained; factor out to a shared module only if a
  third consumer appears.
