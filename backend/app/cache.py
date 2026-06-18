"""Redis-backed query cache.

Caches retrieval results keyed on a SHA-256 of the lowercased query.
TTL is 6 hours — short enough to pick up daily gov.ie updates,
long enough to serve repeated common questions without hitting the DB.

Cache misses are transparent: the caller gets None and falls through
to the normal retrieval pipeline.
"""

import hashlib
import json
import logging
from dataclasses import asdict

import redis.asyncio as aioredis

from app.config import settings
from app.pipeline.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None

CACHE_TTL = 60 * 60 * 6  # 6 hours


def _client() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _cache_key(query: str) -> str:
    digest = hashlib.sha256(query.strip().lower().encode()).hexdigest()
    return f"rag:v1:{digest}"


async def get_cached(query: str) -> list[RetrievedChunk] | None:
    try:
        raw = await _client().get(_cache_key(query))
        if raw is None:
            return None
        data = json.loads(raw)
        chunks = [RetrievedChunk(**item) for item in data]
        logger.debug("Cache hit for query: %s…", query[:60])
        return chunks
    except Exception as exc:
        logger.warning("Cache read failed (ignoring): %s", exc)
        return None


async def set_cached(query: str, chunks: list[RetrievedChunk]) -> None:
    try:
        payload = json.dumps([asdict(c) for c in chunks])
        await _client().setex(_cache_key(query), CACHE_TTL, payload)
        logger.debug("Cached %d chunks for query: %s…", len(chunks), query[:60])
    except Exception as exc:
        logger.warning("Cache write failed (ignoring): %s", exc)
