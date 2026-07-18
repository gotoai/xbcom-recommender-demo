---
name: retrieve-tokyo-geoshapes
description: >-
  Download the Tokyo (東京都) boundary shapefile from the e-stat GIS portal. Looks
  東京都 up by name in the portal's 地域 list, downloads the 2020 Census small-area
  boundary ZIP, and saves it to DATA/s01_raw/geoshape_<original_zip_filename>.
  Optionally extracts to DATA/s02_intermediate/geoshape_13/ with --extract. Use
  when asked to retrieve, refresh, or bootstrap Tokyo map boundaries, ward
  polygons, or geoshapes for the demo.
---

# Retrieve Tokyo geo-shapes

Downloads the **boundary shapefile** (polygons) for 東京都 from the Japanese
government statistics GIS portal **e-stat**. The XBCOM PoC is scoped to Tokyo, so
unlike the multi-prefecture original this skill targets a single prefecture.

## What it produces

**Raw ZIP** in `DATA/s01_raw/`, named `geoshape_<original_zip_filename>` —
`geoshape_A002005212020DDSWC13.zip` (~5.7 MB). This is the original e-stat
download, left byte-for-byte unmodified. It contains `r2ka13.shp`, `.shx`,
`.dbf`, `.prj`.

With `--extract`, the same files are also unpacked to
`DATA/s02_intermediate/geoshape_13/`.

Both the ZIP and any extracted contents are **overwritten** on each run.

## How to run it

From the repo root, with the project `.venv`:

```bash
.venv/bin/python pipeline/skills/retrieve-tokyo-geoshapes/scripts/retrieve_geoshapes.py
```

The script is dependency-free (Python standard library only). It prints one
`[OK]` / `[SKIP]` line and exits non-zero if the prefecture could not be
retrieved.

Options:
- `--repo-root <path>` (auto-detected by default)
- `--pref <name>` — prefecture name as shown on e-stat (default `東京都`)
- `--extract` — also unpack to `DATA/s02_intermediate/geoshape_13/`

## What it does, step by step

1. **Find 東京都 in the portal's 地域 list.** The catalogue is fixed at the 2020
   Census small-area boundaries (世界測地系緯度経度・Shape形式):
   - `serveyId` `A002005212020`, `toukeiCode` `00200521` (国勢調査), year `2020`
   - `aggregateUnitForBoundary=A` (小地域), `coordsys=1`, `datum=2000`, `format=shape`

   The script reads the portal's paginated download list (the JSON behind
   `…/gis/statmap-search/search_detail`) and parses the **地域** column rows
   (`NN 都道府県名`) to resolve 東京都 to `prefCode` **13**.

2. **Download and save the ZIP.** It downloads from the GIS file endpoint
   (`…/gis/statmap-search/data?dlserveyId=…&code=13&…`), derives the original
   filename from the `Content-Disposition` header, and writes
   `DATA/s01_raw/geoshape_<filename>` (overwriting).

3. **Extract (optional).** With `--extract`, unzips into
   `DATA/s02_intermediate/geoshape_13/`, guarding against unsafe ZIP paths.

## Data shape

`r2ka13.shp` holds **6,021** polygons at the 町丁・字 level, of which **3,192**
fall in the 23 special wards (all 23 are present). The `.dbf` is **Shift_JIS
(CP932)** and carries `KEY_CODE`, `PREF` (`13`), `CITY` (3-digit; `PREF`+`CITY`
= the 5-digit 市区町村コード), `S_AREA` (町丁字コード), plus `PREF_NAME`,
`CITY_NAME`, `S_NAME`.

To get the 23 ward polygons used by
[docs/scenarios/travelers.md](../../../docs/scenarios/travelers.md), filter to
`PREF`+`CITY` in **13101–13123** and dissolve on that key:

| コード | 区 | コード | 区 |
| --- | --- | --- | --- |
| 13101 | 千代田区 | 13113 | 渋谷区 |
| 13102 | 中央区 | 13114 | 中野区 |
| 13103 | 港区 | 13115 | 杉並区 |
| 13104 | 新宿区 | 13116 | 豊島区 |
| 13105 | 文京区 | 13117 | 北区 |
| 13106 | 台東区 | 13118 | 荒川区 |
| 13107 | 墨田区 | 13119 | 板橋区 |
| 13108 | 江東区 | 13120 | 練馬区 |
| 13109 | 品川区 | 13121 | 足立区 |
| 13110 | 目黒区 | 13122 | 葛飾区 |
| 13111 | 大田区 | 13123 | 江戸川区 |
| 13112 | 世田谷区 | | |

## Notes & maintenance

- Source: 統計GIS 国勢調査 2020年 小地域（境界データ）. Portal:
  <https://www.e-stat.go.jp/gis/statmap-search?type=2&toukeiCode=00200521&toukeiYear=2020&serveyId=A002005212020>
- CRS is geographic **JGD2000** (lon/lat, EPSG:4612).
- **東京都 is not just the 23 wards.** The file also covers 多摩地域 and the remote
  islands, so its bounding box spans lon 136.07–153.98 / lat 20.43–35.90 —
  沖ノ鳥島, 南鳥島 and 小笠原諸島 are included. Any map or spatial index for the demo
  must filter to 13101–13123 first, or the extent will be meaningless.
- The catalogue ids and the `download_disp_flg=1` / `prefCode` parameters are the
  matching criteria; if e-stat changes its GIS endpoints or markup, the
  `LIST_URL` / `DOWNLOAD_URL` constants and the row regex in
  [scripts/retrieve_geoshapes.py](scripts/retrieve_geoshapes.py) are the parts to
  update.
- To target a different census year or boundary format, update the catalogue
  constants (`SERVEY_ID`, `COORD_SYS`, `DATUM`, `FORMAT`, `DOWNLOAD_TYPE`) at the
  top of the script.
