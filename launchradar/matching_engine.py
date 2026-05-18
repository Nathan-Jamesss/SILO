# matching_engine.py — Past Projects Compatibility Engine
import orjson
from loguru import logger
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models import PastProject, Opportunity, OpportunityMatch
from config import settings

import google.generativeai as genai

_gemini_configured = False
if settings.gemini_api_key:
    try:
        genai.configure(api_key=settings.gemini_api_key)
        _gemini_configured = True
    except Exception:
        pass

MATCHING_SYSTEM_PROMPT = """You are a hackathon compatibility analyzer.
You are given a developer's past project (title, summary, tech stack) and a startup/hackathon opportunity (title, description, stage, funding).
Evaluate how compatible the developer's project is with this opportunity. Can they submit their past project directly, adapt it slightly, or does their tech stack and expertise perfectly fit the requirements of the competition?

Return ONLY a JSON object with exactly these two keys:
- "compatibility_score": an integer between 0 and 100
- "compatibility_reason": a short, encouraging, and highly specific explanation (max 2 sentences) describing why this project matches or how they can adapt it.

Return ONLY the JSON. No markdown, no code blocks."""

async def calculate_compatibility(project: PastProject, opp: Opportunity) -> dict:
    """Compare a single project with a single opportunity using Gemini."""
    if not settings.gemini_api_key or not _gemini_configured:
        return _heuristic_match(project, opp)

    prompt = f"""
    {MATCHING_SYSTEM_PROMPT}

    PAST PROJECT:
    Title: {project.title}
    Technologies: {project.technologies}
    Summary: {project.summary}

    OPPORTUNITY:
    Title: {opp.title}
    Description: {opp.description}
    Type: {opp.type}
    AI Tags: Stage: {opp.startup_stage}, Funding: {opp.funding_range}, Location: {opp.remote_or_onsite}
    """

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2,
            )
        )
        data = orjson.loads(response.text.strip())
        score = int(data.get("compatibility_score", 50))
        reason = data.get("compatibility_reason", "Your background aligns well with this opportunity.")
        return {"score": score, "reason": reason}
    except Exception as e:
        logger.error(f"[Matching Engine] Gemini error during match: {e}")
        return _heuristic_match(project, opp)

def _heuristic_match(project: PastProject, opp: Opportunity) -> dict:
    """Fallback matching logic using text intersection (guarantees 100% uptime)."""
    proj_text = f"{project.title} {project.summary} {project.technologies}".lower()
    opp_text = f"{opp.title} {opp.description} {opp.type}".lower()

    # Calculate token overlap
    proj_words = set(re_words(proj_text))
    opp_words = set(re_words(opp_text))
    overlap = proj_words.intersection(opp_words)

    # Clean out common stopwords
    stopwords = {"and", "the", "with", "using", "for", "built", "project", "app", "hackathon", "web", "ai", "api"}
    overlap = overlap - stopwords

    score = 30  # baseline compatibility
    if overlap:
        score += min(len(overlap) * 12, 60)

    # Direct keyword matches
    techs = [t.strip().lower() for t in (project.technologies or "").split(",") if t.strip()]
    matched_techs = []
    for t in techs:
        if t in opp_text:
            score += 15
            matched_techs.append(t.title())

    score = min(score, 100)

    if score > 75:
        reason = f"Excellent compatibility! Your past project matches this competition's theme. Your expertise in {', '.join(matched_techs[:3])} is highly relevant."
    elif score > 50:
        reason = f"Good match. You can easily adapt your project for this event. Your work with {', '.join(matched_techs[:2]) if matched_techs else 'these technologies'} fits the guidelines."
    else:
        reason = "Moderate match. You have the foundational tech skills, but the theme might require building new features or modifying the scope."

    return {"score": float(score), "reason": reason}

def re_words(text: str):
    import re
    return re.findall(r'\b[a-z]{3,}\b', text)

async def match_project_with_all_opportunities(session: AsyncSession, project_id: int) -> None:
    """Calculate and store matches for a single project against all active opportunities."""
    # 1. Fetch project
    project_res = await session.execute(select(PastProject).where(PastProject.id == project_id))
    project = project_res.scalar_one_or_none()
    if not project:
        logger.error(f"[Matching Engine] Project {project_id} not found")
        return

    # 2. Fetch all active opportunities
    opp_res = await session.execute(select(Opportunity).where(Opportunity.status == "active"))
    opportunities = opp_res.scalars().all()
    logger.info(f"[Matching Engine] Running compatibility match for Project '{project.title}' against {len(opportunities)} opportunities...")

    # 3. Clear existing matches for this project to avoid duplicates
    await session.execute(delete(OpportunityMatch).where(OpportunityMatch.project_id == project_id))
    await session.commit()

    # 4. Compute matches (sequential to prevent API rate limiting, fast fallback guarantees speed)
    for opp in opportunities:
        match_data = await calculate_compatibility(project, opp)
        db_match = OpportunityMatch(
            opportunity_id=opp.id,
            project_id=project_id,
            compatibility_score=match_data["score"],
            compatibility_reason=match_data["reason"]
        )
        session.add(db_match)

    await session.commit()
    logger.info(f"[Matching Engine] Finished matching Project {project_id}")

async def match_all_projects_with_new_opportunity(session: AsyncSession, opp_id: int) -> None:
    """When a new opportunity is scraped, calculate compatibility against all existing projects."""
    opp_res = await session.execute(select(Opportunity).where(Opportunity.id == opp_id))
    opp = opp_res.scalar_one_or_none()
    if not opp:
        return

    proj_res = await session.execute(select(PastProject))
    projects = proj_res.scalars().all()

    for proj in projects:
        match_data = await calculate_compatibility(proj, opp)
        db_match = OpportunityMatch(
            opportunity_id=opp_id,
            project_id=proj.id,
            compatibility_score=match_data["score"],
            compatibility_reason=match_data["reason"]
        )
        session.add(db_match)

    await session.commit()
