#!/usr/bin/env python3
"""Synthesize the demo's inbound traveler population.

Reads the scenario distributions from ``docs/scenarios/travelers.md`` (the source
of truth), allocates travelers per nationality, draws an age and a Japan-visit
count for each, and writes ``DATA/s03_primary/inbound_traveler.tsv``.

Every traveler is assumed to be in Japan for the whole of the same one-week
window (docs/scenarios/travelers.md 「滞在期間」), so no arrival/departure dates
are modelled here.

Inputs
  * ``docs/scenarios/travelers.md``  - 「国籍・地域別 滞在人数」 and 「年齢層分布」
  * ``docs/profiles/users.md``       - the supported 国・地域 list (validation only)
  * ``pipeline/config/config.yaml``  - ``synthetics/random_seed`` and
                                       ``synthetics/inbound_travelers/*``

Output (overwritten each run)
  * ``DATA/s03_primary/inbound_traveler.tsv`` with columns:
    traveler_id, nationality, gender, birthyear, repeating_times

Dependencies: PyYAML (config) -- see ``requirements.txt``.
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from pathlib import Path

import yaml

# --- これまでの訪日回数 (%) -----------------------------------------------------
# 東京都「令和6年 国・地域別外国人旅行者行動特性調査」図表4. Buckets are
# (1回目, 2回目, 3回目, 4～9回, 10回以上, 無回答); 無回答 is redistributed over the
# five real buckets at load time. Only the 21 breakouts the survey publishes are
# listed -- everything else resolves through VISIT_PROXY below.
VISIT_COUNT_PCT = {
    "韓国":         (17.7, 21.8, 15.6, 28.8, 14.0, 2.1),
    "台湾":         ( 9.0, 12.9, 12.0, 36.0, 25.2, 4.9),
    "香港":         ( 8.5,  8.8,  9.7, 32.9, 33.3, 6.8),
    "中国":         (38.2, 20.2, 12.2, 19.4,  7.0, 3.0),
    "タイ":         (18.9, 15.2, 12.6, 32.2, 16.5, 4.6),
    "シンガポール":  (21.2, 22.7, 13.9, 27.7, 13.6, 1.0),
    "マレーシア":    (47.9, 20.6, 11.5, 13.9,  4.8, 1.2),
    "米国":         (60.8, 16.1,  7.1,  8.6,  5.5, 1.9),
    "カナダ":       (53.4, 18.7,  8.0, 10.7,  7.3, 1.9),
    "英国":         (63.7, 14.9,  6.0,  9.3,  4.8, 1.2),
    "ドイツ":       (62.5, 19.5,  4.4,  6.6,  6.3, 0.7),
    "フランス":      (65.4, 12.3,  5.2,  8.0,  6.2, 2.8),
    "イタリア":      (65.7, 15.2,  3.0,  6.1,  6.6, 3.3),
    "スペイン":      (75.7, 15.6,  2.3,  2.3,  2.9, 1.2),
    "オーストラリア": (54.2, 20.0,  7.1, 10.2,  6.4, 2.1),
    "インド":       (61.9, 14.8,  4.0, 11.4,  4.0, 4.0),
    "インドネシア":  (41.9, 22.7, 11.6, 15.9,  6.2, 1.6),
    "フィリピン":    (41.1, 20.4,  9.9, 19.0,  5.0, 4.7),
    "ベトナム":      (48.3, 20.5,  7.9, 10.6,  5.3, 7.3),
    "その他":       (67.2, 14.8,  5.4,  7.0,  3.4, 2.3),
}
# 図表4 response counts, used to weight the European proxy average.
VISIT_COUNT_N = {"英国": 248, "ドイツ": 272, "フランス": 324, "イタリア": 361, "スペイン": 173}

# Markets the survey does not break out -> the series to borrow. Mirrors the
# proxy rules already documented in docs/scenarios/travelers.md 「注記・前提」.
VISIT_PROXY = {
    "豪州": "オーストラリア",
    "ニュージーランド": "オーストラリア",
    "メキシコ": "その他", "イスラエル": "その他", "トルコ": "その他",
    "サウジアラビア": "その他", "アラブ首長国連邦": "その他", "バーレーン": "その他",
    "オマーン": "その他", "カタール": "その他", "クウェート": "その他",
}
# These borrow a response-count-weighted average of the five European breakouts.
EU_PROXY = ["オランダ", "ベルギー", "スイス", "スウェーデン", "デンマーク",
            "ノルウェー", "フィンランド"]


def parse_nationalities(md: str) -> dict[str, int]:
    """Read 「### 国籍・地域別 滞在人数」 -> {nationality: headcount}."""
    section = _section(md, "### 国籍・地域別 滞在人数")
    out: dict[str, int] = {}
    for name, num in re.findall(r"^\|\s*([^|*\s][^|]*?)\s*\|\s*([\d,]+)\s*\|", section, re.M):
        name = name.strip()
        if "合計" in name:
            continue
        out[name] = int(num.replace(",", ""))
    if not out:
        raise SystemExit("No nationality rows parsed from travelers.md")
    return out


def parse_age_bands(md: str) -> list[tuple[int, int, float]]:
    """Read 「## 年齢層分布」 -> [(lo, hi, weight), ...]."""
    section = _section(md, "## 年齢層分布")
    bands = [(int(lo), int(hi), float(pct))
             for lo, hi, pct in re.findall(r"^-\s*(\d+)-(\d+)歳:\s*([\d.]+)%", section, re.M)]
    if not bands:
        raise SystemExit("No age bands parsed from travelers.md")
    return bands


def _section(md: str, heading: str) -> str:
    """Text from `heading` up to the next heading of the same or higher level."""
    i = md.find(heading)
    if i < 0:
        raise SystemExit(f"Heading not found in travelers.md: {heading}")
    start = i + len(heading)
    depth = len(heading) - len(heading.lstrip("#"))
    nxt = re.search(rf"^#{{1,{depth}}}\s", md[start:], re.M)
    return md[start:start + nxt.start()] if nxt else md[start:]


def build_visit_table() -> dict[str, list[float]]:
    """nationality -> 5 cumulative bucket weights, 無回答 redistributed."""
    def norm(pcts):
        real = pcts[:5]                       # drop 無回答
        s = sum(real)
        return [p / s for p in real]

    table = {k: norm(v) for k, v in VISIT_COUNT_PCT.items()}
    n_tot = sum(VISIT_COUNT_N.values())
    eu = [sum(table[c][i] * VISIT_COUNT_N[c] for c in VISIT_COUNT_N) / n_tot
          for i in range(5)]
    for c in EU_PROXY:
        table[c] = eu
    for src, dst in VISIT_PROXY.items():
        table[src] = table[dst]
    return table


def draw_repeating_times(rng: random.Random, w: list[float],
                         tail_mean: float, cap: int) -> int:
    """Bucket -> repeating_times (= 訪日回数 - 1, so 0 == first visit)."""
    r, acc = rng.random(), 0.0
    for i, p in enumerate(w):
        acc += p
        if r < acc:
            if i <= 2:
                return i                       # 1回目/2回目/3回目 -> 0/1/2
            if i == 3:
                return rng.randint(3, 8)       # 4～9回目
            # 10回以上: open-ended bucket, modelled as a capped exponential tail.
            return min(9 + int(rng.expovariate(1.0 / tail_mean)), cap)
    return 0


# gender codes written to the TSV: F = female, M = male, '-' = unknown / not input.
GENDER_CODES = {"F": "F", "M": "M", "unknown": "-"}


def draw_gender(rng: random.Random, weights: dict) -> str:
    """Draw a gender code ('F' / 'M' / '-') from the configured weights."""
    keys = ["F", "M", "unknown"]
    w = [float(weights.get(k, 0)) for k in keys]
    if sum(w) <= 0:
        raise SystemExit("gender_weights must have a positive total")
    return GENDER_CODES[rng.choices(keys, weights=w, k=1)[0]]


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "docs" / "scenarios").is_dir() and (p / "pipeline").is_dir():
            return p
    raise SystemExit("Could not locate repo root (docs/scenarios + pipeline not found).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args()

    root = args.repo_root or find_repo_root(Path(__file__).resolve())
    cfg = yaml.safe_load((args.config or root / "pipeline" / "config" / "config.yaml")
                         .read_text(encoding="utf-8"))
    syn = cfg["synthetics"]
    opts = syn["inbound_travelers"]
    rng = random.Random(syn["random_seed"])
    ref_year = int(opts["reference_year"])

    md = (root / "docs" / "scenarios" / "travelers.md").read_text(encoding="utf-8")
    counts = parse_nationalities(md)
    bands = parse_age_bands(md)
    visits = build_visit_table()

    # Validate against the markets users.md says the app supports.
    users_md = (root / "docs" / "profiles" / "users.md").read_text(encoding="utf-8")
    supported = set(re.findall(r"^-\s*(\S+)\s*$", _section(users_md, "## 対象国・地域"), re.M))
    for nat in counts:
        if supported and nat not in supported:
            print(f"  [WARN] {nat}: in travelers.md but not in users.md 対象国・地域")
        if nat not in visits:
            raise SystemExit(f"No 訪日回数 series or proxy for {nat}")

    band_w = [b[2] for b in bands]
    rows = []
    for nat in sorted(counts):
        for _ in range(counts[nat]):
            lo, hi, _ = rng.choices(bands, weights=band_w, k=1)[0]
            age = rng.randint(lo, hi)
            rows.append([nat, ref_year - age,
                         draw_repeating_times(rng, visits[nat],
                                              float(opts["repeat_tail_mean"]),
                                              int(opts["repeat_max"]))])

    rng.shuffle(rows)                     # so traveler_id order is not by nationality

    # gender is drawn last, after the shuffle, so it does not perturb the RNG stream
    # that produced nationality/birthyear/repeating_times above -- adding the column
    # leaves those values unchanged for a given seed.
    gender_w = opts.get("gender_weights", {"F": 1, "M": 1, "unknown": 1})
    genders = [draw_gender(rng, gender_w) for _ in rows]

    out = root / "DATA" / "s03_primary" / "inbound_traveler.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["traveler_id", "nationality", "gender", "birthyear", "repeating_times"])
        for i, (r, g) in enumerate(zip(rows, genders), 1):
            nat, birthyear, repeating = r
            w.writerow([i, nat, g, birthyear, repeating])

    first = sum(1 for r in rows if r[2] == 0)
    gcount = {code: genders.count(code) for code in ("F", "M", "-")}
    print(f"  [OK]   {len(rows):,} travelers across {len(counts)} nationalities "
          f"-> {out.relative_to(root)}")
    print(f"         seed={syn['random_seed']}  reference_year={ref_year}  "
          f"first-time visitors={first/len(rows)*100:.1f}%")
    print(f"         gender F/M/-: {gcount['F']}/{gcount['M']}/{gcount['-']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
