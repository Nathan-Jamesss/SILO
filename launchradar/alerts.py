# alerts.py — Webhook alert sender for new opportunities
from datetime import datetime, timezone
from typing import Any

import httpx
from loguru import logger

from config import settings


async def send_webhook_alert(new_records: list[dict[str, Any]]) -> None:
    """
    POST a summary of new opportunities to the configured webhook URL.
    Gracefully handles missing configuration or network errors.

    Args:
        new_records: List of newly inserted opportunity dicts
    """
    if not settings.alert_webhook_url:
        return

    if not new_records:
        return

    payload = {
        "event": "new_opportunities",
        "count": len(new_records),
        "preview": [r.get("title", "Unknown") for r in new_records[:3]],
        "dashboard_url": f"http://{settings.app_host}:{settings.app_port}/",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(settings.alert_webhook_url, json=payload)
            resp.raise_for_status()
            logger.info(f"[Alerts] Webhook sent for {len(new_records)} new records")
    except Exception as exc:
        logger.warning(f"[Alerts] Webhook delivery failed (non-critical): {exc}")
