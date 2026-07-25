"""Agent tool: fetch a street-level photo near a coordinate from Mapillary.

The concierge is a text LLM; this tool does the fetching and hands back a plain photo
URL that the model can embed in its HTML reply. It queries the Mapillary v4 Graph API
for images in a small bounding box around the pin, picks the one physically nearest the
pin (tie-broken by most-recently captured), and returns that image's ``thumb_1024_url``.

It returns a ``dict`` with a small ``thumbnail_url`` (to show inline) and a larger
``photo_url`` (to link the thumbnail to). Mapillary imagery is crowdsourced, so many
points have no nearby photo — the tool then returns an empty dict ``{}`` (the ``@tool``
result type must be JSON-serializable, so it returns ``dict``, not ``Optional``). It
needs ``MAPILLARY_TOKEN`` in the environment (see ``config``); with no token it is a
no-op that returns ``{}``. Mapillary thumb URLs are short-lived signed CDN links, so the
returned URLs are meant for prompt display, not durable storage.

Mapillary imagery is licensed CC-BY-SA: whoever shows the photo must credit Mapillary
and its contributors.
"""
from __future__ import annotations

import logging
import math

import httpx

from config import config

log = logging.getLogger(__name__)

_IMAGES_URL = "https://graph.mapillary.com/images"
# Half-side of the search box around the pin, in metres. Start wide enough to still find
# a photo where coverage is sparse; a too-dense city box makes Mapillary reply "reduce
# the amount of data" (a misleading HTTP 500), so we shrink and retry (see _DECAY).
_SEARCH_RADIUS_M = 250.0
_MIN_RADIUS_M = 30.0  # stop shrinking below this; give up if still too dense
_DECAY = 0.5  # multiply the radius by this on each density-500 retry
_LIMIT = 50  # max images to rank from the bbox
_TIMEOUT_S = 20.0


def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _bbox(lat: float, lon: float, radius_m: float) -> str:
    """A "minLon,minLat,maxLon,maxLat" box of half-side ``radius_m`` around the point."""
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))
    return f"{lon - dlon},{lat - dlat},{lon + dlon},{lat + dlat}"


def get_streetview_photo(latitude: float, longitude: float) -> dict:
    """Find a street-level photo taken near a geographic point.

    Searches Mapillary's crowdsourced street imagery within a small area around
    (latitude, longitude) and returns URLs for the photo taken nearest that point (the
    most recently captured one when several are equally close). Use this when the
    traveler asks what a place looks like — the area around their current location, a
    coupon shop, or a station — passing the coordinates of that place. Coverage is
    uneven, so this often finds nothing for a given point.

    Args:
        latitude: Latitude of the point, in WGS84 decimal degrees.
        longitude: Longitude of the point, in WGS84 decimal degrees.

    Returns:
        A dict with two URL strings — ``thumbnail_url`` (a small image to show inline)
        and ``photo_url`` (a larger version to link the thumbnail to) — or an empty dict
        ``{}`` if no photo is available near the point (or the tool is not configured).
    """
    token = config.MAPILLARY_TOKEN
    if not token:
        log.warning("get_streetview_photo: MAPILLARY_TOKEN not set; returning nothing")
        return {}

    # Query the bbox, shrinking it whenever Mapillary says the area is too dense (its
    # "reduce the amount of data" 500). A sparse point just succeeds at the first radius.
    images: list | None = None
    radius = _SEARCH_RADIUS_M
    while radius >= _MIN_RADIUS_M:
        params = {
            "fields": "id,computed_geometry,captured_at,thumb_256_url,thumb_1024_url",
            "bbox": _bbox(latitude, longitude, radius),
            "limit": _LIMIT,
            "access_token": token,
        }
        try:
            resp = httpx.get(_IMAGES_URL, params=params, timeout=_TIMEOUT_S)
        except httpx.HTTPError as exc:  # network/timeout
            log.warning("get_streetview_photo: Mapillary request failed: %s", exc)
            return {}
        if resp.status_code == 500:  # too-dense bbox — shrink and retry
            radius *= _DECAY
            continue
        try:
            resp.raise_for_status()
            images = resp.json().get("data", [])
        except (httpx.HTTPError, ValueError) as exc:  # other HTTP or bad JSON
            log.warning("get_streetview_photo: Mapillary request failed: %s", exc)
            return {}
        break
    if images is None:
        log.warning("get_streetview_photo: area too dense even at %.0f m near "
                    "(%.5f, %.5f)", _MIN_RADIUS_M, latitude, longitude)
        return {}

    best: dict = {}
    best_key = (math.inf, -math.inf)  # (distance_km asc, captured_at desc)
    for img in images:
        thumb = img.get("thumb_256_url")
        full = img.get("thumb_1024_url")
        geom = (img.get("computed_geometry") or {}).get("coordinates")
        if not thumb or not full or not geom:
            continue
        ilon, ilat = geom[0], geom[1]
        dist = _haversine_km(longitude, latitude, ilon, ilat)
        # Nearest wins; among equally near, prefer the most recent capture.
        key = (dist, -float(img.get("captured_at") or 0))
        if key < best_key:
            best_key = key
            best = {"thumbnail_url": thumb, "photo_url": full}

    return best
