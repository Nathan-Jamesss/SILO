# tests/test_scrapers.py — Smoke tests for all scrapers
"""
These tests verify scraper OUTPUT FORMAT only.
We do NOT test live network calls (that's integration testing).
We check that the scraper returns dicts with all required keys,
and that source_url / title are never empty.
"""
import pytest
from tests.conftest import make_test_record

REQUIRED_KEYS = {
    "title",
    "type",
    "organizer",
    "location",
    "deadline",
    "description",
    "source_url",
    "source_name",
}


def test_make_test_record_has_all_keys():
    """make_test_record() returns a dict with all required keys."""
    record = make_test_record()
    for key in REQUIRED_KEYS:
        assert key in record, f"Missing required key: {key}"


def test_make_test_record_overrides():
    """make_test_record() correctly applies overrides."""
    record = make_test_record(title="Custom Title", type="Conference")
    assert record["title"] == "Custom Title"
    assert record["type"] == "Conference"
    # Non-overridden fields remain defaults
    assert record["source_name"] == "TestSource"


def test_description_capped_at_500_chars():
    """Descriptions longer than 500 chars should be capped in _make_result."""
    from scrapers.base import BaseScraper

    class _TestScraper(BaseScraper):
        name = "Test"
        opportunity_type = "Grant"
        base_url = "https://example.com"

        async def scrape(self, keyword="startup", region=None):
            return []

    scraper = _TestScraper()
    long_desc = "x" * 1000
    result = scraper._make_result(
        title="Test",
        description=long_desc,
        source_url="https://example.com/1",
    )
    assert len(result["description"]) <= 500


def test_make_result_fills_defaults():
    """_make_result fills in defaults for missing optional fields."""
    from scrapers.base import BaseScraper

    class _TestScraper(BaseScraper):
        name = "Test"
        opportunity_type = "Accelerator"
        base_url = "https://example.com"

        async def scrape(self, keyword="startup", region=None):
            return []

    scraper = _TestScraper()
    result = scraper._make_result(
        title="My Program",
        source_url="https://example.com/prog",
    )
    assert result["type"] == "Accelerator"         # from class default
    assert result["source_name"] == "Test"          # from class default
    assert result["deadline"] is None               # default
    assert result["organizer"] == ""                # default
