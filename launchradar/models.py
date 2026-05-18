# models.py — SQLAlchemy ORM models
# NOTE: This file imports nothing from the project (avoids circular deps)
from sqlalchemy import (
    Column,
    Integer,
    Text,
    Date,
    Float,
    DateTime,
    String,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Opportunity(Base):
    """Stores a single scraped startup opportunity."""

    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core fields
    title = Column(Text, nullable=False)
    type = Column(Text, nullable=False)          # Grant | Accelerator | Conference | Fellowship | Competition
    organizer = Column(Text)
    location = Column(Text)                       # Remote | City, Country | Global
    deadline = Column(Date)                       # ISO date; NULL if rolling/unknown
    description = Column(Text)                    # Max 500 chars excerpt

    # Source identity — source_url is the primary dedup key
    source_url = Column(Text, nullable=False, unique=True)
    source_name = Column(Text, nullable=False)    # Devpost | F6S | Eventbrite | etc.

    # Lifecycle
    status = Column(Text, nullable=False, default="active")  # active | expired | pending

    # AI-tagged fields (Phase 5) — all nullable until tagged
    funding_range = Column(Text)                  # '$10K-$50K' | 'Up to $500K' | 'Equity-free' | 'Unknown'
    startup_stage = Column(Text)                  # 'Pre-seed' | 'Seed' | 'Series A' | 'Any stage' | 'Unknown'
    remote_or_onsite = Column(Text)               # 'Remote' | 'On-site' | 'Hybrid' | 'Unknown'
    ai_tagged_at = Column(DateTime(timezone=True))  # NULL until AI tagging runs

    # Premium Granular metrics & classification (User request)
    prize_pool = Column(Float, default=0.0)
    prize_pool_display = Column(Text)
    num_applicants = Column(Integer, default=None, nullable=True)
    is_hackathon = Column(Integer, default=1)      # 1 = True Competition/Hackathon; 0 = Other event/source
    sector = Column(Text)                           # AI / ML | FinTech | HealthTech | AgriTech | EdTech | CleanTech | Web3 | SaaS | Hardware | General

    # Timestamps
    scraped_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Opportunity id={self.id} title={self.title!r} "
            f"type={self.type!r} source={self.source_name!r}>"
        )


class PastProject(Base):
    """Stores user's past projects for compatibility matching."""

    __tablename__ = "past_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    technologies = Column(Text)  # comma-separated e.g. "React, FastAPI, Python"
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<PastProject id={self.id} title={self.title!r}>"


class OpportunityMatch(Base):
    """Stores Gemini-calculated compatibility scores between opportunities and past projects."""

    __tablename__ = "opportunity_matches"

    opportunity_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, primary_key=True)
    compatibility_score = Column(Float, nullable=False, default=0.0)
    compatibility_reason = Column(Text)
    matched_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<OpportunityMatch opp_id={self.opportunity_id} "
            f"proj_id={self.project_id} score={self.compatibility_score}>"
        )


class ScrapeLog(Base):
    """Records metadata about each scraping run per source."""

    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(Text, nullable=False)
    run_at = Column(DateTime(timezone=True), nullable=False)
    records_found = Column(Integer, nullable=False, default=0)
    new_records = Column(Integer, nullable=False, default=0)
    duration_sec = Column(Float)
    status = Column(Text, nullable=False)         # success | partial | failed
    error_msg = Column(Text)                      # NULL on success

    def __repr__(self) -> str:
        return (
            f"<ScrapeLog id={self.id} source={self.source_name!r} "
            f"status={self.status!r} new={self.new_records}>"
        )


class OpportunityReminder(Base):
    """Stores user reminders for specific opportunities."""

    __tablename__ = "opportunity_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False)
    opportunity_id = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<OpportunityReminder id={self.id} email={self.email!r} opp_id={self.opportunity_id}>"

