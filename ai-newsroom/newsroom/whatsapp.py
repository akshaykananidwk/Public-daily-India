"""WhatsApp નોટિફિકેશન — તમારી પોતાની API (દા.ત. bulk.akdwk.in) દ્વારા.

POST JSON: { api_key, number, message, session_id, media_url? }
"""
import httpx


async def _up_litterbox(c, data) -> str:
    r = await c.post(
        "https://litterbox.catbox.moe/resources/internals/api.php",
        data={"reqtype": "fileupload", "time": "72h"},
        files={"fileToUpload": ("poster.png", data, "image/png")})
    r.raise_for_status()
    return r.text.strip() if r.text.startswith("http") else ""


async def _up_uguu(c, data) -> str:
    r = await c.post("https://uguu.se/upload.php",
                     files={"files[]": ("poster.png", data, "image/png")})
    r.raise_for_status()
    return r.json()["files"][0]["url"]


async def upload_public(file_path: str) -> str:
    """લોકલ ફાઈલને ફ્રી હોસ્ટ પર ચડાવી *ડાયરેક્ટ ઈમેજ* લિંક પાછી આપે
    (WhatsApp media માટે). એક હોસ્ટ ફેલ થાય તો બીજો ટ્રાય કરે.
    litterbox 72 કલાક રહે — WhatsApp ડિલિવરી માટે પૂરતું."""
    try:
        with open(file_path, "rb") as fh:
            data = fh.read()
    except Exception:
        return ""
    async with httpx.AsyncClient(timeout=90) as c:
        for uploader in (_up_litterbox, _up_uguu):
            try:
                url = await uploader(c, data)
                if url and url.startswith("http"):
                    return url
            except Exception:
                continue
    return ""


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
