"""Concierge-agent wiring for the coupon-detail chat panel.

Naive first cut. The oumigo manager + worker are assumed to be **already running
somewhere** (started out of band); we merely *attach* to the manager with
``oumigo_get_or_create_manager()`` — on a LAN with a live manager advertising, this
reuses it (nothing is spawned) — and build a single agent from it.

Each chat turn is answered by rehydrating an ephemeral ``OumigoChat`` from a
server-held history and calling ``chat.request(message)`` (see the stateless-server
pattern documented in oumigo's agent API: *store the history, not the Chat*). The
browser never holds the transcript; the server owns system prompt + history. For now
there are no tools and no coupon-aware prompting — we just relay the user's text to
the data plane and return the reply. That grows later.
"""
from __future__ import annotations

import threading
from typing import Any

from oumigo import oumigo_get_or_create_manager

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
                _agent = manager.create_agent()
    return _agent


def reply(session_key: str, message: str) -> str:
    """Answer one chat turn, carrying this session's prior turns.

    Rehydrates an ephemeral chat from the server-held history, requests a reply, and
    saves the updated history back. A single ``OumigoChat`` is not thread-safe, so
    one session should not be driven concurrently — fine for the demo's one-user
    conversations.
    """
    agent = _get_agent()
    history = _histories.get(session_key, [])
    chat = agent.create_chat(history=history)
    response = chat.request(message)
    _histories[session_key] = chat.history
    return response.text
