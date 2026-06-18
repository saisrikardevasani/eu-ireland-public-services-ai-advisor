"""Generic multi-source web crawler.

Given a source config from sources.py, crawls the target site using its
XML sitemap (preferred) or falling back to seed URLs. Rate-limited and
idempotent — safe to re-run; the pipeline skips unchanged documents.

Usage:
    from app.ingestion.web_crawler import crawl
    from app.ingestion.sources import SOURCES

    pages = await crawl(SOURCES["revenue"], max_pages=150)
"""

import asyncio
import hashlib
import logging
import xml.etree.ElementTree as ET

import httpx
import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Realistic browser headers — required to pass basic bot-detection on gov sites
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IE,en;q=0.9",
    # Accept-Encoding is intentionally omitted — httpx auto-advertises only encodings
    # it can actually decompress (gzip/deflate). Explicitly listing 'br' without the
    # brotli package causes servers to send brotli-compressed bodies that httpx
    # cannot decode, resulting in garbled HTML that trafilatura rejects.
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


def _extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title_tag = soup.find("title")
    if title_tag:
        # "Page Title | Site Name" — take just the first part
        return title_tag.get_text(strip=True).split("|")[0].strip()
    return "Untitled"


async def _fetch_sitemap_urls(
    client: httpx.AsyncClient,
    sitemap_url: str,
    url_filter,
) -> list[str]:
    """Parse an XML sitemap and return filtered article URLs.

    Handles both plain sitemaps and sitemap index files (sitemaps of sitemaps).
    Returns [] on any failure — caller falls back to seed URLs.
    """
    try:
        resp = await client.get(sitemap_url, timeout=20)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Sitemap index — contains pointers to child sitemaps
        child_sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
        if child_sitemaps:
            all_urls: list[str] = []
            for sitemap_loc in child_sitemaps[:10]:  # cap child sitemaps to avoid explosion
                child_url = sitemap_loc.text
                if not child_url:
                    continue
                try:
                    child_resp = await client.get(child_url, timeout=20)
                    child_resp.raise_for_status()
                    child_root = ET.fromstring(child_resp.text)
                    urls = [
                        loc.text for loc in child_root.findall(".//sm:loc", ns)
                        if loc.text and url_filter(loc.text)
                    ]
                    all_urls.extend(urls)
                    await asyncio.sleep(0.5)
                except Exception as exc:
                    logger.debug("Child sitemap failed (%s): %s", child_url, exc)
            logger.info("Sitemap index: found %d filtered URLs", len(all_urls))
            return all_urls

        # Plain sitemap
        urls = [
            loc.text for loc in root.findall(".//sm:loc", ns)
            if loc.text and url_filter(loc.text)
        ]
        logger.info("Sitemap: found %d filtered URLs", len(urls))
        return urls

    except Exception as exc:
        logger.warning("Sitemap fetch failed (%s): %s", sitemap_url, exc)
        return []


async def crawl(source_config: dict, max_pages: int | None = None) -> list[dict]:
    """Crawl a source and return page dicts ready for ingestion.

    Each returned dict has keys: url, title, content, content_hash, source.

    Args:
        source_config: One entry from sources.SOURCES.
        max_pages: Override the source's default_max_pages.
    """
    source_name = source_config["source"]
    url_filter = source_config["url_filter"]
    crawl_delay = source_config.get("crawl_delay", 1.5)
    limit = max_pages or source_config.get("default_max_pages", 100)

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        # --- Step 1: Discover URLs ---
        urls: list[str] = []

        sitemap_url = source_config.get("sitemap_url")
        if sitemap_url:
            logger.info("[%s] Trying sitemap: %s", source_name, sitemap_url)
            urls = await _fetch_sitemap_urls(client, sitemap_url, url_filter)

        if not urls:
            logger.info("[%s] Using %d seed URLs", source_name, len(source_config["seed_urls"]))
            urls = [u for u in source_config["seed_urls"] if url_filter(u)]

        # De-duplicate, preserve order
        seen: set[str] = set()
        unique_urls: list[str] = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)

        urls = unique_urls[:limit]
        logger.info("[%s] Will crawl %d URLs (limit=%d)", source_name, len(urls), limit)

        # --- Step 2: Fetch and extract ---
        pages: list[dict] = []

        for i, url in enumerate(urls):
            try:
                await asyncio.sleep(crawl_delay)
                response = await client.get(url)
                response.raise_for_status()
            except Exception as exc:
                logger.warning("[%s] [%d/%d] Failed: %s — %s", source_name, i + 1, len(urls), url, exc)
                continue

            content = trafilatura.extract(
                response.text,
                include_links=False,
                include_tables=True,
                favor_recall=True,
            )
            if not content or len(content) < 150:
                logger.debug("[%s] Skipping thin page: %s", source_name, url)
                continue

            title = _extract_title(response.text)

            # Skip soft 404s — sites that return HTTP 200 with a "not found" page
            title_lower = title.lower()
            if (
                "404" in title_lower
                or "page not found" in title_lower
                or "not found" in title_lower
                or title_lower.strip() == "error"
            ):
                logger.debug("[%s] Skipping soft 404: %s — '%s'", source_name, url, title)
                continue

            pages.append({
                "url": url,
                "title": title,
                "content": content,
                "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                "source": source_name,
            })
            logger.info(
                "[%s] [%d/%d] ✓ %s",
                source_name, len(pages), limit, title[:70],
            )

    logger.info("[%s] Crawl complete: %d pages", source_name, len(pages))
    return pages
