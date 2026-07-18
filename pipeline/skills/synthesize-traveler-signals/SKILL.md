---
name: synthesize-traveler-signals
description: >-
  Synthesize per-traveler feature signals in a long/tidy table. For each of the
  2,000 inbound travelers it emits scalar signals (nationality in English,
  gender, age from birthyear + today's date, repeating_times) plus 5-10
  propensity signals: distinct (category_en, subcategory_en) interests drawn from
  product.tsv, each with a Beta-distributed taste score in [-1, 0.99] (negatives =
  dislike; non-negative mean ~0.3) and a score_type (1 historical / 2 inferred).
  Writes DATA/s04_feature/traveler_signal.tsv. Reproducible via
  synthetics/random_seed in pipeline/config/config.yaml (except age, which tracks
  the system date). Use when asked to synthesize, generate, refresh, or bootstrap
  the demo's traveler signals / features / preferences / propensities.
---

# Synthesize traveler signals

Turns the primary traveler and product tables into a **feature table** for the
recommender: what each traveler *is* (nationality, gender, age, visit count) and
what each traveler *likes* (per-category propensity scores). This is the first
table written to the `s04_feature` layer.

## What it produces

`DATA/s04_feature/traveler_signal.tsv` — a UTF-8, tab-separated table in **long
(tidy) format**, one row per (traveler, signal), **overwritten** on each run:

| column | meaning |
| --- | --- |
| `traveler_id` | joins to `inbound_traveler.tsv` |
| `signal_name` | `nationality` \| `gender` \| `age` \| `repeating_times` \| `propensity` |
| `signal_value1` | scalar value, or (propensity) `category_en` |
| `signal_value2` | empty, or (propensity) `subcategory_en` |
| `signal_value3` | empty, or (propensity) `score_type` (`1`/`2`) |
| `signal_value4` | empty, or (propensity) the propensity score |

Per traveler: 4 scalar rows + 5-10 `propensity` rows. At 2,000 travelers that is
~23k rows (~15k of them propensity).

### The five signals

- **`nationality`** — the traveler's `nationality_en` (English), in `signal_value1`.
- **`gender`** — `F` / `M` / `-` (as stored), in `signal_value1`.
- **`age`** — `signal_value1 = today.year - birthyear`. Only the birth **year** is
  known, so this is the whole-year age. It reads the **system current date**, so
  it is the one column that changes over calendar time for a fixed seed.
- **`repeating_times`** — prior visits to Japan (as stored), in `signal_value1`.
- **`propensity`** — a taste score for one interest. `signal_value1` =
  `category_en`, `signal_value2` = `subcategory_en`, `signal_value3` =
  `score_type`, `signal_value4` = the score.

Scalar signals leave `signal_value2`-`4` empty; only `propensity` fills them.

## How to run it

Requires `synthesize-inbound-travelers` and `synthesize-products` to have run.

```bash
.venv/bin/pip install -r pipeline/requirements.txt   # first time only (PyYAML)
.venv/bin/python pipeline/skills/synthesize-traveler-signals/scripts/synthesize_traveler_signals.py
```

Reproducible via `synthetics/random_seed` in `pipeline/config/config.yaml` (the
`age` column excepted — see above).

Options: `--repo-root <path>` and `--config <path>` (both auto-detected).

## Propensity model

The interest space is the **sorted unique `(category_en, subcategory_en)` pairs**
from `product.tsv` — the 117 taxonomy leaves. For each traveler, `rng.randint`
picks a count in `[items_min, items_max]` (5-10) and `rng.sample` draws that many
**distinct** interests. Each gets a score in **[-1, 0.99]**:

- A **dislike** with probability `negative_fraction` (default 0.2): a negative
  score in `[-1, 0)`, drawn as `-Beta(neg_beta_a, neg_beta_b)` and clamped to
  ≤ -0.01. `< 0` means rejection.
- Otherwise a **like**: `0.99 * Beta(pos_beta_a, pos_beta_b)` in `[0, 0.99]`.
  `0` is neutral, `> 0` is preference.

Scores use **Beta, not uniform**, so most likes are mild with a thin tail toward
the 0.99 ceiling. `pos_beta_a=1.6`, `pos_beta_b=3.68` are tuned so the mean of the
**non-negative** scores is ~0.3 (`0.99 * 0.303`); dislikes are excluded from that
mean, as specified. The run prints the achieved figures — with the seeded default
it reports **20.0% negative** and a **non-negative mean of 0.299**.

### `score_type`

Every propensity row carries `score_type` in `signal_value3`, assigned per row:
`1` = derived from historical behaviour, `2` = inferred, split by
`historical_fraction` (default 0.5). In this synthetic demo it is a **provenance
label only** — both types are drawn from the same distribution; a real pipeline
would compute them differently.

## Config

`pipeline/config/config.yaml` → `synthetics/traveler_signals`:

| key | default | effect |
| --- | ---: | --- |
| `items_min` / `items_max` | 5 / 10 | propensity interests per traveler |
| `negative_fraction` | 0.2 | share of interests that are dislikes |
| `pos_beta_a` / `pos_beta_b` | 1.6 / 3.68 | like shape; tuned for a ~0.3 non-negative mean |
| `neg_beta_a` / `neg_beta_b` | 2.0 / 3.0 | dislike-magnitude shape |
| `historical_fraction` | 0.5 | share of `score_type == 1` rows |

## Notes & maintenance

- **Long format is deliberate.** Travelers carry a variable number of propensity
  signals, and more signal types will be added; a wide table would need a ragged,
  ever-growing column set. `signal_value1`-`4` are generic slots keyed by
  `signal_name`, so a new signal costs no schema change.
- **`age` is not seed-stable across dates** — it reads `date.today()`. Everything
  else is reproducible from `random_seed`. Pin a reference year here too if you
  need bit-exact age across a date boundary.
- **`score_type` is a label, not a second model.** Tightening the `historical`
  path to actually consume behavioural data (e.g. a future `visit.tsv` join) is
  the natural next step; the column exists so downstream code can already branch
  on it.
- The interest space is read from `product.tsv`, so it stays in step with the
  shop/product taxonomy automatically. The run fails fast if `product.tsv` lacks
  the `*_en` columns or `inbound_traveler.tsv` lacks `nationality_en`.
