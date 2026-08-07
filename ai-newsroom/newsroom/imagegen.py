"""AI તસવીર જનરેશન — OpenAI ની સત્તાવાર API થી (ChatGPT નું જ ઈમેજ એન્જિન).

ન્યુઝમાં સાચો ફોટો ન હોય ત્યારે હેડલાઈન પરથી પ્રતીકાત્મક તસવીર બનાવે.
લખાણ ક્યારેય ઈમેજમાં નહીં — બધું લખાણ HTML+CSS થી જ.
"""
import base64
from datetime import datetime

import httpx

from .paths import PHOTOS_DIR

PROMPT_TEMPLATE = (
    "Photorealistic editorial news photograph that is directly RELEVANT to "
    "this news: {scene}. Realistic photojournalism, India, natural lighting, "
    "respectful. Do NOT depict any specific real named person's face. "
    "STRICTLY NO text, NO letters, NO numbers, NO logos, NO watermarks "
    "anywhere in the image. {style}")


def build_prompt(cfg: dict, scene: str) -> str:
    """ઓટો પ્રોમ્પ્ટ બિલ્ડર — admin એ કંઈ ન લખવું પડે.
    દ્રશ્ય + સ્ટાઈલ + quality tags એકસાથે જોડે."""
    parts = [PROMPT_TEMPLATE.format(scene=scene,
                                    style=cfg.get("image_ai_style", "")).strip()]
    tags = (cfg.get("image_quality_tags") or "").strip()
    if tags:
        parts.append(tags)
    return ", ".join(p.strip(" ,") for p in parts if p.strip())

# વિષય ઓળખવા — હેડલાઈનમાં આ શબ્દ હોય તો એ દ્રશ્ય (LLM ન હોય ત્યારે વપરાય)
TOPIC_SCENES = [
    (("સંસદ", "લોકસભા", "રાજ્યસભા", "બિલ", "વિધાનસભા", "સરકાર", "મંત્રી"),
     "the Indian Parliament building in New Delhi, government"),
    (("મંદિર", "દ્વારકાધીશ", "દર્શન", "આરતી", "ધાર્મિક", "પૂજા", "યાત્રા"),
     "a Hindu temple in Gujarat with devotees"),
    (("વરસાદ", "હવામાન", "પૂર", "વાવાઝોડું", "ચોમાસું"),
     "monsoon rain over an Indian town, cloudy sky"),
    (("અકસ્માત", "દુર્ઘટના", "આગ", "બચાવ"),
     "an emergency response scene with rescue workers in India"),
    (("શાળા", "શિક્ષણ", "વિદ્યાર્થી", "પરીક્ષા", "કોલેજ"),
     "an Indian school building with students"),
    (("બસ", "રસ્તો", "હાઈવે", "ટ્રાફિક", "વાહન"),
     "an Indian road with a bus and traffic"),
    (("દરિયો", "બીચ", "માછીમાર", "બંદર", "ઓખા"),
     "the Gujarat coastline, sea and fishing boats"),
    (("ખેડૂત", "પાક", "ખેતી", "વાવેતર"),
     "an Indian farmer in a green field"),
    (("રમત", "ક્રિકેट", "ખેલાડી", "મેચ", "ટુર્નામેન્ટ"),
     "a sports ground in India"),
    (("પોલીસ", "ગુનો", "ધરપકડ", "ચોરી"),
     "Indian police officers on duty"),
    (("આરોગ્ય", "હોસ્પિટલ", "દવા", "કેમ્પ", "રસી"),
     "an Indian hospital or health camp"),
]


def topic_scene(title: str) -> str:
    """LLM ન હોય ત્યારે — હેડલાઈનના શબ્દ પરથી યોગ્ય દ્રશ્ય."""
    for words, scene in TOPIC_SCENES:
        if any(w in title for w in words):
            return scene
    return "a relevant local news scene in Gujarat, India"


def is_configured(cfg: dict) -> bool:
    if not cfg.get("image_ai_enabled"):
        return False
    provider = cfg.get("image_ai_provider", "pollinations")
    if provider in ("openai", "gemini"):
        return bool(cfg.get("image_ai_key"))
    if provider == "aiauto":
        return bool(cfg.get("aiauto_key") and cfg.get("aiauto_url"))
    return True  # pollinations / local — key વગર


def _file_url(base: str, f: dict) -> str:
    """ફાઈલ ડાઉનલોડનું સાચું URL — url ગમે તે રીતે આવે તો પણ ચાલે:
    પૂરું http, '/api/public/v1/files/42' (host સાથે જોડો), કે '/files/42'."""
    from urllib.parse import urlparse
    u = (f.get("url") or "").strip()
    if not u:
        return f"{base}/files/{f.get('id')}"
    if u.startswith("http"):
        return u
    p = urlparse(base)
    origin = f"{p.scheme}://{p.netloc}"
    if u.startswith("/api/"):          # host + પૂરો path
        return origin + u
    return base + ("" if u.startswith("/") else "/") + u


async def _aiauto(cfg: dict, prompt: str, on_wait=None) -> bytes:
    """AIAuto પ્લેટફોર્મ — async job: submit → poll → download.
    બધા job એક પછી એક ચાલે — એક ઈમેજને 1-4 મિનિટ (queue હોય તો વધુ)."""
    import asyncio
    base = cfg["aiauto_url"].rstrip("/")
    headers = {"X-API-Key": cfg["aiauto_key"]}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{base}/images", headers=headers,
                         json={"prompt": prompt})
        if r.status_code == 429:
            raise RuntimeError("AIAuto: બહુ ઝડપથી request (rate limit) — "
                               "થોડી વાર પછી ટ્રાય કરો")
        if r.status_code not in (200, 201):
            raise RuntimeError(f"AIAuto submit {r.status_code}: {r.text[:150]}")
        job_id = r.json().get("id")
        if not job_id:
            raise RuntimeError("AIAuto એ job id ન આપ્યો")
        # poll — ઈમેજ 1-4 મિનિટ લે; 15 મિનિટ સુધી રાહ (ગાઈડ મુજબ)
        for i in range(225):                    # 225 × 4s ≈ 15 મિનિટ
            await asyncio.sleep(4)
            j = (await c.get(f"{base}/jobs/{job_id}", headers=headers)).json()
            st = j.get("status")
            if on_wait and i % 5 == 0:          # દર ~20 સેકન્ડે જાણ
                qp = j.get("queue_position")
                await on_wait(st, j.get("progress"), qp, i * 4)
            if st == "completed":
                imgs = [f for f in j.get("files", [])
                        if f.get("kind") == "result_image"] or j.get("files", [])
                if not imgs:
                    raise RuntimeError("AIAuto: પૂરું થયું પણ ઈમેજ નથી")
                dl = await c.get(_file_url(base, imgs[0]), headers=headers,
                                 timeout=60)
                dl.raise_for_status()
                return dl.content
            if st in ("failed", "cancelled"):
                raise RuntimeError(f"AIAuto job {st}: {j.get('error')}")
    raise RuntimeError("AIAuto: 15 મિનિટમાં job પૂરું ન થયું — "
                       "queue લાંબી હોઈ શકે, પછી ટ્રાય કરો")


async def _local_sd(cfg: dict, prompt: str) -> bytes:
    """લોકલ Stable Diffusion (AUTOMATIC1111 / Forge / SD.Next નું API).
    તમારા GPU પર ચાલે — કોઈ ઈન્ટરનેટ નહીં, કાયમ ₹0."""
    base = (cfg.get("image_ai_local_url")
            or "http://127.0.0.1:7860").rstrip("/")
    steps = int(cfg.get("image_ai_local_steps") or 25)
    negative = ("text, letters, words, numbers, watermark, logo, "
                "caption, signature, blurry, distorted, low quality")
    async with httpx.AsyncClient(timeout=300) as c:
        r = await c.post(f"{base}/sdapi/v1/txt2img", json={
            "prompt": prompt,
            "negative_prompt": negative,
            "width": 1024, "height": 704,
            "steps": steps,
            "cfg_scale": float(cfg.get("image_ai_local_cfg") or 6),
            "sampler_name": cfg.get("image_ai_local_sampler") or "DPM++ 2M",
        })
        if r.status_code != 200:
            raise RuntimeError(
                f"લોકલ SD ભૂલ {r.status_code}: {r.text[:200]}")
        data = r.json().get("images")
        if not data:
            raise RuntimeError("લોકલ SD એ ઈમેજ ન આપી")
        return base64.b64decode(data[0])


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


async def diagnose_aiauto(cfg: dict) -> list[dict]:
    """AIAuto કનેક્શન સ્ટેપ-બાય-સ્ટેપ તપાસે — ભૂલ ક્યાં છે એ ચોક્કસ કહે.
    દરેક સ્ટેપ: {step, ok, detail}"""
    import socket
    from urllib.parse import urlparse

    out = []
    url = (cfg.get("aiauto_url") or "").rstrip("/")
    key = cfg.get("aiauto_key") or ""

    # 1) સેટિંગ ભરેલા છે?
    out.append({"step": "1. સેટિંગ", "ok": bool(url and key),
                "detail": (f"URL: {url or '(ખાલી)'} | "
                           f"Key: {'ભરેલી ✓' if key else '(ખાલી)'}")})
    if not (url and key):
        return out

    # 2) કોમ્પ્યુટર/પોર્ટ સુધી પહોંચાય છે? (TCP)
    p = urlparse(url)
    host, port = p.hostname, (p.port or (443 if p.scheme == "https" else 80))
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.close()
        out.append({"step": "2. સર્વર સુધી પહોંચ", "ok": True,
                    "detail": f"{host}:{port} જવાબ આપે છે ✓"})
    except Exception as e:
        out.append({"step": "2. સર્વર સુધી પહોંચ", "ok": False,
                    "detail": (f"{host}:{port} સુધી પહોંચાતું નથી — એ કોમ્પ્યુટર "
                               f"ચાલુ છે? AIAuto ચાલુ છે? ({type(e).__name__})")})
        return out

    # 3) API key ચાલે છે? (GET /me)
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{url}/me", headers={"X-API-Key": key})
        ok = r.status_code == 200
        out.append({"step": "3. API Key", "ok": ok,
                    "detail": (f"/me → {r.status_code} "
                               + ("બરાબર ✓" if ok else r.text[:120]))})
        if not ok:
            return out
    except Exception as e:
        out.append({"step": "3. API Key", "ok": False,
                    "detail": f"/me માં ભૂલ: {str(e)[:120]}"})
        return out

    # 4) ઈમેજ job સબમિટ થાય છે? (POST /images)
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{url}/images", headers={"X-API-Key": key},
                             json={"prompt": "test connection, a simple blue sky"})
        ok = r.status_code in (200, 201)
        jid = r.json().get("id") if ok else None
        out.append({"step": "4. ઈમેજ સબમિટ", "ok": bool(jid),
                    "detail": (f"/images → {r.status_code}, job id: {jid}"
                               if ok else f"{r.status_code}: {r.text[:150]}")})
    except Exception as e:
        out.append({"step": "4. ઈમેજ સબમિટ", "ok": False,
                    "detail": str(e)[:150]})
    return out


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


# કનેક્શન ન થાય ત્યારે સાફ ગુજરાતી સૂચના
CONNECT_HELP = {
    "local": ("લોકલ Stable Diffusion સાથે કનેક્ટ ન થયું — Forge/WebUI ચાલુ "
              "છે? `--api` સાથે ચલાવ્યું છે? URL બરાબર છે "
              "(http://127.0.0.1:7860)?"),
    "pollinations": ("Pollinations સાથે કનેક્ટ ન થયું — ઈન્ટરનેટ ચેક કરો, "
                     "કે થોડી વારે ફરી ટ્રાય કરો."),
    "gemini": "Google Gemini સાથે કનેક્ટ ન થયું — ઈન્ટરનેટ ચેક કરો.",
    "openai": "OpenAI સાથે કનેક્ટ ન થયું — ઈન્ટરનેટ ચેક કરો.",
    "aiauto": ("AIAuto પ્લેટફોર્મ સાથે કનેક્ટ ન થયું — સર્વર ચાલુ છે? "
               "URL/key બરાબર છે? (સેટિંગ → AI તસવીર)"),
}


async def generate(cfg: dict, title: str, scene: str = "",
                   on_wait=None) -> str | None:
    """તસવીર બનાવીને ફાઈલ-પાથ પાછો આપે. ભૂલ પડે તો exception.
    scene = ન્યુઝનું અંગ્રેજી દ્રશ્ય-વર્ણન (LLM થી). ખાલી હોય તો વિષય પરથી."""
    if not is_configured(cfg):
        return None
    if not scene:
        scene = topic_scene(title)
    # ઓટો પ્રોમ્પ્ટ — admin એ કંઈ ન લખવું પડે
    prompt = build_prompt(cfg, scene)
    provider = cfg.get("image_ai_provider", "pollinations")
    try:
        if provider == "openai":
            img = await _openai(cfg, prompt)
        elif provider == "gemini":
            img = await _gemini(cfg, prompt)
        elif provider == "local":
            img = await _local_sd(cfg, prompt)
        elif provider == "aiauto":
            img = await _aiauto(cfg, prompt, on_wait)
        else:
            img = await _pollinations(prompt)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
        msg = CONNECT_HELP.get(provider, "કનેક્ટ ન થયું — સેટિંગ ચેક કરો.")
        url = {"aiauto": cfg.get("aiauto_url"),
               "local": cfg.get("image_ai_local_url")}.get(provider)
        if url:
            msg += f"\n(જ્યાં જોડાવા ગયું: {url})"
        raise RuntimeError(msg) from e
    out = PHOTOS_DIR / f"ai_{datetime.now():%Y%m%d_%H%M%S}.png"
    out.write_bytes(img)
    return str(out)
