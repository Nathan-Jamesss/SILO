# Startup Opportunity Aggregator — Full Project Specification
### For: Antigravity

---

## What This Project Is

A tool that collects startup-related opportunities — grants, conferences, accelerators, hackathons, and more — from multiple public sources. It stores them, removes duplicates, and displays everything in a searchable dashboard. The scraper runs on a regular schedule to keep data updated at all times.

This is NOT a hackathon-only tool. It covers ALL startup opportunity types: grants, conferences, accelerators, hackathons, programs, and anything startup-relevant.

---

## Fixes & Rules (From Review — Must Be Followed Exactly)

These are non-negotiable corrections the project must implement. The current version violates all of these.

---

### Fix 1 — Remove All Emojis

No emojis anywhere in the UI, dashboard, cards, buttons, labels, or exported files. None.

---

### Fix 2 — Beige and Coffee Color Theme

The entire UI must use a beige and coffee color palette only.

- Backgrounds: warm off-white, cream, light beige
- Primary accents: coffee brown, espresso dark, muted tan
- Text: deep brown or dark espresso, not black
- No blues, purples, greens, or generic grays
- Every component — cards, sidebar, buttons, filters, table rows — must use this palette consistently
- Use CSS variables for all colors so the theme is applied globally

---

### Fix 3 — Link Accuracy and No Random Photos

Half the content in the current version is inaccurate. Specifically:

- Links are opening to the event host's main homepage, not the specific opportunity page — this is wrong
- Random unrelated photos are being shown for listings — this must stop entirely
- No stock images, no random photos, no placeholder images for listings
- Every opportunity card or row shows only real extracted data: title, type, organizer, location, deadline, and the verified direct link
- If a link goes anywhere other than the exact opportunity's own page, it is invalid and must not be shown

---

### Fix 4 — Hackathon Links Must Open Directly to the Hackathon Landing or Registration Page

For hackathons specifically:

- Every hackathon link must be verified to open directly to that hackathon's own landing page or registration page
- Before storing any hackathon entry, the scraper must check that the link resolves to the hackathon's own page
- If there is any hindrance — redirect, 404, wrong page, goes to organizer homepage — try again once
- If the link still does not open directly to the hackathon's landing or registration page after the retry, delete that hackathon entry entirely — do not store it, do not display it
- A hackathon with a bad or unverifiable link is worse than no entry at all

---

### Fix 5 — This Is a Tool With Options for All Opportunity Types

The tool must support and display all of the following types, not just hackathons:

- Grants
- Conferences
- Accelerators
- Hackathons
- Any other startup-relevant programs or opportunities

The type filter in the dashboard must include all categories. The scraper must collect all types. The scope of the project is startup opportunities broadly — this is the main description and the project must not drift from it.

---

### Fix 6 — Follow Exactly How Devpost Hackathon Links Work

Devpost hackathon links follow a specific standard format. The scraper must construct and verify links in this exact format:

```
https://[hackathon-name].devpost.com/?ref_feature=[feature-name]&ref_medium=discover
```

Example pattern:
```
https://xxxxxxxx.devpost.com/?ref_feature=xxxxxxx&ref_medium=discover
```

Where:
- `xxxxxxxx` is the specific hackathon's name/slug on Devpost
- `ref_feature` is the feature identifier for that specific hackathon
- `ref_medium=discover` is the standard medium parameter

The scraper must extract the correct slug and feature value for each hackathon individually. Do not use a generic or hardcoded link. Each hackathon on Devpost has its own unique URL in this format — extract and store it correctly per entry.

---

### Fix 7 — Export Options Must Be Complete and Accurate

The current version gives only around 4 exports and the data is inaccurate. This must be fixed:

- Export to CSV — every field included, no missing columns, no truncated data
- Export to JSON — fully structured, every field present
- Export filtered results — whatever is currently visible/filtered on screen must be exportable
- Export all results — full database dump option

Every export must include all of these fields without exception:
- Title
- Type (Grant / Conference / Accelerator / Hackathon / etc.)
- Organizer
- Location or Eligibility
- Deadline or Event Date
- Source Link (the verified direct link)
- Date Scraped

No export should contain partial data, missing fields, or inaccurate information. If the data was not scraped correctly, fix the scraper — do not export bad data.

---

## Core Requirements (Original Project Description)

---

### 1. Scraping

- Scrape from at least 2 public sources
- Support a keyword input (example: "AI startup") and an optional region/location filter
- Extract for every opportunity:
  - Title
  - Type (Grant / Conference / Accelerator / Hackathon / etc.)
  - Organizer
  - Location or Eligibility
  - Deadline or Date
  - Source Link — must be a direct link to the opportunity's own page, not a homepage

---

### 2. Data Handling

- Remove duplicate opportunities before storing
- Deduplication logic: match on Title + Organizer + Deadline
- Store in SQLite (default) or MongoDB
- Track scrape timestamp per entry

---

### 3. Dashboard

- Display all opportunities in a searchable view
- Search by keyword across Title, Organizer, Type
- Filter by:
  - Type
  - Source
  - Deadline (date range or upcoming)
- All displayed data must be accurate — no placeholder or unverified content

---

### 4. Scheduling

- Scraper runs automatically using cron or a scheduler (APScheduler or equivalent)
- Default interval: every 24 hours
- Each run: scrape new data, deduplicate, update changed entries, add new entries
- Log each run with timestamp and count of new entries added

---

## Bonus Features

- AI auto-tagging per opportunity:
  - Funding range (where detectable)
  - Startup stage: idea / early / growth
  - Remote or on-site
- Alerts via email or webhook when a new opportunity matches a saved keyword or filter
- Pagination handling: scraper must go through all pages, not just the first
- Basic anti-scraping handling: rotate user agents, add request delays, handle rate limits (429s) gracefully

---

## Deliverables

- GitHub repo with README covering setup instructions and all sources used
- Working dashboard with at least 20 real, verified entries
- A written note explaining scraping challenges encountered and how they were handled

---

## What Must Not Happen

- No random or unrelated photos on listings
- No links going to an organizer's homepage — only to the specific opportunity page
- No storing or displaying entries with unverified or broken links
- No exporting partial, missing, or inaccurate data
- No emojis anywhere
- No drifting from the original project description — the tool covers all startup opportunity types, not just hackathons
- No Devpost links that do not follow the standard slug format described in Fix 6

---

## Quick Reference Summary

| Rule | Requirement |
|---|---|
| Emojis | None, anywhere |
| Theme | Beige and coffee palette only |
| Photos | None — real extracted data only |
| Links | Must open directly to the opportunity's own page |
| Devpost format | `https://[name].devpost.com/?ref_feature=[x]&ref_medium=discover` |
| Bad hackathon links | Retry once, if still bad — delete the entry |
| Scope | All types: grants, conferences, accelerators, hackathons |
| Exports | CSV + JSON, all fields, accurate, filtered and full options |
| Deduplication | Required before every store operation |
| Scheduling | Automatic every 24 hours |
| Minimum entries | 20 real verified entries in dashboard |
