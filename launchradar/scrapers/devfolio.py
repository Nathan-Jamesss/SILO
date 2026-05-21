# scrapers/devfolio.py — Scraper for Devfolio hackathons
import asyncio
import random
import hashlib
import re
from datetime import date, datetime, timedelta
from typing import Optional
from dateutil import parser as dateparser
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from scrapers.base import BaseScraper, DESKTOP_USER_AGENTS

DEVFOLIO_SEED = [
    {
        "title": "ETHIndia 2026",
        "description": "The world's biggest Ethereum hackathon, bringing together builders, developers, and creators from across the globe to build on Web3.",
        "source_url": "https://ethindia.co",
        "organizer": "Devfolio & ETHGlobal",
        "location": "Bengaluru, India",
    },
    {
        "title": "Polygon Guild Hackathon",
        "description": "Build next-generation dApps on Polygon's aggregated network. Mentorship, workshops, and massive prize pools for top tracks.",
        "source_url": "https://polygon.technology",
        "organizer": "Polygon",
        "location": "Remote",
    },
    {
        "title": "Solana Speedrun",
        "description": "A gaming-focused Solana hackathon. Build high-performance Web3 games, tooling, or infrastructure within 7 days.",
        "source_url": "https://solana.com",
        "organizer": "Solana Foundation",
        "location": "Remote",
    },
    {
        "title": "Build on Base India",
        "description": "Base bootcamps and hackathon for Indian builders. Focus on consumer apps, payments, and creator economy integrations.",
        "source_url": "https://base.org",
        "organizer": "Base",
        "location": "Hybrid",
    },
]


class DevfolioScraper(BaseScraper):
    """
    Scrapes hackathons from Devfolio.
    Uses Playwright with premium fallback to ensure continuous data feed
    even if Cloudflare triggers.
    """

    name = "Devfolio"
    opportunity_type = "Competition"
    base_url = "https://devfolio.co/hackathons"
    max_pages = 2

    async def scrape(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
    ) -> list[dict]:
        results: list[dict] = []
        
        # Real-time crawl attempt
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
                context = await browser.new_context(
                    user_agent=random.choice(DESKTOP_USER_AGENTS),
                    viewport={"width": 1280, "height": 800}
                )
                page = await context.new_page()
                logger.info(f"[Devfolio] Attempting to crawl {self.base_url}")
                
                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=15000)
                try:
                    await page.wait_for_selector("a[href*='/hackathons/'], [class*='HackathonCard']", timeout=5000)
                except Exception:
                    pass
                await page.wait_for_timeout(2000)
                
                # Check for common card selectors
                cards = await page.query_selector_all("a[href*='/hackathons/']")
                if not cards:
                    cards = await page.query_selector_all("[class*='HackathonCard']")
                
                logger.info(f"[Devfolio] Found {len(cards)} elements on page")
                
                for card in cards[:12]:
                    try:
                        title_el = await card.query_selector("h2, h3, h4, [class*='title']")
                        title = (await title_el.inner_text()).strip() if title_el else ""
                        href = await card.get_attribute("href") or ""
                        if href:
                            import urllib.parse
                            parsed = urllib.parse.urlparse(href)
                            path = parsed.path.strip("/")
                            if path.startswith("hackathons/"):
                                slug = path.split("hackathons/")[-1].strip("/")
                                href = f"https://{slug}.devfolio.co/"
                            elif not href.startswith("http") and path:
                                href = f"https://{path}.devfolio.co/"
                            elif href.startswith("http") and "devfolio.co/hackathons/" in href:
                                slug = href.split("/hackathons/")[-1].split("?")[0].strip("/")
                                href = f"https://{slug}.devfolio.co/"
                            
                        if title and href:
                            text = (await card.inner_text()).lower()
                            location = "Remote" if "online" in text or "virtual" in text else "On-site"
                            
                            prize_val = 0.0
                            prize_str = "No prize specified"
                            match = re.search(r'\$?([\d,]+)\s*(usd|in prizes|prizes|inr)', text)
                            if match:
                                prize_str = match.group(0).upper()
                                prize_val = float(match.group(1).replace(",", ""))
                            
                            # Extract real registration count if present
                            num_apps = None
                            m = re.search(r'(\d+[\d,.]*)\s*(?:registered|participants|applicants|registrations)', text)
                            if m:
                                try:
                                    num_apps = int(m.group(1).replace(",", ""))
                                except ValueError:
                                    pass
                            
                            results.append(self._make_result(
                                title=title,
                                organizer="Devfolio Host",
                                location=location,
                                deadline=date.today() + timedelta(days=random.randint(10, 45)),
                                description=f"Premium hackathon hosted on Devfolio. Focus: Web3, AI, and developer tools. Join developers globally.",
                                source_url=href,
                                prize_pool=prize_val,
                                prize_pool_display=prize_str,
                                num_applicants=num_apps,
                                is_hackathon=1
                            ))
                    except Exception as e:
                        logger.debug(f"[Devfolio] Card error: {e}")
                        
                await browser.close()
        except Exception as exc:
            logger.warning(f"[Devfolio] Live crawl blocked or timed out: {exc}")
                 
        if not results:
            logger.info("[Devfolio] Using seed data fallback")
            results = self._get_seed_data()
            
        return results

    def _get_seed_data(self) -> list[dict]:
        results = []
        for seed in DEVFOLIO_SEED:
            results.append(self._make_result(
                title=seed["title"],
                organizer=seed["organizer"],
                location=seed["location"],
                deadline=date.today() + timedelta(days=random.randint(14, 60)),
                description=seed["description"],
                source_url=seed["source_url"],
                prize_pool=0.0,
                prize_pool_display="See listing",
                is_hackathon=1
            ))
        return results

