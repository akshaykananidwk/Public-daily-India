"""AI તસવીર જનરેશન — OpenAI ની સત્તાવાર API થી (ChatGPT નું જ ઈમેજ એન્જિન).

ન્યુઝમાં સાચો ફોટો ન હોય ત્યારે હેડલાઈન પરથી પ્રતીકાત્મક તસવીર બનાવે.
લખાણ ક્યારેય ઈમેજમાં નહીં — બધું લખાણ HTML+CSS થી જ.
"""
import base64
from datetime import datetime

import httpx

from .paths import PHOTOS_DIR

PROMPT_TEMPLATE = (
    "Photorealistic editorial news photograph illustrating this Gujarati "
    "local news headline: {title}. Setting: Devbhumi Dwarka district, "
    "coastal Gujarat, India. Natural lighting, realistic, respectful. "
    "STRICTLY NO text, NO letters, NO numbers, NO logos, NO watermarks "
    "anywhere in the image. {style}")


def is_configured(cfg: dict) -> bool:
    return bool(cfg.get("image_ai_enabled") and cfg.get("image_ai_key"))


async def generate(cfg: dict, title: str) -> str | None:
    """તસવીર બનાવીને ફાઈલ-પાથ પાછો આપે. ભૂલ પડે તો exception."""
    if not is_configured(cfg):
        return None
    prompt = PROMPT_TEMPLATE.format(
        title=title, style=cfg.get("image_ai_style", ""))
    async with httpx.AsyncClient(timeout=240) as c:
        r = await c.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {cfg['image_ai_key']}"},
            json={
                "model": cfg.get("image_ai_model") or "gpt-image-1",
                "prompt": prompt,
                "size": "1536x1024",          # પોસ્ટર માટે લેન્ડસ્કેપ
                "quality": cfg.get("image_ai_quality") or "medium",
                "n": 1,
            })
        if r.status_code != 200:
            raise RuntimeError(
                f"OpenAI ઈમેજ API ભૂલ {r.status_code}: {r.text[:200]}")
        img = base64.b64decode(r.json()["data"][0]["b64_json"])
    out = PHOTOS_DIR / f"ai_{datetime.now():%Y%m%d_%H%M%S}.png"
    out.write_bytes(img)
    return str(out)
