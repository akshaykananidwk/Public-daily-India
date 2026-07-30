"""Telegram ચેનલ ઓટો-પોસ્ટ — બોટ ટોકનથી (મફત, verification વગર).

સેટઅપ:
1. Telegram માં @BotFather ને /newbot કહી બોટ બનાવો → ટોકન મળે
2. તમારી ચેનલમાં એ બોટને Admin બનાવો
3. chat_id = @yourchannel (કે -100... નંબર)
પોસ્ટર સીધું અપલોડ થાય — કોઈ public URL જોઈએ નહીં.
"""
import httpx


def is_configured(cfg: dict) -> bool:
    return bool(cfg.get("telegram_token") and cfg.get("telegram_chat"))


async def send_photo(cfg: dict, file_path: str, caption: str = "") -> dict:
    if not is_configured(cfg):
        return {"skipped": True, "reason": "Telegram સેટ નથી"}
    token, chat = cfg["telegram_token"], cfg["telegram_chat"]
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        async with httpx.AsyncClient(timeout=90) as c:
            with open(file_path, "rb") as fh:
                r = await c.post(url,
                    data={"chat_id": chat, "caption": caption[:1024]},
                    files={"photo": fh})
        ok = r.status_code == 200 and r.json().get("ok")
        return {"ok": bool(ok), "status": r.status_code,
                "response": r.text[:200]}
    except Exception as e:
        return {"error": str(e)[:200]}


async def send_text(cfg: dict, text: str) -> dict:
    if not is_configured(cfg):
        return {"skipped": True}
    token, chat = cfg["telegram_token"], cfg["telegram_chat"]
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat, "text": text[:4000]})
        return {"ok": r.status_code == 200, "status": r.status_code}
    except Exception as e:
        return {"error": str(e)[:200]}
