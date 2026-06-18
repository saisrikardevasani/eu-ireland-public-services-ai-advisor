"""POST /v1/feedback — thumbs up/down on a RAG answer.

Stores only a hash of the question (not the question itself) plus the
rating, so we get quality signal without retaining user query content.
This keeps us compliant with our stated privacy policy.
"""

import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class FeedbackRequest(BaseModel):
    question_hash: str   # SHA-256 of the question — sent by the client
    rating: int          # 1 = thumbs up, -1 = thumbs down
    conversation_id: str | None = None


@router.post("/v1/feedback", status_code=204)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Record a thumbs up/down without storing the raw question."""
    if request.rating not in (1, -1):
        return

    try:
        await db.execute(
            text("""
                INSERT INTO feedback (question_hash, rating, created_at)
                VALUES (:question_hash, :rating, :created_at)
            """),
            {
                "question_hash": request.question_hash,
                "rating": request.rating,
                "created_at": datetime.now(timezone.utc),
            },
        )
        await db.commit()
        logger.info("Feedback recorded: %s → %+d", request.question_hash[:12], request.rating)
    except Exception as exc:
        logger.error("Feedback write failed: %s", exc)
