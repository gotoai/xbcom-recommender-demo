#!/usr/bin/env python3
"""Generate placeholder product thumbnails, one per sub-category.

Stand-ins for real generated imagery, so the web app has something to render
before any image-generation spend. Each is a flat light-sky-blue card printed with
the sub-category's English category and name.

One image per **sub-category** (117), not per product (6,000): the placeholders
carry no product-specific information, so a per-product copy would be 6,000
identical files.

Inputs
  * ``docs/profiles/shops.md`` - the category tree (parsed live)

Output (overwritten each run)
  * ``assets/images/<category>_<subcategory>.png`` - 1024x1024, e.g.
    ``assets/images/レストラン_寿司・海鮮.png``

Note ``assets/`` is NOT gitignored (unlike ``DATA/``), so these are committed —
which is the point: the demo should render without running the pipeline.

Dependencies: Pillow -- see ``requirements.txt``.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from category_names import CATEGORY_EN, SUBCATEGORY_EN  # noqa: E402

SIZE = (1024, 1024)
BG = (135, 206, 250)          # CSS lightskyblue #87CEFA
BORDER = (255, 255, 255)
CATEGORY_FG = (40, 79, 107)   # muted slate blue
SUBCATEGORY_FG = (12, 42, 66)  # near-navy
MARGIN = 64

FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
]


def load_fonts():
    for bold, regular in FONT_CANDIDATES:
        if Path(bold).exists() and Path(regular).exists():
            return bold, regular
    raise SystemExit("No usable TTF found; install fonts-dejavu or fonts-liberation.")


def parse_categories(md: str) -> dict[str, list[str]]:
    """{category: [subcategory, ...]} from docs/profiles/shops.md."""
    heading = "## 対象店舗カテゴリ"
    i = md.find(heading)
    if i < 0:
        raise SystemExit(f"Heading not found in shops.md: {heading}")
    start = i + len(heading)
    nxt = re.search(r"^##\s", md[start:], re.M)
    section = md[start:start + nxt.start()] if nxt else md[start:]
    cats: dict[str, list[str]] = {}
    cur = None
    for line in section.splitlines():
        if m := re.match(r"^-\s+(\S.*?)\s*$", line):
            cur = m.group(1)
            cats[cur] = []
        elif (m := re.match(r"^\s{2,}-\s+(\S.*?)\s*$", line)) and cur:
            cats[cur].append(m.group(1))
    cats = {k: v for k, v in cats.items() if v}
    if not cats:
        raise SystemExit("Failed to parse categories from shops.md")
    return cats


def wrap(draw, text: str, font, max_w: int) -> list[str]:
    """Greedy word wrap to `max_w` pixels."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_font(draw, text: str, path: str, max_w: int, max_h: int,
             start: int, min_size: int = 24):
    """Largest size at which `text` wraps inside (max_w, max_h)."""
    for size in range(start, min_size - 1, -2):
        font = ImageFont.truetype(path, size)
        lines = wrap(draw, text, font, max_w)
        line_h = int(size * 1.25)
        if len(lines) * line_h <= max_h:
            return font, lines, line_h
    font = ImageFont.truetype(path, min_size)
    return font, wrap(draw, text, font, max_w), int(min_size * 1.25)


def render(category_en: str, subcategory_en: str, bold: str, regular: str) -> Image.Image:
    img = Image.new("RGB", SIZE, BG)
    d = ImageDraw.Draw(img)
    d.rectangle([MARGIN // 2, MARGIN // 2, SIZE[0] - MARGIN // 2, SIZE[1] - MARGIN // 2],
                outline=BORDER, width=6)

    inner_w = SIZE[0] - 2 * MARGIN
    # Category: smaller, upper third.
    cat_font, cat_lines, cat_lh = fit_font(d, category_en.upper(), regular,
                                           inner_w, 200, 56)
    # Subcategory: the headline.
    sub_font, sub_lines, sub_lh = fit_font(d, subcategory_en, bold,
                                           inner_w, 460, 104)

    cat_h, sub_h = len(cat_lines) * cat_lh, len(sub_lines) * sub_lh
    gap = 48
    y = (SIZE[1] - (cat_h + gap + sub_h)) // 2

    for line in cat_lines:
        w = d.textlength(line, font=cat_font)
        d.text(((SIZE[0] - w) / 2, y), line, font=cat_font, fill=CATEGORY_FG)
        y += cat_lh
    y += gap
    for line in sub_lines:
        w = d.textlength(line, font=sub_font)
        d.text(((SIZE[0] - w) / 2, y), line, font=sub_font, fill=SUBCATEGORY_FG)
        y += sub_lh
    return img


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "docs" / "profiles").is_dir() and (p / "pipeline").is_dir():
            return p
    raise SystemExit("Could not locate repo root (docs/profiles + pipeline not found).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="Default: <repo>/assets/images")
    args = ap.parse_args()

    root = args.repo_root or find_repo_root(Path(__file__).resolve())
    out_dir = args.out_dir or root / "assets" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    bold, regular = load_fonts()

    cats = parse_categories((root / "docs" / "profiles" / "shops.md")
                            .read_text(encoding="utf-8"))

    missing_cat = [c for c in cats if c not in CATEGORY_EN]
    missing_sub = [(c, s) for c, subs in cats.items() for s in subs
                   if (c, s) not in SUBCATEGORY_EN]
    if missing_cat or missing_sub:
        raise SystemExit(f"category_names is missing {len(missing_cat)} categories "
                         f"{missing_cat[:3]} and {len(missing_sub)} subcategories "
                         f"{missing_sub[:3]}")

    n = 0
    for cat, subs in cats.items():
        for sub in subs:
            img = render(CATEGORY_EN[cat], SUBCATEGORY_EN[(cat, sub)], bold, regular)
            # 「/」 would open a directory; nothing in the taxonomy has one today,
            # but a sub-category could gain one.
            name = f"{cat}_{sub}".replace("/", "_")
            img.save(out_dir / f"{name}.png")
            n += 1

    print(f"  [OK]   {n} placeholder images ({len(cats)} categories) "
          f"-> {out_dir.relative_to(root)}/")
    print(f"         {SIZE[0]}x{SIZE[1]}  bg=#{BG[0]:02X}{BG[1]:02X}{BG[2]:02X} "
          f"(lightskyblue)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
