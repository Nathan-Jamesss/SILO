# scrapers/base.py — Abstract base class for all scrapers
import asyncio
import random
from abc import ABC, abstractmethod
from typing import Optional

import httpx
from loguru import logger

# Realistic desktop user-agent strings — rotated per request
DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


class BaseScraper(ABC):
    """
    Abstract base class for all LaunchRadar scrapers.

    Subclasses must override:
        - name: human-readable source name (e.g. "Devpost")
        - opportunity_type: category string (e.g. "Competition")
        - base_url: root URL of the source
        - scrape(): core scraping logic

    The run() method wraps scrape() with retry logic and logging.
    """

    name: str = "base"
    opportunity_type: str = ""
    base_url: str = ""

    # Rate-limiting — override per subclass
    max_concurrent: int = 3
    delay_between_pages: tuple = (1.0, 3.0)   # (min_sec, max_sec)
    max_pages: int = 5

    @abstractmethod
    async def scrape(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
    ) -> list[dict]:
        """
        Core scraping logic — must be implemented by every subclass.

        Args:
            keyword: Search term to pass to source (e.g. "startup", "AI")
            region:  Optional geographic filter

        Returns:
            List of opportunity dicts. Each dict MUST contain:
                title, type, organizer, location, deadline (date|None),
                description (max 500 chars), source_url, source_name
        """
        ...

    async def run(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
        max_retries: int = 3,
    ) -> list[dict]:
        """
        Run the scraper with exponential-backoff retry logic.
        Never raises — returns [] on total failure so one broken scraper
        never blocks the others.

        Args:
            keyword:     Search term
            region:      Optional geographic filter
            max_retries: Number of attempts before giving up

        Returns:
            List of opportunity dicts (may be empty on failure)
        """
        for attempt in range(max_retries):
            try:
                results = await self.scrape(keyword, region)
                logger.info(f"[{self.name}] Scraped {len(results)} results")
                return results
            except Exception as exc:
                wait = 2 ** attempt
                logger.warning(
                    f"[{self.name}] Attempt {attempt + 1}/{max_retries} failed: {exc}. "
                    f"Retrying in {wait}s"
                )
                await asyncio.sleep(wait)

        logger.error(f"[{self.name}] All {max_retries} attempts failed — returning []")
        return []

    def _make_result(self, **kwargs) -> dict:
        """
        Build a validated result dict with all required keys.
        Fills sensible defaults for any missing field.
        Hard-caps description at 500 characters.
        """
        description = kwargs.get("description", "") or ""
        # Automatically classify default is_hackathon
        is_hack = 1 if self.name.lower() in ["devpost", "devfolio", "hack2skill", "unstop"] else 0
        num_apps = kwargs.get("num_applicants")
        if num_apps is not None:
            try:
                num_apps = int(num_apps)
            except (ValueError, TypeError):
                num_apps = None

        return {
            "title":              kwargs.get("title", "").strip(),
            "type":               kwargs.get("type", self.opportunity_type),
            "organizer":          kwargs.get("organizer", "").strip(),
            "location":           kwargs.get("location", "").strip(),
            "deadline":           kwargs.get("deadline", None),         # date object or None
            "description":        description[:500],
            "source_url":         kwargs.get("source_url", "").strip(),
            "source_name":        kwargs.get("source_name", self.name),
            "prize_pool":         float(kwargs.get("prize_pool", 0.0) or 0.0),
            "prize_pool_display": kwargs.get("prize_pool_display", "").strip(),
            "num_applicants":     num_apps,
            "is_hackathon":       int(kwargs.get("is_hackathon", is_hack) if kwargs.get("is_hackathon") is not None else is_hack),
        }

    def _headers(self) -> dict:
        """
        Return HTTP headers that mimic a real browser.
        Rotates user-agent on each call.
        """
        return {
            "User-Agent":                random.choice(DESKTOP_USER_AGENTS),
            "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language":           "en-US,en;q=0.9",
            "Accept-Encoding":           "gzip, deflate, br",
            "Connection":                "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _polite_delay(self) -> None:
        """Sleep for a random duration within the configured delay range."""
        min_s, max_s = self.delay_between_pages
        await asyncio.sleep(random.uniform(min_s, max_s))
