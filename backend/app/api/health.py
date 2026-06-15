from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@router.get("/v1/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """Liveness + readiness check. Verifies DB connection."""
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
