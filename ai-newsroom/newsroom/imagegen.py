"""AI તસવીર જનરેશન — AIAuto પ્લેટફોર્મ કે Google Gemini થી.

ન્યુઝમાં સાચો ફોટો ન હોય ત્યારે હેડલાઈન પરથી પ્રતીકાત્મક તસવીર બનાવે.
લખાણ ક્યારેય ઈમેજમાં નહીં — બધું લખાણ HTML+CSS થી જ.
"""
import base64
from datetime import datetime

import httpx

from .config import clean_key
from .paths import PHOTOS_DIR

PROMPT_TEMPLATE = (
    "Ultra realistic editorial NEWS PHOTOGRAPH, shot on a professional DSLR "
    "by a press photojournalist, of exactly this scene: {scene}. "
    "{variant} "
    "The main subject is large, centred and unmistakably clear, tack sharp "
    "focus on the subject with shallow depth of field, natural lighting, "
    "realistic shadows and realistic perspective, strong cinematic "
    "contrast, HDR, 8K, ultra detailed, wide 16:9 framing with the subject "
    "in the upper half. Setting is India. "
    "This is a PHOTOGRAPH — absolutely NOT an illustration, NOT a painting, "
    "NOT a drawing, NOT a cartoon, NOT a 3D render, NOT a poster or "
    "collage. Any people must be anonymous ordinary people; never depict a "
    "real politician, celebrity or any identifiable public figure. "
    "STRICTLY NO text, NO letters, NO numbers, NO logos, NO watermarks, "
    "no random unrelated objects anywhere in the image. {style}")

# દરેક ન્યુઝનું દ્રશ્ય જુદું લાગે — એક જ કમ્પોઝિશન વારંવાર ન આવે
VARIANTS = [
    "Eye-level wide establishing shot, morning light.",
    "Low angle looking slightly up, late afternoon golden light.",
    "Slightly elevated three-quarter angle, bright overcast daylight.",
    "Tight mid-shot from the side, warm evening light.",
    "Wide environmental shot with strong foreground depth, midday light.",
    "Over-the-shoulder documentary angle, soft diffused light.",
    "Straight-on centred composition, dramatic side lighting.",
    "Off-centre rule-of-thirds framing, long shadows at dusk.",
]


def _variant(seed: str) -> str:
    """એક જ પ્રકારના ન્યુઝમાં પણ કેમેરા-એંગલ/પ્રકાશ બદલાય."""
    return VARIANTS[sum(ord(c) for c in (seed or "x")) % len(VARIANTS)]


def build_prompt(cfg: dict, scene: str, seed: str = "") -> str:
    """ઓટો પ્રોમ્પ્ટ બિલ્ડર — admin એ કંઈ ન લખવું પડે.
    દ્રશ્ય + કેમેરા વેરિએન્ટ + સ્ટાઈલ + quality tags એકસાથે જોડે."""
    parts = [PROMPT_TEMPLATE.format(
        scene=scene, variant=_variant(seed or scene),
        style=cfg.get("image_ai_style", "")).strip()]
    tags = (cfg.get("image_quality_tags") or "").strip()
    if tags:
        parts.append(tags)
    return ", ".join(p.strip(" ,") for p in parts if p.strip())

# વિષય ઓળખવા — હેડલાઈનમાં આ શબ્દ હોય તો એ દ્રશ્ય (LLM ન હોય ત્યારે વપરાય)
TOPIC_SCENES = [
    (("સંસદ", "લોકસભા", "રાજ્યસભા", "બિલ", "વિધાનસભા", "ચૂંટણી", "મતદાન"),
     "the Indian Parliament / state assembly building, political press "
     "conference setting, microphones and podium"),
    (("સરકાર", "મંત્રી", "કલેક્ટર", "અધિકારી", "બેઠક"),
     "an official Indian government meeting room, officials seated at a "
     "long table with files"),
    (("મંદિર", "દ્વારકાધીશ", "દર્શન", "આરતી", "ધાર્મિક", "પૂજા", "યાત્રા"),
     "a Hindu temple in Gujarat, carved architecture, devotees offering "
     "prayers, oil lamps"),
    (("ઉત્સવ", "તહેવાર", "જન્માષ્ટમી", "નવરાત્રી", "દિવાળી", "ગણેશ",
      "રંગોળી", "શોભાયાત્રા"),
     "a vibrant Indian festival celebration, decorations, marigold "
     "garlands, festive crowd"),
    (("વરસાદ", "હવામાન", "પૂર", "વાવાઝોડું", "ચોમાસું", "એલર્ટ"),
     "heavy monsoon rain over a Gujarat town, dark storm clouds, wet "
     "roads, people with umbrellas"),
    (("અકસ્માત", "દુર્ઘટના", "ટક્કર", "પલટી"),
     "the aftermath of a road accident in India, damaged vehicle on the "
     "roadside, police and onlookers"),
    (("આગ", "બચાવ", "રાહત", "ફાયર"),
     "an emergency rescue operation in India, fire brigade and rescue "
     "workers in action"),
    (("શાળા", "શિક્ષણ", "વિદ્યાર્થી", "પરીક્ષા", "કોલેજ", "પરિણામ"),
     "an Indian school, students in uniform in a classroom or courtyard"),
    (("આરોગ્ય", "હોસ્પિટલ", "દવા", "કેમ્પ", "રસી", "રોગ", "દર્દી"),
     "an Indian hospital ward, doctors in white coats and medical "
     "equipment, clean clinical lighting"),
    (("પોલીસ", "ગુનો", "ધરપકડ", "ચોરી", "લૂંટ", "હત્યા", "તપાસ"),
     "Indian police officers at an investigation scene, uniformed "
     "personnel and a cordoned area"),
    (("ઉદ્યોગ", "કારખાનું", "ફેક્ટરી", "વેપાર", "બજાર", "ધંધો", "રોકાણ",
      "ભાવ"),
     "an Indian factory floor or busy market, workers and machinery, "
     "commerce activity"),
    (("રમત", "ક્રિકેટ", "ખેલાડી", "મેચ", "ટુર્નામેન્ટ", "સ્પર્ધા"),
     "a sports stadium in India during play, athletes in action on the "
     "field, floodlights"),
    (("બસ", "રસ્તો", "હાઈવે", "ટ્રાફિક", "વાહન", "પુલ"),
     "an Indian highway with traffic and a bus, roadside infrastructure"),
    (("દરિયો", "બીચ", "માછીમાર", "બંદર", "ઓખા", "બોટ"),
     "the Gujarat coastline, fishing boats at a harbour, sea and sky"),
    (("ખેડૂત", "પાક", "ખેતી", "વાવેતર", "સિંચાઈ"),
     "an Indian farmer working in a green crop field, agricultural "
     "landscape"),
    (("પાણી", "પુરવઠો", "નળ", "બોર", "ડેમ"),
     "a water supply scheme in rural India, pipeline or village water tap"),
    (("લોકાર્પણ", "ઉદ્ઘાટન", "ખાતમુહૂર્ત", "શિલાન્યાસ", "યોજના", "વિકાસ",
      "સામાનઘર"),
     "an inauguration ceremony of a new public building in India, ribbon "
     "cutting, dignitaries and a crowd"),
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
    provider = cfg.get("image_ai_provider", "aiauto")
    if provider == "gemini":
        return bool(cfg.get("image_ai_key"))
    return bool(cfg.get("aiauto_key") and cfg.get("aiauto_url"))


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
    headers = {"X-API-Key": clean_key(cfg["aiauto_key"])}
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
    raw_key = cfg.get("aiauto_key") or ""
    key = clean_key(raw_key)

    # 1) સેટિંગ ભરેલા છે?
    note = ""
    if raw_key.strip() != key:
        note = ("  ⚠️ Key માં ઈમોજી/space જેવો કચરો હતો — સાફ કરીને વાપર્યો. "
                "સેટિંગમાં ફક્ત ak_... વાળો key જ પેસ્ટ કરો.")
    out.append({"step": "1. સેટિંગ", "ok": bool(url and key),
                "detail": (f"URL: {url or '(ખાલી)'} | "
                           f"Key: {'ભરેલી ✓' if key else '(ખાલી)'}" + note)})
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
        if host in ("127.0.0.1", "localhost", "::1"):
            hint = ("⚠️ 127.0.0.1 એટલે 'આ જ કોમ્પ્યુટર'. AIAuto જો બીજા "
                    "કોમ્પ્યુટર પર ચાલે છે તો એનું સાચું IP લખો — "
                    "દા.ત. http://192.168.10.7:8000/api/public/v1")
        else:
            hint = ("એ કોમ્પ્યુટર ચાલુ છે? AIAuto ચાલુ છે? "
                    "એક જ WiFi/નેટવર્ક પર છો? Firewall બંધ છે?")
        out.append({"step": "2. સર્વર સુધી પહોંચ", "ok": False,
                    "detail": (f"{host}:{port} સુધી પહોંચાતું નથી "
                               f"({type(e).__name__}). {hint}")})
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


# કનેક્શન ન થાય ત્યારે સાફ ગુજરાતી સૂચના
CONNECT_HELP = {
    "gemini": "Google Gemini સાથે કનેક્ટ ન થયું — ઈન્ટરનેટ ચેક કરો.",
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
    prompt = build_prompt(cfg, scene, seed=title)
    provider = cfg.get("image_ai_provider", "aiauto")
    try:
        if provider == "gemini":
            img = await _gemini(cfg, prompt)
        else:
            img = await _aiauto(cfg, prompt, on_wait)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
        msg = CONNECT_HELP.get(provider, "કનેક્ટ ન થયું — સેટિંગ ચેક કરો.")
        if provider != "gemini" and cfg.get("aiauto_url"):
            msg += f"\n(જ્યાં જોડાવા ગયું: {cfg['aiauto_url']})"
        raise RuntimeError(msg) from e
    out = PHOTOS_DIR / f"ai_{datetime.now():%Y%m%d_%H%M%S}.png"
    out.write_bytes(img)
    return str(out)
