---
name: synthesize-dummy-images
description: >-
  Generate placeholder product thumbnails, one per sub-category (117), as
  stand-ins for real generated imagery. Each is a flat light-sky-blue 1024x1024
  card printed with the English category and sub-category name, written to
  assets/images/<category>_<subcategory>.png. Use when asked to build dummy,
  placeholder, or test product images, or to refresh them after the shops.md
  taxonomy changes.
---

# Synthesize dummy images

Placeholder thumbnails so the web app has something to render before spending
anything on image generation.

## What it produces

`assets/images/<category>_<subcategory>.png` — **117** files, one per
sub-category, 1024×1024 PNG, ~3.3 MB total. **Overwritten** on each run.

Filenames are the Japanese taxonomy verbatim, e.g.
`assets/images/レストラン_寿司・海鮮.png`, so they join to `shop.tsv` /
`product.tsv` / `coupon.tsv` on `(category, subcategory)` with no mapping table.

Each card carries the **English** category (small, muted) above the sub-category
(large, bold) on `#87CEFA` (CSS `lightskyblue`) with a white inset border.

`assets/` is **not** gitignored — unlike `DATA/` — so these are committed. That is
deliberate: the demo should render on a fresh clone without running the pipeline.

## How to run it

```bash
.venv/bin/pip install -r pipeline/requirements.txt   # first time only (Pillow)
.venv/bin/python pipeline/skills/synthesize-dummy-images/scripts/make_dummy_images.py
```

Options: `--repo-root <path>` and `--out-dir <path>` (default `<repo>/assets/images`).

No RNG — output is deterministic, so a rerun is a no-op unless shops.md changed.

## Inputs

- `docs/profiles/shops.md` — 「## 対象店舗カテゴリ」, parsed live, so taxonomy edits
  are picked up on the next run.
- [scripts/category_names.py](scripts/category_names.py) — the English names.

## Why a separate English name map

`CATEGORY_EN` (20) and `SUBCATEGORY_EN` (117) are a **translation** of the
taxonomy, and are deliberately *not* reused from
`synthesize-shops/scripts/shop_names.py::SHOP_WORD`. That map is a shop-*naming*
device: it renders 寿司・海鮮 as "Sushi" (right inside 「Sushi Sakura」, wrong as a
category label) and 日用品・雑貨 as "Drug" (meaningless as one). The two happen to
agree sometimes, which makes the mismatch easy to miss.

Sub-categories are keyed by `(category, subcategory)` because 「日用品・雑貨」 appears
under both ドラッグストア and コンビニエンスストア.

**This map is reusable well beyond placeholders.** The XB eSIM app supports 20+
languages (docs/profiles/xbcom.md), so a per-language taxonomy map is needed
regardless — English is simply the first. Promote it out of this skill as soon as
a second consumer appears.

The script fails fast, listing the gaps, if shops.md gains a category or
sub-category with no English name.

## Layout

Text is auto-fitted, not hand-placed: `fit_font` starts at 104 px for the
sub-category (56 px for the category) and steps down until the greedy word-wrap
fits the box. So `Ramen` renders large on one line while
`Theme Cafe (Anime & Animals)` shrinks to three — no clipping, no overflow, and
new sub-categories need no layout work.

Uses DejaVu Sans (falls back to Liberation Sans). **No CJK font is required**
because only English is drawn — worth preserving if the design changes, since
CJK-capable TTFs are a much heavier dependency.

## Notes & maintenance

- **These are 1024×1024, but the real thumbnails are specified 1200×900 (4:3).**
  Square placeholders will not exercise the app's 4:3 layout — anything that
  crops, letterboxes, or object-fits will behave differently once real imagery
  lands. Pass `SIZE` as 1200×900 here first if you want the layout validated
  against the true aspect ratio.
- **One image per sub-category, not per product.** A placeholder carries no
  product-specific information, so 6,000 copies would be 6,000 identical files.
  Real imagery should key on the **distinct product name** (~2,287) instead —
  野菜たっぷり醤油ラーメン and 魚介醤油ラーメン are different dishes.
- **Japanese filenames need percent-encoding when served over HTTP.**
  `レストラン_寿司・海鮮.png` works fine on the filesystem and in `<img src>` once
  encoded, but if that becomes awkward in the web app, romanised or hashed
  filenames are the alternative — the join key would then need a lookup rather
  than being the filename itself.
- Nothing in the taxonomy currently contains `/`; the script replaces it anyway,
  since a `/` in a sub-category would silently address a directory.
