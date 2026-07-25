---
name: build-railway-route-predecessor-matrix
description: >-
  Turn the retrieved 国土数値情報 N02 railway data into a Tokyo rail routing graph and
  precompute all-pairs shortest paths. Reads the N02 UTF-8 GeoJSON from
  DATA/s01_raw/railway_*.zip, filters to a Tokyo bounding box, builds a line-expanded
  (station, line) graph with transfer edges (transfers identified by N02_005g), and
  writes a station table plus M×M distance (float32) and predecessor (int32) matrices
  to DATA/s04_feature/. Use when asked to build/refresh the railway route matrix or
  the data behind get_railway_route.
---

# Build railway route predecessor matrix

Precomputes Tokyo rail routing so that request-time lookups need **no graph search** —
just a nearest-station scan, a distance lookup, and an O(path-length) walk of the
predecessor matrix. Consumed by [web-app/app/tool.py](../../../web-app/app/tool.py)'s
`get_railway_route`. Requires [retrieve-tokyo-railway-data](../retrieve-tokyo-railway-data/SKILL.md)
to have run first.

## What it produces

In `DATA/s04_feature/` (all overwritten each run):

| file | contents |
| --- | --- |
| `railway_stations.tsv` | one row per **ride node** — `ride_idx, group, name, line, lat, lon`. A ride node is a `(station, line)` pair; a physical station (shared `group` = N02_005g) has one ride node per line serving it. |
| `railway_predecessor.bin` | M×M `int32`, row-major `pred[s*M + t]` = the ride node before `t` on the shortest path from `s` (`-1` = self/unreachable). |
| `railway_distance.bin` | M×M `float32`, `dist[s*M + t]` = shortest rail cost (km, incl. transfer penalties); `inf` if unreachable. Needed to pick the best boarding/alighting line at the origin/destination stations. |
| `railway_meta.json` | `m` (ride nodes), `stations`, hop/transfer counts, `transfer_penalty_km`, bbox, source edition, dtypes, timestamp. |

For edition 2025 with the default bbox: **859** logical stations → **1,107** ride
nodes, ~1,023 ride hops + ~382 transfer edges; matrices ~4.9 MB each; build ~1 s.

## How to run it

From the repo root, with the project `.venv`:

```bash
.venv/bin/python pipeline/skills/build-railway-route-predecessor-matrix/scripts/build_matrix.py
```

Dependency-free (standard library only; reads the GeoJSON straight out of the ZIP).

Options:
- `--repo-root <path>` (auto-detected by default)
- `--year <YY>` — pick a specific `railway_*N02-<YY>*.zip` (default: newest `railway_*.zip`)
- `--bbox LON0 LON1 LAT0 LAT1` — Tokyo bounding box (default `139.0 139.93 35.50 35.87`)

## Model (demo-grade — distance-optimal, no timetable)

1. **Nodes are `(station, line)` ride nodes** (a *line-expanded* graph), so the router
   knows which line you are on and a **transfer has a cost**. Physical stations are
   identified by `N02_005g`, so all platforms of a transfer complex are one station.
2. **Ride edges** connect consecutive stations along a line; weight = straight-line km
   between them.
3. **Transfer edges** connect the ride nodes of the same physical station (different
   lines) with a fixed `TRANSFER_PENALTY_KM` (default 1.0 km), so shortest paths
   prefer one-seat rides and only transfer when it pays off.
4. **Ordering a line's stations** (to know which are consecutive): build a graph of the
   line's track polylines (`RailroadSection`), snap each station to the nearest track
   vertex, and sort by shortest-path distance from one terminus (found by a double
   sweep). This is robust to branches and long lines where naive endpoint-chaining
   breaks. Lines with no track geometry in bbox fall back to a nearest-neighbour chain.
5. **All-pairs Dijkstra** over the ride nodes yields the distance + predecessor
   matrices.

## Caveats (acceptable for a demo)

- **No timetable** — routes are distance-optimal, not fastest. Don't label them
  "fastest".
- **Tokyo = a bounding box**, so a few just-outside border stations on Tokyo lines
  (Kawasaki/Saitama/Chiba/Yamanashi edges) may be included — this only helps
  connectivity. Tighten `--bbox` to exclude them.
- **N02 line naming** can surprise: e.g. the east side of the 山手線 loop is tagged
  `東北線` in N02, and some JR lines split names — so a route may name a line you
  wouldn't say colloquially, and occasionally take a 1-transfer detour where a
  through-service exists in reality.
- **Ordering is approximate** on very long/branchy lines; a rare wrong adjacency can
  send a route one stop onto a parallel line. All routes are still valid (they connect
  origin to destination).

## Rebuild triggers

Rerun after `retrieve-tokyo-railway-data` fetches a new N02 edition, or when changing
`--bbox` / `TRANSFER_PENALTY_KM`. The matrices are static (no schedule), so this is a
one-time offline step until the source data changes.
