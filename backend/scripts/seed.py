"""Load fixture documents into the database for local development.

This is the fast alternative to crawling — loads pre-written Citizens
Information content from fixtures/citizens_information.json.

Use this when:
  - You want a quick local demo (takes ~30 seconds)
  - The live site is behind bot protection

Use scripts/ingest.py with --live flag for production crawling.

Usage:
    python scripts/seed.py
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.ingestion.pipeline import ingest_pages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

FIXTURES_PATH = Path(__file__).parent.parent / "fixtures" / "citizens_information.json"


async def main() -> None:
    logger.info("Loading fixtures from %s", FIXTURES_PATH)
    pages = json.loads(FIXTURES_PATH.read_text())
    logger.info("Loaded %d fixture documents", len(pages))

    logger.info("Embedding and indexing (first run downloads the model ~134MB)...")
    async with AsyncSessionLocal() as session:
        stats = await ingest_pages(session, pages)

    logger.info(
        "Done: %d new, %d updated, %d skipped, %d chunks created",
        stats["new"], stats["updated"], stats["skipped"], stats["chunks_created"],
    )
    logger.info("Your database is ready. Start the backend with: make backend")


if __name__ == "__main__":
    asyncio.run(main())
