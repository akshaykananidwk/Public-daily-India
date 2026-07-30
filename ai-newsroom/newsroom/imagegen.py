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
    if not cfg.get("image_ai_enabled"):
        return False
    provider = cfg.get("image_ai_provider", "pollinations")
    if provider in ("openai", "gemini"):
        return bool(cfg.get("image_ai_key"))
    return True  # pollinations — મફત, key વગર


async def _openai(cfg: dict, prompt: str) -> bytes:
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
        return base64.b64decode(r.json()["data"][0]["b64_json"])


async def _gemini(cfg: dict, prompt: str) -> bytes:
    """Google Gemini ઈમેજ જનરેશન (~₹3/તસવીર, ફ્રી ટિયરમાં અમુક રોજ મફત)."""
    model = cfg.get("image_ai_model") or ""
    if not model.startswith("gemini"):
        model = "gemini-2.5-flash-image"
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    async with httpx.AsyncClient(timeout=240) as c:
        r = await c.post(url, params={"key": cfg["image_ai_key"]},
                         json={"contents": [{"parts": [{"text": prompt}]}]})
        if r.status_code != 200:
            raise RuntimeError(
                f"Gemini ઈમેજ API ભૂલ {r.status_code}: {r.text[:200]}")
        for cand in r.json().get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                data = part.get("inlineData") or part.get("inline_data")
                if data and data.get("data"):
                    return base64.b64decode(data["data"])
    raise RuntimeError("Gemini એ ઈમેજ ન આપી — model નામ ચેક કરો "
                       "(gemini-2.5-flash-image)")


async def _pollinations(prompt: str) -> bytes:
    """મફત સર્વિસ — ટેસ્ટિંગ માટે. કોઈ key નહીં, કોઈ ખર્ચ નહીં."""
    from urllib.parse import quote
    url = (f"https://image.pollinations.ai/prompt/{quote(prompt[:400])}"
           f"?width=1536&height=1024&nologo=true&model=flux&enhance=true")
    async with httpx.AsyncClient(timeout=240, follow_redirects=True) as c:
        r = await c.get(url, headers={"User-Agent": "ai-newsroom"})
        if r.status_code != 200:
            raise RuntimeError(
                f"Pollinations ભૂલ {r.status_code}: {r.text[:150]}")
        if len(r.content) < 5000:   # ઈમેજ નહીં પણ error-page આવ્યું હોય
            raise RuntimeError("Pollinations એ ઈમેજ ન આપી")
        return r.content


async def generate(cfg: dict, title: str) -> str | None:
    """તસવીર બનાવીને ફાઈલ-પાથ પાછો આપે. ભૂલ પડે તો exception."""
    if not is_configured(cfg):
        return None
    prompt = PROMPT_TEMPLATE.format(
        title=title, style=cfg.get("image_ai_style", ""))
    provider = cfg.get("image_ai_provider", "pollinations")
    if provider == "openai":
        img = await _openai(cfg, prompt)
    elif provider == "gemini":
        img = await _gemini(cfg, prompt)
    else:
        img = await _pollinations(prompt)
    out = PHOTOS_DIR / f"ai_{datetime.now():%Y%m%d_%H%M%S}.png"
    out.write_bytes(img)
    return str(out)
