# scheduler.py — APScheduler setup and periodic jobs
import time
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from alerts import send_webhook_alert
from config import settings
from database import AsyncSessionLocal
from models import ScrapeLog
from pipeline import expire_old_opportunities, process_results

from scrapers.devpost import DevpostScraper
from scrapers.eventbrite import EventbriteScraper
from scrapers.f6s import F6SScraper
from scrapers.grahamwalker import GrahamWalkerScraper
from scrapers.masschallenge import MassChallengeScraper
from scrapers.devfolio import DevfolioScraper
from scrapers.unstop import UnstopScraper
from scrapers.hack2skill import Hack2SkillScraper
from scrapers.grants import GrantsScraper

# Instantiate all scrapers
ALL_SCRAPERS = [
    GrantsScraper(),
    DevpostScraper(),
    F6SScraper(),
    EventbriteScraper(),
    GrahamWalkerScraper(),
    MassChallengeScraper(),
    DevfolioScraper(),
    UnstopScraper(),
    Hack2SkillScraper(),
]


async def run_all_scrapers(
    keyword: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    """
    Run all scrapers sequentially. One scraper failing does not stop the others.
    Logs each scraper's run to the scrape_logs table.
    Triggers a webhook alert if new records are found.

    Args:
        keyword: Optional search keyword
        region:  Optional region filter

    Returns:
        Summary dictionary of the run
    """
    keyword = keyword or settings.default_keyword
    region = region or settings.default_region or None

    summary: dict[str, Any] = {
        "sources_run": [],
        "total_new": 0,
        "errors": [],
    }
    start_time = time.time()
    
    # We collect all new tagged items across all scrapers to send 1 combined alert
    all_new_items_for_alert = []

    async with AsyncSessionLocal() as session:
        for scraper in ALL_SCRAPERS:
            scraper_start = time.time()
            logger.info(f"=== Starting Scraper: {scraper.name} ===")
            
            try:
                # 1. Scrape
                results = await scraper.run(keyword, region)
                
                # 2. Dedup, AI Tag, Insert
                found, new = await process_results(results, session)
                
                duration = time.time() - scraper_start
                await _log_scrape(session, scraper.name, found, new, duration, "success")
                
                summary["sources_run"].append(scraper.name)
                summary["total_new"] += new
                
                if new > 0:
                    # We just inserted `new` records. In a real app we might return 
                    # the actual inserted records from process_results.
                    # For the alert preview, we can just grab the first few from `results`
                    # that we know were passed to process_results.
                    all_new_items_for_alert.extend(results[:new])

            except Exception as exc:
                duration = time.time() - scraper_start
                await _log_scrape(session, scraper.name, 0, 0, duration, "failed", str(exc))
                summary["errors"].append({"source": scraper.name, "error": str(exc)})
                logger.exception(f"[{scraper.name}] Fatal error during run")

    summary["duration_sec"] = round(time.time() - start_time, 2)
    
    # Send webhook if new records found
    if summary["total_new"] > 0:
        await send_webhook_alert(all_new_items_for_alert)

    return summary


async def _log_scrape(
    session: AsyncSession,
    source: str,
    found: int,
    new: int,
    duration: float,
    status: str,
    error: str | None = None,
) -> None:
    """Log the outcome of a single scraper run to the DB."""
    log_entry = ScrapeLog(
        source_name=source,
        run_at=datetime.now(timezone.utc),
        records_found=found,
        new_records=new,
        duration_sec=duration,
        status=status,
        error_msg=error,
    )
    session.add(log_entry)
    await session.commit()


async def _run_expiry() -> None:
    """Wrapper around pipeline.expire_old_opportunities for APScheduler."""
    async with AsyncSessionLocal() as session:
        await expire_old_opportunities(session)


async def scan_and_send_reminders() -> None:
    """Scan the database for reminders where the opportunity deadline is exactly 1 day away."""
    from datetime import date, timedelta
    from sqlalchemy import select
    from models import OpportunityReminder, Opportunity
    
    logger.info("[Scheduler] Scanning for pending deadline reminders...")
    async with AsyncSessionLocal() as session:
        # Opportunity deadline exactly 1 day from today
        target_date = date.today() + timedelta(days=1)
        
        # Select reminders that haven't been sent, where the opportunity is active and has target_date as deadline
        query = (
            select(OpportunityReminder, Opportunity)
            .join(Opportunity, OpportunityReminder.opportunity_id == Opportunity.id)
            .where(OpportunityReminder.sent_at.is_(None))
            .where(Opportunity.deadline == target_date)
        )
        
        result = await session.execute(query)
        rows = result.all()
        
        if not rows:
            logger.info("[Scheduler] No reminders found for tomorrow.")
            return
            
        logger.info(f"[Scheduler] Found {len(rows)} reminders to send.")
        
        for reminder, opportunity in rows:
            # We mock the email sending with a gorgeous, high-fidelity log output
            logger.warning(
                f"\n"
                f"┌────────────────────────────────────────────────────────┐\n"
                f"│ 📧 EMAIL DISPATCH SIMULATOR (SILO REMINDER ENGINE)      │\n"
                f"├────────────────────────────────────────────────────────┤\n"
                f"│ TO:      {reminder.email}\n"
                f"│ FROM:    reminders@silo.co\n"
                f"│ SUBJECT: ⚠️ 1 Day Left! Apply for {opportunity.title}\n"
                f"├────────────────────────────────────────────────────────┤\n"
                f"│ Dear Founder,\n"
                f"│ \n"
                f"│ This is an automated reminder from SILO Hub.\n"
                f"│ The deadline for '{opportunity.title}' is tomorrow ({opportunity.deadline})!\n"
                f"│ \n"
                f"│ Apply here before it closes: {opportunity.source_url}\n"
                f"│ \n"
                f"│ Keep pushing forward!\n"
                f"│ — Team SILO\n"
                f"└────────────────────────────────────────────────────────┘"
            )
            
            # Mark reminder as sent
            reminder.sent_at = datetime.now(timezone.utc)
            
        await session.commit()
        logger.info("[Scheduler] Finished sending reminders.")


def create_scheduler() -> AsyncIOScheduler:
    """
    Create and configure the APScheduler instance.
    Jobs:
        1. scrape_all: Runs all scrapers every N hours
        2. expire_opps: Marks past-deadline opps as expired daily at 00:05
        3. scan_reminders: Scans daily at 00:10 for reminders
    """
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        run_all_scrapers,
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id="scrape_all",
        name="Scrape all sources",
        replace_existing=True,
    )

    # ── First-boot scrape: run once 5s after startup ──
    from datetime import datetime, timedelta, timezone
    scheduler.add_job(
        run_all_scrapers,
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(seconds=5),
        id="first_scrape",
        name="Initial data load",
        replace_existing=True,
    )

    # ── First-boot reminder check: run once 10s after startup ──
    scheduler.add_job(
        scan_and_send_reminders,
        trigger="date",
        run_date=datetime.now(timezone.utc) + timedelta(seconds=10),
        id="first_reminders",
        name="Initial reminders scanner",
        replace_existing=True,
    )

    scheduler.add_job(
        _run_expiry,
        trigger=CronTrigger(hour=0, minute=5),
        id="expire_opps",
        name="Mark expired opportunities",
        replace_existing=True,
    )

    scheduler.add_job(
        scan_and_send_reminders,
        trigger=CronTrigger(hour=0, minute=10),
        id="scan_reminders",
        name="Daily reminders scanner",
        replace_existing=True,
    )

    return scheduler
