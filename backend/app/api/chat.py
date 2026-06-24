"""POST /v1/chat/messages — the main RAG endpoint.

Returns a Server-Sent Events (SSE) stream with three event types:
  event: token   — a chunk of generated text
  event: citations — the source passages used (sent at the end)
  event: done    — signals the stream is complete

Why SSE instead of WebSockets?
SSE is unidirectional (server → client) and HTTP-based, which makes it:
- Simpler to implement and proxy
- Reconnectable automatically by browsers
- Compatible with standard HTTP caching and load balancers
For LLM streaming (one-way), SSE is the right tool.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import check_daily_limit, get_cached, set_cached
from app.database import get_db
from app.pipeline.generator import generate
from app.pipeline.retrieval import retrieve
from app.session import append_turn, get_history

limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

    @property
    def validated_message(self) -> str:
        msg = self.message.strip()
        if not msg:
            raise ValueError("message cannot be empty")
        if len(msg) > 2000:
            raise ValueError("message exceeds 2000 character limit")
        return msg


def _sse(event: str, data: dict | str) -> str:
    """Format a single SSE frame."""
    payload = data if isinstance(data, str) else json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/v1/chat/messages")
@limiter.limit("10/minute")
async def chat(
    http_request: Request,  # required by slowapi for IP-based rate limiting
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Retrieve relevant passages and stream a grounded answer."""
    ip = get_remote_address(http_request)
    if not await check_daily_limit(ip):
        raise HTTPException(
            status_code=429,
            detail="You've reached the daily limit of 20 questions. Please try again tomorrow.",
        )

    async def event_stream():
        query = request.validated_message
        conv_id = request.conversation_id

        # ── Step 1: Load conversation history ────────────────────────────────
        history = get_history(conv_id)

        # ── Step 2: Retrieve (cache-first) ───────────────────────────────────
        try:
            chunks = await get_cached(query)
            if chunks is None:
                chunks = await retrieve(db, query)
                await set_cached(query, chunks)
        except Exception as exc:
            logger.error("Retrieval failed: %s", exc, exc_info=True)
            yield _sse("error", {"message": "Retrieval failed. Please try again."})
            return

        yield _sse("meta", {"retrieved_count": len(chunks)})

        # ── Step 3: Generate (streaming) ─────────────────────────────────────
        full_response = ""
        try:
            async for token in generate(query, chunks, history=history):
                full_response += token
                yield _sse("token", {"text": token})
        except Exception as exc:
            logger.error("Generation failed: %s", exc, exc_info=True)
            yield _sse("error", {"message": "Generation failed. Please try again."})
            return

        # ── Step 4: Persist this exchange in the session ──────────────────────
        append_turn(conv_id, "user", query)
        append_turn(conv_id, "assistant", full_response)

        # ── Step 5: Send citations ────────────────────────────────────────────
        citations = [
            {
                "n": i + 1,
                "title": chunk.title,
                "url": chunk.url,
                "snippet": chunk.content[:300] + ("..." if len(chunk.content) > 300 else ""),
                "crawled_at": chunk.crawled_at,
            }
            for i, chunk in enumerate(chunks)
        ]
        yield _sse("citations", {"citations": citations})
        yield _sse("done", {"message": "Stream complete"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disables nginx response buffering
            "Connection": "keep-alive",
        },
    )
