# LaunchRadar ⚡

Real-time startup opportunity intelligence — aggregates grants, accelerators, conferences, and competitions from 8 public sources.

## Features
- **8 scraped sources**, auto-refreshed every 6 hours via APScheduler
- **AI-tagged metadata & Hackathon Verification** (funding range, startup stage, remote/on-site, true hackathon check) via Google Gemini API
- **Past Projects Compatibility Engine**: Dynamic AI matching against user portfolios to generate compatibility scorecards (0-100%).
- **Smart deduplication** (exact URL + fuzzy title matching via `rapidfuzz`)
- **Searchable + filterable dashboard** (no-JS form submission, server-side rendered)
- **CSV/JSON export** directly from current filter state
- **Webhook alerts** for new matches

## Setup

```bash
# Clone and enter repo
cd launchradar

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Start the application
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

## Trigger a manual scrape
```bash
curl -X POST http://localhost:8000/api/scrape-now
```

## AI Tagging
To run the AI tagger over any untagged records in the DB:
```bash
curl -X POST http://localhost:8000/api/tag-all
```

## Sources

| Source | Type | URL |
|--------|------|-----|
| **Devpost** | Competitions/Hackathons | devpost.com/hackathons |
| **Devfolio** | Competitions/Hackathons | devfolio.co/hackathons |
| **Unstop** | Competitions/Hackathons | unstop.com/hackathons |
| **Hack2Skill** | Competitions/Hackathons | hack2skill.com/hackathons |
| **F6S** | Accelerators | f6s.com/programs |
| **Eventbrite** | Conferences | eventbrite.com (API) |
| **Graham & Walker** | Grants | grahamwalker.com/blog/grants-accelerators |
| **MassChallenge** | Accelerators | masschallenge.org/programs |

## Scraping Challenges & Solutions

1. **JS-Rendered Pages & Cloudflare** → Playwright headless Chromium for Devpost, Devfolio, Unstop, and Hack2Skill, complete with resilient premium fallback datasets.
2. **Rate Limiting** → `asyncio.Semaphore` + exponential back-off retries for F6S (avoids 429 errors)
3. **Date Parsing** → `python-dateutil` fuzzy parser with graceful `None` fallback for textual "rolling" deadlines
4. **Cross-Source Dedup** → Two-tier logic: URL exact match first, then fuzzy title (`rapidfuzz` >90%) within the same source.
5. **Expired Opportunities** → Nightly APScheduler job safely marks past-deadline records as "expired" instead of deleting them.
6. **Anti-scraping measures** → User-agent rotation, randomized page delays, and headless arguments applied.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/scrape-now` | POST | Trigger manual scrape |
| `/api/tag-all` | POST | AI-tag all untagged records |
| `/api/sources` | GET | Source health + stats |
| `/api/projects` | GET | List user's past projects |
| `/api/projects` | POST | Add a past project and trigger matching |
| `/api/projects/{id}` | DELETE | Delete a past project |
| `/api/projects/{id}/match` | POST | Force recalculate matches for a project |
| `/api/export/csv` | GET | Export filtered data as CSV |
| `/api/export/json` | GET | Export filtered data as JSON |
| `/docs` | GET | Auto-generated API docs (FastAPI) |

## Running Tests

```bash
pytest tests/ -v
```
