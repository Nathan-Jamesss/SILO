# ai_tagger.py — Gemini API Batch Tagging
import orjson
from loguru import logger

from config import settings

# We use google-generativeai (legacy) but with the correct model name.
# The new SDK is google.genai but we keep this for compatibility since it's installed.
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai

# Configure Gemini
_gemini_ready = False
if settings.gemini_api_key:
    try:
        genai.configure(api_key=settings.gemini_api_key)
        _gemini_ready = True
    except Exception:
        pass

SYSTEM_PROMPT = """You are a startup opportunity classifier.
Given a list of opportunities, return ONLY a JSON array (same order as input).
Each element must have exactly these keys:
- "funding_range": string like "$10K-$50K", "Up to $500K", "Equity-free", "Not specified"  
- "startup_stage": one of "Pre-seed", "Seed", "Series A", "Any stage", "Not specified"
- "remote_or_onsite": one of "Remote", "On-site", "Hybrid", "Not specified"
- "is_hackathon": integer 1 or 0 (1 if it is a true hackathon/competition/pitch contest where projects are built or pitch decks are judged; 0 if it is a passive conference, general networking event, non-competitive grant, or generic accelerator program)
- "sector": one of "AI / ML", "FinTech", "HealthTech", "Quantum", "AgriTech", "EdTech", "CleanTech", "Web3", "SaaS", "Hardware", "BioTech", "DeepTech", "SpaceTech", "Robotics", "General"

Rules:
- Infer from title + description + location. For example, if it is about quantum computing, choose "Quantum". If it's medical or healthcare, choose "HealthTech".
- If a conference location is a city, it's "On-site"
- If description mentions "virtual" or "online", it's "Remote"
- If grant has no equity, note "Equity-free" for funding_range with amount if visible
- Return ONLY the JSON array. No markdown, no code blocks."""


async def tag_opportunities(records: list[dict]) -> list[dict]:
    """
    Tag a list of opportunity dicts with AI metadata.
    Processes in batches of 10. Returns same list with tags filled in.
    If API key not configured, returns records unchanged with "Unknown" tags.
    """
    # Separate pre-tagged records to protect curated fields (e.g. from GrantsScraper)
    to_tag = []
    already_tagged = []
    for r in records:
        if r.get("ai_tagged_at") is not None:
            already_tagged.append(r)
        else:
            to_tag.append(r)

    if not to_tag:
        return already_tagged

    if not settings.gemini_api_key:
        logger.warning("[AI Tagger] GEMINI_API_KEY not set — skipping AI tagging")
        for record in to_tag:
            record["funding_range"] = "Unknown"
            record["startup_stage"] = "Unknown"
            record["remote_or_onsite"] = "Unknown"
            record["is_hackathon"] = 1
            record["sector"] = "General"
        return to_tag + already_tagged

    tagged = []
    batch_size = 10

    for i in range(0, len(to_tag), batch_size):
        batch = to_tag[i:i + batch_size]
        try:
            batch_tagged = await _tag_batch(batch)
            tagged.extend(batch_tagged)
        except Exception as e:
            logger.error(f"[AI Tagger] Batch {i // batch_size + 1} failed: {e}")
            # On failure, return records with "Unknown" tags rather than crashing
            for record in batch:
                record["funding_range"] = "Unknown"
                record["startup_stage"] = "Unknown"
                record["remote_or_onsite"] = "Unknown"
                record["is_hackathon"] = 1
                record["sector"] = "General"
                tagged.append(record)

    return tagged + already_tagged


async def _tag_batch(records: list[dict]) -> list[dict]:
    """Tag one batch of ≤10 records using Gemini."""
    user_content = "\n".join([
        f"{idx+1}. Title: {r.get('title', '')}\n"
        f"   Description: {r.get('description', '')[:200]}\n"
        f"   Location: {r.get('location', '')}"
        for idx, r in enumerate(records)
    ])
    
    full_prompt = f"{SYSTEM_PROMPT}\n\nOpportunities:\n{user_content}"

    # Use gemini-2.0-flash (widely available free tier model)
    # Fallback order: gemini-2.0-flash → gemini-1.5-flash-latest → gemini-pro
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    response = await model.generate_content_async(
        full_prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1,
        )
    )

    raw_text = response.text.strip()
    
    try:
        tags_list = orjson.loads(raw_text)
    except Exception as e:
        logger.error(f"[AI Tagger] Failed to parse JSON from Gemini: {e}")
        raise ValueError("Invalid JSON response from Gemini")

    if len(tags_list) != len(records):
        logger.warning(f"[AI Tagger] Length mismatch: got {len(tags_list)} tags for {len(records)} records")
        # Pad with empty dicts if short
        while len(tags_list) < len(records):
            tags_list.append({})

    for record, tags in zip(records, tags_list):
        record["funding_range"] = tags.get("funding_range", "Unknown")
        record["startup_stage"] = tags.get("startup_stage", "Unknown")
        record["remote_or_onsite"] = tags.get("remote_or_onsite", "Unknown")
        record["sector"] = tags.get("sector", "General")
        try:
            record["is_hackathon"] = int(tags.get("is_hackathon", 1))
        except (ValueError, TypeError):
            record["is_hackathon"] = 1

    return records
