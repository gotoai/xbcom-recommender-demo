"""Agent tools for the concierge — currently a Tokyo railway route lookup.

Backed by the precomputed artifacts in ``DATA/s04_feature/`` (built offline by the
``build-railway-route-predecessor-matrix`` pipeline skill): a *(station, line)* "ride
node" table plus M×M distance (``float32``) and predecessor (``int32``) matrices over
those ride nodes. Routing at request time is a nearest-station scan + a distance
lookup to pick the best boarding/alighting line + an O(path-length) walk of the
predecessor matrix — no graph search. Standard library only.
"""
from __future__ import annotations

import array
import csv
import json
import math

from config import config

_DATA_DIR = config.REPO_ROOT / "DATA" / "s04_feature"

# Lazy singleton cache of the railway artifacts.
_rail: dict | None = None


def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _load() -> dict:
    """Load and cache the ride-node table + distance/predecessor matrices."""
    global _rail
    if _rail is not None:
        return _rail

    meta = json.loads((_DATA_DIR / "railway_meta.json").read_text(encoding="utf-8"))
    m = int(meta["m"])

    name: list[str] = []
    line: list[str] = []
    group: list[str] = []
    coord: list[tuple[float, float]] = []  # (lon, lat), shared by a group's ride nodes
    with (_DATA_DIR / "railway_stations.tsv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            name.append(row["name"])
            line.append(row["line"])
            group.append(row["group"])
            coord.append((float(row["lon"]), float(row["lat"])))

    # group -> list of ride ids, and one representative coord per group
    group_rides: dict[str, list[int]] = {}
    group_rep: dict[str, tuple[float, float]] = {}
    for rid, g in enumerate(group):
        group_rides.setdefault(g, []).append(rid)
        group_rep.setdefault(g, coord[rid])

    pred = array.array("i")
    pred.frombytes((_DATA_DIR / "railway_predecessor.bin").read_bytes())
    dist = array.array("f")
    dist.frombytes((_DATA_DIR / "railway_distance.bin").read_bytes())
    if len(pred) != m * m or len(dist) != m * m:
        raise RuntimeError(f"matrix size mismatch (m={m}, pred={len(pred)}, dist={len(dist)})")

    _rail = {"m": m, "name": name, "line": line, "group_rides": group_rides,
             "group_rep": group_rep, "groups": list(group_rides), "pred": pred, "dist": dist}
    return _rail


def _nearest_group(r: dict, lon: float, lat: float) -> str:
    rep = r["group_rep"]
    return min(r["groups"], key=lambda g: _haversine_km(rep[g][0], rep[g][1], lon, lat))


def _reconstruct(pred: array.array, m: int, s: int, t: int) -> list[int]:
    """Ride-node path s -> t via the predecessor matrix (s and t assumed connected)."""
    seq = [t]
    cur = t
    while cur != s:
        cur = pred[s * m + cur]
        seq.append(cur)
    seq.reverse()
    return seq


def get_railway_route(latitude1: float, longitude1: float,
                      latitude2: float, longitude2: float) -> str:
    """Find the Tokyo railway route between two geographic points.

    Routes from the station nearest (latitude1, longitude1) to the station nearest
    (latitude2, longitude2) over Tokyo's rail and subway network. Returns 'walking'
    when the two points are close enough that walking beats taking the train;
    otherwise a route string like "新宿 (山手線) -> 神田 (中央線) -> 東京 (中央線)" —
    the origin, each transfer station, and the destination, each annotated with the
    line boarded there (the destination shows the arriving line); or 'no route found'
    if the stations are on disconnected networks. Covers Tokyo only. Call this when the
    traveler asks how to get from one place to another by train, passing the
    coordinates of their current location and of the destination (e.g. a coupon shop).

    Args:
        latitude1: Latitude of the origin point, in WGS84 decimal degrees.
        longitude1: Longitude of the origin point, in WGS84 decimal degrees.
        latitude2: Latitude of the destination point, in WGS84 decimal degrees.
        longitude2: Longitude of the destination point, in WGS84 decimal degrees.

    Returns:
        A route string, 'walking', or 'no route found'.
    """
    r = _load()
    m, name, line = r["m"], r["name"], r["line"]
    dist, pred = r["dist"], r["pred"]

    g1 = _nearest_group(r, longitude1, latitude1)
    g2 = _nearest_group(r, longitude2, latitude2)

    rep = r["group_rep"]
    walk1 = _haversine_km(longitude1, latitude1, rep[g1][0], rep[g1][1])
    walk2 = _haversine_km(longitude2, latitude2, rep[g2][0], rep[g2][1])
    d_pins = _haversine_km(longitude1, latitude1, longitude2, latitude2)
    # Walking beats the train when the direct walk is no farther than the walk needed
    # just to reach both stations (same station -> nothing to ride).
    if g1 == g2 or d_pins <= walk1 + walk2:
        return "walking"

    # Best boarding/alighting line pair: minimise total rail distance between the
    # origin group's ride nodes and the destination group's ride nodes.
    best = math.inf
    src = dst = -1
    for o in r["group_rides"][g1]:
        base = o * m
        for d in r["group_rides"][g2]:
            if dist[base + d] < best:
                best = dist[base + d]
                src, dst = o, d
    if not math.isfinite(best):
        return "no route found"

    path = _reconstruct(pred, m, src, dst)
    # Collapse consecutive same-line ride nodes into legs; a line change (a transfer
    # edge, always within one physical station) starts a new leg.
    tokens: list[str] = []
    start = 0
    for i in range(1, len(path)):
        if line[path[i]] != line[path[i - 1]]:
            tokens.append(f"{name[path[start]]} ({line[path[start]]})")
            start = i
    tokens.append(f"{name[path[start]]} ({line[path[start]]})")
    tokens.append(f"{name[path[-1]]} ({line[path[-1]]})")  # destination, arriving line
    return " -> ".join(tokens)
