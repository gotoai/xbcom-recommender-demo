---
name: synthesize-inbound-travelers
description: >-
  Synthesize the demo's 2,000 inbound travelers. Allocates travelers per
  nationality from the 「国籍・地域別 滞在人数」 table in docs/scenarios/travelers.md,
  draws an age from 「年齢層分布」 (converted to a birth year), draws a Japan-visit
  count from the 東京都 survey's 訪日回数 distribution for that nationality, draws
  a gender (F/M/unknown, even split by default), and
  writes DATA/s03_primary/inbound_traveler.tsv. Reproducible via
  synthetics/random_seed in pipeline/config/config.yaml. Use when asked to
  synthesize, generate, sample, refresh, or bootstrap the demo's inbound
  travelers / traveler population.
---

# Synthesize inbound travelers

Generates the demo's **traveler population** as primary data. All 2,000 travelers
are assumed to be in Japan for the whole of the same one-week window
(docs/scenarios/travelers.md 「滞在期間」), so no arrival or departure dates are
modelled — the week is the unit of time.

## What it produces

`DATA/s03_primary/inbound_traveler.tsv` — a UTF-8, tab-separated table (header +
2,000 rows), **overwritten** on each run:

| column | meaning |
| --- | --- |
| `traveler_id` | 1-based unique integer |
| `nationality` | 国・地域名 in Japanese (e.g. `台湾`), matching docs/profiles/users.md |
| `nationality_en` | English name of `nationality` (e.g. `Taiwan`) |
| `gender` | `F` = female, `M` = male, `-` = unknown / not disclosed |
| `birthyear` | `YYYY`; `reference_year - age`, age drawn from the 年齢層分布 |
| `repeating_times` | prior visits to Japan; **0 = first visit**, 1 = second, … |

Rows are shuffled, so `traveler_id` order carries no nationality signal.

## How to run it

From the repo root, with the project `.venv`:

```bash
.venv/bin/pip install -r pipeline/requirements.txt   # first time only (PyYAML)
.venv/bin/python pipeline/skills/synthesize-inbound-travelers/scripts/synthesize_inbound_travelers.py
```

The run is **reproducible**: it reads `synthetics/random_seed` from
`pipeline/config/config.yaml` and seeds a single RNG, so the same seed yields the
same population. Change the seed (or any input) to resample.

Options: `--repo-root <path>` and `--config <path>` (both auto-detected).

## Inputs

- `docs/scenarios/travelers.md` — 「### 国籍・地域別 滞在人数」 (the 36 nationality
  headcounts, already summing to 2,000) and 「## 年齢層分布」 (the six age bands).
- `docs/profiles/users.md` — 「## 対象国・地域」, used only to validate that every
  nationality in travelers.md is a market the app actually supports (prints
  `[WARN]` otherwise).
- `pipeline/config/config.yaml` — `synthetics/random_seed`,
  `synthetics/inbound_travelers/{reference_year, repeat_tail_mean, repeat_max,
  gender_weights}`.

## How each column is drawn

**`nationality`** — taken **exactly** from the travelers.md table, not resampled.
That table is already an apportionment of 2,000 (α = 0.4 smoothed), so re-drawing
it would only add noise and break agreement with the doc. Headcounts in the TSV
match the doc row for row.

**`nationality_en`** — a static English name looked up from the `NATIONALITY_EN`
table in the script, which covers every 対象国・地域 in docs/profiles/users.md (the
supported superset, so a market added to travelers.md later still resolves). It is
a pure lookup — no RNG — so adding it leaves the other columns unchanged for a
given seed. The run fails fast if a nationality has no translation.

**`birthyear`** — an age band is drawn with the 年齢層分布 weights
(16-22: 15%, 23-30: 20%, 31-40: 25%, 41-50: 25%, 51-60: 10%, 61-70: 5%), then an
age uniformly within the band, then `birthyear = reference_year - age`
(`reference_year` = 2026, matching the JNTO 2026年1月～4月 base period of the
nationality distribution). users.md registers 生年 only, never a full date, so a
year is the correct granularity. Yields birth years 1956-2010.

**`gender`** — drawn independently per traveler from
`synthetics/inbound_travelers/gender_weights` (`F` / `M` / `unknown`), written as
`F` / `M` / `-`. The default `1:1:1` gives an even three-way split (female / male /
not disclosed). The nationality/訪日回数 sources carry no gender breakdown, so this
is a **demo assumption**, not survey-backed — adjust the weights to reshape it. It
is drawn *after* the shuffle, so adding or reweighting it leaves the other columns
unchanged for a given seed.

**`repeating_times`** — drawn from 東京都「令和6年 国・地域別外国人旅行者行動特性調査」
図表4「これまでの訪日回数」, per nationality. The survey's buckets map as:

| 調査区分 | repeating_times |
| --- | --- |
| 1回目（初訪日） | 0 |
| 2回目 | 1 |
| 3回目 | 2 |
| 4～9回目 | uniform 3-8 |
| 10回以上 | 9 + Exp(mean `repeat_tail_mean`), capped at `repeat_max` |
| 無回答 | redistributed proportionally over the five real buckets |

This varies sharply by market and is the point of sourcing it rather than
inventing it — 台湾 and 香港 are dominated by frequent repeaters (25-33% have
visited 10+ times) while 3/4 of スペイン travelers are first-timers. Overall the
generated population is ~48% first-time visitors.

## Proxy rules

The survey breaks out only 21 markets; the remaining 15 in users.md borrow a
series, mirroring the proxy rules already documented in
[travelers.md](../../../docs/scenarios/travelers.md) 「注記・前提」:

| 市場 | 借用元 |
| --- | --- |
| 豪州、ニュージーランド | オーストラリア |
| メキシコ、イスラエル、トルコ、湾岸6か国 | その他 |
| オランダ、ベルギー、スイス、北欧4か国 | 欧州5か国(英・独・仏・伊・西)の回答数加重平均 |

## Notes & maintenance

- **The 「10回以上」 tail is an assumption.** The survey's top bucket is
  open-ended, so its shape (a capped exponential) is invented, not measured. It
  matters most for 台湾/香港, where a third of travelers land in that bucket.
  `repeat_tail_mean` / `repeat_max` in config.yaml are the knobs.
- **Vintage mismatch.** 訪日回数 is from the 令和6年 (2024) survey while the
  nationality distribution is on a 2026年1月～4月 base — the same mismatch already
  noted in travelers.md.
- **The ≥1-week assumption is a simplification.** The nationality distribution
  already embeds stay length (it is person-day derived, so short-stay markets are
  down-weighted), but 韓国's real average stay is 3.6 nights — far under a week.
  Treating all 2,000 as present for the full week is a demo convenience, not a
  claim about real behaviour.
- The 年齢層分布 in travelers.md is itself hypothetical (16-70), so ages carry no
  survey backing — only the nationality mix and 訪日回数 do.
- If travelers.md's table or age bands change, this skill picks the change up on
  the next run; the headings 「### 国籍・地域別 滞在人数」 and 「## 年齢層分布」 are the
  parse anchors and are the parts to keep stable.
