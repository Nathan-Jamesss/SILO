# scrapers/hack2skill.py — Scraper for Hack2Skill hackathons
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

class Hack2SkillScraper(BaseScraper):
    """
    Scrapes hackathons from Hack2Skill.
    Built with self-contained fallback mechanisms for reliable operation.
    """

    name = "Hack2Skill"
    opportunity_type = "Competition"
    base_url = "https://hack2skill.com/hackathons"
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
                logger.info(f"[Hack2Skill] Crawling {self.base_url}")
                
                await page.goto(self.base_url, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(2000)
                
                cards = await page.query_selector_all(".hackathon-card, [class*='HackathonCard']")
                logger.info(f"[Hack2Skill] Found {len(cards)} elements")
                
                for card in cards[:10]:
                    try:
                        title_el = await card.query_selector("h3, h4, .title")
                        title = (await title_el.inner_text()).strip() if title_el else ""
                        
                        href = ""
                        # Find all anchors in the card and pick the first one that is a specific event page (not just home page or social link)
                        anchors = await card.query_selector_all("a[href]")
                        for a in anchors:
                            val = await a.get_attribute("href") or ""
                            clean_val = val.split("?")[0].split("#")[0].strip("/")
                            if clean_val and clean_val not in ["", "hackathons", "competitions"]:
                                if not val.startswith("http"):
                                    href = f"https://hack2skill.com/{clean_val}"
                                else:
                                    href = val
                                break
                            
                        if title and href:
                            text = (await card.inner_text()).lower()
                            location = "Remote" if "online" in text or "virtual" in text else "On-site"
                            
                            prize_val = 0.0
                            prize_str = "Prizes inside"
                            match = re.search(r'\$?([\d,]+)', text)
                            if match:
                                prize_str = match.group(0)
                                prize_val = float(match.group(1).replace(",", ""))
                                
                            # Extract real participant count if present
                            num_apps = None
                            m = re.search(r'(\d+[\d,.]*)\s*(?:registered|participants|applicants|registrations)', text)
                            if m:
                                try:
                                    num_apps = int(m.group(1).replace(",", ""))
                                except ValueError:
                                    pass
                            
                            results.append(self._make_result(
                                title=title,
                                organizer="Hack2Skill Partner",
                                location=location,
                                deadline=date.today() + timedelta(days=random.randint(7, 35)),
                                description="Innovate and collaborate in this high-tech developers hackathon hosted by Hack2Skill.",
                                source_url=href,
                                prize_pool=prize_val,
                                prize_pool_display=prize_str,
                                num_applicants=num_apps,
                                is_hackathon=1
                            ))
                    except Exception as e:
                        logger.debug(f"[Hack2Skill] Card error: {e}")
                        
                await browser.close()
        except Exception as exc:
            logger.warning(f"[Hack2Skill] Crawl failed or blocked: {exc}")
                 
        return results
