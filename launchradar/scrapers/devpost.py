# scrapers/devpost.py — Playwright-based scraper for Devpost hackathons
import asyncio
import random
from datetime import date
from typing import Optional

from dateutil import parser as dateparser
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from scrapers.base import BaseScraper, DESKTOP_USER_AGENTS

BASE_URL = "https://devpost.com/hackathons"


class DevpostScraper(BaseScraper):
    """
    Scrapes hackathons from Devpost using Playwright (async Chromium).
    Devpost is Vue.js rendered — a plain HTTP request returns an empty shell.
    Paginates via ?page=N, max 3 pages.

    Live HTML analysis (2026-05-17):
      - Cards use class: .hackathon-tile
      - Title: h3 inside the tile
      - Link: a.tile-anchor[href]
      - Organizer: .host-label text
      - Deadline: .submission-period text ("Apr 09 - May 20, 2026")
      - Location: .info-with-icon span ("Online" / city)
      - Prize: .prize-amount text
    """

    name = "Devpost"
    opportunity_type = "Competition"
    base_url = BASE_URL
    max_pages = 3
    delay_between_pages = (1.5, 3.0)

    async def scrape(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
    ) -> list[dict]:
        """
        Launch headless Chromium, iterate pages of Devpost hackathons,
        and extract all required fields.

        Args:
            keyword: Search query passed to Devpost's filter
            region:  Not used by Devpost — ignored

        Returns:
            List of opportunity dicts
        """
        results: list[dict] = []

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

            for page_num in range(1, self.max_pages + 1):
                url = f"{BASE_URL}?page={page_num}&challenge_type=all&search={keyword}"
                logger.info(f"[Devpost] Fetching page {page_num}: {url}")

                try:
                    await page.goto(url, wait_until="networkidle", timeout=30_000)
                    # Wait for .hackathon-tile to be present (confirmed working selector)
                    await page.wait_for_selector(
                        ".hackathon-tile",
                        timeout=15_000,
                    )
                except PlaywrightTimeout:
                    logger.warning(f"[Devpost] Timeout on page {page_num} — stopping pagination")
                    break

                # Polite delay between pages
                await asyncio.sleep(random.uniform(*self.delay_between_pages))

                # Extract cards using confirmed selector
                cards = await page.query_selector_all(".hackathon-tile")

                logger.info(f"[Devpost] Page {page_num}: found {len(cards)} cards")

                if not cards:
                    logger.info(f"[Devpost] No cards on page {page_num} — stopping")
                    break

                for card in cards:
                    try:
                        record = await self._parse_card(card, page)
                        if record and record.get("source_url") and record.get("title"):
                            results.append(record)
                    except Exception as exc:
                        logger.debug(f"[Devpost] Card parse error: {exc}")
                        continue

            await browser.close()

        logger.info(f"[Devpost] Total extracted: {len(results)} hackathons")
        return results

    async def _parse_card(self, card, page) -> Optional[dict]:
        """
        Extract all required fields from a single .hackathon-tile element.

        Confirmed selectors from live HTML:
          - a.tile-anchor       → href = full URL to hackathon
          - h3                  → title text
          - .host-label         → organizer name
          - .submission-period  → date range ("Apr 09 - May 20, 2026")
          - .prize-amount       → prize money
          - .info-with-icon span → location info ("Online" / city)

        Args:
            card: Playwright ElementHandle for the .hackathon-tile
            page: Playwright Page (not used here but kept for consistency)

        Returns:
            Opportunity dict or None if card is invalid
        """
        # ── Link / source URL (a.tile-anchor is the main wrapper link) ──
        link_el = await card.query_selector("a.tile-anchor")
        if not link_el:
            link_el = await card.query_selector("a[href]")
        href = await link_el.get_attribute("href") if link_el else ""
        if href and href.startswith("/"):
            href = f"https://devpost.com{href}"
            
        import urllib.parse
        if href:
            parsed = urllib.parse.urlparse(href)
            hostname = parsed.hostname or ""
            if hostname.endswith("devpost.com") and hostname != "devpost.com":
                subdomain = hostname.split(".")[0]
                query_params = urllib.parse.parse_qs(parsed.query)
                ref_feature = query_params.get("ref_feature", ["challenge"])[0]
                href = f"https://{subdomain}.devpost.com/?ref_feature={ref_feature}&ref_medium=discover"
            elif "/hackathons/" in href:
                slug = href.split("/hackathons/")[-1].split("?")[0].strip("/")
                href = f"https://{slug}.devpost.com/?ref_feature=challenge&ref_medium=discover"

        # ── Title (h3 inside .content) ──────────────────────────────────
        title_el = await card.query_selector("h3, h2, .content h4")
        title = (await title_el.inner_text()).strip() if title_el else ""

        # ── Organizer (.host-label) ──────────────────────────────────────
        org_el = await card.query_selector(".host-label")
        organizer = (await org_el.inner_text()).strip() if org_el else ""
        # Clean up icon text from .host-label
        organizer = organizer.replace("", "").strip()

        # ── Deadline (.submission-period: "Apr 09 - May 20, 2026") ──────
        deadline = None
        date_el = await card.query_selector(".submission-period")
        if date_el:
            date_text = (await date_el.inner_text()).strip()
            # "Apr 09 - May 20, 2026" → take the END date (after " - ")
            if " - " in date_text:
                end_part = date_text.split(" - ")[-1]
                deadline = self._parse_date(end_part)
            else:
                deadline = self._parse_date(date_text)

        # ── Location ────────────────────────────────────────────────────
        # Check full card text for "Online" / "Virtual" keywords
        card_text = (await card.inner_text()).lower()
        if any(kw in card_text for kw in ["online", "virtual", "remote", "worldwide"]):
            location = "Remote"
        else:
            # Try to get location from info-with-icon spans
            info_spans = await card.query_selector_all(".info-with-icon .info span")
            location_parts = []
            for span in info_spans:
                text = (await span.inner_text()).strip()
                if text and text.lower() not in ["online", ""]:
                    location_parts.append(text)
            location = ", ".join(location_parts) if location_parts else "Global"

        # ── Description (prize amount + themes) ─────────────────────────
        prize_el = await card.query_selector(".prize-amount")
        prize_text = (await prize_el.inner_text()).strip() if prize_el else ""

        theme_els = await card.query_selector_all(".theme-label")
        themes = []
        for el in theme_els:
            t = (await el.inner_text()).strip()
            if t:
                themes.append(t)

        description = ""
        if prize_text:
            description += f"Prize: {prize_text} in prizes. "
        if themes:
            description += f"Themes: {', '.join(themes)}."
        description = description.strip()[:500]

        # Numerical prize pool parsing (e.g. "$15,000" -> 15000.0)
        import re
        prize_val = 0.0
        if prize_text:
            cleaned = prize_text.replace(",", "")
            match = re.search(r'\$?(\d+)', cleaned)
            if match:
                try:
                    prize_val = float(match.group(1))
                except ValueError:
                    pass

        # Extract applicant/participant count from card inner text if present
        num_apps = None
        card_text = (await card.inner_text()).lower()
        m = re.search(r'(\d+[\d,.]*)\s*(?:participants|registered|applicants)', card_text)
        if m:
            try:
                num_apps = int(m.group(1).replace(",", ""))
            except ValueError:
                pass

        if not title or not href:
            return None

        return self._make_result(
            title=title,
            organizer=organizer,
            location=location,
            deadline=deadline,
            description=description,
            source_url=href,
            prize_pool=prize_val,
            prize_pool_display=prize_text or "No prizes",
            num_applicants=num_apps,
            is_hackathon=1,
        )

    @staticmethod
    def _parse_date(text: str) -> Optional[date]:
        """
        Parse a free-text date string into a date object.
        Returns None if parsing fails (never crashes).
        """
        if not text:
            return None
        # Skip rolling/unknown indicators
        skip_words = ["rolling", "ongoing", "tbd", "tba", "open", "no deadline"]
        if any(w in text.lower() for w in skip_words):
            return None
        try:
            return dateparser.parse(text, fuzzy=True).date()
        except (ValueError, OverflowError, TypeError, AttributeError):
            return None
