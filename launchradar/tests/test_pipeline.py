# tests/test_pipeline.py — Unit tests for the data pipeline logic
from datetime import date, timedelta
import pytest
from sqlalchemy import select

from pipeline import process_results, expire_old_opportunities
from models import Opportunity
from tests.conftest import make_test_record
from unittest.mock import patch

# A mock for the AI tagger to prevent real API calls during tests
async def mock_tag_opportunities(records):
    for r in records:
        r["funding_range"] = "Unknown"
        r["startup_stage"] = "Unknown"
        r["remote_or_onsite"] = "Unknown"
    return records

async def mock_verify_link(url):
    return True


@pytest.mark.asyncio
@patch("pipeline.tag_opportunities", side_effect=mock_tag_opportunities)
@patch("pipeline.verify_link_resolves", side_effect=mock_verify_link)
async def test_url_dedup(mock_verify, mock_tag, test_db):
    """Test Tier 1 dedup: identical source_url is blocked."""
    record = make_test_record(source_url="https://example.com/opp1")
    
    # First insert
    total1, new1 = await process_results([record], test_db)
    assert total1 == 1
    assert new1 == 1
    
    # Second insert with exact same URL
    total2, new2 = await process_results([record], test_db)
    assert total2 == 1
    assert new2 == 0  # Deduplicated


@pytest.mark.asyncio
@patch("pipeline.tag_opportunities", side_effect=mock_tag_opportunities)
@patch("pipeline.verify_link_resolves", side_effect=mock_verify_link)
async def test_title_organizer_deadline_dedup(mock_verify, mock_tag, test_db):
    """Test Title + Organizer + Deadline dedup per MIDWAY READNE.md."""
    r1 = make_test_record(
        title="Y Combinator 2025 Summer Batch", 
        organizer="Y Combinator",
        deadline=date(2025, 6, 1),
        source_url="https://a.com/1"
    )
    r2 = make_test_record(
        title="Y Combinator 2025 Summer Batch", 
        organizer="Y Combinator",
        deadline=date(2025, 6, 1),
        source_url="https://a.com/2" # different URL
    )
    
    _, new1 = await process_results([r1], test_db)
    assert new1 == 1
    
    _, new2 = await process_results([r2], test_db)
    assert new2 == 0  # Title + Organizer + Deadline match -> deduplicated


@pytest.mark.asyncio
@patch("pipeline.tag_opportunities", side_effect=mock_tag_opportunities)
@patch("pipeline.verify_link_resolves", side_effect=mock_verify_link)
async def test_different_deadline_no_dedup(mock_verify, mock_tag, test_db):
    """Test that different deadline allows both entries even if title/organizer match."""
    r1 = make_test_record(
        title="AI Startup Grant 2025", 
        organizer="F6S",
        deadline=date(2025, 6, 1),
        source_url="https://f6s.com/1"
    )
    r2 = make_test_record(
        title="AI Startup Grant 2025", 
        organizer="F6S",
        deadline=date(2025, 7, 1), # Different deadline!
        source_url="https://devpost.com/1"
    )
    
    _, new1 = await process_results([r1], test_db)
    assert new1 == 1
    
    _, new2 = await process_results([r2], test_db)
    assert new2 == 1  # Different deadline -> allowed


@pytest.mark.asyncio
@patch("pipeline.tag_opportunities", side_effect=mock_tag_opportunities)
@patch("pipeline.verify_link_resolves", side_effect=mock_verify_link)
async def test_expiry_logic(mock_verify, mock_tag, test_db):
    """Test that expire_old_opportunities correctly marks past deadlines."""
    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)
    
    r_expired = make_test_record(title="Expired Grant", deadline=yesterday, source_url="https://example.com/1")
    r_active = make_test_record(title="Active Grant", deadline=tomorrow, source_url="https://example.com/2")
    r_nodeadline = make_test_record(title="Rolling Grant", deadline=None, source_url="https://example.com/3")
    
    await process_results([r_expired, r_active, r_nodeadline], test_db)
    
    # Run expiry task
    expired_count = await expire_old_opportunities(test_db)
    assert expired_count == 1
    
    # Verify in DB
    result = await test_db.execute(select(Opportunity.status).where(Opportunity.source_url == "https://example.com/1"))
    assert result.scalar() == "expired"
    
    result = await test_db.execute(select(Opportunity.status).where(Opportunity.source_url == "https://example.com/2"))
    assert result.scalar() == "active"
    
    result = await test_db.execute(select(Opportunity.status).where(Opportunity.source_url == "https://example.com/3"))
    assert result.scalar() == "active"
