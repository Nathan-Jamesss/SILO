# SILO: Startup Intelligence for Launch and Outreach

SILO is a comprehensive startup enablement platform designed to help builders transition their hackathon prototypes into registered companies. It automates opportunity discovery, matches portfolios with funding options, and provides structured startup guidance.

Deployed Live Site: https://silo-web.vercel.app (or your custom Vercel deployment link)

---

## Architecture Overview

SILO has been refactored into a fully serverless, zero-maintenance static architecture:

1. **Frontend (React 19, Vite, TypeScript, Tailwind v4)**: A high-performance, single-page application styled with a premium glassmorphic beige-and-coffee theme. It fetches static opportunity data directly from the edge network.
2. **AI Companion (Vercel Serverless)**: SAILO Bot runs as a serverless Python function (located in `silo-web/api/sailo-bot.py`) that processes startup queries and analyzes project fit without exposing API keys.
3. **Scraper Pipeline (GitHub Actions)**: A Python pipeline (located in `launchradar/`) runs daily at midnight UTC inside GitHub Actions. It scrapes 8 platforms using Playwright, tags metadata with Google Gemini, deduplicates records, and commits the fresh dataset directly to the frontend.

---

## Key Features

* **Multi-Source Aggregator**: Collects startup programs, grants, and hackathons across 8 major platforms (Devpost, Devfolio, Unstop, Hack2Skill, F6S, Eventbrite, Graham and Walker, and MassChallenge).
* **Gemini AI Classification**: Analyzes opportunities to tag metadata such as funding stage, eligibility, and industry sectors.
* **Past Projects Compatibility Engine**: Matches user portfolios against active opportunities using AI to generate suitability scorecards.
* **Smart Deduplication**: Utilizes URL checks and fuzzy title matching (via RapidFuzz) to prevent duplicate records.
* **Data Export**: Exporters for both filtered views and complete databases into fully structured CSV or JSON files.
* **Email Alert System**: Allows users to set email alerts 1 day before deadlines.

---

## Local Setup

### Prerequisites
* Node.js v18 or newer
* Python 3.12 or newer

### 1. Run the Frontend Dashboard
Navigate to the frontend directory, install dependencies, and run the development server:

```bash
cd silo-web
npm install
npm run dev
```

The app will be active at: http://localhost:5173/

### 2. Test the Scraper Pipeline Locally
Initialize your virtual environment, install requirements, and run a manual scrape:

```bash
cd launchradar
python -m venv venv
source venv/Scripts/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python pipeline.py
```

---

## Deployment Configuration

### 1. Frontend & Serverless APIs (Vercel)
* Connect your repository to Vercel.
* Set the build directory or root to `silo-web`.
* Add `GEMINI_API_KEY` to your Vercel Environment Variables so SAILO Bot can answer questions.

### 2. Scraper Automation (GitHub Actions)
* The workflow is defined in `.github/workflows/scraper.yml`.
* Add `GEMINI_API_KEY` to your GitHub Repository Secrets to allow the daily scraper run to tag records.
