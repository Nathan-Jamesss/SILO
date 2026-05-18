# scrapers/masschallenge.py — Playwright + BeautifulSoup scraper for MassChallenge programs
import asyncio
import random
from typing import Optional

from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, DESKTOP_USER_AGENTS

# MassChallenge program listing pages (Traction and Challenge accelerators)
MC_URLS = [
    "https://masschallenge.org/accelerators/traction/",
    "https://masschallenge.org/accelerators/challenge/",
    "https://masschallenge.org/programs/",
]

BASE_DOMAIN = "https://masschallenge.org"

# Hardcoded seed data for MassChallenge programs that are reliably published
# Used as a guaranteed fallback when the live site is JS-rendered / blocked
MASSCHALLENGE_SEED = [
    {
        "title": "MassChallenge HealthTech",
        "description": "MassChallenge HealthTech accelerates early-stage health tech startups with mentorship, resources, and connections to the Boston health ecosystem.",
        "source_url": "https://masschallenge.org/programs/masschallenge-healthtech/",
        "location": "Boston, MA",
    },
    {
        "title": "MassChallenge Switzerland",
        "description": "Zero-equity accelerator for startups in Switzerland, supporting innovation across sectors including MedTech, AgriTech, and Fintech.",
        "source_url": "https://masschallenge.org/programs/masschallenge-switzerland/",
        "location": "Geneva, Switzerland",
    },
    {
        "title": "MassChallenge Texas",
        "description": "Accelerating high-impact startups in Texas with access to mentors, corporate partners, and a $1M+ prize pool.",
        "source_url": "https://masschallenge.org/programs/masschallenge-texas/",
        "location": "Austin, TX",
    },
    {
        "title": "MassChallenge Israel",
        "description": "Connecting Israeli startups to global markets through a zero-equity, zero-fee accelerator program.",
        "source_url": "https://masschallenge.org/programs/masschallenge-israel/",
        "location": "Tel Aviv, Israel",
    },
    {
        "title": "MassChallenge UK",
        "description": "Supporting UK-based and international startups with mentorship, workspace, and access to a global network.",
        "source_url": "https://masschallenge.org/programs/masschallenge-uk/",
        "location": "London, UK",
    },
    {
        "title": "MassChallenge AgriFood",
        "description": "Accelerating startups building solutions for the future of food and agriculture systems.",
        "source_url": "https://masschallenge.org/programs/masschallenge-agrifood/",
        "location": "Remote",
    },
    {
        "title": "MassChallenge Traction Accelerator",
        "description": "A 12-week program for revenue-generating startups ready to scale, offering mentorship from industry experts and corporate partners.",
        "source_url": "https://masschallenge.org/accelerators/traction/",
        "location": "Global",
    },
    {
        "title": "MassChallenge Challenge Accelerator",
        "description": "Zero-equity accelerator program focused on connecting early-stage startups with corporate challenge sponsors.",
        "source_url": "https://masschallenge.org/accelerators/challenge/",
        "location": "Global",
    },
]


class MassChallengeScraper(BaseScraper):
    """
    Scrapes MassChallenge accelerator programs via Playwright + BeautifulSoup.

    MassChallenge uses client-side JS rendering. This scraper:
    1. Tries to scrape live program data from the Playwright-rendered page
    2. Falls back to curated seed data if the live page yields nothing
       (e.g., when the site only shows a corporate partner page like AARP)
    """

    name = "MassChallenge"
    opportunity_type = "Accelerator"
    base_url = MC_URLS[0]
    max_pages = 1
    delay_between_pages = (1.0, 2.0)

    async def scrape(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
    ) -> list[dict]:
        """
        Fetch MassChallenge programs via Playwright, fall back to seed data.

        Args:
            keyword: Not used for this source
            region:  Not used for this source

        Returns:
            List of opportunity dicts
        """
        results: list[dict] = []

        # Try live scraping via Playwright
        try:
            results = await self._scrape_live()
        except Exception as exc:
            logger.warning(f"[MassChallenge] Live scraping failed: {exc}")

        # If live scraping returned nothing, use seed data
        if not results:
            logger.info("[MassChallenge] Using seed data fallback")
            results = self._get_seed_data()

        logger.info(f"[MassChallenge] Total: {len(results)} programs")
        return results

    async def _scrape_live(self) -> list[dict]:
        """Attempt to scrape live data via Playwright from multiple MC URLs."""
        results = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = await browser.new_context(
                user_agent=random.choice(DESKTOP_USER_AGENTS),
                viewport={"width": 1280, "height": 900},
                locale="en-US",
            )
            page = await context.new_page()

            for url in MC_URLS:
                logger.info(f"[MassChallenge] Trying {url}")
                try:
                    await page.goto(url, wait_until="networkidle", timeout=25_000)
                    await asyncio.sleep(random.uniform(1.5, 2.5))

                    html = await page.content()
                    soup = BeautifulSoup(html, "lxml")

                    page_results = self._parse_soup(soup)
                    if page_results:
                        results.extend(page_results)
                        logger.info(f"[MassChallenge] Got {len(page_results)} from {url}")

                except PlaywrightTimeout:
                    logger.warning(f"[MassChallenge] Timeout on {url}")
                    continue
                except Exception as exc:
                    logger.debug(f"[MassChallenge] Error on {url}: {exc}")
                    continue

            await browser.close()

        # Deduplicate by URL
        seen = set()
        unique = []
        for r in results:
            if r["source_url"] not in seen:
                seen.add(r["source_url"])
                unique.append(r)
        return unique

    def _parse_soup(self, soup: BeautifulSoup) -> list[dict]:
        """Parse BeautifulSoup from a MassChallenge page."""
        results = []

        # Try various card selectors
        cards = (
            soup.select(".program-card")
            or soup.select("article.type-program")
            or soup.select(".card-grid__item")
            or soup.select(".grid-item")
            or soup.select(".elementor-post")
            or soup.select("article")
        )

        for card in cards:
            try:
                record = self._parse_card(card)
                if record and record.get("title") and record.get("source_url"):
                    results.append(record)
            except Exception as exc:
                logger.debug(f"[MassChallenge] Card parse error: {exc}")

        return results

    def _parse_card(self, card) -> Optional[dict]:
        """Extract fields from a MassChallenge program card."""
        # Title
        title_el = card.select_one(
            "h2, h3, h4, .program-card__title, .elementor-post__title, "
            ".entry-title, [class*=title]"
        )
        title = title_el.get_text(strip=True) if title_el else ""

        # Link
        link_el = card.select_one("a[href]")
        href = link_el["href"] if link_el else ""
        if href.startswith("/"):
            href = f"{BASE_DOMAIN}{href}"

        # Ensure URL is real
        if not href or "masschallenge.org" not in href:
            return None

        # Location
        loc_el = card.select_one(
            ".program-card__location, .location, [class*=location], "
            "[class*=country], [class*=city]"
        )
        location = loc_el.get_text(strip=True) if loc_el else "Global"

        # Description
        desc_el = card.select_one(
            ".program-card__excerpt, .elementor-post__excerpt, p, "
            ".excerpt, .summary, [class*=excerpt]"
        )
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        if not title or not href:
            return None

        return self._make_result(
            title=title,
            organizer="MassChallenge",
            location=location,
            deadline=None,  # Deadline requires visiting individual program pages
            description=description,
            source_url=href,
        )

    def _get_seed_data(self) -> list[dict]:
        """Return curated seed data for MassChallenge programs."""
        results = []
        for seed in MASSCHALLENGE_SEED:
            record = self._make_result(
                title=seed["title"],
                organizer="MassChallenge",
                location=seed["location"],
                deadline=None,
                description=seed["description"],
                source_url=seed["source_url"],
            )
            results.append(record)
        return results
