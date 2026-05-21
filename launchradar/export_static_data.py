import sqlite3
import json
import os
import re

UNSTOP_FALLBACK = "https://unstop.com/hackathons"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def is_real_unstop_url(url: str) -> bool:
    """
    Real Unstop competition/hackathon URLs contain a numeric ID or have a long
    descriptive slug (e.g. /competitions/flipkart-grid-70-...-flipkart).
    Short generic slugs like /competitions/accenture-innovation-challenge are
    guessed/seed data and likely 404 on the actual SPA.
    """
    if not url or "unstop.com" not in url:
        return True  # not an unstop URL, leave alone
    slug = url.rstrip("/").split("/")[-1]
    # Real URLs: contain a number OR slug is long (>40 chars)
    has_number = bool(re.search(r'\d', slug))
    is_long = len(slug) > 40
    return has_number or is_long

def fix_url(opp: dict) -> dict:
    """Replace fake Unstop URLs with the main hackathons page."""
    url = opp.get("source_url", "")
    if "unstop.com" in url and not is_real_unstop_url(url):
        opp = dict(opp)
        opp["source_url"] = UNSTOP_FALLBACK
    return opp

def sort_key(opp: dict) -> int:
    """Devpost entries sort first (0), everything else after (1)."""
    source = (opp.get("source_name") or "").lower()
    return 0 if source == "devpost" else 1

def export_data():
    db_path = os.path.join(os.path.dirname(__file__), 'launchradar.db')
    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'silo-web', 'public', 'data.json')

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Exporting empty list.")
        opportunities = []
    else:
        conn = sqlite3.connect(db_path)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM opportunities ORDER BY scraped_at DESC")
        opportunities = cursor.fetchall()
        conn.close()

    # Fix fake Unstop URLs → fallback to main page
    opportunities = [fix_url(o) for o in opportunities]

    # Sort: Devpost first, then rest
    opportunities.sort(key=sort_key)

    data = {"opportunities": opportunities}

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    fixed = sum(1 for o in opportunities if o.get("source_url") == UNSTOP_FALLBACK)
    devpost_count = sum(1 for o in opportunities if (o.get("source_name") or "").lower() == "devpost")
    print(f"Exported {len(opportunities)} opportunities to {out_path}")
    print(f"  Devpost entries (sorted first): {devpost_count}")
    print(f"  Unstop URLs replaced with fallback: {fixed}")

if __name__ == "__main__":
    export_data()
