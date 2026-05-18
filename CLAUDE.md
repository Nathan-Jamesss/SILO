# CLAUDE.md — LaunchRadar Project Intelligence File
> **READ THIS ENTIRE FILE BEFORE WRITING A SINGLE LINE OF CODE.**
> This file is the single source of truth for the LaunchRadar project.
> Every architectural decision, file location, naming convention, tool choice,
> and implementation detail is specified here. Do not deviate without explicit instruction.

---

## TABLE OF CONTENTS

1. [Project Overview & Mission](#1-project-overview--mission)
2. [Tech Stack — Tools & Why](#2-tech-stack--tools--why)
3. [Complete Folder Structure](#3-complete-folder-structure)
4. [Database Schema](#4-database-schema)
5. [Environment Variables](#5-environment-variables)
6. [Phase 1 — Scaffold & Database](#phase-1--scaffold--database)
7. [Phase 2 — Base Scraper + Devpost + F6S](#phase-2--base-scraper--devpost--f6s)
8. [Phase 3 — More Sources + Scheduler](#phase-3--more-sources--scheduler)
9. [Phase 4 — Dashboard UI](#phase-4--dashboard-ui)
10. [Phase 5 — AI Tagging](#phase-5--ai-tagging)
11. [Phase 6 — Export, Alerts, Tests, README](#phase-6--export-alerts-tests-readme)
12. [Coding Standards](#12-coding-standards)
13. [Testing Strategy](#13-testing-strategy)
14. [Anti-Scraping Rules](#14-anti-scraping-rules)
15. [Common Pitfalls — Do Not Do These](#15-common-pitfalls--do-not-do-these)

---

## 1. Project Overview & Mission

**Project Name:** LaunchRadar  
**Tagline:** Real-time startup opportunity intelligence — grants, accelerators, conferences, competitions in one place.

### What It Does
LaunchRadar is a web application that:
1. **Scrapes** startup opportunities (grants, accelerators, conferences, competitions, fellowships) from 5+ public sources on a schedule
2. **Stores** them deduplicated in a local SQLite database
3. **Tags** each opportunity with AI-extracted metadata (funding range, startup stage, remote/onsite)
4. **Displays** them in a searchable, filterable dashboard
5. **Exports** filtered results to CSV/JSON
6. **Alerts** via webhook when new matching opportunities are found

### What Makes It Different From Other Tools
- **Real-time**: Scrapes every 6 hours automatically, not monthly curated lists
- **Multi-type**: Grants + Accelerators + Conferences + Competitions + Fellowships all in one feed
- **AI-tagged**: Claude API auto-extracts funding range, startup stage, remote vs onsite
- **Deadline urgency**: Visual badge system (red <7d, amber 8-30d, green >30d)
- **Fit scoring**: Opportunities scored against saved keyword profiles
- **Export**: One-click CSV/JSON with current filters applied

### Assignment Requirements Met
- ✅ Scrape from ≥2 sources (we do 5+)
- ✅ Keyword + region filter support
- ✅ Extract all required fields
- ✅ Deduplication
- ✅ SQLite storage
- ✅ Searchable dashboard
- ✅ Filter by type, source, deadline
- ✅ Auto-scheduled scraping (APScheduler)
- ✅ BONUS: AI tagging, webhook alerts, pagination, anti-scraping, CSV/JSON export

---

## 2. Tech Stack — Tools & Why

> Do not substitute these libraries unless a specific version conflict arises.
> Each choice is deliberate.

### Backend

| Layer | Library | Version | Why This One |
|-------|---------|---------|--------------|
| Web Framework | `fastapi` | latest | Async-native, auto OpenAPI docs, Jinja2 support |
| ASGI Server | `uvicorn[standard]` | latest | FastAPI's recommended server |
| ORM | `sqlalchemy[asyncio]` | latest | Async support, clean declarative models |
| Async DB Driver | `aiosqlite` | latest | SQLite async adapter for SQLAlchemy |
| HTTP Client | `httpx` | latest | Async-first, better than aiohttp for our use |
| Browser Scraping | `playwright` | latest | Handles JS-rendered pages; Devpost needs this |
| HTML Parsing | `beautifulsoup4` + `lxml` | latest | Fast HTML parsing |
| Fuzzy Dedup | `rapidfuzz` | latest | 10x faster than fuzzywuzzy, same API |
| Date Parsing | `python-dateutil` | latest | Handles any date format across sources |
| Scheduler | `apscheduler` | 3.x | Integrates cleanly with FastAPI lifespan |
| AI Tagging | `anthropic` | latest | Claude API for batch metadata extraction |
| Config | `pydantic-settings` + `python-dotenv` | latest | Type-safe .env config |
| Logging | `loguru` | latest | Structured JSON logs, colored output, file rotation |
| JSON | `orjson` | latest | 3x faster than stdlib json, handles datetimes |
| Export | `csv` (stdlib) | — | No extra dep needed |
| Testing | `pytest` + `pytest-asyncio` | latest | Async test support |

### Frontend (Zero Build Step)

| Layer | Choice | Why |
|-------|--------|-----|
| Templating | Jinja2 (via FastAPI) | Server-side rendering, no SPA complexity |
| CSS | Tailwind CSS v3 CDN | No npm needed, utility-first, fast iteration |
| JS | Alpine.js CDN | Reactive dropdowns/toggles without React overhead |
| Icons | Heroicons (inline SVG) | Clean, consistent icon set |

### requirements.txt (exact content to create)

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
aiosqlite
httpx
playwright
beautifulsoup4
lxml
rapidfuzz
python-dateutil
apscheduler==3.10.4
anthropic
pydantic-settings
python-dotenv
loguru
orjson
pytest
pytest-asyncio
jinja2
python-multipart
```

---

## 3. Complete Folder Structure

> Create this exact structure. Every file listed will be created across the phases.

```
launchradar/
│
├── CLAUDE.md                    ← This file (project brain)
├── README.md                    ← Created in Phase 6
├── requirements.txt             ← Created in Phase 1
├── .env.example                 ← Created in Phase 1
├── .env                         ← Created by user (never committed)
├── .gitignore                   ← Created in Phase 1
│
├── main.py                      ← FastAPI app entry + lifespan (Phase 1)
├── config.py                    ← Pydantic settings from .env (Phase 1)
├── models.py                    ← SQLAlchemy ORM models (Phase 1)
├── database.py                  ← DB engine + session + init (Phase 1)
├── pipeline.py                  ← Dedup + upsert + expiry logic (Phase 2)
├── ai_tagger.py                 ← Claude API batch tagging (Phase 5)
├── scheduler.py                 ← APScheduler setup + jobs (Phase 3)
├── alerts.py                    ← Webhook alert sender (Phase 6)
│
├── scrapers/
│   ├── __init__.py              ← Empty
│   ├── base.py                  ← Abstract BaseScraper class (Phase 2)
│   ├── devpost.py               ← Devpost hackathons - Playwright (Phase 2)
│   ├── f6s.py                   ← F6S accelerators - httpx (Phase 2)
│   ├── eventbrite.py            ← Eventbrite API (Phase 3)
│   ├── grahamwalker.py          ← Blog grants list - BeautifulSoup (Phase 3)
│   └── masschallenge.py         ← MassChallenge programs - httpx (Phase 3)
│
├── routers/
│   ├── __init__.py              ← Empty
│   ├── dashboard.py             ← Main UI routes (Phase 4)
│   └── api.py                   ← JSON API + export endpoints (Phase 3+6)
│
├── templates/
│   ├── base.html                ← Layout: nav, Tailwind CDN, Alpine CDN (Phase 4)
│   ├── index.html               ← Dashboard: search, filters, card grid (Phase 4)
│   └── partials/
│       └── card.html            ← Individual opportunity card (Phase 4)
│
├── static/
│   ├── favicon.ico              ← Optional
│   └── custom.css               ← Minimal overrides only (Phase 4)
│
├── tests/
│   ├── __init__.py              ← Empty
│   ├── conftest.py              ← Pytest fixtures: test DB, test client (Phase 2)
│   ├── test_scrapers.py         ← Scraper smoke tests (Phase 2)
│   └── test_pipeline.py         ← Dedup + expiry unit tests (Phase 6)
│
└── launchradar.db               ← Created automatically on first run (never commit)
```

---

## 4. Database Schema

### Table: `opportunities`

```sql
CREATE TABLE opportunities (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT NOT NULL,
    type              TEXT NOT NULL,           -- 'Grant' | 'Accelerator' | 'Conference' | 'Fellowship' | 'Competition'
    organizer         TEXT,
    location          TEXT,                    -- 'Remote' | 'New York, US' | 'Global' | eligibility text
    deadline          DATE,                    -- ISO format YYYY-MM-DD, NULL if rolling/unknown
    description       TEXT,                   -- Max 500 chars excerpt
    source_url        TEXT NOT NULL UNIQUE,    -- PRIMARY DEDUP KEY
    source_name       TEXT NOT NULL,           -- 'Devpost' | 'F6S' | 'Eventbrite' | 'Graham & Walker' | 'MassChallenge'
    status            TEXT NOT NULL DEFAULT 'active',  -- 'active' | 'expired' | 'pending'
    -- AI-tagged fields (Phase 5, all nullable until tagged)
    funding_range     TEXT,                    -- '$10K-$50K' | 'Up to $500K' | 'Equity-free' | 'Unknown'
    startup_stage     TEXT,                    -- 'Pre-seed' | 'Seed' | 'Series A' | 'Any stage' | 'Unknown'
    remote_or_onsite  TEXT,                    -- 'Remote' | 'On-site' | 'Hybrid' | 'Unknown'
    ai_tagged_at      DATETIME,               -- NULL until AI tagging runs
    -- Timestamps
    scraped_at        DATETIME NOT NULL,       -- Auto-set on insert
    updated_at        DATETIME NOT NULL        -- Auto-updated on any change
);

CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_type ON opportunities(type);
CREATE INDEX idx_opportunities_source ON opportunities(source_name);
CREATE INDEX idx_opportunities_deadline ON opportunities(deadline);
```

### Table: `scrape_logs`

```sql
CREATE TABLE scrape_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name     TEXT NOT NULL,
    run_at          DATETIME NOT NULL,
    records_found   INTEGER NOT NULL DEFAULT 0,
    new_records     INTEGER NOT NULL DEFAULT 0,
    duration_sec    FLOAT,
    status          TEXT NOT NULL,   -- 'success' | 'partial' | 'failed'
    error_msg       TEXT             -- NULL on success
);
```

### SQLAlchemy Model Notes
- Use `DateTime(timezone=True)` for all datetime columns
- Use `server_default=func.now()` for `scraped_at`
- Use `onupdate=func.now()` for `updated_at`
- Add `__repr__` to every model for debugging
- The `source_url` column has `unique=True` at the DB level — this is the hard dedup guard

---

## 5. Environment Variables

### .env.example (create this exactly)

```env
# ── Application ──────────────────────────────────────
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO

# ── Database ──────────────────────────────────────────
DATABASE_URL=sqlite+aiosqlite:///./launchradar.db

# ── Scraping ──────────────────────────────────────────
SCRAPE_INTERVAL_HOURS=6
DEFAULT_KEYWORD=startup
DEFAULT_REGION=

# ── API Keys (get free keys at the URLs below) ────────
# Anthropic: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_key_here

# Eventbrite: https://www.eventbrite.com/platform/api
EVENTBRITE_API_KEY=your_key_here

# ── Alerts (optional) ─────────────────────────────────
# Leave empty to disable webhook alerts
ALERT_WEBHOOK_URL=
```

### config.py (how to read these)

```python
# config.py — Pydantic BaseSettings reads from .env automatically
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # App
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    log_level: str = "INFO"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./launchradar.db"
    
    # Scraping
    scrape_interval_hours: int = 6
    default_keyword: str = "startup"
    default_region: str = ""
    
    # API Keys
    anthropic_api_key: str = ""
    eventbrite_api_key: str = ""
    
    # Alerts
    alert_webhook_url: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## PHASE 1 — Scaffold & Database

**Goal:** App starts, DB tables created, GET / returns 200. No scraping yet.  
**Files to create:** `requirements.txt`, `.env.example`, `.gitignore`, `config.py`, `models.py`, `database.py`, `main.py`  
**Time estimate:** ~1.5 hours  
**Test:** `uvicorn main:app --reload` → no errors → `curl localhost:8000/` returns `{"status":"ok"}`

### What to build in each file:

#### `config.py`
- Paste the exact code from Section 5 above
- Add `@lru_cache` to a `get_settings()` function so settings are loaded once
- Import `settings` singleton at module level for convenience

#### `models.py`
- Import: `sqlalchemy`, `sqlalchemy.orm`, `sqlalchemy.sql.sqltypes`
- Create `Base = declarative_base()`
- `Opportunity` model — all columns from Section 4 schema
- `ScrapeLog` model — all columns from Section 4 schema
- Add `__tablename__`, `__repr__` to both
- Use `Column(DateTime(timezone=True), server_default=func.now())` for `scraped_at`
- Use `Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())` for `updated_at`

#### `database.py`
```python
# Exact pattern to implement:
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models import Base
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

#### `main.py`
```python
# Exact structure to implement:
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import loguru

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    loguru.logger.info("Starting LaunchRadar...")
    await create_tables()
    # Phase 3: start_scheduler() goes here
    yield
    # SHUTDOWN
    loguru.logger.info("Shutting down LaunchRadar...")
    # Phase 3: scheduler.shutdown() goes here

app = FastAPI(title="LaunchRadar", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def health():
    return {"status": "ok", "app": "LaunchRadar", "version": "1.0.0"}
```

#### `.gitignore`
```
.env
*.db
__pycache__/
.pytest_cache/
.playwright/
node_modules/
*.pyc
.DS_Store
```

### Phase 1 Acceptance Criteria
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `playwright install chromium` succeeds
- [ ] `uvicorn main:app --reload` starts with no errors
- [ ] `launchradar.db` is created in project root
- [ ] `GET /` returns `{"status":"ok",...}`
- [ ] Both tables exist in DB (verify with `sqlite3 launchradar.db .tables`)

---

## PHASE 2 — Base Scraper + Devpost + F6S

**Goal:** Real data in DB from 2 sources. Dedup working.  
**Files to create:** `scrapers/__init__.py`, `scrapers/base.py`, `scrapers/devpost.py`, `scrapers/f6s.py`, `pipeline.py`, `tests/conftest.py`, `tests/test_scrapers.py`  
**Time estimate:** ~3 hours  
**Test:** Run both scrapers manually → 20+ records in DB → no duplicates on second run

### `scrapers/base.py` — Abstract Base Class

```python
# Exact interface to implement:
from abc import ABC, abstractmethod
from typing import Optional
import asyncio
import httpx
from loguru import logger

class BaseScraper(ABC):
    name: str = "base"           # Override in subclass: e.g. "Devpost"
    opportunity_type: str = ""   # Override: "Competition", "Accelerator", etc.
    base_url: str = ""           # Override: root URL of source
    
    # Rate limiting config — override in subclass
    max_concurrent: int = 3
    delay_between_pages: tuple = (1.0, 3.0)  # (min_sec, max_sec) random range
    max_pages: int = 5
    
    @abstractmethod
    async def scrape(
        self,
        keyword: str = "startup",
        region: Optional[str] = None
    ) -> list[dict]:
        """
        Scrape the source. Must return list of dicts.
        Each dict MUST have these keys (others optional):
          title, type, organizer, location, deadline (date|None),
          description, source_url, source_name
        """
        pass
    
    async def run(
        self,
        keyword: str = "startup",
        region: Optional[str] = None,
        max_retries: int = 3
    ) -> list[dict]:
        """Run scraper with retry logic. Never raises — returns [] on total failure."""
        for attempt in range(max_retries):
            try:
                results = await self.scrape(keyword, region)
                logger.info(f"[{self.name}] Scraped {len(results)} results")
                return results
            except Exception as e:
                wait = 2 ** attempt
                logger.warning(f"[{self.name}] Attempt {attempt+1} failed: {e}. Retrying in {wait}s")
                await asyncio.sleep(wait)
        logger.error(f"[{self.name}] All {max_retries} attempts failed. Returning []")
        return []
    
    def _make_result(self, **kwargs) -> dict:
        """Build a result dict with all required fields, filling defaults."""
        return {
            "title": kwargs.get("title", ""),
            "type": kwargs.get("type", self.opportunity_type),
            "organizer": kwargs.get("organizer", ""),
            "location": kwargs.get("location", ""),
            "deadline": kwargs.get("deadline", None),
            "description": kwargs.get("description", "")[:500],  # Hard cap 500 chars
            "source_url": kwargs.get("source_url", ""),
            "source_name": kwargs.get("source_name", self.name),
        }
```

### `pipeline.py` — Dedup + Upsert + Expiry

```python
# Exact logic to implement:

async def process_results(
    results: list[dict],
    session: AsyncSession
) -> tuple[int, int]:
    """
    Dedup and insert results into DB.
    Returns (total_found, new_inserted).
    
    Dedup strategy (in order):
    1. source_url exact match → skip (DB unique constraint also catches this)
    2. Title fuzzy match >90% AND same source_name → skip
    """
    total = len(results)
    new_count = 0
    
    # Load existing URLs and titles for this session's dedup check
    existing_urls = await _get_existing_urls(session)
    existing_titles_by_source = await _get_existing_titles_by_source(session)
    
    for item in results:
        url = item.get("source_url", "").strip()
        if not url:
            logger.warning(f"Skipping result with no source_url: {item.get('title')}")
            continue
        
        # Check 1: exact URL dedup
        if url in existing_urls:
            continue
        
        # Check 2: fuzzy title dedup within same source
        source = item.get("source_name", "")
        title = item.get("title", "")
        existing_titles = existing_titles_by_source.get(source, [])
        
        if _is_fuzzy_duplicate(title, existing_titles, threshold=90):
            logger.debug(f"Fuzzy dedup skip: '{title}'")
            continue
        
        # Insert new record
        opp = Opportunity(**item, status="active")
        session.add(opp)
        existing_urls.add(url)
        existing_titles.append(title)
        existing_titles_by_source[source] = existing_titles
        new_count += 1
    
    await session.commit()
    return total, new_count

def _is_fuzzy_duplicate(title: str, existing: list[str], threshold: int) -> bool:
    from rapidfuzz import fuzz
    for existing_title in existing:
        if fuzz.ratio(title.lower(), existing_title.lower()) >= threshold:
            return True
    return False

async def expire_old_opportunities(session: AsyncSession) -> int:
    """Mark opportunities with past deadlines as expired. Returns count updated."""
    from datetime import date
    today = date.today()
    result = await session.execute(
        update(Opportunity)
        .where(Opportunity.deadline < today, Opportunity.status == "active")
        .values(status="expired")
    )
    await session.commit()
    return result.rowcount
```

### `scrapers/devpost.py` — Playwright Scraper

**Source:** `https://devpost.com/hackathons`  
**Method:** Playwright (async) — page is JS-rendered  
**Pagination:** Use `?page=N` query param, max 3 pages  
**Fields to extract per hackathon:**
- `title` → `.hackathon-tile h2` or `.hackathon-title`
- `organizer` → `.submitted-by` or organizer text
- `deadline` → `.submission-period .date` — parse with `dateutil.parser.parse()`
- `description` → prize/theme text, max 500 chars
- `location` → "Remote" if online/virtual, else location text
- `source_url` → `a.hackathon-tile[href]` — prepend `https://devpost.com` if relative
- `type` → "Competition" (hardcoded)
- `source_name` → "Devpost" (hardcoded)

**Anti-scraping for Devpost:**
```python
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# In scrape():
browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
context = await browser.new_context(
    user_agent=random.choice(user_agents),
    viewport={"width": 1280, "height": 900},
    locale="en-US"
)
page = await context.new_page()
await page.goto(url, wait_until="networkidle", timeout=30000)
await page.wait_for_selector(".hackathon-tile", timeout=15000)
await asyncio.sleep(random.uniform(1.5, 3.0))  # polite delay
```

### `scrapers/f6s.py` — httpx Scraper

**Source:** `https://www.f6s.com/programs`  
**Method:** httpx async — server-rendered HTML  
**Rate limit:** Max 15 requests/min → use `asyncio.Semaphore(3)` + 2s min delay  
**Pagination:** Scroll through pages via `?page=N`, max 5 pages  
**Fields to extract:**
- `title` → program name from listing card
- `organizer` → organization name
- `deadline` → application deadline text → parse to date
- `location` → country/city of program
- `description` → short program description
- `source_url` → full URL to program page
- `type` → "Accelerator"
- `source_name` → "F6S"

**Rate limit implementation:**
```python
_semaphore = asyncio.Semaphore(3)

async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
    async with _semaphore:
        await asyncio.sleep(random.uniform(2.0, 4.0))
        response = await client.get(url, headers=self._headers(), timeout=20)
        response.raise_for_status()
        return response.text
```

### `tests/conftest.py`

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models import Base

@pytest_asyncio.fixture
async def test_db():
    """In-memory SQLite DB for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    AsyncTestSession = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncTestSession() as session:
        yield session
    await engine.dispose()
```

### Phase 2 Acceptance Criteria
- [ ] `python -m scrapers.devpost` prints ≥5 hackathon titles
- [ ] `python -m scrapers.f6s` prints ≥5 accelerator names
- [ ] Running pipeline twice with same data → record count stays the same (dedup works)
- [ ] `pytest tests/test_scrapers.py -v` passes
- [ ] DB has ≥20 records after running both scrapers

---

## PHASE 3 — More Sources + Scheduler

**Goal:** 5 sources running. Scheduler auto-runs every 6h. `/api/scrape-now` works.  
**Files to create:** `scrapers/eventbrite.py`, `scrapers/grahamwalker.py`, `scrapers/masschallenge.py`, `scheduler.py`, update `routers/api.py`, update `main.py`  
**Time estimate:** ~2 hours

### `scrapers/eventbrite.py` — API-based

**Method:** Eventbrite REST API (free tier: 1,000 calls/day — use API first, never scrape)  
**Endpoint:** `GET https://www.eventbriteapi.com/v3/events/search/`  
**Auth:** Bearer token from `settings.eventbrite_api_key` in Authorization header  
**Params to pass:**
```python
params = {
    "q": keyword,          # e.g. "startup"
    "categories": "102",   # Business & Professional category ID
    "sort_by": "date",
    "expand": "organizer,venue",
    "page_size": 50,
}
```
**Pagination:** Use `pagination.continuation` from response for next page, max 3 pages  
**Field mapping:**
```python
{
    "title": event["name"]["text"],
    "organizer": event["organizer"]["name"],
    "deadline": event["start"]["local"][:10],   # ISO date string
    "location": f"{venue.city}, {venue.country}" if venue else "Online",
    "description": event.get("description", {}).get("text", "")[:500],
    "source_url": event["url"],
    "type": "Conference",
    "source_name": "Eventbrite",
}
```
**Fallback:** If `EVENTBRITE_API_KEY` is empty, log warning and return `[]`

### `scrapers/grahamwalker.py` — BeautifulSoup

**Source:** `https://grahamwalker.com/blog/grants-accelerators-for-early-stage-founders/`  
**Method:** httpx GET + BeautifulSoup4 with lxml parser  
**What to parse:** The page has a list of grants/programs. Extract each item's:
- Title (likely `h3` or strong text in list items)
- Deadline text (look for "Apply by", "Deadline:", date patterns)
- Funding amount (look for "$" amounts → goes into description)
- Organizer (organization name near the title)
- Source URL (look for `a href` near each item — link to actual grant page)

**Date parsing:**
```python
from dateutil import parser as dateparser

def _parse_deadline(text: str) -> date | None:
    try:
        return dateparser.parse(text, fuzzy=True).date()
    except (ValueError, OverflowError):
        return None
```

**Graceful handling:** If page structure changes, log warning, return whatever was found, don't crash.

### `scrapers/masschallenge.py` — httpx + BS4

**Source:** `https://masschallenge.org/programs-and-accelerators/`  
**Method:** httpx GET + BeautifulSoup4  
**Fields:** program title, description excerpt, location, application URL  
**type:** "Accelerator", **source_name:** "MassChallenge"

### `scheduler.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
import time

from config import settings
from database import AsyncSessionLocal
from pipeline import process_results, expire_old_opportunities
from scrapers.devpost import DevpostScraper
from scrapers.f6s import F6SScraper
from scrapers.eventbrite import EventbriteScraper
from scrapers.grahamwalker import GrahamWalkerScraper
from scrapers.masschallenge import MassChallengeScaper

ALL_SCRAPERS = [
    DevpostScraper(),
    F6SScraper(),
    EventbriteScraper(),
    GrahamWalkerScraper(),
    MassChallengeScraper(),
]

async def run_all_scrapers(
    keyword: str = None,
    region: str = None
) -> dict:
    """
    Run all scrapers. Returns summary dict.
    One scraper failure does NOT stop others.
    Logs to scrape_logs table.
    """
    keyword = keyword or settings.default_keyword
    region = region or settings.default_region or None
    
    summary = {"sources_run": [], "total_new": 0, "errors": []}
    start = time.time()
    
    async with AsyncSessionLocal() as session:
        for scraper in ALL_SCRAPERS:
            scraper_start = time.time()
            try:
                results = await scraper.run(keyword, region)
                found, new = await process_results(results, session)
                duration = time.time() - scraper_start
                
                await _log_scrape(session, scraper.name, found, new, duration, "success")
                summary["sources_run"].append(scraper.name)
                summary["total_new"] += new
                logger.info(f"[{scraper.name}] {found} found, {new} new ({duration:.1f}s)")
                
            except Exception as e:
                duration = time.time() - scraper_start
                await _log_scrape(session, scraper.name, 0, 0, duration, "failed", str(e))
                summary["errors"].append({"source": scraper.name, "error": str(e)})
                logger.error(f"[{scraper.name}] Failed: {e}")
    
    summary["duration_sec"] = round(time.time() - start, 2)
    
    # Phase 6: send_webhook_alert() if total_new > 0
    return summary


async def _log_scrape(session, source, found, new, duration, status, error=None):
    from models import ScrapeLog
    from datetime import datetime, timezone
    log = ScrapeLog(
        source_name=source,
        run_at=datetime.now(timezone.utc),
        records_found=found,
        new_records=new,
        duration_sec=duration,
        status=status,
        error_msg=error
    )
    session.add(log)
    await session.commit()


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    
    # Scrape every N hours
    scheduler.add_job(
        run_all_scrapers,
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id="scrape_all",
        name="Scrape all sources",
        replace_existing=True
    )
    
    # Expire old opportunities daily at 00:05
    scheduler.add_job(
        _run_expiry,
        trigger=CronTrigger(hour=0, minute=5),
        id="expire_opps",
        name="Mark expired opportunities",
        replace_existing=True
    )
    
    return scheduler

async def _run_expiry():
    async with AsyncSessionLocal() as session:
        count = await expire_old_opportunities(session)
        logger.info(f"[Scheduler] Expired {count} opportunities")
```

### Update `main.py` lifespan:

```python
# Add to lifespan STARTUP section:
from scheduler import create_scheduler
scheduler = create_scheduler()
scheduler.start()
app.state.scheduler = scheduler

# Add to lifespan SHUTDOWN section:
app.state.scheduler.shutdown()
```

### `routers/api.py` — Initial endpoints

```python
# Create this file with these endpoints:

@router.post("/api/scrape-now")
async def scrape_now():
    """Manually trigger all scrapers."""
    summary = await run_all_scrapers()
    return summary

@router.get("/api/sources")
async def get_sources(session: AsyncSession = Depends(get_db)):
    """Return scrape health per source."""
    # Query latest ScrapeLog per source_name
    # Return: [{source_name, last_scraped, total_records, last_status}]
    ...
```

### Phase 3 Acceptance Criteria
- [ ] All 5 scrapers run without crashing
- [ ] `POST /api/scrape-now` returns JSON summary with `total_new` > 0
- [ ] Scheduler starts on app boot (check logs for "Scheduler started")
- [ ] DB has ≥50 records
- [ ] `GET /api/sources` returns all 5 sources with last_scraped timestamp

---

## PHASE 4 — Dashboard UI

**Goal:** Beautiful, functional dashboard. The centerpiece of the submission.  
**Files to create:** `templates/base.html`, `templates/index.html`, `templates/partials/card.html`, `routers/dashboard.py`, `static/custom.css`  
**Time estimate:** ~3 hours

### Design Language
- **Color palette:** Dark navy `#0F172A` nav + clean white content area + accent blue `#2563EB`
- **Typography:** System UI stack for body; no custom fonts needed (fast load)
- **Cards:** Subtle shadow, rounded-xl, hover lift effect (`transition-transform hover:-translate-y-1`)
- **Feel:** Professional dashboard tool, not a blog. Think Linear or Notion aesthetics.

### `templates/base.html` structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}LaunchRadar{% endblock %}</title>
    <!-- Tailwind CSS CDN v3 -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Alpine.js CDN -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <link rel="stylesheet" href="/static/custom.css">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        brand: { 900: '#0F172A', 700: '#1E3A5F', 500: '#2563EB', 100: '#EFF6FF' }
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-slate-50 min-h-screen">

    <!-- Top Navigation -->
    <nav class="bg-slate-900 text-white px-6 py-4 flex items-center justify-between shadow-lg">
        <div class="flex items-center gap-3">
            <span class="text-2xl">⚡</span>
            <span class="text-xl font-bold tracking-tight">LaunchRadar</span>
            <span class="text-slate-400 text-sm ml-2">startup opportunity intelligence</span>
        </div>
        <div class="flex items-center gap-4 text-sm">
            <a href="/" class="hover:text-blue-400 transition-colors">Dashboard</a>
            <a href="/docs" class="hover:text-blue-400 transition-colors">API Docs</a>
            <a href="/api/export/csv" class="bg-blue-600 hover:bg-blue-500 px-3 py-1.5 rounded-lg transition-colors">
                ⬇ Export CSV
            </a>
        </div>
    </nav>

    <!-- Stats Bar (populated per page) -->
    {% block stats_bar %}{% endblock %}

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-6 py-8">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-200 mt-16 py-8 text-center text-slate-400 text-sm">
        LaunchRadar — Last scraped: {{ last_scraped or "Never" }} · 
        <a href="https://github.com" class="hover:text-slate-600">GitHub</a>
    </footer>

</body>
</html>
```

### `templates/index.html` structure:

```
{% extends "base.html" %}

Stats bar:
- Total active: N opportunities
- Expiring soon (<7d): N  [shown in red if >0]
- Sources: N/5 live
- Last updated: X minutes ago

Search + Filter row:
┌─────────────────────────────────────────────────────────────────────┐
│ 🔍 [Search opportunities...]                                         │
├─────────┬─────────┬──────────────┬──────────────┬─────────────────┤
│ Type ▾  │ Source ▾│ Deadline ▾   │ Stage ▾      │  Sort by ▾      │
└─────────┴─────────┴──────────────┴──────────────┴─────────────────┘

Active filters display (chips that can be removed):
[Devpost ×] [Grant ×] [This month ×]

Results count: "Showing 47 of 124 opportunities"

Card Grid (3 cols desktop, 2 tablet, 1 mobile):
[Card] [Card] [Card]
[Card] [Card] [Card]
...

Pagination:
← Previous  Page 2 of 5  Next →
```

**Filter form behavior:**
- All filters submit as GET params (not POST) so URLs are shareable
- Use `<form method="GET" action="/">` — no JavaScript needed for filter submission
- Alpine.js only used for dropdown open/close state

**Query params the dashboard route must support:**
- `q` → keyword search
- `type` → Grant | Accelerator | Conference | Fellowship | Competition
- `source` → source_name value
- `deadline` → this_week | this_month | next_3_months | all
- `stage` → Pre-seed | Seed | Series A | Any stage (from AI tags)
- `sort` → newest | deadline_asc | relevance
- `page` → integer, default 1
- `per_page` → 24 (hardcoded default)

### `templates/partials/card.html` — Opportunity Card

```
┌─────────────────────────────────────────────────────┐
│ [TYPE BADGE]                          [DEADLINE BADGE]│
│                                                       │
│ Title (bold, 2 lines max, ellipsis overflow)          │
│ Organizer · 📍 Location                              │
│                                                       │
│ Description excerpt (3 lines, fade out bottom)        │
│                                                       │
│ [💰 $10K-$50K] [🌱 Seed] [🌐 Remote]  ← AI tags     │
│                                                       │
│ [Apply Now →]                    Source: Devpost      │
└─────────────────────────────────────────────────────┘
```

**Type badge colors:**
```
Grant       → bg-green-100  text-green-800  border-green-200
Accelerator → bg-blue-100   text-blue-800   border-blue-200
Conference  → bg-purple-100 text-purple-800 border-purple-200
Competition → bg-orange-100 text-orange-800 border-orange-200
Fellowship  → bg-teal-100   text-teal-800   border-teal-200
```

**Deadline badge colors:**
```python
# Server-side logic in dashboard.py:
def get_deadline_badge(deadline: date | None) -> dict:
    if not deadline:
        return {"text": "No deadline", "class": "bg-slate-100 text-slate-500"}
    days = (deadline - date.today()).days
    if days < 0:
        return {"text": "Expired", "class": "bg-red-100 text-red-800"}
    elif days <= 7:
        return {"text": f"🔴 {days}d left", "class": "bg-red-100 text-red-800"}
    elif days <= 30:
        return {"text": f"🟡 {days}d left", "class": "bg-amber-100 text-amber-800"}
    else:
        return {"text": f"🟢 {days}d left", "class": "bg-green-100 text-green-800"}
```

### `routers/dashboard.py` — Route Logic

```python
# GET / route — must pass these to template:
{
    "opportunities": [...],   # Paged list of Opportunity objects
    "total": 124,             # Total matching records
    "page": 2,
    "total_pages": 6,
    "per_page": 24,
    # Current filter state (to repopulate form):
    "q": "AI startup",
    "type_filter": "Grant",
    "source_filter": "Devpost",
    "deadline_filter": "this_month",
    "stage_filter": "Seed",
    "sort": "deadline_asc",
    # Stats for stats bar:
    "stats": {
        "total_active": 124,
        "expiring_soon": 8,
        "sources_live": 5,
        "last_scraped": "2 hours ago",
    },
    # For each card, pre-computed deadline badge:
    "deadline_badges": {opp.id: badge_dict, ...}
}
```

### Phase 4 Acceptance Criteria
- [ ] Dashboard loads at `GET /` in <2 seconds
- [ ] Cards display all fields (title, organizer, location, deadline badge, type badge)
- [ ] Keyword search returns filtered results
- [ ] All 4 filters work (type, source, deadline, stage)
- [ ] Pagination navigates between pages
- [ ] Page URL updates with filter params (shareable links)
- [ ] Mobile responsive (stack to 1 column)
- [ ] No JavaScript errors in browser console

---

## PHASE 5 — AI Tagging

**Goal:** Every opportunity gets `funding_range`, `startup_stage`, `remote_or_onsite` from Claude API.  
**Files to create:** `ai_tagger.py`, update `pipeline.py`, update `routers/api.py`  
**Time estimate:** ~2 hours  
**Cost estimate:** ~$0.08 per 100 records

### `ai_tagger.py` — Claude API Batch Tagging

```python
# Exact implementation pattern:

import anthropic
import orjson
from loguru import logger
from config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """You are a startup opportunity classifier.
Given a list of opportunities, return ONLY a JSON array (same order as input).
Each element must have exactly these keys:
- "funding_range": string like "$10K-$50K", "Up to $500K", "Equity-free", "Not specified"  
- "startup_stage": one of "Pre-seed", "Seed", "Series A", "Any stage", "Not specified"
- "remote_or_onsite": one of "Remote", "On-site", "Hybrid", "Not specified"

Rules:
- Infer from title + description + location
- If a conference location is a city, it's "On-site"
- If description mentions "virtual" or "online", it's "Remote"
- If grant has no equity, note "Equity-free" for funding_range with amount if visible
- Return ONLY the JSON array. No explanation. No markdown. No code blocks."""


async def tag_opportunities(records: list[dict]) -> list[dict]:
    """
    Tag a list of opportunity dicts with AI metadata.
    Processes in batches of 10. Returns same list with tags filled in.
    If API key not configured, returns records unchanged.
    """
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set — skipping AI tagging")
        return records
    
    tagged = []
    batch_size = 10
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            batch_tagged = await _tag_batch(batch)
            tagged.extend(batch_tagged)
        except Exception as e:
            logger.error(f"AI tagging batch {i//batch_size + 1} failed: {e}")
            # On failure, return records with "Unknown" tags rather than crashing
            for record in batch:
                record["funding_range"] = "Unknown"
                record["startup_stage"] = "Unknown"
                record["remote_or_onsite"] = "Unknown"
                tagged.append(record)
    
    return tagged


async def _tag_batch(records: list[dict]) -> list[dict]:
    """Tag one batch of ≤10 records."""
    user_content = "\n".join([
        f"{idx+1}. Title: {r.get('title','')}\n"
        f"   Description: {r.get('description','')[:200]}\n"
        f"   Location: {r.get('location','')}"
        for idx, r in enumerate(records)
    ])
    
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}]
    )
    
    # Log token usage for cost tracking
    usage = response.usage
    logger.debug(f"AI tagging: {usage.input_tokens} in / {usage.output_tokens} out tokens")
    
    raw = response.content[0].text.strip()
    tags_list = orjson.loads(raw)  # Will raise if not valid JSON
    
    for record, tags in zip(records, tags_list):
        record["funding_range"] = tags.get("funding_range", "Unknown")
        record["startup_stage"] = tags.get("startup_stage", "Unknown")
        record["remote_or_onsite"] = tags.get("remote_or_onsite", "Unknown")
    
    return records
```

### Update `pipeline.py`:
After inserting new records → call `await tag_opportunities(new_records_list)` → update DB with tags

### Add to `routers/api.py`:
```python
@router.post("/api/tag-all")
async def tag_all_untagged(session: AsyncSession = Depends(get_db)):
    """Tag all records where ai_tagged_at is NULL."""
    # Query untagged records
    # Batch through ai_tagger.tag_opportunities()
    # Update DB records
    # Return {tagged: N, skipped_no_key: bool}
```

### Phase 5 Acceptance Criteria
- [ ] `POST /api/tag-all` tags all untagged records
- [ ] Records in DB have non-null `funding_range`, `startup_stage`, `remote_or_onsite`
- [ ] Stage filter on dashboard shows filtered results using AI tags
- [ ] If `ANTHROPIC_API_KEY` is empty, tagging is skipped gracefully (no crash)
- [ ] Token usage logged to console

---

## PHASE 6 — Export, Alerts, Tests, README

**Goal:** Submission-ready. All bonus features complete. Tests pass. README done.  
**Files to create:** `alerts.py`, `tests/test_pipeline.py`, `README.md`, update `routers/api.py`, update `templates/index.html`  
**Time estimate:** ~2 hours

### `routers/api.py` — Export Endpoints

```python
# GET /api/export/csv
@router.get("/api/export/csv")
async def export_csv(
    q: str = "",
    type_filter: str = "",
    source: str = "",
    deadline: str = "",
    session: AsyncSession = Depends(get_db)
):
    """Stream CSV of filtered opportunities."""
    opportunities = await _query_opportunities(session, q, type_filter, source, deadline)
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "title", "type", "organizer", "location", "deadline",
        "source_url", "source_name", "funding_range", "startup_stage", "remote_or_onsite"
    ])
    writer.writeheader()
    for opp in opportunities:
        writer.writerow({field: getattr(opp, field, "") for field in writer.fieldnames})
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=launchradar_{date.today()}.csv"}
    )


# GET /api/export/json
@router.get("/api/export/json")
async def export_json(
    q: str = "",
    type_filter: str = "",
    source: str = "",
    deadline: str = "",
    session: AsyncSession = Depends(get_db)
):
    """Return JSON array of filtered opportunities."""
    opportunities = await _query_opportunities(session, q, type_filter, source, deadline)
    data = [
        {col: getattr(opp, col) for col in [
            "id", "title", "type", "organizer", "location", "deadline",
            "source_url", "source_name", "funding_range", "startup_stage",
            "remote_or_onsite", "scraped_at"
        ]}
        for opp in opportunities
    ]
    return Response(
        content=orjson.dumps({
            "exported_at": datetime.now().isoformat(),
            "total": len(data),
            "filters": {"q": q, "type": type_filter, "source": source, "deadline": deadline},
            "data": data
        }),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=launchradar_{date.today()}.json"}
    )
```

### `alerts.py`

```python
async def send_webhook_alert(new_records: list[dict]) -> None:
    """
    POST to ALERT_WEBHOOK_URL if configured.
    Never raises — log and return on any failure.
    """
    if not settings.alert_webhook_url:
        return
    
    payload = {
        "event": "new_opportunities",
        "count": len(new_records),
        "preview": [r["title"] for r in new_records[:3]],
        "dashboard_url": f"http://{settings.app_host}:{settings.app_port}/",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(settings.alert_webhook_url, json=payload)
            resp.raise_for_status()
            logger.info(f"Webhook alert sent: {len(new_records)} new opportunities")
    except Exception as e:
        logger.warning(f"Webhook alert failed (non-critical): {e}")
```

### `tests/test_pipeline.py`

```python
# Test 1: Exact URL dedup
async def test_url_dedup(test_db):
    record = make_test_record(source_url="https://example.com/opp1")
    total1, new1 = await process_results([record], test_db)
    total2, new2 = await process_results([record], test_db)  # Same URL again
    assert new1 == 1
    assert new2 == 0  # Must be 0 — dedup worked

# Test 2: Fuzzy title dedup
async def test_fuzzy_title_dedup(test_db):
    r1 = make_test_record(title="Y Combinator 2025 Summer Batch", source_url="https://a.com/1")
    r2 = make_test_record(title="Y Combinator 2025 Batch",        source_url="https://a.com/2")
    _, new1 = await process_results([r1], test_db)
    _, new2 = await process_results([r2], test_db)
    assert new1 == 1
    assert new2 == 0  # Fuzzy match >90%, same source → skip

# Test 3: Different sources — same title OK
async def test_different_source_no_dedup(test_db):
    r1 = make_test_record(title="AI Startup Grant 2025", source_name="F6S",     source_url="https://f6s.com/1")
    r2 = make_test_record(title="AI Startup Grant 2025", source_name="Devpost", source_url="https://devpost.com/1")
    _, new1 = await process_results([r1], test_db)
    _, new2 = await process_results([r2], test_db)
    assert new1 == 1
    assert new2 == 1  # Different source → allow both

# Test 4: Expiry
async def test_expiry(test_db):
    from datetime import date, timedelta
    yesterday = date.today() - timedelta(days=1)
    record = make_test_record(deadline=yesterday, source_url="https://example.com/old")
    await process_results([record], test_db)
    expired_count = await expire_old_opportunities(test_db)
    assert expired_count == 1
```

### `README.md` must include:

```markdown
# LaunchRadar ⚡

Startup opportunity intelligence — aggregates grants, accelerators, 
conferences, and competitions from 5+ sources in real-time.

## Features
- 5 scraped sources, auto-refreshed every 6 hours
- AI-tagged metadata (funding range, startup stage, remote/on-site)
- Searchable + filterable dashboard
- CSV/JSON export
- Webhook alerts for new matches

## Setup

\`\`\`bash
git clone <repo>
cd launchradar
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Edit .env with your API keys
uvicorn main:app --reload
\`\`\`

Open http://localhost:8000

## Trigger a manual scrape

\`\`\`bash
curl -X POST http://localhost:8000/api/scrape-now
\`\`\`

## Sources

| Source | Type | URL |
|--------|------|-----|
| Devpost | Competitions/Hackathons | devpost.com/hackathons |
| F6S | Accelerators | f6s.com/programs |
| Eventbrite | Conferences | eventbrite.com (API) |
| Graham & Walker | Grants | grahamwalker.com/blog/grants-accelerators |
| MassChallenge | Accelerators | masschallenge.org/programs-and-accelerators |

## Scraping Challenges & Solutions

[See Part 6 of CLAUDE.md for full detail]

1. **JS-Rendered Pages** → Playwright headless Chromium for Devpost/F6S
2. **Rate Limiting** → asyncio.Semaphore + exponential back-off
3. **Date Parsing** → python-dateutil fuzzy parser with None fallback
4. **Cross-Source Dedup** → Two-tier: URL exact + fuzzy title (rapidfuzz >90%)
5. **Expired Opportunities** → Nightly APScheduler job marks past-deadline records

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| / | GET | Dashboard UI |
| /api/scrape-now | POST | Trigger manual scrape |
| /api/tag-all | POST | AI-tag all untagged records |
| /api/sources | GET | Source health + stats |
| /api/export/csv | GET | Export filtered data as CSV |
| /api/export/json | GET | Export filtered data as JSON |
| /docs | GET | Auto-generated API docs (FastAPI) |

## Environment Variables

See `.env.example`

## Running Tests

\`\`\`bash
pytest tests/ -v
\`\`\`
```

### Phase 6 Acceptance Criteria
- [ ] `GET /api/export/csv` downloads valid CSV with headers
- [ ] `GET /api/export/json` downloads valid JSON with metadata wrapper
- [ ] Export buttons in dashboard UI work with current filters applied
- [ ] Webhook fires if `ALERT_WEBHOOK_URL` is set and new records found
- [ ] `pytest tests/ -v` → all tests pass (0 failures)
- [ ] README.md complete with all sections above
- [ ] Final DB has ≥20 active, non-expired records

---

## 12. Coding Standards

> These are non-negotiable. Every file must follow these.

### Python Standards

```python
# ✅ CORRECT: Type hints on everything
async def process_results(
    results: list[dict],
    session: AsyncSession
) -> tuple[int, int]:

# ❌ WRONG: No type hints
async def process_results(results, session):
```

```python
# ✅ CORRECT: Loguru for all logging
from loguru import logger
logger.info(f"[Devpost] Scraped {count} results")
logger.error(f"Failed: {e}")

# ❌ WRONG: print() or stdlib logging
print(f"Scraped {count}")
import logging; logging.info(...)
```

```python
# ✅ CORRECT: Config from settings, never hardcoded
from config import settings
api_key = settings.anthropic_api_key

# ❌ WRONG: Hardcoded values
api_key = "sk-ant-..."
```

```python
# ✅ CORRECT: Async everywhere
async def get_data() -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

# ❌ WRONG: Sync blocking calls in async context
def get_data():
    response = requests.get(url)  # requests is sync — never use this
```

```python
# ✅ CORRECT: Docstrings on every function
async def tag_opportunities(records: list[dict]) -> list[dict]:
    """
    Tag a list of opportunity dicts with AI-extracted metadata.
    
    Args:
        records: List of opportunity dicts, each with title/description/location
        
    Returns:
        Same list with funding_range, startup_stage, remote_or_onsite filled
    """
```

### File Organization Rules
- One class per scraper file
- No circular imports — models.py imports nothing from the project
- database.py imports only models.py and config.py
- pipeline.py imports models.py, database.py, and rapidfuzz
- scrapers/* import only base.py, config.py, loguru
- routers/* import database.py, models.py, pipeline.py

### Error Handling Rules
```python
# ✅ CORRECT: Specific exceptions, always log
try:
    result = await client.get(url, timeout=20)
    result.raise_for_status()
except httpx.TimeoutException:
    logger.warning(f"[{self.name}] Timeout fetching {url}")
    return []
except httpx.HTTPStatusError as e:
    logger.error(f"[{self.name}] HTTP {e.response.status_code} for {url}")
    return []

# ❌ WRONG: Bare except, silent failures
try:
    result = requests.get(url)
except:
    pass
```

---

## 13. Testing Strategy

### What to test (priority order)

1. **Pipeline dedup logic** — most important, core correctness
2. **Expiry logic** — date math must be right
3. **Scraper output format** — does each scraper return dicts with all required keys?
4. **API endpoints** — do routes return 200 with expected structure?

### What NOT to test
- Don't test Playwright browser rendering (integration, not unit)
- Don't test Claude API responses (external service, mock instead)
- Don't test Tailwind CSS rendering

### pytest configuration

Add `pytest.ini` to project root:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
log_cli = true
log_level = INFO
```

### Test helper function

```python
# In tests/conftest.py — add this helper:
def make_test_record(**overrides) -> dict:
    base = {
        "title": "Test Startup Grant 2025",
        "type": "Grant",
        "organizer": "Test Foundation",
        "location": "Remote",
        "deadline": None,
        "description": "A test grant for testing.",
        "source_url": "https://test.example.com/grant-1",
        "source_name": "TestSource",
    }
    base.update(overrides)
    return base
```

---

## 14. Anti-Scraping Rules

> Follow these to avoid bans and respect server resources.

### User Agent Rotation

```python
# In scrapers/base.py — add this list:
DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]
```

### Request Headers

```python
def _headers(self) -> dict:
    return {
        "User-Agent": random.choice(DESKTOP_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
```

### Rate Limits Per Source

| Source | Max Req/Min | Semaphore | Min Delay |
|--------|------------|-----------|-----------|
| Devpost | ~30/min | 2 concurrent | 2-4s per page |
| F6S | ~15/min | 3 concurrent | 3-5s per page |
| Graham & Walker | Unlimited | 1 concurrent | 1s |
| MassChallenge | ~30/min | 2 concurrent | 1-2s per page |

### robots.txt Rule
- Always check `robots.txt` before scraping a new source
- Only scrape paths that are not disallowed
- Eventbrite: use the official API only (never scrape)

---

## 15. Common Pitfalls — Do Not Do These

### ❌ Don't use `requests` — use `httpx`
```python
# WRONG
import requests
response = requests.get(url)  # Blocking, kills async performance

# RIGHT
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### ❌ Don't hardcode API URLs in scrapers
```python
# WRONG
url = "https://www.f6s.com/programs?page=1&q=AI"

# RIGHT
BASE_URL = "https://www.f6s.com/programs"
url = f"{BASE_URL}?page={page}&q={keyword}"
```

### ❌ Don't store more than 500 chars in description
```python
# RIGHT — always cap it
"description": text[:500] if text else "",
```

### ❌ Don't crash if date parsing fails
```python
# RIGHT
try:
    deadline = dateparser.parse(date_text, fuzzy=True).date()
except (ValueError, OverflowError, TypeError):
    deadline = None  # Store None, not crash
```

### ❌ Don't use `time.sleep()` in async code
```python
# WRONG — blocks the entire event loop
time.sleep(2)

# RIGHT
await asyncio.sleep(2)
```

### ❌ Don't commit `.env` or `launchradar.db`
- `.gitignore` must include both from Phase 1

### ❌ Don't call AI tagger for every record individually
```python
# WRONG — 1 API call per record = expensive
for record in records:
    await tag_single(record)  # N API calls

# RIGHT — batch 10 at a time
for i in range(0, len(records), 10):
    batch = records[i:i+10]
    await tag_batch(batch)  # N/10 API calls
```

### ❌ Don't render dashboard with sync SQLAlchemy queries
```python
# WRONG — sync query in async FastAPI handler
results = session.execute(select(Opportunity)).all()

# RIGHT
results = await session.execute(select(Opportunity))
opps = results.scalars().all()
```

---

## Quick Reference — Phase Checklist

| Phase | What | Key Files | Done? |
|-------|------|-----------|-------|
| 1 | Scaffold + DB | config, models, database, main | ☐ |
| 2 | Base scraper + Devpost + F6S + pipeline | scrapers/base, scrapers/devpost, scrapers/f6s, pipeline | ☐ |
| 3 | More sources + scheduler + API | scrapers/eventbrite+grahamwalker+masschallenge, scheduler, routers/api | ☐ |
| 4 | Dashboard UI | templates/*, routers/dashboard | ☐ |
| 5 | AI tagging | ai_tagger, update pipeline + api | ☐ |
| 6 | Export + alerts + tests + README | alerts, tests/*, README | ☐ |

---

## How to Start RIGHT NOW

```bash
# 1. Create project folder
mkdir launchradar && cd launchradar

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Place this CLAUDE.md file in the project root

# 4. Start Phase 1 — tell Claude:
# "Read CLAUDE.md and implement Phase 1 exactly as specified."

# 5. After Phase 1 passes its criteria, move to Phase 2:
# "Phase 1 complete. Implement Phase 2 from CLAUDE.md."

# Continue phase by phase.
```

---

*CLAUDE.md v1.0 — LaunchRadar Project · Assignment 3: Web Scraping + Data Pipeline*
