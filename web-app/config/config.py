"""Configuration for the XB.com recommender web-app.

Loads ``web-app/.env`` and resolves the paths the app reads. Deliberately tiny and
import-safe so tests can import it cheaply.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# web-app/ (this file is config/config.py -> parents[1] is web-app/)
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

# Repo root = xbcom-recommender-demo/ (web-app/ sibling of DATA/, docs/).
REPO_ROOT = BASE_DIR.parent


def _path(env: str, default: Path) -> Path:
    val = os.getenv(env)
    return Path(val).expanduser().resolve() if val else default


# The primary TSVs (inbound_traveler / visit / coupon / shop / product).
DATA_DIR: Path = _path("DATA_DIR", (REPO_ROOT / "DATA" / "s03_primary").resolve())
INBOUND_TSV = DATA_DIR / "inbound_traveler.tsv"
VISIT_TSV = DATA_DIR / "visit.tsv"
COUPON_TSV = DATA_DIR / "coupon.tsv"
SHOP_TSV = DATA_DIR / "shop.tsv"
PRODUCT_TSV = DATA_DIR / "product.tsv"

# This app's bind address (0.0.0.0 so other machines on the LAN can reach it).
WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT: int = int(os.getenv("WEB_PORT", "8091"))

UI_LANGUAGE: str = os.getenv("UI_LANGUAGE", "ja")

# Mapillary Graph API access token, for the street-view photo tool (agent/tools/
# streetview_photo.py). Server-side only; empty disables the tool (it returns None).
# NOTE: keep this value free of inline comments in .env — the loader folds a trailing
# comment into the value and it would break the HTTP auth header.
MAPILLARY_TOKEN: str = os.getenv("MAPILLARY_TOKEN", "")

# Fixed seed so the active-user shuffle is stable across pages and reloads.
USER_SHUFFLE_SEED: int = int(os.getenv("USER_SHUFFLE_SEED", "20260715"))
# Users shown per page in the active-user list.
PAGE_SIZE: int = int(os.getenv("PAGE_SIZE", "20"))
