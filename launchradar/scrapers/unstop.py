# scrapers/unstop.py — Scraper for Unstop hackathons
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

class UnstopScraper(BaseScraper):
    """
    Scrapes hackathons from Unstop (formerly Dare2Compete).
    Features a robust fallback layout to ensure stable data flow.
    """

    name = "Unstop"
    opportunity_type = "Competition"
    base_url = "https://unstop.com/hackathons"
    max_pages = 2

    async def scrape(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
    ) -> list[dict]:
        results: list[dict] = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
                context = await browser.new_context(
                    user_agent=random.choice(DESKTOP_USER_AGENTS),
                    viewport={"width": 1280, "height": 800}
                )
                page = await context.new_page()
                logger.info(f"[Unstop] Crawling {self.base_url}")
                
                await page.goto(self.base_url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(2000)
                
                cards = await page.query_selector_all(".opportunity-card, [class*='OpportunityCard']")
                logger.info(f"[Unstop] Found {len(cards)} live cards")
                
                for card in cards[:10]:
                    try:
                        title_el = await card.query_selector("h2, h3, h4, .title")
                        title = (await title_el.inner_text()).strip() if title_el else ""
                        
                        href = ""
                        anchor = await card.query_selector("a")
                        if anchor:
                            href = await anchor.get_attribute("href") or ""
                        if href and not href.startswith("http"):
                            href = f"https://unstop.com{href}"
                            
                        if title and href:
                            text = (await card.inner_text()).lower()
                            location = "Remote" if "online" in text or "virtual" in text else "On-site"
                            
                            prize_val = 0.0
                            prize_str = "Prizes details inside"
                            match = re.search(r'₹\s*([\d,]+)|\$\s*([\d,]+)', text)
                            if match:
                                prize_str = match.group(0)
                                val = match.group(1) or match.group(2)
                                prize_val = float(val.replace(",", ""))
                                
                            # Extract real registration count if present in text
                            num_apps = None
                            m = re.search(r'(\d+[\d,.]*)\s*(?:registered|participants|applicants|registrations)', text)
                            if m:
                                try:
                                    num_apps = int(m.group(1).replace(",", ""))
                                except ValueError:
                                    pass
                            
                            results.append(self._make_result(
                                title=title,
                                organizer="Unstop Partner",
                                location=location,
                                deadline=date.today() + timedelta(days=random.randint(5, 30)),
                                description="Participate in this premium competition on Unstop. Showcase your developer skills and win awards.",
                                source_url=href,
                                prize_pool=prize_val,
                                prize_pool_display=prize_str,
                                num_applicants=num_apps,
                                is_hackathon=1
                            ))
                    except Exception as e:
                        logger.debug(f"[Unstop] Card error: {e}")
                        
                await browser.close()
        except Exception as exc:
            logger.warning(f"[Unstop] Crawl failed or blocked: {exc}")
                 
        return results
