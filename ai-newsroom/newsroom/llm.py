"""Ollama ક્લાયન્ટ + બે-પગલાંનું ગુજરાતી લેખન.

Ollama ન ચાલતું હોય તો ડેમો મોડ — સિસ્ટમ અટકે નહીં, નમૂના લખાણથી
આખો પ્રવાહ ટેસ્ટ થઈ શકે.
"""
import httpx

DEMO_BODY = (
    "આ સમાચારની વધુ વિગતો ટૂંક સમયમાં ઉપલબ્ધ થશે. "
    "આપની આસપાસ બનતી ઘટના કે સમાચાર અમને મોકલો.")


class LLM:
    def __init__(self, cfg: dict):
        self.base = cfg["ollama_url"].rstrip("/")
        self.model_think = cfg["model_think"]
        self.model_write = cfg["model_write"]
        self.model_translate = cfg.get("model_translate") or cfg["model_write"]
        self.mode = cfg.get("writing_mode", "translate")

    async def available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{self.base}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def generate(self, model: str, prompt: str, system: str = "") -> str:
        async with httpx.AsyncClient(timeout=600) as c:
            r = await c.post(f"{self.base}/api/generate", json={
                "model": model, "prompt": prompt, "system": system,
                "stream": False})
            r.raise_for_status()
            return r.json().get("response", "").strip()

    # ── CEO: સ્કોરિંગ ────────────────────────────────────────────
    async def score_items(self, items: list[dict], count: int) -> list[dict]:
        if not await self.available():
            return items[:count]
        titles = "\n".join(f"{i}. {it['title']}" for i, it in enumerate(items))
        try:
            out = await self.generate(
                self.model_think,
                f"You are the news editor of a local Gujarati news channel in "
                f"Devbhumi Dwarka, Gujarat. From the list below pick the {count} "
                f"most relevant items for a local audience. Reply ONLY with the "
                f"numbers, comma separated.\n\n{titles}")
            picked = []
            for tok in out.replace("\n", ",").split(","):
                tok = "".join(ch for ch in tok if ch.isdigit())
                if tok and int(tok) < len(items):
                    picked.append(items[int(tok)])
            return (picked or items)[:count]
        except Exception:
            return items[:count]

    # ── લેખક: બે-પગલાંનું ગુજરાતી ───────────────────────────────
    async def write_news(self, item: dict) -> dict:
        title = item.get("title", "")
        if not await self.available():
            return {"title": title, "body": DEMO_BODY, "demo": True}
        if self.mode == "direct":
            body = await self.generate(
                self.model_write,
                f"તમે ગુજરાતી ન્યુઝ ચેનલના પત્રકાર છો. આ હેડલાઈન પરથી 4-5 "
                f"વાક્યનો ટૂંકો, હકીકતલક્ષી ગુજરાતી ન્યુઝ લખો. અતિશયોક્તિ "
                f"નહીં, શુદ્ધ જોડણી:\n\n{title}")
            return {"title": title, "body": body, "demo": False}
        # translate મોડ — પગલું 1: અંગ્રેજી ડ્રાફ્ટ
        english = await self.generate(
            self.model_write,
            f"You are a local news reporter. Write a short factual news "
            f"paragraph (4-5 sentences) in English from this headline. No "
            f"exaggeration:\n\n{title}")
        # પગલું 2: ગુજરાતી અનુવાદ (IndicTrans2 હોય તો એ, નહીંતર LLM)
        gujarati = await self.generate(
            self.model_translate,
            f"Translate the following news paragraph to Gujarati. Output only "
            f"the Gujarati translation, nothing else:\n\n{english}")
        # પગલું 3: ન્યુઝ-શૈલી પોલિશ
        polished = await self.generate(
            self.model_write,
            f"નીચેના ગુજરાતી લખાણને ન્યુઝ-શૈલીમાં પોલિશ કરો. જોડણી અને "
            f"માત્રા સુધારો. ફક્ત સુધારેલું લખાણ આપો:\n\n{gujarati}")
        return {"title": title, "body": polished or gujarati, "demo": False}

    # ── શુદ્ધિ: ચકાસણી ──────────────────────────────────────────
    async def proofread(self, title: str, body: str) -> dict:
        issues = []
        if len(body.strip()) < 30:
            issues.append("લખાણ ખૂબ ટૂંકું છે")
        if "  " in body:
            body = " ".join(body.split())
        if await self.available():
            try:
                body = await self.generate(
                    self.model_write,
                    f"આ ગુજરાતી ન્યુઝમાં જોડણી/વ્યાકરણની ભૂલ હોય તો સુધારો. "
                    f"ફક્ત સુધારેલું લખાણ આપો, બીજું કંઈ નહીં:\n\n{body}")
            except Exception:
                pass
        return {"title": title.strip(), "body": body.strip(), "issues": issues}
