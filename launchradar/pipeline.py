# pipeline.py — Deduplication, upsert, and expiry logic
import httpx
from datetime import date, datetime, timezone
from typing import Optional

from loguru import logger
from rapidfuzz import fuzz
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Opportunity
from ai_tagger import tag_opportunities


async def verify_link_resolves(url: str) -> bool:
    """
    Verifies that the link resolves to a valid, direct page.
    For hackathons specifically:
    - Retries once if there is a redirection/hindrance/404/wrong page.
    - Ensures it doesn't just go to a generic organizer homepage (like devpost.com main page).
    """
    if not url:
        return False
        
    async def attempt():
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(
                    url, 
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
                )
                if resp.status_code >= 400:
                    return False
                # If it's a Devpost link, ensure the resolved URL doesn't redirect to devpost.com homepage
                resolved_url = str(resp.url)
                if "devpost.com" in url:
                    if resolved_url.strip("/").endswith("devpost.com") or resolved_url.strip("/").endswith("devpost.com/hackathons"):
                        return False
                return True
        except Exception:
            return False

    # Attempt 1
    if await attempt():
        return True
    # Retry once
    logger.info(f"[Link Verifier] Hindrance detected for {url}. Retrying once...")
    return await attempt()


async def process_results(
    results: list[dict],
    session: AsyncSession,
) -> tuple[int, int]:
    """
    Deduplicate and insert scraped results into the database.

    Dedup strategy (applied in order):
        1. source_url exact match  → skip
        2. Title + Organizer + Deadline match (per MIDWAY READNE.md) → skip

    Args:
        results: List of raw opportunity dicts from a scraper
        session: Async SQLAlchemy session

    Returns:
        Tuple of (total_found, new_inserted)
    """
    total = len(results)
    new_count = 0
    new_items_batch = []

    # Load existing data into memory for fast dedup checks
    existing_urls = await _get_existing_urls(session)
    existing_triplets = await _get_existing_triplets(session)

    for item in results:
        url = (item.get("source_url") or "").strip()
        title = (item.get("title") or "").strip()
        organizer = (item.get("organizer") or "").strip()
        deadline = item.get("deadline")

        if not url:
            logger.warning(f"[Pipeline] Skipping item with no source_url: '{title}'")
            continue

        if not title:
            logger.warning(f"[Pipeline] Skipping item with no title: {url}")
            continue

        # ── Tier 1: Exact URL dedup ───────────────────────────────
        if url in existing_urls:
            logger.debug(f"[Pipeline] URL dedup skip: {url}")
            continue

        # ── Tier 2: Title + Organizer + Deadline dedup ────────────
        triplet = (title.lower().strip(), organizer.lower().strip(), deadline)
        if triplet in existing_triplets:
            logger.debug(f"[Pipeline] Title+Organizer+Deadline dedup skip: '{title}'")
            continue

        # ── Tier 3: Link Verification (Fix 4) ─────────────────────
        is_hack = item.get("is_hackathon", 1)
        if is_hack:
            resolves = await verify_link_resolves(url)
            if not resolves:
                logger.warning(f"[Pipeline] Discarding hackathon due to broken/homepage link: '{title}' ({url})")
                continue

        # Add to batch for AI tagging
        new_items_batch.append(item)

        # Update in-memory sets to prevent duplicates within this batch
        existing_urls.add(url)
        existing_triplets.add(triplet)

    if not new_items_batch:
        logger.info(f"[Pipeline] No new records from {total} results (all duplicates or broken links)")
        return total, 0

    # ── AI Tagging ────────────────────────────────────────────
    logger.info(f"[Pipeline] Running AI tagger on {len(new_items_batch)} new records...")
    tagged_items = await tag_opportunities(new_items_batch)

    # ── Insert new records ────────────────────────────────────
    now = datetime.now(timezone.utc)
    for item in tagged_items:
        opp = Opportunity(
            title=item.get("title", ""),
            type=item.get("type", ""),
            organizer=item.get("organizer", ""),
            location=item.get("location", ""),
            deadline=item.get("deadline"),
            description=(item.get("description") or "")[:500],
            source_url=item.get("source_url", ""),
            source_name=item.get("source_name", ""),
            status="active",
            funding_range=item.get("funding_range"),
            startup_stage=item.get("startup_stage"),
            remote_or_onsite=item.get("remote_or_onsite"),
            prize_pool=float(item.get("prize_pool", 0.0) or 0.0),
            prize_pool_display=item.get("prize_pool_display", ""),
            num_applicants=int(item.get("num_applicants", 0) or 0),
            is_hackathon=int(item.get("is_hackathon", 1) if item.get("is_hackathon") is not None else 1),
            sector=item.get("sector", "General"),
            ai_tagged_at=now,
        )
        session.add(opp)
        new_count += 1

    await session.commit()
    logger.info(f"[Pipeline] Committed {new_count} new records (of {total} found)")

    return total, new_count


async def _get_existing_urls(session: AsyncSession) -> set[str]:
    """Load all existing source_urls from DB into a set for O(1) lookup."""
    result = await session.execute(select(Opportunity.source_url))
    return set(result.scalars().all())


async def _get_existing_triplets(session: AsyncSession) -> set[tuple[str, str, Optional[date]]]:
    """Load all existing (Title, Organizer, Deadline) keys from DB into a set for O(1) deduplication."""
    result = await session.execute(
        select(Opportunity.title, Opportunity.organizer, Opportunity.deadline)
    )
    triplets = set()
    for t_title, t_org, t_dl in result.all():
        triplets.add(
            (
                (t_title or "").strip().lower(),
                (t_org or "").strip().lower(),
                t_dl,
            )
        )
    return triplets


async def expire_old_opportunities(session: AsyncSession) -> int:
    """
    Mark all active opportunities with a past deadline as 'expired'.
    Called nightly by APScheduler.

    Args:
        session: Async SQLAlchemy session

    Returns:
        Count of records updated
    """
    today = date.today()
    result = await session.execute(
        update(Opportunity)
        .where(
            Opportunity.deadline < today,
            Opportunity.status == "active",
        )
        .values(status="expired")
    )
    await session.commit()
    count = result.rowcount
    if count:
        logger.info(f"[Pipeline] Expired {count} past-deadline opportunities")
    return count
