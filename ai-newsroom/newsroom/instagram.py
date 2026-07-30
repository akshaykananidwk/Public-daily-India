"""Instagram ઓટો-પોસ્ટ — Facebook Graph API (Content Publishing) થી.

જોઈએ:
- Instagram Business/Creator એકાઉન્ટ, Facebook Page સાથે જોડાયેલું
- facebook_page_token (long-lived, permissions: instagram_basic,
  instagram_content_publish, pages_read_engagement)
- instagram_account_id (IG Business Account ID)

IG ને પબ્લિક image_url જોઈએ — એટલે પોસ્ટર પહેલા ફ્રી હોસ્ટ પર ચડે.
"""
import asyncio

import httpx

GRAPH = "https://graph.facebook.com/v19.0"


def is_configured(cfg: dict) -> bool:
    return bool(cfg.get("instagram_account_id")
                and cfg.get("facebook_page_token"))


async def publish(cfg: dict, image_url: str, caption: str) -> dict:
    if not is_configured(cfg):
        return {"skipped": True, "reason": "Instagram સેટ નથી"}
    if not image_url:
        return {"error": "પબ્લિક image_url નથી (પોસ્ટર અપલોડ ફેલ)"}
    ig_id = cfg["instagram_account_id"]
    token = cfg["facebook_page_token"]
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            # 1. મીડિયા કન્ટેનર બનાવો
            r = await c.post(f"{GRAPH}/{ig_id}/media", data={
                "image_url": image_url, "caption": caption[:2200],
                "access_token": token})
            if r.status_code != 200:
                return {"error": f"કન્ટેનર ભૂલ: {r.text[:200]}"}
            creation_id = r.json().get("id")
            # 2. પ્રોસેસ થવાની થોડી રાહ
            await asyncio.sleep(5)
            # 3. પબ્લિશ કરો
            r2 = await c.post(f"{GRAPH}/{ig_id}/media_publish", data={
                "creation_id": creation_id, "access_token": token})
            if r2.status_code != 200:
                return {"error": f"પબ્લિશ ભૂલ: {r2.text[:200]}"}
        return {"ok": True, "id": r2.json().get("id")}
    except Exception as e:
        return {"error": str(e)[:200]}
