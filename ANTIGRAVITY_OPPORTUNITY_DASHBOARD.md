# Startup Opportunity Aggregator — Project Specification
### For: Antigravity | Tool Category: Startup Opportunities Dashboard

---

## Overview

A tool that collects startup-related opportunities (grants, conferences, accelerators, hackathons, etc.) from multiple public sources, stores them, removes duplicates, and displays them in a searchable dashboard. The scraper runs on a schedule to keep data continuously updated.

---

## Theme & UI

- Color palette: Beige and coffee tones — warm off-whites, muted browns, espresso darks, cream highlights
- No emojis anywhere in the UI
- Clean, readable typography — no clutter
- Minimal, purposeful layout

---

## Core Requirements

---

### 1. Scraping

**Sources to scrape (minimum 2, real and verified):**

- Devpost (hackathons) — `https://devpost.com/hackathons`
- F6S (accelerators, grants) — `https://www.f6s.com/programs`

**Additional sources (expand as needed):**
- Eventbrite (conferences) — `https://www.eventbrite.com`
- Grants.gov (grants) — `https://www.grants.gov`
- AngelList / Wellfound (accelerators)

**Keyword support:**
- Accept a keyword input (e.g., `"AI startup"`)
- Accept optional region/location filter

**Fields to extract for every opportunity:**

| Field | Description |
|---|---|
| Title | Name of the opportunity |
| Type | Grant / Conference / Accelerator / Hackathon |
| Organizer | Who is hosting or running it |
| Location / Eligibility | Where it is or who can apply |
| Deadline or Date | Application deadline or event date |
| Source Link | Direct link — must open to the exact landing/registration page |

**Link accuracy rules (critical):**

- Every link must open directly to the opportunity's own landing page or registration page
- No redirects to a host's homepage or a generic listing page
- For Devpost hackathons specifically, links must follow this exact format:
  ```
  https://[hackathon-name].devpost.com/?ref_feature=[feature]&ref_medium=discover
  ```
  Example: `https://xxxxxxxx.devpost.com/?ref_feature=xxxxxxx&ref_medium=discover`
- Before storing any hackathon link, verify it resolves to the hackathon's own page
- If a link cannot be verified to open directly to the hackathon landing/registration page, delete that entry — do not store it

---

### 2. Data Handling

- Remove duplicate opportunities before storing
- Deduplication logic: match on Title + Organizer + Deadline combination
- Store in SQLite (default) or MongoDB
- Database schema must include all extracted fields above
- Track when each entry was last scraped (timestamp)

---

### 3. Dashboard

**Display:**
- List all stored opportunities in a table/card view
- Show: Title, Type, Organizer, Location, Deadline, Source Link

**Search:**
- Full-text keyword search across Title, Organizer, Type

**Filters:**
- By Type (Grant / Conference / Accelerator / Hackathon)
- By Source (Devpost / F6S / Eventbrite / etc.)
- By Deadline (date range or upcoming only)

**Export options (must be accurate and complete):**
- Export to CSV — all fields included, no truncation
- Export to JSON — structured, all fields included
- Export filtered results only (whatever is currently shown on screen)
- Each export must include: Title, Type, Organizer, Location/Eligibility, Deadline, Source Link, Scraped Date

---

### 4. Scheduling

- Scraper runs automatically using a cron job or scheduler (e.g., APScheduler in Python)
- Default schedule: every 24 hours
- On each run: scrape, deduplicate, update existing entries if changed, add new entries
- Log each run with timestamp and count of new entries added

---

## Bonus Features

- **AI auto-tagging** for each opportunity:
  - Funding range (if detectable)
  - Startup stage (idea / early / growth)
  - Remote or on-site
- **Alerts:** Email or webhook notification when a new opportunity matches a saved keyword/filter
- **Pagination handling:** Scraper must page through all results, not just the first page
- **Basic anti-scraping handling:** Rotate user agents, add request delays, handle 429s gracefully

---

## Deliverables

- GitHub repo with README covering setup instructions and sources used
- Working dashboard with at least 20 real, verified entries
- A written note explaining scraping challenges encountered and how they were handled

---

## What This Tool Is

This is a startup opportunity aggregator tool. It covers:
- Hackathons
- Grants
- Conferences
- Accelerators
- Any other startup-relevant programs

It is NOT limited to hackathons only. All opportunity types are in scope.

---

## What to Avoid

- Do not use random photos or stock images for opportunity listings
- Do not link to an event organizer's main website — only the specific opportunity page
- Do not store entries where the source link cannot be verified
- Do not show broken or unverified links in the dashboard
- Do not export partial or inaccurate data — all fields must be present in exports
- Do not remove any filter or export option to save effort — all must work correctly

---

## Summary of Key Rules

| Rule | Requirement |
|---|---|
| Links | Must open directly to hackathon/opportunity registration page |
| Devpost format | `https://[name].devpost.com/?ref_feature=[x]&ref_medium=discover` |
| Unverifiable links | Delete the entry, do not store |
| Exports | CSV and JSON, all fields, accurate data |
| Theme | Beige and coffee color palette, no emojis |
| Scope | All startup opportunity types, not just hackathons |
| Deduplication | Required before every store operation |
| Scheduling | Automatic, runs every 24 hours |
