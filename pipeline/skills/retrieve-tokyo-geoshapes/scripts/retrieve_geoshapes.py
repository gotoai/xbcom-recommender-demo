#!/usr/bin/env python3
"""Retrieve Tokyo boundary shapefiles from the e-stat GIS portal.

The XBCOM PoC is scoped to Tokyo, so this script:

1. looks 東京都 up by name in the portal's 地域 (region) list,
2. downloads the 2020 Census small-area boundary ZIP (世界測地系緯度経度・Shape形式),
3. saves the original ZIP as ``DATA/s01_raw/geoshape_<original_zip_filename>``
   (overwriting), and
4. optionally extracts it to ``DATA/s02_intermediate/geoshape_<NN>/`` with
   ``--extract``.

The boundaries are 町丁・字 level and carry ``CITY`` (= 市区町村コード), so the 23
wards used by docs/scenarios/travelers.md are obtained by dissolving on that field
(Tokyo's 23 special wards are CITY codes 13101-13123).

Only the Python standard library is used so the script runs with no extra
dependencies in the project's .venv.

Data source: 統計GIS 国勢調査 2020年 小地域（境界データ） (e-stat).
    https://www.e-stat.go.jp/gis/statmap-search?type=2&toukeiCode=00200521&toukeiYear=2020&serveyId=A002005212020
"""
from __future__ import annotations

import argparse
import html
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

# --- e-stat GIS catalogue coordinates (2020 Census small-area boundaries) ------
BASE = "https://www.e-stat.go.jp"
SERVEY_ID = "A002005212020"   # 国勢調査 2020 boundary survey id
TOUKEI_CODE = "00200521"      # 国勢調査
TOUKEI_YEAR = "2020"
AGG_UNIT = "A"                # 小地域（町丁・字等）
COORD_SYS = "1"               # 緯度経度
DATUM = "2000"                # 世界測地系 (JGD2000)
FORMAT = "shape"
DOWNLOAD_TYPE = "5"           # Shape形式

# JSON endpoint that backs the portal's download list (the 地域 column).
LIST_URL = (
    BASE + "/gis/statmap-search/search_detail"
    f"?type=2&aggregateUnitForBoundary={AGG_UNIT}&toukeiCode={TOUKEI_CODE}"
    f"&toukeiYear={TOUKEI_YEAR}&serveyId={SERVEY_ID}&coordsys={COORD_SYS}"
    f"&format={FORMAT}&datum={DATUM}&download_disp_flg=1&page={{page}}"
)
# Direct file-download endpoint (returns A002005212020DDSWC<code>.zip).
DOWNLOAD_URL = (
    BASE + "/gis/statmap-search/data"
    f"?dlserveyId={SERVEY_ID}&code={{code}}&coordSys={COORD_SYS}"
    f"&format={FORMAT}&downloadType={DOWNLOAD_TYPE}&datum={DATUM}"
)
MAX_LIST_PAGES = 10           # safety cap (47 prefectures, 20 per page)

USER_AGENT = "Mozilla/5.0 (compatible; xbcom-demo/1.0; +tokyo-geoshapes skill)"
REQUEST_PAUSE_SEC = 1.0       # be polite between requests

DEFAULT_PREF = "東京都"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def fetch_with_headers(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read(), dict(resp.headers)


# -------------------------------------------------------------------------------
def build_prefecture_index() -> dict[str, str]:
    """Map prefecture name -> 2-digit code from the portal's 地域 list.

    The list is paginated; rows look like::

        ...prefCode=12&...">  <li ...>12 千葉県</li>
    """
    index: dict[str, str] = {}
    for page in range(1, MAX_LIST_PAGES + 1):
        data = json.loads(fetch(LIST_URL.format(page=page)).decode("utf-8", "replace"))
        detail = html.unescape(str(data.get("detail", "")))
        rows = re.findall(
            r'prefCode=(\d{2})[^"]*"[^>]*>\s*<li[^>]*>\s*\d{2}\s+([^<]+?)\s*</li>',
            detail,
        )
        if not rows:
            break
        for code, name in rows:
            index.setdefault(name.strip(), code)
        if len(index) >= 47:
            break
        time.sleep(REQUEST_PAUSE_SEC)
    return index


def original_filename(headers: dict, fallback: str) -> str:
    cd = headers.get("Content-Disposition", "") or headers.get("content-disposition", "")
    m = re.search(r"filename\*=UTF-8''([^;\s]+)", cd)
    if m:
        return urllib.parse.unquote(m.group(1))
    m = re.search(r'filename="?([^";]+)"?', cd)
    if m:
        return m.group(1).strip()
    return fallback


def safe_extract(zip_bytes: bytes, dest_dir: Path) -> list[str]:
    """Extract a ZIP to dest_dir (overwriting), guarding against path traversal."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    root = dest_dir.resolve()
    names: list[str] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for member in zf.namelist():
            target = (dest_dir / member).resolve()
            if root != target and root not in target.parents:
                raise SystemExit(f"Unsafe path in ZIP: {member}")
            zf.extract(member, dest_dir)
            names.append(member)
    return names


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "docs" / "profiles").is_dir() and (p / "pipeline").is_dir():
            return p
    raise SystemExit("Could not locate repo root (docs/profiles + pipeline not found).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=None,
                    help="Repo root (auto-detected if omitted).")
    ap.add_argument("--pref", default=DEFAULT_PREF,
                    help=f"Prefecture name as shown on e-stat (default: {DEFAULT_PREF}).")
    ap.add_argument("--extract", action="store_true",
                    help="Also extract the ZIP to DATA/s02_intermediate/geoshape_<NN>/.")
    args = ap.parse_args()

    repo_root = args.repo_root or find_repo_root(Path(__file__).resolve())
    raw_dir = repo_root / "DATA" / "s01_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Target prefecture: {args.pref}")
    print("Fetching e-stat GIS 地域 (region) list ...")
    index = build_prefecture_index()

    code = index.get(args.pref)
    if not code:
        print(f"  [SKIP] {args.pref}: not found in portal 地域 list "
              f"({len(index)} entries retrieved)")
        return 1

    time.sleep(REQUEST_PAUSE_SEC)
    body, headers = fetch_with_headers(DOWNLOAD_URL.format(code=code))
    fname = original_filename(headers, fallback=f"{SERVEY_ID}DDSWC{code}.zip")

    zip_path = raw_dir / f"geoshape_{fname}"
    zip_path.write_bytes(body)                          # overwrite

    print(f"  [OK]   {args.pref} (code {code}): {zip_path.relative_to(repo_root)} "
          f"({len(body):,} bytes)")

    if args.extract:
        dest = repo_root / "DATA" / "s02_intermediate" / f"geoshape_{code}"
        members = safe_extract(body, dest)              # overwrite
        print(f"  [OK]   extracted -> {dest.relative_to(repo_root)}/ "
              f"[{', '.join(members)}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
