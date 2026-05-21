"""
scrape_and_export.py
Run all scrapers → export to silo-web/public/data.json → rebuild frontend.
Run manually: python scrape_and_export.py
Run on schedule: python scrape_and_export.py --watch   (repeats every 24h)
"""
import asyncio
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
SILO_WEB = ROOT / "silo-web"

async def scrape():
    from scheduler import run_all_scrapers
    print("[1/3] Running all scrapers...")
    summary = await run_all_scrapers()
    print(f"      Sources: {summary['sources_run']}")
    print(f"      New records: {summary['total_new']}")
    if summary["errors"]:
        print(f"      Errors: {summary['errors']}")
    return summary

def export():
    print("[2/3] Exporting to data.json...")
    import export_static_data
    export_static_data.export_data()

def rebuild():
    print("[3/3] Rebuilding silo-web...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(SILO_WEB),
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("      Build successful.")
    else:
        print("      Build failed:")
        print(result.stderr[-500:])

async def run_once():
    await scrape()
    export()
    rebuild()
    print("Done.\n")

async def watch(interval_hours: int = 24):
    while True:
        print(f"=== Scrape + Export cycle starting ===")
        await run_once()
        print(f"Next run in {interval_hours}h. Press Ctrl+C to stop.\n")
        await asyncio.sleep(interval_hours * 3600)

if __name__ == "__main__":
    watch_mode = "--watch" in sys.argv
    if watch_mode:
        asyncio.run(watch(24))
    else:
        asyncio.run(run_once())
