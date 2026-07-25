#!/usr/bin/env python3
"""Build a Tokyo railway routing graph + all-pairs predecessor matrix from N02.

Reads the UTF-8 GeoJSON inside the N02 ZIP produced by ``retrieve-tokyo-railway-
data`` (``DATA/s01_raw/railway_*.zip``) and writes, to ``DATA/s04_feature/``:

  * ``railway_stations.tsv``      — one row per logical station (idx, group code,
                                     name, lat, lon, lines).
  * ``railway_edges.tsv``         — station-to-station adjacency (u, v, line,
                                     operator, weight_km); one row per line serving
                                     that hop.
  * ``railway_predecessor.bin``   — N×N ``int32`` predecessor matrix (row-major;
                                     ``pred[s*N + t]`` = the node before ``t`` on the
                                     shortest path from ``s``, or ``-1``).
  * ``railway_meta.json``         — N, source, bbox, edition, edge count, timestamp.

Model (demo-grade, no timetable — shortest path by geographic distance):
  * **Nodes** are *(station, line)* "ride nodes" — a line-expanded graph, so the
    router knows which line you are on and a **transfer has a cost**. Physical
    stations are identified by the 同一駅グループコード ``N02_005g`` (every platform
    of a transfer complex — e.g. all 7 lines at 新宿 — shares one group).
  * **Ride edges** connect consecutive stations along a line (weight = straight-line
    km between them). Ordering a line's stations is done by snapping them onto that
    line's track polylines (``RailroadSection``), then sorting by shortest-path
    distance from one terminus of the track graph (robust to branches / long lines;
    see the skill's SKILL.md).
  * **Transfer edges** connect the ride nodes of the same physical station (different
    lines) with a fixed ``TRANSFER_PENALTY_KM`` cost, so the shortest path prefers
    one-seat rides and only transfers when it genuinely pays off.

The all-pairs Dijkstra yields BOTH a distance and a predecessor matrix (float32 /
int32, M×M over ride nodes); the tool needs the distances to choose the best
boarding/alighting line at the origin and destination stations.

Tokyo is a **bounding-box** filter (default covers the 23 wards + inner Tama); a few
just-outside border stations on Tokyo lines may be included, which only helps
connectivity. Only the Python standard library is used.
"""
from __future__ import annotations

import argparse
import array
import collections
import heapq
import json
import math
import sys
import time
import zipfile
from pathlib import Path

# Default Tokyo-ish bounding box (lon0, lon1, lat0, lat1): 23 wards + inner Tama,
# excludes the Izu/Ogasawara islands. Override with --bbox.
DEFAULT_BBOX = (139.0, 139.93, 35.50, 35.87)
ROUND = 5  # vertex coordinate rounding (~1 m) for track-graph node identity
TRANSFER_PENALTY_KM = 1.0  # cost of one line change; keeps routes on one-seat rides


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "docs" / "profiles").is_dir() and (p / "pipeline").is_dir():
            return p
    raise SystemExit("Could not locate repo root (docs/profiles + pipeline not found).")


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle km between (lon, lat) points a and b."""
    r = 6371.0088
    p1, p2 = math.radians(a[1]), math.radians(b[1])
    dp = math.radians(b[1] - a[1])
    dl = math.radians(b[0] - a[0])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _midpoint(coords: list) -> tuple[float, float]:
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _load_geojson_from_zip(zip_path: Path) -> tuple[dict, dict]:
    """Return (stations, sections) GeoJSON dicts from the ZIP's UTF-8 members."""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()

        def pick(suffix: str) -> str:
            hits = [n for n in names if n.endswith(suffix) and "UTF-8" in n]
            if not hits:
                raise SystemExit(f"{zip_path.name}: no UTF-8 member ending {suffix}")
            return hits[0]

        st = json.loads(zf.read(pick("_Station.geojson")).decode("utf-8"))
        rs = json.loads(zf.read(pick("_RailroadSection.geojson")).decode("utf-8"))
    return st, rs


def _dijkstra(adj: dict, src, want_pred: bool = False):
    """Shortest paths from src over adjacency {node: [(nbr, w), ...]}."""
    dist = {src: 0.0}
    pred: dict = {src: None}
    pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, math.inf):
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                if want_pred:
                    pred[v] = u
                heapq.heappush(pq, (nd, v))
    return (dist, pred) if want_pred else dist


def _order_line_stations(sections: list, records: list) -> list:
    """Order a line's station *records* along its track.

    ``sections`` = list of coordinate arrays (the line's RailroadSection polylines in
    bbox). ``records`` = list of (group, name, (lon,lat)) for that line's stations in
    bbox. Returns the records sorted along the line (see module docstring); falls back
    to a nearest-neighbour chain when the line has no track geometry in bbox.
    """
    key = lambda p: (round(p[0], ROUND), round(p[1], ROUND))
    if sections:
        adj: dict = collections.defaultdict(list)
        for s in sections:
            for a, b in zip(s, s[1:]):
                ka, kb, w = key(a), key(b), haversine_km(tuple(a), tuple(b))
                adj[ka].append((kb, w))
                adj[kb].append((ka, w))
        verts = list(adj)
        snap = [min(verts, key=lambda v: haversine_km(v, pt))
                for (_g, _n, pt) in records]
        # double sweep: farthest station from an arbitrary one is a terminus (e1);
        # order all stations by track distance from e1.
        d0 = _dijkstra(adj, snap[0])
        e1 = max(snap, key=lambda v: d0.get(v, -1.0))
        d1 = _dijkstra(adj, e1)
        order = sorted(range(len(records)), key=lambda i: d1.get(snap[i], math.inf))
        return [records[i] for i in order]
    # fallback: greedy nearest-neighbour chain from the westernmost station
    remaining = list(records)
    chain = [min(remaining, key=lambda r: r[2][0])]
    remaining.remove(chain[0])
    while remaining:
        last = chain[-1][2]
        nxt = min(remaining, key=lambda r: haversine_km(last, r[2]))
        chain.append(nxt)
        remaining.remove(nxt)
    return chain


def build(zip_path: Path, bbox: tuple, out_dir: Path, year: str) -> None:
    lon0, lon1, lat0, lat1 = bbox
    in_bb = lambda lon, lat: lon0 <= lon <= lon1 and lat0 <= lat <= lat1

    print(f"Reading {zip_path.name} ...")
    st, rs = _load_geojson_from_zip(zip_path)

    # --- station records in bbox, grouped into logical stations by N02_005g -------
    # group -> {"name":.., "pts":[(lon,lat)..], "lines":set()}
    groups: dict = {}
    # (operator, line) -> list of (group, name, (lon,lat))
    line_records: dict = collections.defaultdict(list)
    for f in st["features"]:
        pt = _midpoint(f["geometry"]["coordinates"])
        if not in_bb(*pt):
            continue
        p = f["properties"]
        g, name, line, op = p["N02_005g"], p["N02_005"], p["N02_003"], p["N02_004"]
        gr = groups.setdefault(g, {"name": name, "pts": [], "lines": set()})
        gr["pts"].append(pt)
        gr["lines"].add(line)
        line_records[(op, line)].append((g, name, pt))

    node_ids = sorted(groups)
    idx = {g: i for i, g in enumerate(node_ids)}
    n = len(node_ids)
    reps = [(_midpoint(groups[g]["pts"])) for g in node_ids]  # representative (lon,lat)
    print(f"  {n} logical stations in bbox (from {sum(len(v) for v in line_records.values())} records)")

    # --- sections in bbox, keyed by (operator, line) ------------------------------
    line_sections: dict = collections.defaultdict(list)
    for f in rs["features"]:
        coords = f["geometry"]["coordinates"]
        if in_bb(*_midpoint(coords)):
            p = f["properties"]
            line_sections[(p["N02_004"], p["N02_003"])].append(coords)

    reps_by_group = {g: reps[i] for i, g in enumerate(node_ids)}

    # --- line-expanded ride nodes: one node per (group, line) ----------------------
    ride_idx: dict = {}          # (group, line) -> ride id
    r_group: list = []           # ride id -> group code
    r_line: list = []            # ride id -> line name
    adj_w: dict = collections.defaultdict(dict)

    def ride(g: str, line: str) -> int:
        key = (g, line)
        rid = ride_idx.get(key)
        if rid is None:
            rid = ride_idx[key] = len(r_group)
            r_group.append(g)
            r_line.append(line)
        return rid

    def link(a: int, b: int, w: float) -> None:
        if b not in adj_w[a] or w < adj_w[a][b]:
            adj_w[a][b] = w
            adj_w[b][a] = w

    # ride edges: consecutive stations along each line
    hops = 0
    for (op, line), records in line_records.items():
        ordered = _order_line_stations(line_sections.get((op, line), []), records)
        seq: list = []  # collapse consecutive same-group
        for g, _name, _pt in ordered:
            if not seq or seq[-1] != g:
                seq.append(g)
        for ga, gb in zip(seq, seq[1:]):
            link(ride(ga, line), ride(gb, line),
                 haversine_km(reps_by_group[ga], reps_by_group[gb]))
            hops += 1

    # transfer edges: between the ride nodes of the same physical station
    group_rides: dict = collections.defaultdict(list)
    for (g, _line), rid in ride_idx.items():
        group_rides[g].append(rid)
    transfers = 0
    for rids in group_rides.values():
        for i in range(len(rids)):
            for j in range(i + 1, len(rids)):
                link(rids[i], rids[j], TRANSFER_PENALTY_KM)
                transfers += 1

    m = len(r_group)
    adj = {u: list(nbrs.items()) for u, nbrs in adj_w.items()}
    for u in range(m):
        adj.setdefault(u, [])
    print(f"  {m} ride nodes; {hops} ride hops + {transfers} transfer edges")

    # --- all-pairs Dijkstra -> distance + predecessor matrices --------------------
    print(f"  computing all-pairs shortest paths ({m} sources) ...")
    dist = array.array("f", [math.inf]) * m * m  # dist[s*m + t]
    pred = array.array("i", [-1]) * m * m         # pred[s*m + t]; -1 = self/unreachable
    t0 = time.time()
    for s in range(m):
        d, p = _dijkstra(adj, s, want_pred=True)
        base = s * m
        for t, dd in d.items():
            dist[base + t] = dd
        for t, prev in p.items():
            if prev is not None:
                pred[base + t] = prev
    print(f"  APSP done in {time.time() - t0:.1f}s")

    # --- write outputs ------------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "railway_stations.tsv").open("w", encoding="utf-8") as fh:
        fh.write("ride_idx\tgroup\tname\tline\tlat\tlon\n")
        for rid in range(m):
            g = r_group[rid]
            lon, lat = reps_by_group[g]
            fh.write(f"{rid}\t{g}\t{groups[g]['name']}\t{r_line[rid]}\t{lat:.6f}\t{lon:.6f}\n")
    (out_dir / "railway_predecessor.bin").write_bytes(pred.tobytes())
    (out_dir / "railway_distance.bin").write_bytes(dist.tobytes())
    meta = {
        "m": m, "stations": n, "ride_hops": hops, "transfer_edges": transfers,
        "transfer_penalty_km": TRANSFER_PENALTY_KM,
        "source": zip_path.name, "edition": year, "bbox": list(bbox),
        "pred_dtype": "int32", "dist_dtype": "float32", "layout": "row-major [s*m+t]",
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "note": "demo rail graph; distance-optimal, no timetable; line-expanded ride "
                "nodes; transfers via N02_005g cost transfer_penalty_km.",
    }
    (out_dir / "railway_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [OK] wrote stations/predecessor/distance/meta ({m} ride nodes) -> {out_dir}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--year", default=None,
                    help="N02 edition to locate the ZIP (default: newest railway_*.zip).")
    ap.add_argument("--bbox", type=float, nargs=4, default=DEFAULT_BBOX,
                    metavar=("LON0", "LON1", "LAT0", "LAT1"),
                    help=f"Tokyo bounding box (default: {DEFAULT_BBOX}).")
    args = ap.parse_args()

    repo_root = args.repo_root or find_repo_root(Path(__file__).resolve())
    raw_dir = repo_root / "DATA" / "s01_raw"
    pattern = f"railway_*N02-{args.year}*.zip" if args.year else "railway_*.zip"
    zips = sorted(raw_dir.glob(pattern))
    if not zips:
        print(f"  [SKIP] no {pattern} in {raw_dir} — run retrieve-tokyo-railway-data first")
        return 1
    zip_path = zips[-1]
    year = args.year or "".join(ch for ch in zip_path.stem if ch.isdigit())[-2:]

    build(zip_path, tuple(args.bbox), repo_root / "DATA" / "s04_feature", year)
    return 0


if __name__ == "__main__":
    sys.exit(main())
