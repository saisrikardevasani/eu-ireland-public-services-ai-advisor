"""Redis-backed query cache and daily rate limit counter.

Query cache: keyed on SHA-256 of the lowercased query, TTL 6 hours.
Daily limit: per-IP request counter, resets at midnight UTC.

Cache misses and Redis errors are transparent — the caller falls through
to the normal retrieval pipeline. Rate limit errors fail open (allow the
request) so a Redis outage never takes down the service.
"""

import hashlib
import json
import logging
from dataclasses import asdict
from datetime import date

import redis.asyncio as aioredis

from app.config import settings
from app.pipeline.retrieval import RetrievedChunk

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None

CACHE_TTL = 60 * 60 * 6  # 6 hours
DAILY_LIMIT = 20          # max requests per IP per calendar day


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


async def check_daily_limit(ip: str) -> bool:
    """Increment the per-IP daily request counter. Returns False if the cap is exceeded.

    Key format: ratelimit:daily:<ip>:<YYYY-MM-DD> (resets at midnight UTC).
    Fails open on Redis errors so a cache outage never blocks the service.
    """
    key = f"ratelimit:daily:{ip}:{date.today().isoformat()}"
    try:
        client = _client()
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, 86400)  # 24h TTL set on first request of the day
        return count <= DAILY_LIMIT
    except Exception as exc:
        logger.warning("Daily rate limit check failed (failing open): %s", exc)
        return True
