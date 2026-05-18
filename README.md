# SILO: Startup Intelligence for Launch and Outreach

SILO (Startup Intelligence for Launch and Outreach) is a comprehensive startup enablement platform designed to bridge the gap between initial ideation and successful execution. The journey begins with competitive hackathons, which provide real-world problem statements and pressure-tested challenges. From there, founders ideate and prototype solutions, refining their product-market fit. SILO then streamlines the transition from a successful prototype to a registered company, helping founders navigate structural entity decisions, secure government and private grants, and prepare structured pitching milestones.

---

## Tech Stack

The workspace is structured into a fast backend opportunity engine and a high-performance modern frontend landing page.

### 1. Backend Opportunity Aggregator (launchradar)
* Core Framework: FastAPI (Python 3.13)
* Web Server: Uvicorn
* Database Layer: SQLite via SQLAlchemy (asyncio) and aiosqlite
* Scraper Suite: Async crawlers powered by Playwright, HTTPX, BeautifulSoup4, and lxml
* Scheduling: APScheduler for automated, periodic background scraping
* Templating: Jinja2 for server-side HTML rendering
* Interactivity: Alpine.js for lightweight, reactive dashboard operations

### 2. Landing Page Frontend (silo-web)
* Core Framework: React 19
* Build Tool: Vite
* Language: TypeScript
* Styling: Tailwind CSS and Vanilla CSS custom properties for hardware-accelerated animations

---

## Core Workflow

### 1. Opportunity Harvesting
The system runs background async crawler tasks that target top developer networks, government portals, and challenge boards. It gathers full descriptions, prize pools, eligibility metrics, and exact deadlines.

### 2. Standardization and Deduplication
A robust pipeline processes all ingested records, parsing deadlines, standardizing reward tiers, and deduplicating entries by URL or date rules. Expired opportunities are marked and filtered automatically.

### 3. Entity and Grant Advisory (SAILO Bot)
An integrated startup mentor assistant is served via the dashboard. It guides founders who have developed a successful hackathon prototype through:
* Selecting appropriate company structures (Private Limited vs. LLP)
* Applying for DPIIT startup recognition and tax holiday eligibility
* Navigating government grant applications (such as MSME schemes)
* Structuring pitch decks and funding projections

### 4. Matching Engine
Founders can link past project profiles against the active database of challenges, hackathons, and corporate grants to identify the best matching avenues for launch.

---

## Local Setup

### Prerequisite Checklist
* Python 3.12 or newer
* Node.js v18 or newer
* npm package manager

### 1. Running the FastAPI Backend
Initialize your virtual environment, install dependencies, and start the development server:

```bash
cd launchradar
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The FastAPI dashboard will be active at: http://localhost:8000/

### 2. Running the React Frontend
Install dependencies and run the Vite development server:

```bash
cd silo-web
npm install
npm run dev
```

The SILO React landing page will be active at: http://localhost:5173/

---

## Project Structure

```text
├── components/           # Reusable React components
├── launchradar/          # FastAPI aggregator application
│   ├── scrapers/         # Async crawler scripts (MSME, Devfolio, Unstop, etc.)
│   ├── static/           # CSS stylesheets and client scripts
│   ├── templates/        # Jinja2 dashboard templates
│   ├── tests/            # Automated pytest suite
│   └── main.py           # Application entry point
└── silo-web/             # Vite React landing page application
```
