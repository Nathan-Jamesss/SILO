# main.py — FastAPI application entry point
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from database import create_tables
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    STARTUP: initialise DB, start scheduler.
    SHUTDOWN: gracefully stop scheduler.
    """
    # ── STARTUP ──────────────────────────────────────────────
    logger.info("Starting SOI...")
    logger.info(f"Database: {settings.database_url}")

    # Initialise database tables (idempotent)
    await create_tables()
    logger.info("Database tables ready.")

    # Store templates on app.state so routers can access them
    app.state.templates = Jinja2Templates(directory="templates")

    # Start the scheduler
    from scheduler import create_scheduler
    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info(f"Scheduler started — scraping every {settings.scrape_interval_hours}h")

    yield  # ← app runs here

    # ── SHUTDOWN ──────────────────────────────────────────────
    logger.info("Shutting down SOI...")
    # Gracefully stop the scheduler
    app.state.scheduler.shutdown()


# Create FastAPI app
app = FastAPI(
    title="SOI",
    description="SOI — Startup & Opportunities Intelligence Index.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routers
from routers import api, dashboard
app.include_router(api.router)
app.include_router(dashboard.router)
