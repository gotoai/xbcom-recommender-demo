"""Concierge-agent wiring for the coupon chats (reco-list + coupon-detail panels).

The oumigo manager + worker are assumed to be **already running somewhere** (started
out of band); we merely *attach* to the manager with ``oumigo_get_or_create_manager()``
— on a LAN with a live manager advertising, this reuses it (nothing is spawned) — and
build a single agent from it.

Each chat turn rehydrates an ephemeral ``OumigoChat`` from a server-held history and
calls ``chat.request(message)`` (the stateless-server pattern: *store the history, not
the Chat*). The **system message** is server-owned and rebuilt per turn from three
grounding sources:

  1. a formatting directive (reply in a safe HTML fragment, no Markdown/LaTeX);
  2. the coupon Q&A knowledge book (``docs/q&a/coupon_q&a.md``);
  3. the current traveler's profile, distilled from ``DATA/s04_feature/
     traveler_signal.tsv`` (nationality / gender / age / repeat visits + shopping
     affinities).

The Q&A book and the signal index are read once and cached.
"""
from __future__ import annotations

import functools
import logging
import threading
from typing import Any

from oumigo import oumigo_get_or_create_manager

from config import config

from .tools.railway_route import get_railway_route
from .tools.streetview_photo import get_streetview_photo

log = logging.getLogger(__name__)

_QA_PATH = config.REPO_ROOT / "docs" / "q&a" / "coupon_q&a.md"
_SIGNAL_PATH = config.REPO_ROOT / "DATA" / "s04_feature" / "traveler_signal.tsv"

# The agent is built lazily on first use (attaching to the manager can block while it
# discovers the LAN), then cached. ``_lock`` guards the one-time build.
_lock = threading.Lock()
_agent: Any = None

# session_key -> conversation history (list of {"role", "content"} dicts). In-memory
# and process-local — good enough for the demo; a durable/keyed store comes later.
_histories: dict[str, list[dict[str, Any]]] = {}


def _get_agent() -> Any:
    """Attach to the running manager once and build the concierge agent."""
    global _agent
    if _agent is None:
        with _lock:
            if _agent is None:
                manager = oumigo_get_or_create_manager()
                _agent = manager.create_agent(
                    tools=[get_railway_route, get_streetview_photo])
    return _agent


@functools.lru_cache(maxsize=1)
def _qa_book() -> str:
    """The coupon Q&A knowledge book (markdown), read once."""
    try:
        return _QA_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        log.warning("Q&A knowledge book not found at %s", _QA_PATH)
        return ""


@functools.lru_cache(maxsize=1)
def _signals() -> dict[int, dict[str, Any]]:
    """Parse ``traveler_signal.tsv`` once into ``{traveler_id: profile}``.

    The file is long/narrow — one row per (traveler, signal). Scalar signals
    (nationality/gender/age/repeating_times) map to a single value; the repeated
    ``propensity`` rows accumulate into a list of ``[category, subcategory, n, score]``.
    """
    index: dict[int, dict[str, Any]] = {}
    try:
        lines = _SIGNAL_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        log.warning("traveler signals not found at %s", _SIGNAL_PATH)
        return index
    for row in lines[1:]:  # skip header
        parts = row.split("\t")
        if len(parts) < 2:
            continue
        try:
            tid = int(parts[0])
        except ValueError:
            continue
        name = parts[1]
        vals = (parts[2:] + ["", "", "", ""])[:4]
        prof = index.setdefault(tid, {"propensity": []})
        if name == "propensity":
            prof["propensity"].append(vals)
        else:
            prof[name] = vals[0]
    return index


def _profile_text(traveler_id: int) -> str:
    """A short, readable profile for ``traveler_id`` (for the system message)."""
    prof = _signals().get(traveler_id)
    if not prof:
        return "(no profile on file for this traveler)"

    def show(v: str) -> str:
        return v if v and v != "-" else "(unspecified)"

    lines = [
        f"- Nationality: {show(prof.get('nationality', ''))}",
        f"- Gender: {show(prof.get('gender', ''))}",
        f"- Age: {show(prof.get('age', ''))}",
        f"- Repeat visits to Japan: {show(prof.get('repeating_times', ''))}",
    ]

    def score(p: list[str]) -> float:
        try:
            return float(p[3])
        except (ValueError, IndexError):
            return 0.0

    props = sorted(prof.get("propensity", []), key=score, reverse=True)
    if props:
        lines.append("- Shopping affinities (category / subcategory, strongest first):")
        lines += [f"  * {p[0]} / {p[1]} ({p[3]})" for p in props]
    return "\n".join(lines)


def _directions_block(origin: tuple[float, float] | None,
                      destination: tuple[float, float] | None) -> str:
    """Location facts + railway-tool guidance, appended to the system prompt.

    ``origin`` is the traveler's current (lat, lon); ``destination`` (coupon-detail
    chat only) is the coupon shop's (lat, lon). The model has no coordinates otherwise,
    so these are what let it call ``get_railway_route``.
    """
    lines: list[str] = []
    if origin:
        lines.append(f"- Traveler's current location: latitude {origin[0]:.6f}, "
                     f"longitude {origin[1]:.6f}.")
    if destination:
        lines.append(f"- This coupon's shop location: latitude {destination[0]:.6f}, "
                     f"longitude {destination[1]:.6f}.")
    if not lines:
        return ""
    return (
        "\n\nLOCATION & DIRECTIONS:\n" + "\n".join(lines) + "\n"
        "- For any question about how to travel between places by train, call the "
        "get_railway_route tool with the relevant coordinates above (or coordinates the "
        "traveler gives) instead of guessing the route. It covers Tokyo rail only; never "
        "invent train times, fares, or platforms. If you need a location you don't have, "
        "ask the traveler.\n"
        "- When the traveler asks what the street or scenery around a place looks like, "
        "first ask whether they would like to see a street photo; only if they say yes, "
        "call the get_streetview_photo tool with that place's coordinates above. If it "
        "returns a dict with 'thumbnail_url' and 'photo_url', embed the thumbnail as a "
        "clickable image that links to the larger photo, exactly like: "
        "<a href=\"PHOTO_URL\"><img src=\"THUMBNAIL_URL\" alt=\"street view near here\">"
        "</a> — substituting the two URLs from the tool — and add a small "
        "\"© contributors, Mapillary\" credit. If it returns an empty result, tell them "
        "no street photo is available near there. Do not call the tool before they "
        "confirm."
    )


def _coupon_block(coupon: dict[str, Any] | None) -> str:
    """The specific coupon on screen (coupon-detail chat only), for the system prompt.

    Folds the enriched coupon record the app already renders (product, shop, discount,
    price, validity window, code, address) into a facts block so the model can answer
    questions about *this* coupon precisely instead of speaking in generalities.
    """
    if not coupon:
        return ""

    def show(v: Any) -> str:
        return str(v) if v not in (None, "") else "(unspecified)"

    lines = [
        f"- Product: {show(coupon.get('product_name_en'))}",
        f"- Shop: {show(coupon.get('shop_name_en'))}",
        f"- Category: {show(coupon.get('category_en'))} / "
        f"{show(coupon.get('subcategory_en'))}",
        f"- Discount: {show(coupon.get('discount_label'))}",
    ]
    price, off = coupon.get("price"), coupon.get("discount_off")
    if price is not None:
        line = f"- Price: ¥{price:,}"
        if off:
            line += f" (about ¥{off:,} off)"
        lines.append(line)
    start, end = coupon.get("coupon_start_date"), coupon.get("coupon_end_date")
    if start and end:
        active = " — currently active" if coupon.get("active") else " — NOT currently active"
        lines.append(f"- Valid: {start} to {end}{active}")
    if coupon.get("coupon_code"):
        lines.append(f"- Coupon code: {coupon['coupon_code']}")
    if coupon.get("address"):
        lines.append(f"- Shop address: {coupon['address']}")
    if coupon.get("product_description_en"):
        lines.append(f"- Product details: {coupon['product_description_en']}")

    return (
        "\n\nCURRENT COUPON — the specific coupon the traveler is viewing right now. "
        "Answer questions about this coupon from these facts; do not invent other "
        "offers, prices, or codes:\n" + "\n".join(lines)
    )


def _system_message(traveler_id: int,
                    origin: tuple[float, float] | None = None,
                    destination: tuple[float, float] | None = None,
                    coupon: dict[str, Any] | None = None) -> str:
    """Assemble the server-owned system prompt for this traveler."""
    return (
        "You are the XB eSIM in-app travel concierge for an inbound traveler in Tokyo. "
        "You help them understand and use the coupons shown in the app — active offers "
        "within 5 km of their current location, each with a discount, price, validity "
        "window, and code.\n\n"
        "LANGUAGE — always reply in the same language the traveler writes in.\n\n"
        "FORMATTING — IMPORTANT:\n"
        "- Write every reply as a small HTML fragment, NOT Markdown and NOT LaTeX.\n"
        "- Use only these tags: <p> <br> <strong> <em> <ul> <ol> <li> <code> <a href> "
        "<h4> <blockquote> <img>. Use <img> ONLY to show a photo URL returned by the "
        "get_streetview_photo tool — never invent or embed any other image URL. Never "
        "emit <script>, <style>, tables, inline styles, or <html>/<head>/<body> "
        "wrappers.\n"
        "- Write symbols directly (e.g. →, ×, ≤, ¥) — never "
        "LaTeX such as $\\rightarrow$.\n"
        "- Keep answers short and easy to read on a phone.\n\n"
        "KNOWLEDGE BOOK — ground your answers in this Q&A and the app's data "
        "model; do not invent facts beyond it. If a question falls outside this scope, "
        "say so briefly.\n"
        "<<<KNOWLEDGE_BOOK\n" + _qa_book() + "\nKNOWLEDGE_BOOK>>>\n\n"
        "CURRENT USER PROFILE — the traveler you are talking to (use it to "
        "personalise suggestions; do not read the raw numbers back to them):\n"
        + _profile_text(traveler_id)
        + _coupon_block(coupon)
        + _directions_block(origin, destination)
    )


def reply(session_key: str, traveler_id: int, message: str,
          origin: tuple[float, float] | None = None,
          destination: tuple[float, float] | None = None,
          coupon: dict[str, Any] | None = None) -> str:
    """Answer one chat turn for ``traveler_id``, carrying this session's prior turns.

    ``origin`` (traveler's current lat/lon) and ``destination`` (a coupon shop's
    lat/lon, coupon-detail chat only) are folded into the system prompt so the model
    can call ``get_railway_route``. ``coupon`` (the enriched record for the coupon being
    viewed, coupon-detail chat only) is folded in so the model can answer about that
    exact offer. Rehydrates an ephemeral chat (server-owned system message + stored
    history), requests a reply, and saves the updated history back. A single
    ``OumigoChat`` is not thread-safe, so one session should not be driven concurrently
    — fine for the demo's one-user conversations.
    """
    agent = _get_agent()
    history = _histories.get(session_key, [])
    chat = agent.create_chat(
        system=_system_message(traveler_id, origin, destination, coupon),
        history=history)
    response = chat.request(message)
    _histories[session_key] = chat.history
    return response.text
