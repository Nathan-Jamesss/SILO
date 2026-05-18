# Implementation Plan — Aggregator Quality & Filter Overhaul

This plan details the technical fixes to address scraped data quality, fix link and scraper issues across Unstop, Devfolio, Hack2Skill, and SOSV, remove the "True Hackathons Only" option, and enhance the visual distinction between different opportunity types under the strict Beige & Coffee palette.

## Proposed Changes

### 1. Database & Scrapers Base Integration
#### [MODIFY] [base.py](file:///c:/Users/natha/Desktop/Projects/AI%20start%20up/launchradar/scrapers/base.py)
- Update the default mapping in `_make_result`:
  - Do not default `num_applicants` to `0` or force conversion if it is missing.
  - Keep `num_applicants` as `None` if it is not successfully extracted, allowing the database to store `NULL`.

### 2. Devpost Scraper Real Applicant Counts
#### [MODIFY] [devpost.py](file:///c:/Users/natha/Desktop/Projects/AI%20start%20up/launchradar/scrapers/devpost.py)
- Replace title-hash applicant count simulation with real page text parser:
  - Query elements for text like `"participants"` or `"registered"` or `"applicants"`.
  - Parse the integer number of applicants. If not found or not parseable, return `None`.

### 3. Remove Fake Fallbacks & Fix Scraper URL Errors
#### [MODIFY] [unstop.py](file:///c:/Users/natha/Desktop/Projects/AI%20start%20up/launchradar/scrapers/unstop.py)
- Delete all hardcoded fallback lists. If the live crawl fails or is blocked, the scraper should safely return `[]` to maintain a 100% real and verifiable database.

#### [MODIFY] [hack2skill.py](file:///c:/Users/natha/Desktop/Projects/AI%20start%20up/launchradar/scrapers/hack2skill.py)
- Delete hardcoded fallbacks.
- Strengthen relative link extraction: check if the card is an anchor itself or contains specific child anchor links, filtering out homepages, hashtags, or unrelated pages.

#### [MODIFY] [devfolio.py](file:///c:/Users/natha/Desktop/Projects/AI%20start%20up/launchradar/scrapers/devfolio.py)
- Delete hardcoded fallbacks.
- Re-architect link extractor: parse any `devfolio.co/hackathons/[slug]` or relative `/hackathons/[slug]` URL and dynamically reconstruct the valid subdomain URL pattern: `https://[slug].devfolio.co/` to prevent all 404 errors.

#### [MODIFY] [f6s.py](file:///c:/Users/natha/Desktop/Projects/AI%20start%20up/launchradar/scrapers/f6s.py)
- Fix typo in the SOSV seed data URL: change `https://sosv.com/programmes/` to `https://sosv.com/programs/`.

### 4. UI Badging and Type Distinction
#### [MODIFY] [dashboard.py](file:///c:/Users/natha/Desktop/Projects/AI%20start%20up/launchradar/routers/dashboard.py)
- Redefine type colors in `get_type_badge` to provide heavy visual distinction while remaining perfectly within the Beige & Coffee theme:
  - **Grant:** Dark Espresso solid (`bg-coffee-800 text-beige-50 border-coffee-800`)
  - **Accelerator:** Medium Coffee solid (`bg-coffee-600 text-beige-50 border-coffee-700`)
  - **Conference:** Soft Muted Tan (`bg-beige-300 text-coffee-900 border-beige-300`)
  - **Competition:** Cream with Coffee border (`bg-beige-100 text-coffee-800 border-coffee-500`)
  - **Fellowship:** White with dashed border (`bg-white text-coffee-600 border-dashed border-coffee-500`)
- Update `applicants_desc` sorting to use `.nulls_last()` in SQL.

#### [MODIFY] [card.html](file:///c:/Users/natha/Desktop/Projects/AI%20start%20up/launchradar/templates/partials/card.html)
- Clean up applicant badge renderer: if `opp.num_applicants` is `None` or not positive, show `N/A`. Otherwise, show `[X] registered`.

### 5. Delete Hackathon Only UI Option
#### [MODIFY] [index.html](file:///c:/Users/natha/Desktop/Projects/AI%20start%20up/launchradar/templates/index.html)
- Delete the "True Hackathons Only" checkbox and its active filter label completely from the UI console.

---

## Verification Plan

### Automated Tests
- Run `pytest` to confirm the test suite remains fully correct and functional.

### Manual Verification
- Launch the FastAPI server locally.
- Access the dashboard at `http://localhost:8000`.
- Verify the following:
  1. The "True Hackathons Only" checkbox is completely gone.
  2. Opportunity type badges have distinct background styles matching the Beige & Coffee theme.
  3. Real parsed applicant counts are shown or safely default to `N/A`.
  4. Perform test clicks on Devfolio, Hack2Skill, and SOSV URLs to confirm zero 404s.
