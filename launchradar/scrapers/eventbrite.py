# scrapers/eventbrite.py — Eventbrite REST API scraper for startup conferences
import asyncio
from datetime import date
from typing import Optional

import httpx
from loguru import logger

from config import settings
from scrapers.base import BaseScraper

API_BASE = "https://www.eventbriteapi.com/v3"


class EventbriteScraper(BaseScraper):
    """
    Fetches startup-related events from the Eventbrite REST API.
    Uses the official API (never scrapes) — free tier gives 1,000 calls/day.
    If EVENTBRITE_API_KEY is not configured, returns [] gracefully.
    Paginates via continuation token, max 3 pages.
    """

    name = "Eventbrite"
    opportunity_type = "Conference"
    base_url = API_BASE
    max_pages = 3

    async def scrape(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
    ) -> list[dict]:
        """
        Search Eventbrite events matching the keyword and map to opportunity dicts.

        Args:
            keyword: Search query (e.g. "startup", "AI startup")
            region:  Optional location hint (e.g. "London")

        Returns:
            List of opportunity dicts, or [] if API key missing
        """
        if not settings.eventbrite_api_key:
            logger.warning("[Eventbrite] EVENTBRITE_API_KEY not set — skipping")
            return []

        results: list[dict] = []
        continuation: Optional[str] = None

        headers = {
            "Authorization": f"Bearer {settings.eventbrite_api_key}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(headers=headers, timeout=20) as client:
            for page_num in range(1, self.max_pages + 1):
                params = {
                    "q":          keyword,
                    "categories": "102",          # Business & Professional
                    "sort_by":    "date",
                    "expand":     "organizer,venue",
                    "page_size":  50,
                }
                if region:
                    params["location.address"] = region
                if continuation:
                    params["continuation"] = continuation

                logger.info(f"[Eventbrite] Fetching page {page_num}")

                try:
                    response = await client.get(
                        f"{API_BASE}/events/search/",
                        params=params,
                    )
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPStatusError as exc:
                    logger.error(
                        f"[Eventbrite] HTTP {exc.response.status_code} — stopping"
                    )
                    break
                except Exception as exc:
                    logger.error(f"[Eventbrite] Request failed: {exc}")
                    break

                events = data.get("events", [])
                logger.info(f"[Eventbrite] Page {page_num}: {len(events)} events")

                for event in events:
                    try:
                        record = self._map_event(event)
                        if record:
                            results.append(record)
                    except Exception as exc:
                        logger.debug(f"[Eventbrite] Event parse error: {exc}")

                # Check for next page
                pagination = data.get("pagination", {})
                continuation = pagination.get("continuation")
                if not continuation or not pagination.get("has_more_items"):
                    break

                await asyncio.sleep(1.0)   # polite delay between API calls

        logger.info(f"[Eventbrite] Total extracted: {len(results)} events")
        return results

    def _map_event(self, event: dict) -> Optional[dict]:
        """
        Map a raw Eventbrite event dict to our standard opportunity format.

        Args:
            event: Raw event dict from Eventbrite API

        Returns:
            Opportunity dict or None if event is missing critical fields
        """
        title = (event.get("name") or {}).get("text", "").strip()
        if not title:
            return None

        url = event.get("url", "").strip()
        if not url:
            return None

        # Organizer name
        organizer = ""
        org_data = event.get("organizer")
        if org_data:
            organizer = org_data.get("name", "").strip()

        # Location — prefer venue city, fall back to "Online"
        location = "Online"
        venue = event.get("venue")
        if venue:
            city = (venue.get("address") or {}).get("city", "")
            country = (venue.get("address") or {}).get("country", "")
            if city and country:
                location = f"{city}, {country}"
            elif city:
                location = city
        if event.get("online_event"):
            location = "Remote"

        # Deadline = event start date (ISO string like "2026-06-15T09:00:00")
        deadline: Optional[date] = None
        start = event.get("start", {}).get("local", "")
        if start and len(start) >= 10:
            try:
                deadline = date.fromisoformat(start[:10])
            except ValueError:
                pass

        # Description
        description = (
            (event.get("description") or {}).get("text", "")
            or (event.get("summary") or "")
        )[:500]

        return self._make_result(
            title=title,
            organizer=organizer,
            location=location,
            deadline=deadline,
            description=description,
            source_url=url,
        )
