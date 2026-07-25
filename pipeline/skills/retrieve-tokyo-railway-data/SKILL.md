---
name: retrieve-tokyo-railway-data
description: >-
  Download the 国土数値情報 N02（鉄道） railway dataset from MLIT and save it to
  DATA/s01_raw/railway_<original_zip_filename>. N02 ships nationwide in one ZIP per
  edition (there is no per-prefecture download), carrying two layers — Station (駅)
  and RailroadSection (鉄道区間) — as Shapefile and GeoJSON, in both Shift-JIS and
  UTF-8. Optionally extracts to DATA/s02_intermediate/ with --extract. Use when
  asked to retrieve, refresh, or bootstrap Tokyo railway / station / rail-line data
  for the demo (e.g. for the route-search matrix).
---

# Retrieve Tokyo railway data (N02)

Downloads the **国土数値情報 N02 鉄道データ** (railway stations + line geometry) from
MLIT's KSJ file server. N02 is the standard open dataset for Japanese rail: point/line
geometry for every station and track segment, tagged with line name (`N02_003`),
operator (`N02_004`), station name (`N02_005`) and a same-station group code
(`N02_005g`). It is what the [build-railway-route-predecessor-matrix](../build-railway-route-predecessor-matrix/SKILL.md)
skill turns into a Tokyo routing graph.

## What it produces

**Raw ZIP** in `DATA/s01_raw/`, named `railway_<original_filename>` —
`railway_N02-25_GML.zip` (~15 MB for edition 2025). Left byte-for-byte as downloaded.

Inside (`N02-<YY>_GML/`):
- `UTF-8/N02-<YY>_Station.geojson` + `…_RailroadSection.geojson` — **what the build
  step reads** (UTF-8, stdlib-`json`-parseable).
- `UTF-8/…` and `Shift-JIS/…` Shapefiles (`.shp/.shx/.dbf/.prj`) of the same two
  layers, plus the source GML/XML and metadata.

With `--extract`, the archive is also unpacked to
`DATA/s02_intermediate/railway_N02_<YY>/`. Both the ZIP and any extract are
**overwritten** on each run.

Tokyo scoping is **not** done here — the download is nationwide; the build step
applies a Tokyo bounding-box filter. This mirrors `retrieve-tokyo-geoshapes` (retrieve
raw, filter later).

## How to run it

From the repo root, with the project `.venv`:

```bash
.venv/bin/python pipeline/skills/retrieve-tokyo-railway-data/scripts/retrieve_railway.py
```

Dependency-free (Python standard library only). Prints one `[OK]` / `[SKIP]` line and
exits non-zero if the download fails.

Options:
- `--repo-root <path>` (auto-detected by default)
- `--year <YY>` — N02 edition, 2-digit year as on KSJ (default `25` = 2025)
- `--extract` — also unpack to `DATA/s02_intermediate/railway_N02_<YY>/`

## Data shape

Edition 2025 nationwide: **10,234** station features, **21,933** RailroadSection
features. Station properties:

| field | meaning | example |
| --- | --- | --- |
| `N02_003` | 路線名 (line name) | `山手線`, `3号線銀座線` |
| `N02_004` | 運営会社 (operator) | `東日本旅客鉄道`, `東京地下鉄` |
| `N02_005` | 駅名 (station name) | `新宿` |
| `N02_005g` | 同一駅グループコード (same-station group) | `003700` |
| `N02_001` / `N02_002` | 鉄道区分 / 事業者種別 codes | `24` / `5` |

`N02_005g` is the key to transfers: every platform of a transfer complex shares one
group code — e.g. all seven lines at 新宿 (JR 山手・中央, 京王, 小田急, 東京メトロ
丸ノ内, 都営 新宿・大江戸) share `003700`. Station geometry is a short LineString along
the platform (use its midpoint as the station point). Sections are the track polylines
(same line/operator fields, no station name).

## Notes & maintenance

- Source: 国土数値情報 N02 鉄道データ (MLIT 国土政策局). Datalist:
  <https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html>
  Direct file: `https://nlftp.mlit.go.jp/ksj/gml/data/N02/N02-<YY>/N02-<YY>_GML.zip`.
- **License:** 国土数値情報 利用約款 — free to use/redistribute **with attribution**
  ("「国土数値情報（鉄道データ）」（国土交通省）"); do not misrepresent it as official.
- CRS is geographic **JGD2011** (lon/lat, EPSG:6668).
- Editions are yearly (`N02-20` … `N02-25` …). To pin or update, pass `--year`; the
  URL template `DOWNLOAD_URL` at the top of
  [scripts/retrieve_railway.py](scripts/retrieve_railway.py) is the only thing to
  change if MLIT reorganises the endpoint.
- Nationwide file: Tokyo is ~1,100 station records of the 10k. The build step's
  bounding box does the filtering.
