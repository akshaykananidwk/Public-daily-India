"""WhatsApp નોટિફિકેશન — તમારી પોતાની API (દા.ત. bulk.akdwk.in) દ્વારા.

POST JSON: { api_key, number, message, session_id, media_url? }
"""
import httpx


def is_configured(cfg: dict) -> bool:
    return bool(cfg.get("whatsapp_api_url") and cfg.get("whatsapp_api_key")
                and cfg.get("whatsapp_session_id")
                and cfg.get("whatsapp_number"))


async def send(cfg: dict, message: str, media_url: str = "") -> dict:
    if not is_configured(cfg):
        return {"skipped": True,
                "reason": "સેટિંગમાં WhatsApp API ભરેલું નથી"}
    payload = {
        "api_key": cfg["whatsapp_api_key"],
        "number": cfg["whatsapp_number"],
        "message": message,
        "session_id": cfg["whatsapp_session_id"],
    }
    if media_url:
        payload["media_url"] = media_url
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(cfg["whatsapp_api_url"], json=payload)
        return {"status": r.status_code, "response": r.text[:300]}
    except Exception as e:
        return {"error": str(e)[:300]}
