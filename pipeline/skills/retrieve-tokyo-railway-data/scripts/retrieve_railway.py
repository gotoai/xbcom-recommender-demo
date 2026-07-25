#!/usr/bin/env python3
"""Retrieve the 国土数値情報 N02（鉄道） railway dataset from MLIT.

N02 is published **nationwide in one ZIP per year** (there is no per-prefecture
download), so this script:

1. downloads ``N02-<YY>_GML.zip`` from the KSJ file server,
2. saves the original ZIP as ``DATA/s01_raw/railway_<original_filename>``
   (overwriting), and
3. optionally extracts it to ``DATA/s02_intermediate/railway_N02_<YY>/`` with
   ``--extract``.

The ZIP carries both Shift-JIS and UTF-8 variants of two layers — ``…_Station`` and
``…_RailroadSection`` — as Shapefile **and GeoJSON**. The downstream matrix build
reads the UTF-8 GeoJSON (``build-railway-route-predecessor-matrix``), so no extract
is required; the raw ZIP is enough.

Tokyo scoping happens in the *build* step (a bounding-box filter), not here — this
skill keeps the government download byte-for-byte, mirroring ``retrieve-tokyo-
geoshapes``.

Only the Python standard library is used.

Data source: 国土数値情報 N02 鉄道データ (MLIT 国土政策局).
    https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-2025.html
    License: 国土数値情報 利用約款 (CC BY 4.0 compatible; attribution required).
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://nlftp.mlit.go.jp/ksj/gml/data/N02"
# Direct nationwide file endpoint, e.g. .../N02/N02-25/N02-25_GML.zip (year 2025).
DOWNLOAD_URL = BASE + "/N02-{yy}/N02-{yy}_GML.zip"
DEFAULT_YEAR = "25"  # N02 edition (2-digit year); 25 = 2025, the latest at time of writing

USER_AGENT = "Mozilla/5.0 (compatible; xbcom-demo/1.0; +tokyo-railway skill)"


def fetch_with_headers(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read(), dict(resp.headers)


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
    ap.add_argument("--year", default=DEFAULT_YEAR,
                    help=f"N02 edition, 2-digit year as on KSJ (default: {DEFAULT_YEAR} = 2025).")
    ap.add_argument("--extract", action="store_true",
                    help="Also extract the ZIP to DATA/s02_intermediate/railway_N02_<YY>/.")
    args = ap.parse_args()

    repo_root = args.repo_root or find_repo_root(Path(__file__).resolve())
    raw_dir = repo_root / "DATA" / "s01_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    url = DOWNLOAD_URL.format(yy=args.year)
    print(f"Fetching N02 railway data (edition {args.year}) ...")
    print(f"  {url}")
    try:
        body, headers = fetch_with_headers(url)
    except Exception as exc:  # noqa: BLE001 — one clear failure line, non-zero exit
        print(f"  [SKIP] download failed: {exc}")
        return 1

    fname = original_filename(headers, fallback=f"N02-{args.year}_GML.zip")
    zip_path = raw_dir / f"railway_{fname}"
    zip_path.write_bytes(body)  # overwrite

    print(f"  [OK]   {zip_path.relative_to(repo_root)} ({len(body):,} bytes)")

    if args.extract:
        dest = repo_root / "DATA" / "s02_intermediate" / f"railway_N02_{args.year}"
        members = safe_extract(body, dest)  # overwrite
        print(f"  [OK]   extracted {len(members)} members -> {dest.relative_to(repo_root)}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
