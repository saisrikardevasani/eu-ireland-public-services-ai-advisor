"""Citizens Information crawler.

Crawls citizensinformation.ie using their XML sitemap, with browser-like
headers to pass basic bot-detection. Rate-limited to 1 req/sec per robots.txt.
"""

import asyncio
import hashlib
import logging
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Sitemap — gives us a clean list of canonical article URLs without crawling
SITEMAP_URL = "https://www.citizensinformation.ie/sitemap.xml"

# Fallback: if sitemap fails, crawl from known article URLs
FALLBACK_ARTICLE_URLS = [
    "https://www.citizensinformation.ie/en/moving-country/moving-to-ireland/rights-of-residence-in-ireland/residence-rights-eu-national/",
    "https://www.citizensinformation.ie/en/moving-country/working-in-ireland/employment-permits/overview-employment-permits/",
    "https://www.citizensinformation.ie/en/moving-country/working-in-ireland/employment-permits/critical-skills-employment-permit/",
    "https://www.citizensinformation.ie/en/moving-country/visas-for-ireland/student-visas/",
    "https://www.citizensinformation.ie/en/money-and-tax/tax/income-tax/how-your-tax-is-calculated/",
    "https://www.citizensinformation.ie/en/money-and-tax/tax/income-tax/universal-social-charge/",
    "https://www.citizensinformation.ie/en/money-and-tax/personal-finance/pensions/occupational-pensions/",
    "https://www.citizensinformation.ie/en/social-welfare/unemployed-people/jobseekers-benefit/",
    "https://www.citizensinformation.ie/en/social-welfare/unemployed-people/jobseekers-allowance/",
    "https://www.citizensinformation.ie/en/social-welfare/families-and-children/child-benefit/",
    "https://www.citizensinformation.ie/en/health/health-services/gp-and-hospital-services/gp-visit-cards/",
    "https://www.citizensinformation.ie/en/health/medical-cards-and-gp-visit-cards/medical-card/",
    "https://www.citizensinformation.ie/en/employment/starting-work-and-changing-job/starting-work/your-rights-when-you-start-work/",
    "https://www.citizensinformation.ie/en/employment/employment-rights-and-conditions/pay-and-employment/minimum-wage/",
    "https://www.citizensinformation.ie/en/employment/retirement/retiring-from-work/retirement-age/",
    "https://www.citizensinformation.ie/en/government-in-ireland/national-government/national-government/ppsn/",
    "https://www.citizensinformation.ie/en/returning-to-ireland/",
    "https://www.citizensinformation.ie/en/moving-country/moving-to-ireland/introduction-to-the-irish-system/overview-of-irish-system/",
]

CRAWL_DELAY_SECONDS = 1.2

# Realistic browser headers — required to pass basic Cloudflare bot detection
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IE,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


def _is_article_url(url: str) -> bool:
    """Accept only English-language article pages, not section indexes."""
    parsed = urlparse(url)
    if not parsed.path.startswith("/en/"):
        return False
    # Section indexes end at /en/topic/ — articles have at least 3 path segments after /en/
    parts = [p for p in parsed.path.split("/") if p]
    return len(parts) >= 3 and not parsed.path.endswith((".pdf", ".docx", ".zip"))


def _extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title = soup.find("title")
    if title:
        # "Page Title | Citizens Information" — take just the first part
        return title.get_text(strip=True).split("|")[0].strip()
    return "Untitled"


async def _fetch_sitemap_urls(client: httpx.AsyncClient) -> list[str]:
    """Try to read the XML sitemap. Returns article URLs or [] on failure."""
    try:
        resp = await client.get(SITEMAP_URL, timeout=20)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [loc.text for loc in root.findall(".//sm:loc", ns) if loc.text]
        article_urls = [u for u in urls if _is_article_url(u)]
        logger.info("Sitemap returned %d article URLs", len(article_urls))
        return article_urls
    except Exception as exc:
        logger.warning("Sitemap fetch failed (%s), falling back to seed URLs", exc)
        return []


async def crawl(max_pages: int = 200) -> list[dict]:
    """Crawl Citizens Information and return page dicts.

    Each dict: {url, title, content, content_hash}
    """
    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        # Try sitemap first (most reliable, avoids JS-protected landing pages)
        urls = await _fetch_sitemap_urls(client)

        # Fall back to known article URLs
        if not urls:
            logger.info("Using %d fallback article URLs", len(FALLBACK_ARTICLE_URLS))
            urls = FALLBACK_ARTICLE_URLS

        urls = urls[:max_pages]
        pages: list[dict] = []

        for i, url in enumerate(urls):
            try:
                await asyncio.sleep(CRAWL_DELAY_SECONDS)
                response = await client.get(url)
                response.raise_for_status()
            except Exception as exc:
                logger.warning("[%d/%d] Failed: %s — %s", i + 1, len(urls), url, exc)
                continue

            content = trafilatura.extract(
                response.text,
                include_links=False,
                include_tables=True,
                favor_recall=True,
            )
            if not content or len(content) < 100:
                logger.debug("Skipping thin page: %s", url)
                continue

            title = _extract_title(response.text)
            pages.append(
                {
                    "url": url,
                    "title": title,
                    "content": content,
                    "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                }
            )
            logger.info("[%d/%d] ✓ %s", len(pages), max_pages, title[:60])

    logger.info("Crawl complete: %d pages collected", len(pages))
    return pages
