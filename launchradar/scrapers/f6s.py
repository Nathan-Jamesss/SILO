# scrapers/f6s.py — httpx-based scraper for F6S accelerator programs
# F6S uses server-side rendering with some JS, so we try httpx first (fast path)
# then fall back to a curated seed list if the live site returns 0 results.
import asyncio
import random
from datetime import date
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from loguru import logger

from scrapers.base import BaseScraper

BASE_URL = "https://www.f6s.com"
PROGRAMS_URL = "https://www.f6s.com/programs"

# Semaphore limits concurrent requests to 3 — respects F6S rate limits (~15 req/min)
_semaphore = asyncio.Semaphore(3)

# Curated seed data for reliable baseline results
F6S_SEED = [
    {
        "title": "Techstars Startup Accelerator",
        "description": "One of the world's most active pre-seed investors, Techstars accelerates high-potential, early-stage companies across industries.",
        "source_url": "https://www.techstars.com/accelerators",
        "organizer": "Techstars",
        "location": "Global",
    },
    {
        "title": "Y Combinator (YC) Batch Application",
        "description": "Y Combinator provides seed funding for startups twice a year. Work with YC partners, a community of thousands of founders.",
        "source_url": "https://www.ycombinator.com/apply",
        "organizer": "Y Combinator",
        "location": "San Francisco, CA",
    },
    {
        "title": "500 Global Accelerator",
        "description": "500 Global is a venture capital firm with a network of thousands of founders, mentors, advisors, and investors globally.",
        "source_url": "https://500.co/accelerators",
        "organizer": "500 Global",
        "location": "Global",
    },
    {
        "title": "Plug and Play Tech Center",
        "description": "Plug and Play is a global innovation platform connecting startups with corporations and investors across 50+ industries.",
        "source_url": "https://www.plugandplaytechcenter.com/join/",
        "organizer": "Plug and Play",
        "location": "Sunnyvale, CA",
    },
    {
        "title": "SOSV Accelerator Programs",
        "description": "SOSV is a multi-stage venture capital fund that operates deep tech accelerators including HAX, IndieBio, and dlab.",
        "source_url": "https://sosv.com/programs/",
        "organizer": "SOSV",
        "location": "Global",
    },
    {
        "title": "Entrepreneur First Talent Investor",
        "description": "Entrepreneur First invests in exceptional individuals before they have an idea or co-founder, in London, Paris, Berlin, Singapore, and more.",
        "source_url": "https://www.joinef.com/",
        "organizer": "Entrepreneur First",
        "location": "Global",
    },
    {
        "title": "AngelPad Accelerator",
        "description": "AngelPad is a highly selective startup accelerator based in San Francisco and New York, consistently ranked the #1 accelerator in the US.",
        "source_url": "https://angelpad.com/apply/",
        "organizer": "AngelPad",
        "location": "San Francisco, CA",
    },
    {
        "title": "Seedcamp Accelerator",
        "description": "Seedcamp is Europe's leading seed fund. They invest early in world-class founders attacking large, global markets.",
        "source_url": "https://seedcamp.com/apply/",
        "organizer": "Seedcamp",
        "location": "London, UK",
    },
    {
        "title": "Google for Startups Accelerator",
        "description": "Google for Startups Accelerator provides equity-free support, mentorship, and Google resources for seed to Series A startups.",
        "source_url": "https://startup.google.com/programs/accelerator/",
        "organizer": "Google",
        "location": "Remote",
    },
    {
        "title": "Microsoft for Startups Founders Hub",
        "description": "Microsoft for Startups Founders Hub helps startups build and scale their products with up to $150k in Azure credits.",
        "source_url": "https://foundershub.startups.microsoft.com/",
        "organizer": "Microsoft",
        "location": "Remote",
    },
]


class F6SScraper(BaseScraper):
    """
    Scrapes accelerator programs from F6S using httpx + BeautifulSoup.
    Falls back to curated seed data if live scraping returns 0 results.
    """

    name = "F6S"
    opportunity_type = "Accelerator"
    base_url = PROGRAMS_URL
    max_pages = 3
    delay_between_pages = (2.0, 4.0)

    async def scrape(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
    ) -> list[dict]:
        """
        Fetch F6S program listings page by page and extract all required fields.
        Falls back to seed data if live scraping fails.

        Args:
            keyword: Search query for F6S
            region:  Optional country/city filter

        Returns:
            List of opportunity dicts
        """
        results: list[dict] = []

        try:
            results = await self._scrape_live(keyword, region)
        except Exception as exc:
            logger.warning(f"[F6S] Live scraping failed: {exc}")

        if not results:
            logger.info("[F6S] Using seed data fallback")
            results = self._get_seed_data()

        logger.info(f"[F6S] Total extracted: {len(results)} accelerators")
        return results

    async def _scrape_live(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
    ) -> list[dict]:
        """Try to scrape live data from F6S."""
        results = []

        async with httpx.AsyncClient(
            headers=self._headers(),
            timeout=20,
            follow_redirects=True,
        ) as client:
            for page_num in range(1, self.max_pages + 1):
                params = {"page": page_num, "search": keyword}
                if region:
                    params["location"] = region

                logger.info(f"[F6S] Fetching page {page_num}")

                try:
                    html = await self._fetch_page(client, PROGRAMS_URL, params)
                except Exception as exc:
                    logger.error(f"[F6S] Failed to fetch page {page_num}: {exc}")
                    break

                page_results = self._parse_page(html)
                logger.info(f"[F6S] Page {page_num}: found {len(page_results)} programs")

                if not page_results:
                    logger.info(f"[F6S] Empty page {page_num} — stopping pagination")
                    break

                results.extend(page_results)

        return results

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict,
    ) -> str:
        """
        Fetch a single page with semaphore gating and polite delay.
        Raises on HTTP error so the caller can handle / retry.
        """
        async with _semaphore:
            await asyncio.sleep(random.uniform(*self.delay_between_pages))
            response = await client.get(url, params=params)
            if response.status_code == 429:
                # Rate limited — wait longer and retry once
                logger.warning("[F6S] Rate limited (429) — waiting 10s")
                await asyncio.sleep(10)
                response = await client.get(url, params=params)
            response.raise_for_status()
            return response.text

    def _parse_page(self, html: str) -> list[dict]:
        """
        Parse a single F6S listing page and return opportunity dicts.

        Args:
            html: Raw HTML string

        Returns:
            List of opportunity dicts from this page
        """
        soup = BeautifulSoup(html, "lxml")
        results: list[dict] = []

        # F6S uses various card selectors depending on page version
        cards = (
            soup.select(".program-card")
            or soup.select(".program-listing")
            or soup.select("article.program")
            or soup.select(".card.program")
            or soup.select("[class*='program']")
            or soup.select("article")
        )

        for card in cards:
            try:
                record = self._parse_card(card)
                if record and record.get("source_url") and record.get("title"):
                    results.append(record)
            except Exception as exc:
                logger.debug(f"[F6S] Card parse error: {exc}")
                continue

        return results

    def _parse_card(self, card) -> Optional[dict]:
        """
        Extract fields from a single F6S program card.

        Args:
            card: BeautifulSoup Tag element

        Returns:
            Opportunity dict or None if invalid
        """
        # Title
        title_el = card.select_one("h2, h3, h4, .program-name, .title, strong")
        title = title_el.get_text(strip=True) if title_el else ""

        # Source URL
        link_el = card.select_one("a[href]")
        href = link_el["href"] if link_el else ""
        if href.startswith("/"):
            href = f"{BASE_URL}{href}"

        # Organizer
        org_el = card.select_one(".organization, .organizer, .company-name, .by")
        organizer = org_el.get_text(strip=True) if org_el else ""

        # Location
        loc_el = card.select_one(".location, .country, .where, [class*='location']")
        location = loc_el.get_text(strip=True) if loc_el else "Global"

        # Deadline
        deadline_el = card.select_one(".deadline, .apply-by, time, [class*='deadline']")
        deadline = None
        if deadline_el:
            date_text = deadline_el.get("datetime") or deadline_el.get_text(strip=True)
            deadline = self._parse_date(date_text)

        # Description
        desc_el = card.select_one(".description, .summary, p, .tagline")
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        if not title or not href:
            return None

        return self._make_result(
            title=title,
            organizer=organizer,
            location=location,
            deadline=deadline,
            description=description,
            source_url=href,
        )

    def _get_seed_data(self) -> list[dict]:
        """Return curated seed data for well-known accelerator programs."""
        results = []
        for seed in F6S_SEED:
            record = self._make_result(
                title=seed["title"],
                organizer=seed["organizer"],
                location=seed["location"],
                deadline=None,
                description=seed["description"],
                source_url=seed["source_url"],
            )
            results.append(record)
        return results

    @staticmethod
    def _parse_date(text: str) -> Optional[date]:
        """Parse date text to date object — returns None on failure."""
        if not text:
            return None
        skip_words = ["rolling", "ongoing", "tbd", "tba", "open", "no deadline", "n/a"]
        if any(w in text.lower() for w in skip_words):
            return None
        try:
            return dateparser.parse(text, fuzzy=True).date()
        except (ValueError, OverflowError, TypeError, AttributeError):
            return None
