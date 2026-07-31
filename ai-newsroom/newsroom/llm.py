"""ટેક્સ્ટ AI — ન્યુઝ *રિરાઈટ* કરે (કોપીરાઈટ ટાળવા), ગુજરાતીમાં લખે.

પ્રોવાઈડર: ollama (લોકલ) | gemini | openai
દરેક ન્યુઝ પોતાના શબ્દોમાં નવેસરથી લખાય — બીજાનું હૂબહૂ નહીં.
કોઈ પ્રોવાઈડર સેટ ન હોય તો લખાણ ખાલી (પ્લેસહોલ્ડર નહીં) — Gemini ચાલુ કરો.
"""
import json

import httpx

# Gemini મોડેલ — પહેલું ન ચાલે તો બીજું (Google સમયે સમયે બદલે છે)
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-flash-latest",
                 "gemini-2.5-flash", "gemini-2.0-flash-001",
                 "gemini-1.5-flash-latest"]
_WORKING_GEMINI = {"text": None, "vision": None}   # જે ચાલ્યું એ યાદ રાખો


class LLM:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.provider = cfg.get("text_provider", "ollama")
        self.base = cfg["ollama_url"].rstrip("/")
        self.model_think = cfg["model_think"]
        self.model_write = cfg["model_write"]
        self.model_translate = cfg.get("model_translate") or cfg["model_write"]
        self.mode = cfg.get("writing_mode", "translate")
        self.api_key = cfg.get("text_api_key", "")
        self.text_model = cfg.get("text_model", "")

    # ── ઉપલબ્ધ છે? ──────────────────────────────────────────────
    async def available(self) -> bool:
        if self.provider in ("gemini", "openai"):
            return bool(self.api_key)
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{self.base}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    # ── જનરેટ (પ્રોવાઈડર પ્રમાણે) ────────────────────────────────
    async def generate(self, model: str, prompt: str, system: str = "") -> str:
        if self.provider == "gemini":
            return await self._gemini(prompt, system)
        if self.provider == "openai":
            return await self._openai(prompt, system)
        return await self._ollama(model, prompt, system)

    async def _ollama(self, model, prompt, system) -> str:
        async with httpx.AsyncClient(timeout=600) as c:
            r = await c.post(f"{self.base}/api/generate", json={
                "model": model, "prompt": prompt, "system": system,
                "stream": False})
            r.raise_for_status()
            return r.json().get("response", "").strip()

    def _model_candidates(self, kind: str) -> list:
        """ટ્રાય કરવાના મોડેલ — user નું, જે પહેલા ચાલ્યું, પછી યાદી."""
        cands = []
        if self.text_model:
            cands.append(self.text_model)
        if _WORKING_GEMINI.get(kind):
            cands.append(_WORKING_GEMINI[kind])
        cands += GEMINI_MODELS
        seen, out = set(), []
        for m in cands:
            if m and m not in seen:
                seen.add(m); out.append(m)
        return out

    async def _gemini_call(self, body: dict, kind: str) -> str:
        """એક પછી એક મોડેલ ટ્રાય કરે; 404 (મોડેલ નથી) હોય તો બીજું."""
        last = None
        async with httpx.AsyncClient(timeout=120) as c:
            for model in self._model_candidates(kind):
                url = (f"https://generativelanguage.googleapis.com/v1beta/"
                       f"models/{model}:generateContent")
                r = await c.post(url, params={"key": self.api_key}, json=body)
                if r.status_code == 404:
                    last = r
                    continue                # આ મોડેલ નથી — બીજું ટ્રાય
                r.raise_for_status()
                _WORKING_GEMINI[kind] = model    # ચાલ્યું — યાદ રાખો
                data = r.json()
                cand = (data.get("candidates") or [{}])[0]
                parts = cand.get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts).strip()
        if last is not None:
            last.raise_for_status()
        return ""

    async def _gemini(self, prompt, system) -> str:
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        return await self._gemini_call(body, "text")

    async def _openai(self, prompt, system) -> str:
        model = self.text_model or "gpt-4o-mini"
        msgs = ([{"role": "system", "content": system}] if system else []) + \
            [{"role": "user", "content": prompt}]
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post("https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": msgs})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()

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

    # ── લેખક: આખો ન્યુઝ *રિરાઈટ* કરે (કોપીરાઈટ ટાળવા) ────────────
    SYSTEM = ("તમે 'Public Daily India' ગુજરાતી ન્યુઝ ચેનલના અનુભવી પત્રકાર છો. "
              "તમે સ્વચ્છ, હકીકતલક્ષી, મૌલિક ગુજરાતી ન્યુઝ લખો છો — બીજાનું "
              "લખાણ ક્યારેય હૂબહૂ નકલ કરતા નથી.")

    async def write_news(self, item: dict) -> dict:
        title = item.get("title", "")
        source = item.get("press_note") or title
        if not await self.available():
            # કોઈ પ્રોવાઈડર નથી — પ્લેસહોલ્ડર નહીં, ખાલી (Gemini ચાલુ કરો)
            return {"title": title, "body": "", "demo": True}
        prompt = (
            "નીચેની માહિતી પરથી એક *મૌલિક* ગુજરાતી સમાચાર લખો — તમારા પોતાના "
            "શબ્દોમાં, બીજાનું લખાણ હૂબહૂ નકલ કર્યા વગર (કોપીરાઈટ ટાળવા). "
            "આપો:\n"
            "લાઈન 1: નવી, આકર્ષક હેડલાઈન (ટૂંકી)\n"
            "પછી: 3-4 વાક્યનો હકીકતલક્ષી સમાચાર (અતિશયોક્તિ નહીં, શુદ્ધ જોડણી)\n"
            "ફક્ત આટલું જ, બીજું કંઈ નહીં.\n\nમાહિતી:\n" + source)
        try:
            out = await self.generate(self.model_write, prompt, self.SYSTEM)
        except Exception:
            return {"title": title, "body": "", "demo": True}
        lines = [l.strip() for l in out.split("\n") if l.strip()]
        if not lines:
            return {"title": title, "body": "", "demo": False}
        new_title = lines[0].lstrip("#*-• ").replace("હેડલાઈન:", "").strip()
        new_body = " ".join(lines[1:]).strip()
        if not new_body:                    # બધું એક લાઈનમાં આવ્યું
            new_body, new_title = new_title, title
        return {"title": new_title or title, "body": new_body, "demo": False}

    # ── Vision: ઈમેજ (PDF પાનું) જોઈને ન્યુઝ કાઢે ────────────────
    async def vision_news(self, image_b64: str, mime: str = "image/jpeg") -> dict:
        """પ્રેસ નોટના ફોટા/પાનાને *જોઈને* સ્વચ્છ ગુજરાતી ન્યુઝ કાઢે.
        ભૂલ પડે તો {'error': ...} પાછું આપે (છુપાવે નહીં)."""
        prompt = (
            "આ એક પ્રેસ નોટ / સમાચાર દસ્તાવેજની તસવીર છે. તેને ધ્યાનથી વાંચો "
            "અને એમાંથી *મૌલિક* ગુજરાતી સમાચાર બનાવો (હૂબહૂ નકલ નહીં). આપો:\n"
            "લાઈન 1: આકર્ષક હેડલાઈન\n"
            "પછી: 3-4 વાક્યનો હકીકતલક્ષી સમાચાર. ફક્ત આટલું જ.")
        try:
            if self.provider == "gemini":
                out = await self._gemini_vision(prompt, image_b64, mime)
            elif self.provider == "openai":
                out = await self._openai_vision(prompt, image_b64)
            else:
                return {"error": "Vision માટે Gemini/OpenAI જોઈએ"}
        except httpx.HTTPStatusError as e:
            return {"error": f"AI {e.response.status_code}: "
                             f"{e.response.text[:180]}"}
        except Exception as e:
            return {"error": str(e)[:180]}
        lines = [l.strip() for l in out.split("\n") if l.strip()]
        if not lines:
            return {"error": "AI એ ખાલી જવાબ આપ્યો"}
        title = lines[0].lstrip("#*-• ").replace("હેડલાઈન:", "").strip()
        body = " ".join(lines[1:]).strip()
        return {"title": title, "body": body}

    async def _gemini_vision(self, prompt, image_b64, mime="image/jpeg") -> str:
        body = {"contents": [{"parts": [
            {"text": prompt},
            {"inlineData": {"mimeType": mime, "data": image_b64}}]}]}
        return await self._gemini_call(body, "vision")

    async def _openai_vision(self, prompt, image_b64) -> str:
        model = self.text_model or "gpt-4o-mini"
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post("https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": [{"role": "user",
                    "content": [{"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"}}]}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()

    # ── ફોટો એજન્ટ: ન્યુઝ પરથી અંગ્રેજી દ્રશ્ય-વર્ણન ─────────────
    async def image_scene(self, title: str) -> str:
        if not await self.available():
            return ""
        try:
            out = await self.generate(
                self.model_think,
                "You describe a photo scene for a news poster. In ONE short "
                "English sentence, describe a realistic, relevant news photo "
                "for this Gujarati headline. Describe only the scene/objects/"
                "place — NO text in the image, and do NOT name or depict any "
                "specific real person. Headline:\n\n" + title)
            return out.strip().strip('"')[:200]
        except Exception:
            return ""

    # ── સારાંશ ──────────────────────────────────────────────────
    async def summarize(self, text: str) -> str:
        text = text.strip()
        if not await self.available():
            parts = text.replace("।", ".").split(".")
            return ". ".join(p.strip() for p in parts[:2] if p.strip()) + "."
        try:
            return await self.generate(
                self.model_write,
                "નીચેના ગુજરાતી લખાણનો 2-3 વાક્યનો ટૂંકો સારાંશ આપો. "
                "ફક્ત સારાંશ:\n\n" + text)
        except Exception:
            return text[:200]

    # ── શુદ્ધિ: ચકાસણી ──────────────────────────────────────────
    async def proofread(self, title: str, body: str) -> dict:
        issues = []
        if body and "  " in body:
            body = " ".join(body.split())
        return {"title": title.strip(), "body": body.strip(), "issues": issues}
