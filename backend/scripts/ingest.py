"""CLI entry point: crawl Citizens Information and index into Postgres.

Usage:
    python scripts/ingest.py                   # default 200 pages
    python scripts/ingest.py --max-pages 50    # quick smoke test
    python scripts/ingest.py --max-pages 3000  # full crawl (~50 min)
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Make sure `app` is importable when running from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.ingestion.crawler import crawl
from app.ingestion.pipeline import ingest_pages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main(max_pages: int) -> None:
    logger.info("Starting ingestion — max %d pages", max_pages)

    # Step 1: Crawl
    logger.info("Phase 1/2: Crawling Citizens Information...")
    pages = await crawl(max_pages=max_pages)
    logger.info("Crawled %d pages", len(pages))

    # Step 2: Ingest (chunk + embed + store)
    logger.info("Phase 2/2: Indexing into Postgres...")
    async with AsyncSessionLocal() as session:
        stats = await ingest_pages(session, pages)

    logger.info(
        "Ingestion complete: %d new, %d updated, %d skipped, %d chunks created",
        stats["new"],
        stats["updated"],
        stats["skipped"],
        stats["chunks_created"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Citizens Information into Postgres")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=200,
        help="Maximum number of pages to crawl (default: 200)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.max_pages))
