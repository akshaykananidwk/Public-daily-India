"""WhatsApp નોટિફિકેશન — તમારી પોતાની API (દા.ત. bulk.akdwk.in) દ્વારા.

POST JSON: { api_key, number, message, session_id, media_url? }
"""
import re

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


# ગ્રુપનું જૂનું ફોર્મેટ: બનાવનારનો નંબર - બન્યાનો સમય (919978123146-1616161616)
_GROUP_RE = re.compile(r"^\d{10,}-\d{9,}$")


def clean_target(v: str) -> str:
    """મોકલવાનું ઠેકાણું સાફ કરે — નંબર હોય કે ગ્રુપ ID, બંને ચાલે.

    ગ્રુપ ID આવા દેખાય: 120363041234567890@g.us  કે  919978123146-1616161616
    — એ જેમનાં તેમ મોકલવાં. સાદો નંબર હોય તો ફક્ત આંકડા રાખવા, જેથી
    '+91 99781-23146' જેવું લખો તો પણ ચાલે."""
    v = (v or "").strip()
    if not v:
        return ""
    if "@" in v or _GROUP_RE.match(v):       # ગ્રુપ ID — બદલવું નહીં
        return v
    return "".join(ch for ch in v if ch.isdigit())


def _base_ok(cfg: dict) -> bool:
    """API પોતે ગોઠવાયેલી છે? (ઠેકાણું બાદ કરતાં)"""
    return bool(cfg.get("whatsapp_api_url") and cfg.get("whatsapp_api_key")
                and cfg.get("whatsapp_session_id"))


def is_configured(cfg: dict) -> bool:
    return bool(_base_ok(cfg) and cfg.get("whatsapp_number"))


def instant_target(cfg: dict) -> str:
    """ન્યુઝ બનતાં જ જ્યાં મોકલવાનું છે એ — કોમન નંબર કે ગ્રુપ ID.
    ખાલી હોય તો મુખ્ય નંબર વપરાય."""
    return clean_target(cfg.get("whatsapp_instant_to")
                        or cfg.get("whatsapp_number") or "")


def instant_ready(cfg: dict) -> bool:
    return bool(cfg.get("whatsapp_instant_enabled") and _base_ok(cfg)
                and instant_target(cfg))


async def poster_link(cfg: dict, file_path: str) -> str:
    """પોસ્ટરની પબ્લિક લિંક — તમારી hosting હોય તો એ, નહીંતર ફ્રી હોસ્ટ."""
    if not file_path:
        return ""
    base = (cfg.get("public_base_url") or "").rstrip("/")
    if base:
        from pathlib import Path
        from .paths import STORAGE_DIR
        try:
            rel = Path(file_path).relative_to(STORAGE_DIR)
            return f"{base}/storage/{rel.as_posix()}"
        except ValueError:
            pass
    return await upload_public(file_path)


async def send_instant(cfg: dict, message: str, media_url: str = "") -> dict:
    """ન્યુઝ બનતાં જ કોમન નંબર/ગ્રુપ પર મોકલો (અપ્રુવલ પહેલાં)."""
    if not instant_ready(cfg):
        return {"skipped": True, "reason": "instant WhatsApp બંધ કે અધૂરું"}
    return await _send_one(cfg, instant_target(cfg), message, media_url)


async def _send_one(cfg: dict, number: str, message: str,
                    media_url: str = "") -> dict:
    payload = {
        "api_key": cfg["whatsapp_api_key"],
        "number": clean_target(number),
        "message": message,
        "session_id": cfg["whatsapp_session_id"],
    }
    if media_url:
        payload["media_url"] = media_url
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(cfg["whatsapp_api_url"], json=payload)
        return {"number": number, "status": r.status_code}
    except Exception as e:
        return {"number": number, "error": str(e)[:200]}


async def send(cfg: dict, message: str, media_url: str = "") -> dict:
    """મુખ્ય નંબર પર મોકલો."""
    if not is_configured(cfg):
        return {"skipped": True,
                "reason": "સેટિંગમાં WhatsApp API ભરેલું નથી"}
    return await _send_one(cfg, cfg["whatsapp_number"], message, media_url)


async def send_broadcast(cfg: dict, message: str,
                         media_url: str = "") -> dict:
    """મુખ્ય નંબર + બ્રોડકાસ્ટ યાદીના બધા નંબર પર મોકલો."""
    if not is_configured(cfg):
        return {"skipped": True, "reason": "WhatsApp API ભરેલું નથી"}
    numbers = [clean_target(cfg["whatsapp_number"])]
    for n in (cfg.get("whatsapp_broadcast") or "").replace("\n", ",").split(","):
        n = clean_target(n)
        if n and n not in numbers:
            numbers.append(n)
    results = []
    for n in numbers:
        results.append(await _send_one(cfg, n, message, media_url))
    ok = sum(1 for r in results if r.get("status") == 200)
    return {"sent": ok, "total": len(numbers), "results": results}
