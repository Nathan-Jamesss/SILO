# scrapers/grahamwalker.py — BeautifulSoup scraper for Graham & Walker grants blog
import asyncio
from datetime import date
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from loguru import logger

from scrapers.base import BaseScraper

SOURCE_URL = "https://grahamwalker.com/blog/grants-accelerators-for-early-stage-founders/"


class GrahamWalkerScraper(BaseScraper):
    """
    Scrapes the Graham & Walker curated grants list via httpx + BeautifulSoup.
    This is a single static blog page — no pagination needed.

    Live HTML analysis (2026-05-17):
    - The page contains a curated list of links in the article body.
    - Each opportunity is an <a href="...">Name:</a> element followed by text.
    - Links like: 'a16z / Speedrun:', 'Google for startups:', 'MassNextGen:', etc.
    - These are inside the article / .entry-content element.
    """

    name = "Graham & Walker"
    opportunity_type = "Grant"
    base_url = SOURCE_URL
    max_pages = 1
    delay_between_pages = (1.0, 1.0)

    # Skip generic non-opportunity links
    SKIP_TITLES = {
        "email us", "read more", "learn more", "apply", "click here",
        "here", "source", "general", "blog", "subscribe", "contact",
        "view all",
    }

    async def scrape(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
    ) -> list[dict]:
        """
        Fetch the grants blog page and extract all listed opportunities.

        Args:
            keyword: Not used (single curated page) — ignored
            region:  Not used — ignored

        Returns:
            List of opportunity dicts
        """
        logger.info(f"[Graham & Walker] Fetching {SOURCE_URL}")

        try:
            async with httpx.AsyncClient(
                headers=self._headers(),
                timeout=20,
                follow_redirects=True,
            ) as client:
                response = await client.get(SOURCE_URL)
                response.raise_for_status()
                html = response.text
        except httpx.TimeoutException:
            logger.warning("[Graham & Walker] Timeout fetching page")
            return []
        except httpx.HTTPStatusError as exc:
            logger.error(f"[Graham & Walker] HTTP {exc.response.status_code}")
            return []

        results = self._parse_page(html)
        logger.info(f"[Graham & Walker] Extracted {len(results)} grants")
        return results

    def _parse_page(self, html: str) -> list[dict]:
        """
        Parse the blog page HTML and extract grant/program listings.

        Strategy: Find all <a> links inside the article content that look like
        opportunity names (end with ':', contain a real org name, and point to
        external sites). Each link text IS the grant/program name.

        Args:
            html: Raw HTML string

        Returns:
            List of opportunity dicts
        """
        soup = BeautifulSoup(html, "lxml")
        results: list[dict] = []

        # Find the article / content container
        content = (
            soup.select_one("article .entry-content")
            or soup.select_one(".entry-content")
            or soup.select_one("article")
            or soup.select_one("main")
        )

        if not content:
            logger.warning("[Graham & Walker] Could not find content container")
            return []

        # Find all links that look like opportunity listings
        # Pattern: <a href="...">ProgramName:</a> some description text
        seen_urls: set[str] = set()

        for link in content.find_all("a", href=True):
            href = link["href"].strip()
            link_text = link.get_text(strip=True)

            # Skip empty, self-referential, or email links
            if not href or href.startswith("#") or href.startswith("mailto:"):
                continue
            if href == SOURCE_URL or "grahamwalker.com" in href:
                continue
            if not link_text or len(link_text) < 4:
                continue

            # Clean up the title (remove trailing colon/space)
            title = link_text.rstrip(": ").strip()

            # Skip non-opportunity links
            if title.lower() in self.SKIP_TITLES:
                continue

            # Skip obvious navigation/category links (too short or all lowercase)
            if len(title) < 5:
                continue

            # Avoid exact URL duplicates
            if href in seen_urls:
                continue
            seen_urls.add(href)

            # Get description from surrounding text (parent li or p element)
            parent = link.parent
            description = ""
            if parent:
                full_text = parent.get_text(strip=True)
                # Remove the link text from the full paragraph text to get description
                description = full_text.replace(link_text, "").strip().lstrip(":").strip()
                description = description[:500]

            # Try to extract deadline from surrounding text
            deadline = self._find_deadline_in_text(description) or self._find_deadline_in_text(full_text if parent else "")

            # Determine opportunity type from title/description keywords
            opp_type = self._classify_type(title, description)

            record = self._make_result(
                title=title,
                organizer="",   # organizer often embedded in title
                location="Global",
                deadline=deadline,
                description=description,
                source_url=href,
            )
            # Override the type determined by _make_result
            record["type"] = opp_type
            results.append(record)

        if not results:
            logger.warning(
                "[Graham & Walker] Could not parse any opportunities from page — "
                "site structure may have changed."
            )

        return results

    @staticmethod
    def _classify_type(title: str, description: str) -> str:
        """Classify opportunity type from title/description keywords."""
        combined = (title + " " + description).lower()
        if any(k in combined for k in ["accelerator", "incubator", "cohort", "program"]):
            return "Accelerator"
        if any(k in combined for k in ["grant", "award", "fellowship", "prize"]):
            return "Grant"
        if any(k in combined for k in ["summit", "conference", "week", "showcase"]):
            return "Conference"
        if any(k in combined for k in ["hackathon", "hack", "competition", "pitch"]):
            return "Competition"
        return "Grant"  # Default for this source

    @staticmethod
    def _find_deadline_in_text(text: str) -> Optional[date]:
        """
        Search text for common deadline phrases and attempt to parse the date.

        Args:
            text: Free-text string that may contain a date

        Returns:
            Parsed date or None
        """
        if not text:
            return None

        # Look for phrases that indicate a deadline
        triggers = ["apply by", "deadline:", "closes", "due:", "applications due", "by "]
        text_lower = text.lower()

        for trigger in triggers:
            idx = text_lower.find(trigger)
            if idx != -1:
                # Extract substring after the trigger (next ~30 chars)
                snippet = text[idx + len(trigger):idx + len(trigger) + 30]
                try:
                    return dateparser.parse(snippet, fuzzy=True).date()
                except (ValueError, OverflowError, TypeError, AttributeError):
                    continue

        return None
