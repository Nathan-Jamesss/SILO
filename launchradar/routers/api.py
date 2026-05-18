# routers/api.py — JSON API endpoints for export, tagging, and scraping
import csv
import io
from datetime import date, datetime, timezone

import orjson
from fastapi import APIRouter, Depends, Response
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel
from ai_tagger import tag_opportunities
from database import get_db
from models import Opportunity, ScrapeLog, PastProject, OpportunityMatch, OpportunityReminder
from scheduler import run_all_scrapers
from config import settings
import google.generativeai as genai

# Configure Generative AI globally if key is available
if settings.gemini_api_key:
    try:
        genai.configure(api_key=settings.gemini_api_key)
        logger.info("[SAILO Bot] Gemini client configured successfully.")
    except Exception as e:
        logger.error(f"[SAILO Bot] Global configuration failed: {e}")

router = APIRouter(tags=["API"])


class ReminderCreate(BaseModel):
    email: str
    opportunity_id: int


class ChatMessage(BaseModel):
    message: str


@router.post("/api/reminders")
async def create_reminder(data: ReminderCreate, session: AsyncSession = Depends(get_db)):
    """Set an email deadline reminder for an opportunity."""
    reminder = OpportunityReminder(
        email=data.email,
        opportunity_id=data.opportunity_id
    )
    session.add(reminder)
    await session.commit()
    logger.info(f"[API] Registered email reminder for email={data.email} opportunity_id={data.opportunity_id}")
    return {"status": "success", "message": f"Deadline reminder set for {data.email}!"}


@router.post("/api/sailo-bot")
async def sailo_bot_chat(payload: ChatMessage):
    """Chat with SAILO Bot - Startup Mentor AI."""
    if not settings.gemini_api_key:
        return {
            "response": (
                "Hello! I am **SAILO Bot**, your dedicated startup mentor. It looks like the Gemini API key "
                "is not currently set in the `.env` file, so I am running in offline mode. \n\n"
                "Here are key insights to help you right now:\n"
                "- **How to ask for grants:** Focus on government portals (like MSME and state-level startup portals). Categorize your project under a specific technical domain (e.g. HealthTech, Quantum, SaaS). Prepare a high-fidelity pitch deck, and apply early before deadlines.\n"
                "- **Startup Registration Workflow:** Formulate a structured legal entity (Pvt Ltd, LLP, or Proprietorship). Register under DIPP (DPIIT recognition) to qualify for tax exemptions and exclusive MSME funding.\n"
                "- **Incubators & Accelerators:** Match with platforms that offer active co-working spaces, mentors, and seed funds. Avoid empty networking events.\n\n"
                "To enable interactive chat conversations, please set your `GEMINI_API_KEY` in the workspace environment!"
            )
        }
    
    system_prompt = (
        "You are SAILO Bot, a highly professional, encouraging, and expert AI startup mentor. "
        "Your mission is to guide startup founders with extremely detailed, actionable, and structured advice on:\n"
        "1. How and when to apply for government grants (like MSME portals, state-level grants, capital subsidies) vs. private corporate grants.\n"
        "2. Structured legal entity registration workflows (explaining the differences between Private Limited Company, LLP, and Proprietorship; how to secure DIPP/DPIIT startup recognition; tax holiday eligibility; and PAN/GST setup).\n"
        "3. Pitching templates, standard slide structures, financial and business model projections, and milestone-based fundable planning.\n\n"
        "Keep your advice extremely actionable, structured, and easy to read. "
        "Use bullet points, bold headers, and clean markdown spacing. "
        "Always give specific step-by-step checklists where possible. "
        "Never say you are Gemini or created by Google. You are purely SAILO Bot, powered by SILO's intelligence."
    )
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        full_content = f"{system_prompt}\n\nUser Question: {payload.message}"
        response = await model.generate_content_async(full_content)
        return {"response": response.text.strip()}
    except Exception as e:
        err_msg = str(e)
        logger.error(f"[SAILO Bot] Error encountered during chat generation: {err_msg}")
        
        # Check if this is a Gemini API quota or rate limit error
        if "429" in err_msg or "quota" in err_msg.lower() or "limit" in err_msg.lower() or "exceeded" in err_msg.lower():
            msg_lower = payload.message.lower()
            offline_advice = ""
            
            if "msme" in msg_lower or "grant" in msg_lower:
                offline_advice = (
                    "\n\n**💡 Fast-Track Grants Advice:**\n"
                    "1. Register on the government MSME Udyam portal to acquire a unique Udyam Registration Number.\n"
                    "2. Access the **MSME Innovative Scheme** to check eligibility for the ₹15 Lakhs incubation/equity-free design grant.\n"
                    "3. Submit a proof-of-concept pitch deck early, aligning with a specific priority sector (e.g., AgriTech, HealthTech, deep tech)."
                )
            elif "regis" in msg_lower or "llp" in msg_lower or "pvt" in msg_lower or "company" in msg_lower:
                offline_advice = (
                    "\n\n**📋 Registration Fast-Track:**\n"
                    "1. Choose **Pvt Ltd** if you plan to raise equity from angel investors/VCs; Choose **LLP** for simple compliance with multiple equal partners.\n"
                    "2. File for DPIIT recognition via the Startup India portal to qualify for Section 80-IAC 3-year income tax holiday benefits.\n"
                    "3. Prepare your PAN, GST, and corporate bank accounts before applying for any capital funding."
                )
            elif "pitch" in msg_lower or "deck" in msg_lower or "milestone" in msg_lower:
                offline_advice = (
                    "\n\n**💰 Pitching & Funding Fast-Track:**\n"
                    "1. Structure your pitch deck with 10 standard slides: Problem, Solution, Market Size, Product, Traction, Team, Competition, Business Model, Financials, and Ask.\n"
                    "2. Focus heavily on traction and target segment metrics rather than general technology descriptions.\n"
                    "3. Align your funding 'Ask' with concrete, 12-to-18-month operational and tech milestones."
                )
            
            return {
                "response": (
                    "👋 Hello there! I'm SAILO Bot. It looks like our active free-tier Gemini API key "
                    "has reached its temporary API quota limit for the moment.\n\n"
                    "Please wait a few moments or try asking again shortly! In the meantime, based on your inquiry, "
                    f"here is a quick offline mentor checklist to help you move forward immediately:{offline_advice or '\n- Keep refining your startup idea and pitch metrics!\n- Leverage standard MSME schemes and Startup India portals.'}"
                )
            }
            
        return {
            "response": (
                "Oops! I hit a temporary network hiccup while connecting to the AI brain. "
                "Please wait a moment and try asking me again. I'm always here to help!"
            )
        }


@router.post("/api/scrape-now")
async def scrape_now():
    """Manually trigger all scrapers to run immediately."""
    logger.info("[API] Manual scrape triggered")
    summary = await run_all_scrapers()
    return summary


@router.get("/api/sources")
async def get_sources(session: AsyncSession = Depends(get_db)):
    """Return health and stats for all configured sources."""
    # Group by source_name, get the latest ScrapeLog
    subq = (
        select(
            ScrapeLog.source_name,
            func.max(ScrapeLog.run_at).label("max_run_at")
        )
        .group_by(ScrapeLog.source_name)
        .subquery()
    )
    
    query = (
        select(ScrapeLog)
        .join(subq, (ScrapeLog.source_name == subq.c.source_name) & (ScrapeLog.run_at == subq.c.max_run_at))
    )
    result = await session.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "source": log.source_name,
            "last_run": log.run_at.isoformat(),
            "status": log.status,
            "found": log.records_found,
            "new": log.new_records,
            "duration": log.duration_sec,
        }
        for log in logs
    ]


@router.post("/api/tag-all")
async def tag_all_untagged(session: AsyncSession = Depends(get_db)):
    """Find all opportunities without AI tags and batch-tag them."""
    result = await session.execute(
        select(Opportunity).where(Opportunity.ai_tagged_at.is_(None))
    )
    untagged_opps = result.scalars().all()
    
    if not untagged_opps:
        return {"tagged": 0, "message": "All records are already tagged."}
        
    logger.info(f"[API] Found {len(untagged_opps)} untagged records. Running AI tagger...")
    
    # Convert ORM objects to dicts for the tagger
    records = [
        {
            "id": opp.id,
            "title": opp.title,
            "description": opp.description,
            "location": opp.location,
        }
        for opp in untagged_opps
    ]
    
    tagged_records = await tag_opportunities(records)
    
    # Map tags back to ORM objects
    tags_by_id = {r["id"]: r for r in tagged_records}
    now = datetime.now(timezone.utc)
    
    for opp in untagged_opps:
        tags = tags_by_id.get(opp.id, {})
        opp.funding_range = tags.get("funding_range", "Unknown")
        opp.startup_stage = tags.get("startup_stage", "Unknown")
        opp.remote_or_onsite = tags.get("remote_or_onsite", "Unknown")
        opp.ai_tagged_at = now
        
    await session.commit()
    return {"tagged": len(untagged_opps)}


async def _query_opportunities(
    session: AsyncSession,
    q: str = "",
    type_filter: str = "",
    source: str = "",
    deadline: str = "",
    stage: str = "",
    export_all: bool = False,
) -> list[Opportunity]:
    """Helper to apply the same filters as the dashboard for export endpoints."""
    query = select(Opportunity)
    if not export_all:
        query = query.where(Opportunity.status == "active")

    if not export_all and q:
        search_term = f"%{q.lower()}%"
        query = query.where(
            func.lower(Opportunity.title).like(search_term) |
            func.lower(Opportunity.description).like(search_term) |
            func.lower(Opportunity.organizer).like(search_term)
        )
    if not export_all and type_filter:
        query = query.where(Opportunity.type == type_filter)
    if not export_all and source:
        query = query.where(Opportunity.source_name == source)
    if not export_all and stage:
        query = query.where(Opportunity.startup_stage == stage)
    if not export_all and deadline == "this_week":
        query = query.where(Opportunity.deadline <= date.today() + __import__("datetime").timedelta(days=7))
    elif not export_all and deadline == "this_month":
        query = query.where(Opportunity.deadline <= date.today() + __import__("datetime").timedelta(days=30))
    elif not export_all and deadline == "next_3_months":
        query = query.where(Opportunity.deadline <= date.today() + __import__("datetime").timedelta(days=90))

    query = query.order_by(Opportunity.scraped_at.desc())
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/api/export/csv")
async def export_csv(
    q: str = "",
    type_filter: str = "",
    source: str = "",
    deadline: str = "",
    stage: str = "",
    export_all: bool = False,
    session: AsyncSession = Depends(get_db)
):
    """Stream CSV of filtered opportunities."""
    opportunities = await _query_opportunities(session, q, type_filter, source, deadline, stage, export_all)
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "Title", "Type", "Organizer", "Location or Eligibility", "Deadline or Event Date", "Source Link", "Date Scraped"
    ])
    writer.writeheader()
    for opp in opportunities:
        writer.writerow({
            "Title": opp.title,
            "Type": opp.type,
            "Organizer": opp.organizer or "",
            "Location or Eligibility": opp.location or "",
            "Deadline or Event Date": opp.deadline.isoformat() if opp.deadline else "",
            "Source Link": opp.source_url,
            "Date Scraped": opp.scraped_at.isoformat() if opp.scraped_at else "",
        })
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=soi_{date.today()}.csv"}
    )


@router.get("/api/export/json")
async def export_json(
    q: str = "",
    type_filter: str = "",
    source: str = "",
    deadline: str = "",
    stage: str = "",
    export_all: bool = False,
    session: AsyncSession = Depends(get_db)
):
    """Return JSON array of filtered opportunities with metadata wrapper."""
    opportunities = await _query_opportunities(session, q, type_filter, source, deadline, stage, export_all)
    
    data = []
    for opp in opportunities:
        data.append({
            "Title": opp.title,
            "Type": opp.type,
            "Organizer": opp.organizer or "",
            "Location or Eligibility": opp.location or "",
            "Deadline or Event Date": opp.deadline.isoformat() if opp.deadline else None,
            "Source Link": opp.source_url,
            "Date Scraped": opp.scraped_at.isoformat() if opp.scraped_at else None,
        })
        
    return Response(
        content=orjson.dumps({
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total": len(data),
            "filters": {"q": q, "type": type_filter, "source": source, "deadline": deadline, "stage": stage, "export_all": export_all},
            "data": data
        }),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=soi_{date.today()}.json"}
    )


# ── Past Projects Matching REST API ───────────────────────────────────────
from pydantic import BaseModel
from sqlalchemy import delete
from matching_engine import match_project_with_all_opportunities

class ProjectCreate(BaseModel):
    title: str
    summary: str
    technologies: str


@router.get("/api/projects")
async def get_projects(session: AsyncSession = Depends(get_db)):
    """Fetch all saved past projects."""
    result = await session.execute(select(PastProject).order_by(PastProject.created_at.desc()))
    projects = result.scalars().all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "summary": p.summary,
            "technologies": p.technologies,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in projects
    ]


@router.post("/api/projects")
async def create_project(data: ProjectCreate, session: AsyncSession = Depends(get_db)):
    """Create a new project and trigger compatibility matching immediately."""
    proj = PastProject(
        title=data.title,
        summary=data.summary,
        technologies=data.technologies
    )
    session.add(proj)
    await session.commit()
    await session.refresh(proj)

    # Automatically trigger compatibility matching for this project
    await match_project_with_all_opportunities(session, proj.id)

    return {
        "status": "success",
        "project": {
            "id": proj.id,
            "title": proj.title,
            "summary": proj.summary,
            "technologies": proj.technologies
        }
    }


@router.delete("/api/projects/{project_id}")
async def delete_project(project_id: int, session: AsyncSession = Depends(get_db)):
    """Delete a past project and all its calculated compatibility matches."""
    # Delete matches first
    await session.execute(delete(OpportunityMatch).where(OpportunityMatch.project_id == project_id))
    # Delete project
    await session.execute(delete(PastProject).where(PastProject.id == project_id))
    await session.commit()
    return {"status": "success", "message": f"Project {project_id} deleted"}


@router.post("/api/projects/{project_id}/match")
async def force_match_project(project_id: int, session: AsyncSession = Depends(get_db)):
    """Manually force recalculating compatibility matches for a past project."""
    await match_project_with_all_opportunities(session, project_id)
    return {"status": "success", "message": f"Project {project_id} matched"}
