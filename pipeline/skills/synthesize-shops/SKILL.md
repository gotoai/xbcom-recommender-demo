---
name: synthesize-shops
description: >-
  Synthesize the demo's 6,000 coupon-providing shops (1,000 per PoC ward). Draws
  a category / sub-category from the configured mix, picks a 町丁・字 in the ward,
  places the shop at a uniformly random point inside that polygon (from the
  Tokyo geoshape ZIP), builds a Japanese address from the polygon's own S_NAME
  plus a synthetic 番地, generates paired JA/EN names, and writes
  DATA/s03_primary/shop.tsv. Reproducible via synthetics/random_seed in
  pipeline/config/config.yaml. Use when asked to synthesize, generate, sample,
  refresh, or bootstrap the demo's shops / merchants / coupon providers.
---

# Synthesize shops

Generates the demo's **shop network** as primary data: the merchants that supply
coupons to XB eSIM users, placed on real Tokyo geography.

## What it produces

`DATA/s03_primary/shop.tsv` — a UTF-8, tab-separated table (header + 6,000
rows = 1,000 x 6 wards), **overwritten** on each run:

| column | meaning |
| --- | --- |
| `shop_id` | 1-based unique integer |
| `shop_name` | Japanese name, e.g. `朝日立ち飲み 新宿店` |
| `shop_name_en` | English name, e.g. `Asahi Standing Bar Shinjuku` |
| `category` | one of the 20 categories in docs/profiles/shops.md |
| `subcategory` | one of that category's sub-categories |
| `address` | `東京都<区><町丁字><番>番<号>号` |
| `latitude` | WGS84/JGD2000, 6 dp |
| `longitude` | WGS84/JGD2000, 6 dp |

Rows are shuffled, so `shop_id` order carries no ward or category signal.

## How to run it

Requires the Tokyo geoshape ZIP — run `retrieve-tokyo-geoshapes` first.

```bash
.venv/bin/pip install -r pipeline/requirements.txt   # first time only (pyshp, PyYAML)
.venv/bin/python pipeline/skills/synthesize-shops/scripts/synthesize_shops.py
```

Reproducible via `synthetics/random_seed` in `pipeline/config/config.yaml`.

Options: `--repo-root <path>` and `--config <path>` (both auto-detected).

## Inputs

- `docs/profiles/shops.md` — 「## 対象地域」 (the 6 wards) and 「## 対象店舗カテゴリ」
  (20 categories / 117 sub-categories). Parsed live, so edits are picked up.
- `pipeline/config/config.yaml` — `synthetics/random_seed` and
  `synthetics/shops/*` (per_ward, category_weights, ward_category_multipliers,
  subcategory_weights, banchi_max, go_max).
- `DATA/s01_raw/geoshape_*13.zip` — read **directly from the ZIP**; no extract
  step, so `retrieve-tokyo-geoshapes --extract` is not required.

## How placement works

1. A 町丁・字 is chosen **uniformly** among the ward's polygons.
2. A point is drawn uniformly inside that polygon by rejection sampling within
   its bounding box, using even-odd ray casting across every ring (so holes and
   multi-part shapes are handled).
3. The address is built from that same polygon's `S_NAME`, so **address and
   coordinates always agree** — verified 0/6000 mismatches.

Only `HCODE == 8101` (通常の町丁・字) polygons are used — 676 of them across the 6
wards. The other 23 are `HCODE == 8154` 水面調査区 (Tokyo Bay, rivers, canals);
including them would put shops in the water.

### Why not weight by population

The shapefile carries a `JINKO` (population) field, and the sibling
`synthesize-stores` skill in the reference project uses population-weighted
sampling. That is **wrong for commercial premises** and is deliberately not used
here:

| 町丁字 | JINKO | 実態 |
| --- | ---: | --- |
| 千代田区大手町一丁目 | 0 | 金融街 |
| 千代田区丸の内一丁目 | 10 | オフィス・商業 |
| 中央区銀座四丁目 | 152 | 日本最大級の商業地 |
| 港区高輪三丁目 | 4,868 | 住宅地 |

Population-weighting would place **zero** shops in 大手町 and almost none in 銀座.
Uniform-over-町丁字 is used instead: 町丁・字 are subdivided more finely where
activity is denser, so uniform selection approximates commercial density better
than `JINKO` does. The correct input, if realism matters later, is 経済センサス
事業所数 by 町丁字 — not in the repo today.

## Category distribution

`docs/profiles/shops.md` defines the taxonomy but **no distribution**, so the mix
in `config.yaml` is hypothetical. It has two layers:

- `category_weights` — a base mix (%) shaped for inbound-facing central Tokyo:
  レストラン 24, バー 10, コンビニエンスストア 8, コーヒーショップ 7, 衣料品店 7, …,
  映画館 0.5.
- `ward_category_multipliers` — per-ward tilts, renormalised per ward, so the
  six wards do not come out identical. Without these, location would carry no
  category signal and the recommender would have nothing to rank on:
  千代田区 gets ×3 家電量販店 / 音楽・映像・ゲーム店 (秋葉原) and ×2 書店 (神保町);
  渋谷区 ×2 衣料品店; 中央区 ×1.8 衣料品店 / ×1.3 免税・スイーツ (銀座・築地);
  新宿区 ×1.5 バー・カラオケ (歌舞伎町); 台東区 ×1.5 ディスカウント・スイーツ
  (アメ横); 港区 ×1.5 スパ・ジム (六本木・赤坂).

Result: 家電量販店 is 5.5% of 千代田区 but 1.4% of 台東区; 衣料品店 is 14.1% of
渋谷区 and 10.2% of 中央区 but 4.9% of 台東区; カラオケボックス is 0.9% of 中央区 but
4.6% of 渋谷区.

`subcategory_weights` tilts within a category (ラーメン ×2.0, 居酒屋 ×3.0, …);
anything unlisted defaults to 1.0.

## Shop names

[scripts/shop_names.py](scripts/shop_names.py) holds a **paired** JA/EN
vocabulary: every entry carries both forms, so the English name is a parallel
name rather than a transliteration and no romanisation library is needed.

- `SHOP_WORD` — one (JA, EN) shop word per **(category, subcategory)** pair. Keyed
  by the pair, not the sub-category alone, because 「日用品・雑貨」 appears under
  both ドラッグストア and コンビニエンスストア.
- `YAGO` — 50 paired 屋号 (さくら/Sakura, 武蔵/Musashi, …).
- `PATTERNS` — 5 paired templates; the same index drives both languages.

The script fails fast if shops.md gains a sub-category with no `SHOP_WORD` entry.

## Notes & maintenance

- **Addresses containing 番 are ambiguous.** 千代田区四番町・五番町・六番町 and
  港区麻布十番 produce addresses like `東京都千代田区五番町19番14号`, which cannot be
  split back into 町丁字 + 番地 by a naive `split("番")`. This is true of real
  Japanese addresses too. Any consumer must match S_NAME against the shapefile
  rather than parse on the delimiter.
- **Four 町丁・字 are discontiguous** — 新宿区四谷, 新宿区山吹町, 千代田区神田紺屋町,
  港区台場一丁目 span multiple polygons. Keep them as a multimap; a
  name→single-polygon dict silently drops half of each.
- **Names collide.** 5,316 distinct JA names and 5,042 distinct EN names across
  6,000 shops. Patterns 0 and 1 (`{w}{y}` and `{y}{w}`) both render as `{Y} {W}`
  in English, which drives most of the EN collisions. Realistic enough for small
  independent shops; add a branch suffix or a numeric disambiguator if unique
  names are needed.
- Coupons themselves are **not** modelled here — this skill produces only the
  shops that would offer them.
- The 番地/号 in each address are synthetic (`banchi_max` / `go_max`) and do not
  correspond to real lots.
