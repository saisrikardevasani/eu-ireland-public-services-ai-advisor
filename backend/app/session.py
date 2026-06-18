"""In-memory conversation session store.

Keeps the last N turns per conversation_id with a TTL so memory is
bounded — idle sessions are evicted on the next access that exceeds their TTL.

Not persisted: a backend restart clears all sessions. This is intentional —
we do not want to store user query history.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

from app.pipeline.generator import Turn

MAX_TURNS = 3       # how many prior exchanges (user+assistant pairs) to include
SESSION_TTL = 1800  # 30 minutes of inactivity before eviction


@dataclass
class Session:
    turns: deque[Turn] = field(default_factory=lambda: deque(maxlen=MAX_TURNS * 2))
    last_access: float = field(default_factory=time.monotonic)


_store: dict[str, Session] = {}
_lock = Lock()


def _evict_stale() -> None:
    now = time.monotonic()
    stale = [k for k, s in _store.items() if now - s.last_access > SESSION_TTL]
    for k in stale:
        del _store[k]


def get_history(conversation_id: str | None) -> list[Turn]:
    if not conversation_id:
        return []
    with _lock:
        _evict_stale()
        session = _store.get(conversation_id)
        if session is None:
            return []
        session.last_access = time.monotonic()
        return list(session.turns)


def append_turn(conversation_id: str | None, role: str, content: str) -> None:
    if not conversation_id:
        return
    with _lock:
        if conversation_id not in _store:
            _store[conversation_id] = Session()
        session = _store[conversation_id]
        session.turns.append({"role": role, "content": content})
        session.last_access = time.monotonic()
