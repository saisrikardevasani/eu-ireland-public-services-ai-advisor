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

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.pipeline.generator import generate
from app.pipeline.retrieval import retrieve

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None  # for future multi-turn support


def _sse(event: str, data: dict | str) -> str:
    """Format a single SSE frame."""
    payload = data if isinstance(data, str) else json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/v1/chat/messages")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Retrieve relevant passages and stream a Claude-generated answer."""

    async def event_stream():
        # ── Step 1: Retrieve ─────────────────────────────────────────────────
        try:
            chunks = await retrieve(db, request.message)
        except Exception as exc:
            logger.error("Retrieval failed: %s", exc, exc_info=True)
            yield _sse("error", {"message": "Retrieval failed. Please try again."})
            return

        # Send chunk count so the UI can show a "found N sources" indicator
        yield _sse("meta", {"retrieved_count": len(chunks)})

        # ── Step 2: Generate (streaming) ────────────────────────────────────
        full_response = ""
        try:
            async for token in generate(request.message, chunks):
                full_response += token
                yield _sse("token", {"text": token})
        except Exception as exc:
            logger.error("Generation failed: %s", exc, exc_info=True)
            yield _sse("error", {"message": "Generation failed. Please try again."})
            return

        # ── Step 3: Send citations ───────────────────────────────────────────
        citations = [
            {
                "n": i + 1,
                "title": chunk.title,
                "url": chunk.url,
                "snippet": chunk.content[:300] + ("..." if len(chunk.content) > 300 else ""),
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
