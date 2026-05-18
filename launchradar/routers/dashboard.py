# routers/dashboard.py — Main web UI routes
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Opportunity, ScrapeLog, PastProject, OpportunityMatch

router = APIRouter(tags=["Dashboard"])


def get_deadline_badge(deadline: date | None) -> dict[str, str]:
    """Calculate deadline urgency and return badge styling."""
    if not deadline:
        return {"text": "No deadline", "class": "deadline-none"}
    
    days = (deadline - date.today()).days
    if days < 0:
        return {"text": "Expired", "class": "deadline-expired"}
    elif days <= 7:
        return {"text": f"{days}d left", "class": "deadline-urgent"}
    elif days <= 30:
        return {"text": f"{days}d left", "class": "deadline-soon"}
    else:
        return {"text": f"{days}d left", "class": "deadline-ok"}


# Type badge CSS classes — each type gets a distinct visual weight within the beige/coffee palette
_TYPE_BADGE_CLASSES: dict[str, str] = {
    # Darkest — solid espresso fill, white text
    "Grant":       "type-badge-grant",
    # Medium — coffee brown fill, cream text
    "Accelerator": "type-badge-accelerator",
    # Warm tan — solid mid-beige, dark espresso text
    "Conference":  "type-badge-conference",
    # Light — cream fill with coffee border
    "Competition": "type-badge-competition",
    # Outline only — white fill, dashed coffee border
    "Fellowship":  "type-badge-fellowship",
}


def get_type_badge(opp_type: str) -> str:
    """Return CSS class string for the given opportunity type badge."""
    return _TYPE_BADGE_CLASSES.get(opp_type, "type-badge-default")


@router.get("/")
async def dashboard(
    request: Request,
    q: str = "",
    type_filter: str = "",
    source: str = "",
    deadline: str = "",
    stage: str = "",
    sort: str = "newest",
    page: int = 1,
    selected_project_id: int = 0,
    sector: str = "",
    session: AsyncSession = Depends(get_db),
):
    """
    Render the main dashboard.
    Handles all filtering, sorting, pagination, and stats calculations server-side.
    """
    per_page = 24
    offset = (page - 1) * per_page
    today = date.today()

    selected_project_id = int(selected_project_id) if selected_project_id else 0

    # Base query — join matches if a project is selected
    if selected_project_id > 0:
        query = (
            select(
                Opportunity, 
                OpportunityMatch.compatibility_score, 
                OpportunityMatch.compatibility_reason
            )
            .outerjoin(
                OpportunityMatch, 
                (Opportunity.id == OpportunityMatch.opportunity_id) & 
                (OpportunityMatch.project_id == selected_project_id)
            )
            .where(Opportunity.status == "active")
        )
    else:
        query = select(Opportunity).where(Opportunity.status == "active")

    # Apply filters
    if q:
        search_term = f"%{q.lower()}%"
        query = query.where(
            func.lower(Opportunity.title).like(search_term)
            | func.lower(Opportunity.description).like(search_term)
            | func.lower(Opportunity.organizer).like(search_term)
        )
    
    if type_filter:
        query = query.where(Opportunity.type == type_filter)
        
    if source:
        query = query.where(Opportunity.source_name == source)
        
    if stage:
        query = query.where(Opportunity.startup_stage == stage)

    if sector:
        query = query.where(Opportunity.sector == sector)

    if deadline == "this_week":
        query = query.where(Opportunity.deadline <= today + timedelta(days=7))
    elif deadline == "this_month":
        query = query.where(Opportunity.deadline <= today + timedelta(days=30))
    elif deadline == "next_3_months":
        query = query.where(Opportunity.deadline <= today + timedelta(days=90))

    # Calculate total matching before pagination
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(total_query)
    total_matches = total_result.scalar() or 0
    total_pages = max(1, (total_matches + per_page - 1) // per_page)

    # Apply sorting
    if sort == "deadline_asc":
        query = query.order_by(Opportunity.deadline.asc().nulls_last())
    elif sort == "prize_desc":
        query = query.order_by(Opportunity.prize_pool.desc().nulls_last())
    elif sort == "applicants_desc":
        query = query.order_by(Opportunity.num_applicants.desc().nulls_last())
    elif sort == "compatibility_desc" and selected_project_id > 0:
        query = query.order_by(OpportunityMatch.compatibility_score.desc().nulls_last())
    else:  # newest
        query = query.order_by(Opportunity.scraped_at.desc())

    # Pagination
    query = query.limit(per_page).offset(offset)
    
    result = await session.execute(query)
    rows = result.all()

    opportunities = []
    compatibility_scores = {}
    compatibility_reasons = {}

    for row in rows:
        if selected_project_id > 0:
            opp, score, reason = row
            opportunities.append(opp)
            compatibility_scores[opp.id] = int(score) if score is not None else 0
            compatibility_reasons[opp.id] = reason or "No compatibility details analyzed yet."
        else:
            opp = row[0]
            opportunities.append(opp)

    # Calculate global stats for the top bar
    stats_result = await session.execute(
        select(
            func.count().label("total_active"),
            func.sum(
                case(
                    (Opportunity.deadline <= today + timedelta(days=7), 1),
                    else_=0
                )
            ).label("expiring_soon")
        ).where(Opportunity.status == "active")
    )
    stats_row = stats_result.first()
    
    # Sources live (how many sources successfully scraped in last 24h)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    sources_result = await session.execute(
        select(func.count(func.distinct(ScrapeLog.source_name)))
        .where(ScrapeLog.status == "success", ScrapeLog.run_at >= yesterday)
    )
    sources_live = sources_result.scalar() or 0
    
    # Last updated
    last_run_result = await session.execute(
        select(ScrapeLog.run_at).order_by(ScrapeLog.run_at.desc()).limit(1)
    )
    last_run = last_run_result.scalar()

    stats = {
        "total_active": stats_row.total_active if stats_row else 0,
        "expiring_soon": int(stats_row.expiring_soon or 0) if stats_row else 0,
        "sources_live": sources_live,
        "last_scraped": last_run.strftime("%Y-%m-%d %H:%M UTC") if last_run else "Never",
    }

    # Pre-compute badges for template
    deadline_badges = {opp.id: get_deadline_badge(opp.deadline) for opp in opportunities}
    type_badges = {opp.id: get_type_badge(opp.type) for opp in opportunities}

    # Fetch user projects for selector/manager
    projects_res = await session.execute(select(PastProject).order_by(PastProject.created_at.desc()))
    all_projects = projects_res.scalars().all()

    # Helper to generate URL with updated param (flawless clearing)
    def url_with(param: str, value: Any) -> str:
        current = dict(request.query_params)
        if value is None or value == "":
            current.pop(param, None)
        else:
            current[param] = str(value)
        # Always reset to page 1 if changing a filter
        if param != "page":
            current.pop("page", None)
        from urllib.parse import urlencode
        query_string = urlencode(current)
        return f"/?{query_string}" if query_string else "/"

    return request.app.state.templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "opportunities": opportunities,
            "total": total_matches,
            "page": page,
            "total_pages": total_pages,
            "q": q,
            "type_filter": type_filter,
            "source_filter": source,
            "deadline_filter": deadline,
            "stage_filter": stage,
            "sector_filter": sector,
            "sort": sort,
            "selected_project_id": selected_project_id,
            "all_projects": all_projects,
            "compatibility_scores": compatibility_scores,
            "compatibility_reasons": compatibility_reasons,
            "stats": stats,
            "deadline_badges": deadline_badges,
            "type_badges": type_badges,
            "url_with": url_with,
        },
    )
