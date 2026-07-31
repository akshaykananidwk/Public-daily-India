"""મુખ્ય પ્રવાહ — CEO કામ વહેંચે: સ્કાઉટ → લેખક → શુદ્ધિ → ડિઝાઈનર → અપ્રુવલ."""
import asyncio
from datetime import datetime, date

import httpx

from pathlib import Path

from . import (db, scout, poster, whatsapp, imagegen, branding, telegram,
               instagram, accountant)
from .bus import BUS, run_agent
from .config import load_config
from .llm import LLM

_running = False

BREAKING_WORDS = ("બ્રેકિંગ", "અકસ્માત", "મૃત્યુ", "આગ ", "ભૂકંપ", "હુમલો",
                  "હુમલા", "તાત્કાલિક", "દુર્ઘટના", "ધડાકો", "ચેતવણી")
BIRTHDAY_WORDS = ("જન્મદિવસ", "વર્ષગાંઠ", "શુભેચ્છા", "અભિનંદન")
TRIBUTE_WORDS = ("શ્રદ્ધાંજલિ", "નિધન", "અવસાન", "દુઃખદ અવસાન", "સ્વર્ગવાસ")

# ઓટો-ટેગ — ન્યુઝ કઈ કેટેગરીનો (લેબલ માટે)
TAG_WORDS = {
    "રાજકારણ": ("સંસદ", "લોકસભા", "રાજ્યસભા", "ચૂંટણી", "સરકાર", "મંત્રી",
                "ભાજપ", "કોંગ્રેસ", "વિધાનસભા", "બિલ"),
    "ગુના": ("પોલીસ", "ધરપકડ", "ચોરી", "લૂંટ", "હત્યા", "ગુનો", "છેતરપિંડી"),
    "રમત": ("ક્રિકેટ", "મેચ", "ટુર્નામેન્ટ", "ખેલાડી", "ગોલ", "રમત"),
    "ધર્મ": ("મંદિર", "દર્શન", "આરતી", "ધાર્મિક", "પૂજા", "યાત્રા", "કથા"),
    "હવામાન": ("વરસાદ", "હવામાન", "પૂર", "વાવાઝોડું", "ગરમી", "ઠંડી"),
    "શિક્ષણ": ("શાળા", "કોલેજ", "પરીક્ષા", "વિદ્યાર્થી", "શિક્ષણ", "પરિણામ"),
    "આરોગ્ય": ("હોસ્પિટલ", "આરોગ્ય", "દવા", "રસી", "કેમ્પ", "રોગ"),
    "ખેતી": ("ખેડૂત", "પાક", "ખેતી", "વાવેતર", "ટેકાના ભાવ"),
    "વિકાસ": ("લોકાર્પણ", "ઉદ્ઘાટન", "યોજના", "રસ્તો", "પુલ", "વિકાસ"),
}


def detect_category(title: str, body: str = "") -> str:
    text = f"{title} {body}"
    if any(w in text for w in BIRTHDAY_WORDS):
        return "birthday"
    if any(w in text for w in TRIBUTE_WORDS):
        return "tribute"
    if any(w in text for w in BREAKING_WORDS):
        return "breaking"
    return "general"


def auto_tag(title: str, body: str = "") -> str:
    """ન્યુઝનો વિષય-ટેગ (રાજકારણ/ગુના/રમત...)."""
    text = f"{title} {body}"
    for tag, words in TAG_WORDS.items():
        if any(w in text for w in words):
            return tag
    return "સામાન્ય"


def dedupe_body(title: str, body: str) -> str:
    """હેડલાઈન બોડીમાં ફરી ન આવે (ડબલ લખાણ ફિક્સ)."""
    t = title.strip().rstrip(".।!").strip()
    b = (body or "").strip()
    if t and b.startswith(t):
        b = b[len(t):].lstrip(" .।,!-–\n")
    return b.strip()


def is_running() -> bool:
    return _running


async def run_day(press_note: str | None = None,
                  photo_path: str | None = None,
                  news_count: int | None = None,
                  ai_limit: int | None = None,
                  overrides: dict | None = None,
                  reporter: str = ""):
    """આખા દિવસનો રન. press_note આપો તો ફક્ત એ એક ન્યુઝ બને.
    news_count = આજે કેટલા ન્યુઝ (ખાલી તો સેટિંગ મુજબ).
    ai_limit = આજે વધુમાં વધુ કેટલી AI તસવીર (ખર્ચ કંટ્રોલ; 0 = એક પણ નહીં)."""
    global _running
    if _running:
        return {"error": "કામ પહેલેથી ચાલુ છે"}
    _running = True
    cfg = load_config()
    if overrides:                       # મલ્ટી-જિલ્લા — સ્થળ/સંપર્ક બદલો
        cfg = dict(cfg)
        for k in ("location", "contact_number"):
            if overrides.get(k):
                cfg[k] = overrides[k]
    llm = LLM(cfg)
    job_id = "job_" + datetime.now().strftime("%Y%m%d_%H%M")
    today = date.today().isoformat()
    t_start = datetime.now()

    try:
        await BUS.emit("ceo", "", "started", job_id=job_id, status="thinking",
                       message="દિવસ શરૂ — કામ વહેંચી રહ્યો છું...", log_db=True)
        await BUS.job_progress(3, "દિવસ શરૂ થયો", "શરૂ")

        # ── 1. સ્કાઉટ / પ્રેસ નોટ ──────────────────────────────
        if press_note:
            # હેડલાઈન = પહેલું વાક્ય (।, ., ! કે નવી લાઈન સુધી)
            first_line = press_note.strip().split("\n")[0]
            for sep in ("।", "؟", "!", "."):
                if sep in first_line:
                    first_line = first_line.split(sep)[0]
                    break
            photos = photo_path if isinstance(photo_path, list) \
                else ([photo_path] if photo_path else [])
            items = [{"title": first_line.strip()[:120],
                      "url": "", "press_note": press_note,
                      "photos": photos}]
        else:
            async def scout_fn(progress):
                await progress("RSS ફીડ વાંચી રહ્યો છું...")
                # છેલ્લા 30 દિવસના ન્યુઝ — ડુપ્લિકેટ ટાળવા
                recent = db.query(
                    "SELECT title FROM news WHERE created_at > date('now','-30 day')")
                seen = {scout._norm(r["title"]) for r in recent}
                block = [w for w in (cfg.get("block_words", "") or "")
                         .replace("\n", ",").split(",") if w.strip()]
                found = await scout.fetch_news(
                    cfg["rss_feeds"], cfg.get("keyword_filter", ""), seen,
                    block)
                await progress(f"{len(found)} નવા ન્યુઝ મળ્યા",
                               detail={"found": len(found)})
                return found
            items = await run_agent("scout", "ceo", scout_fn, job_id=job_id,
                                    message="ન્યુઝ શોધો")
            db.bump_stat(today, "news_collected", len(items))

        # ── 2. CEO પસંદગી ──────────────────────────────────────
        count = 1 if press_note else int(
            news_count or cfg["daily_news_count"])
        await BUS.emit("ceo", "", "progress", job_id=job_id, status="thinking",
                       message=f"{len(items)} માંથી {count} પસંદ કરું છું...")
        selected = await llm.score_items(items, count)
        db.bump_stat(today, "news_selected", len(selected))
        await BUS.job_progress(15, f"{len(selected)} ન્યુઝ પસંદ થયા", "પસંદગી")
        await BUS.emit("ceo", "", "progress", job_id=job_id, status="working",
                       message=f"લેખકને {len(selected)} ન્યુઝ સોંપ્યા")

        # ── 3. દરેક ન્યુઝ: લેખક → શુદ્ધિ → ડિઝાઈનર ─────────────
        done = 0
        ai_used = 0
        for idx, item in enumerate(selected, start=1):
            await BUS.job_progress(
                15 + int((idx - 1) * 80 / len(selected)),
                f"ન્યુઝ {idx}/{len(selected)} — રિરાઈટ થઈ રહ્યો છે...")

            async def editor_fn(progress, item=item, idx=idx):
                await progress(f"ન્યુઝ #{idx} મૌલિક રીતે લખાઈ રહ્યો છે...",
                               pct=int(idx * 100 / len(selected)),
                               detail={"current": idx, "total": len(selected)})
                # RSS હોય કે પ્રેસ નોટ — બંને રિરાઈટ થાય (કોપીરાઈટ ટાળવા)
                return await llm.write_news(item)
            written = await run_agent("editor", "ceo", editor_fn,
                                      job_id=job_id, message="ન્યુઝ લખો")
            if not written.get("demo"):     # ટેક્સ્ટ AI ખર્ચ નોંધો
                accountant.record("text", cfg.get("text_provider", "ollama"),
                                  written.get("title", "")[:40])

            async def proof_fn(progress, written=written, idx=idx):
                await progress(f"ન્યુઝ #{idx} તપાસાઈ રહ્યો છે...")
                return await llm.proofread(written["title"], written["body"])
            clean = await run_agent("proofreader", "editor", proof_fn,
                                    job_id=job_id, message="તપાસો")

            category = detect_category(clean["title"], clean["body"])
            body = dedupe_body(clean["title"], clean["body"])
            photos = list(item.get("photos", []))
            image_ai = False
            # ડેમો મોડ (લખાણ AI નથી) → ખરો ન્યુઝ નથી, ફોટાના પૈસા ન બગડે
            has_real_text = bool(body) and not written.get("demo")

            # 📷 ફોટો એજન્ટ — સાચો ફોટો ન હોય તો AI તસવીર બનાવે
            # (જન્મદિવસમાં નહીં; ડેમો/ખાલી લખાણમાં નહીં — પૈસા બચે)
            # ai_limit થી ખર્ચ કંટ્રોલ: આજની મર્યાદા પૂરી થાય પછી નહીં
            if (not photos and category != "birthday" and has_real_text
                    and imagegen.is_configured(cfg)
                    and (ai_limit is None or ai_used < ai_limit)):
                async def photo_fn(progress, clean=clean, idx=idx):
                    await progress(
                        f"ન્યુઝ #{idx} માટે AI તસવીર બની રહી છે... (~30 સે)")
                    # ન્યુઝના વિષય પ્રમાણે દ્રશ્ય (LLM હોય તો સચોટ)
                    scene = await llm.image_scene(clean["title"])
                    return await imagegen.generate(
                        cfg, clean["title"], scene=scene)
                try:
                    p = await run_agent("photo", "ceo", photo_fn,
                                        job_id=job_id, message="AI તસવીર")
                    if p:
                        photos, image_ai = [p], True
                        ai_used += 1
                        db.bump_stat(today, "ai_images")
                        accountant.record(
                            "image", cfg.get("image_ai_provider", ""),
                            clean["title"][:40])
                except Exception:
                    pass  # તસવીર ન બને તો પોસ્ટર ફોટા વગર બને — અટકવું નહીં

            tag = auto_tag(clean["title"], body)
            news_id = db.execute(
                """INSERT INTO news(job_id, title, body, category, source_title,
                   source_url, status, photo, tag, reporter)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (job_id, clean["title"], body, category,
                 item.get("source", "") or item.get("title", ""),
                 item.get("url", ""), "proofread", "|".join(photos), tag,
                 reporter))
            db.bump_stat(today, "news_written")

            async def design_fn(progress, news_id=news_id, clean=clean,
                                idx=idx, category=category, photos=photos,
                                image_ai=image_ai, body=body):
                images = [Path(p).as_uri() for p in photos if p]
                logo = cfg.get("logo_path")
                logo_uri = (Path(logo).as_uri()
                            if logo and Path(logo).exists() else "")
                qr = ""
                if cfg.get("qr_enabled"):
                    qr_data = (cfg.get("qr_data")
                               or f"https://{cfg.get('website_url','')}")
                    qr = branding.make_qr_datauri(qr_data)
                news = {"id": news_id, "title": clean["title"],
                        "body": body, "category": category,
                        "channel": cfg["channel_name"],
                        "location": cfg["location"],
                        "tagline": cfg.get("tagline", ""),
                        "editor": cfg.get("editor_name", ""),
                        "reporter": reporter,
                        "contact": cfg.get("contact_number", ""),
                        "website": cfg.get("website_url", ""),
                        "theme_navy": cfg.get("theme_navy", ""),
                        "theme_accent": cfg.get("theme_accent", ""),
                        "theme_red": cfg.get("theme_red", ""),
                        "logo": logo_uri, "qr": qr,
                        "watermark": cfg.get("watermark_enabled", True),
            "font": cfg.get("poster_font", "AnekGuj"),
                        "font": cfg.get("poster_font", "AnekGuj"),
                        "images": images,
                        "image": images[0] if images else "",
                        "image_ai": image_ai,
                        "date": datetime.now().strftime("%d/%m/%Y")}
                # મુખ્ય રેફરન્સ ડિઝાઈન — જન્મદિવસ અને શ્રદ્ધાંજલિ અલગ
                template = ("birthday" if category == "birthday"
                           else "tribute" if category == "tribute"
                           else "general")
                results = []
                for size in cfg["poster_sizes"]:
                    await progress(
                        f"ન્યુઝ #{idx} — {size['name']} પોસ્ટર બની રહ્યું છે...")
                    results.append(await poster.render_poster(
                        template, news, size))
                    db.bump_stat(today, "posters_created")
                return results
            await run_agent("designer", "proofreader", design_fn,
                            job_id=job_id, message="પોસ્ટર બનાવો")

            db.execute("UPDATE news SET status='pending_approval', "
                       "updated_at=CURRENT_TIMESTAMP WHERE id=?", (news_id,))
            done += 1
            await BUS.emit("publisher", "designer", "progress", job_id=job_id,
                           status="waiting", news_id=news_id,
                           message=f"ન્યુઝ #{idx} અપ્રુવલની રાહમાં 🟠")

        # ── 4. એનાલિસ્ટ ────────────────────────────────────────
        async def analyst_fn(progress):
            await progress("આજના આંકડા ગણી રહ્યો છું...")
            mins = int((datetime.now() - t_start).total_seconds() / 60)
            db.bump_stat(today, "total_runtime_min", mins)
            return db.query("SELECT * FROM daily_stats WHERE date=?", (today,))
        await run_agent("analyst", "ceo", analyst_fn, job_id=job_id,
                        message="આંકડા")

        await BUS.job_progress(100, f"{done} ન્યુઝ તૈયાર — અપ્રુવલ બાકી", "પૂર્ણ")
        await BUS.emit("ceo", "", "completed", job_id=job_id, status="done",
                       message=f"દિવસ પૂરો — {done} ન્યુઝ અપ્રુવલ માટે તૈયાર ✅",
                       log_db=True)
        return {"ok": True, "job_id": job_id, "news_ready": done}
    except Exception as e:
        db.bump_stat(today, "errors")
        await BUS.emit("ceo", "", "failed", job_id=job_id, status="error",
                       message=str(e)[:300], error=str(e)[:1000], log_db=True)
        # ભૂલ-એલર્ટ WhatsApp પર
        if cfg.get("error_alert_enabled") and whatsapp.is_configured(cfg):
            try:
                await whatsapp.send(
                    cfg, f"⚠️ AI Newsroom ભૂલ:\n{str(e)[:300]}")
            except Exception:
                pass
        raise
    finally:
        _running = False


async def run_from_pdf_file(pdf_path: str, reporter: str = ""):
    """PDF ફાઈલ → Vision AI થી દરેક પાનું જોઈ સ્વચ્છ ન્યુઝ કાઢી બધા બનાવો."""
    from . import pdfnews
    cfg = load_config()
    llm = LLM(cfg)
    await BUS.job_progress(5, "PDF ના પાનાં જોઈ રહ્યો છું (Vision AI)...", "PDF")

    async def page_prog(i, total):
        await BUS.job_progress(5 + int(i * 10 / max(total, 1)),
                               f"પાનું {i}/{total} વાંચી રહ્યો છું...", "PDF")
    try:
        items, err = await pdfnews.extract_news(pdf_path, llm, page_prog)
    except Exception as e:
        await BUS.job_progress(100, f"PDF ભૂલ: {e}", "ભૂલ")
        return
    if not items:
        msg = ("PDF ભૂલ — " + err) if err else \
            ("PDF માંથી ન્યુઝ ન મળ્યા — Gemini key/મોડેલ ચેક કરો "
             "(સેટિંગ → ન્યુઝ લેખન AI)")
        await BUS.job_progress(100, msg, "ભૂલ")
        return
    await BUS.job_progress(15, f"{len(items)} ન્યુઝ મળ્યા — બનાવી રહ્યો છું", "PDF")
    for i, it in enumerate(items, 1):
        # Vision એ પહેલેથી સ્વચ્છ ન્યુઝ આપ્યો — એ જ પ્રેસ નોટ તરીકે
        note = it["title"] + "\n" + it.get("body", "")
        await run_day(press_note=note, reporter=reporter)
        await BUS.job_progress(
            15 + int(i * 80 / len(items)),
            f"PDF ન્યુઝ {i}/{len(items)} બન્યો", "PDF")
    await BUS.job_progress(100, f"PDF માંથી {len(items)} ન્યુઝ તૈયાર", "પૂર્ણ")


async def render_news_posters(news_id: int) -> list[dict]:
    """એક ન્યુઝના પોસ્ટર (ફરી) બનાવે — એડિટ/ફરી-બનાવો માટે."""
    cfg = load_config()
    rows = db.query("SELECT * FROM news WHERE id=?", (news_id,))
    if not rows:
        return []
    n = rows[0]
    # જૂના પોસ્ટર રેકોર્ડ કાઢો
    db.execute("DELETE FROM poster_log WHERE news_id=?", (news_id,))
    photos = [p for p in (n.get("photo") or "").split("|") if p]
    images = [Path(p).as_uri() for p in photos if Path(p).exists()]
    logo = cfg.get("logo_path")
    logo_uri = Path(logo).as_uri() if logo and Path(logo).exists() else ""
    qr = ""
    if cfg.get("qr_enabled"):
        qr = branding.make_qr_datauri(
            cfg.get("qr_data") or f"https://{cfg.get('website_url','')}")
    news = {"id": news_id, "title": n["title"], "body": n["body"],
            "category": n["category"], "channel": cfg["channel_name"],
            "location": cfg["location"], "tagline": cfg.get("tagline", ""),
            "editor": cfg.get("editor_name", ""),
            "reporter": n.get("reporter", ""),
            "contact": cfg.get("contact_number", ""),
            "website": cfg.get("website_url", ""),
            "theme_navy": cfg.get("theme_navy", ""),
            "theme_accent": cfg.get("theme_accent", ""),
            "theme_red": cfg.get("theme_red", ""),
            "logo": logo_uri, "qr": qr, "images": images,
            "watermark": cfg.get("watermark_enabled", True),
            "image": images[0] if images else "",
            "date": datetime.now().strftime("%d/%m/%Y")}
    template = ("birthday" if n["category"] == "birthday"
                else "tribute" if n["category"] == "tribute" else "general")
    results = []
    for size in cfg["poster_sizes"]:
        results.append(await poster.render_poster(template, news, size))
    return results


# ── પબ્લિશર ─────────────────────────────────────────────────────
async def publish_news(news_id: int) -> dict:
    cfg = load_config()
    today = date.today().isoformat()
    rows = db.query("SELECT * FROM news WHERE id=?", (news_id,))
    if not rows:
        return {"error": "ન્યુઝ મળ્યો નહીં"}
    news = rows[0]
    posters = db.query(
        "SELECT * FROM poster_log WHERE news_id=? ORDER BY id", (news_id,))

    async def publish_fn(progress):
        results = {}
        token = cfg.get("facebook_page_token")
        page_id = cfg.get("facebook_page_id")
        caption = f"{news['title']}\n\n{news['body']}\n\n#PublicDayIndia #Dwarka"
        if token and page_id and posters:
            await progress("Facebook પર પોસ્ટ થઈ રહ્યું છે...")
            try:
                async with httpx.AsyncClient(timeout=120) as c:
                    with open(posters[0]["file_path"], "rb") as f:
                        r = await c.post(
                            f"https://graph.facebook.com/v19.0/{page_id}/photos",
                            data={"caption": caption, "access_token": token},
                            files={"source": f})
                    r.raise_for_status()
                results["facebook"] = "ok"
                db.bump_stat(today, "published_fb")
            except Exception as e:
                results["facebook"] = f"ભૂલ: {e}"
        else:
            await progress("ટોકન સેટ નથી — સિમ્યુલેશન મોડમાં પબ્લિશ")
            results["facebook"] = "simulated"
            db.bump_stat(today, "published_fb")
        db.execute("UPDATE news SET status='published', "
                   "updated_at=CURRENT_TIMESTAMP WHERE id=?", (news_id,))

        # 📱 WhatsApp નોટિફિકેશન — પબ્લિશ થાય એટલે તમારા નંબર પર (પોસ્ટર સાથે)
        if whatsapp.is_configured(cfg):
            await progress("WhatsApp પર પોસ્ટર મોકલી રહ્યો છું...")
            media_url = ""
            base = (cfg.get("public_base_url") or "").rstrip("/")
            if posters:
                from pathlib import Path
                from .paths import STORAGE_DIR
                if base:
                    # તમારી પોતાની hosting હોય તો એ વાપરો
                    try:
                        rel = Path(posters[0]["file_path"]).relative_to(
                            STORAGE_DIR)
                        media_url = f"{base}/storage/{rel.as_posix()}"
                    except ValueError:
                        pass
                if not media_url:
                    # નહીંતર પોસ્ટર ફ્રી હોસ્ટ પર ચડાવી લિંક બનાવો
                    media_url = await whatsapp.upload_public(
                        posters[0]["file_path"])
            msg = branding.build_caption(news["title"], news["body"], cfg)
            results["whatsapp"] = await whatsapp.send_broadcast(
                cfg, msg, media_url)
            db.bump_stat(today, "published_wa")

        # 📢 Telegram ચેનલ પર પોસ્ટર (મફત, public URL વગર)
        if telegram.is_configured(cfg) and posters:
            await progress("Telegram ચેનલ પર પોસ્ટ કરી રહ્યો છું...")
            cap = branding.build_caption(news["title"], news["body"], cfg)
            results["telegram"] = await telegram.send_photo(
                cfg, posters[0]["file_path"], cap)

        # 📸 Instagram પર પોસ્ટ (પબ્લિક image_url જોઈએ)
        if instagram.is_configured(cfg) and posters:
            await progress("Instagram પર પોસ્ટ કરી રહ્યો છું...")
            ig_url = media_url or await whatsapp.upload_public(
                posters[0]["file_path"])
            cap = branding.build_caption(news["title"], news["body"], cfg)
            results["instagram"] = await instagram.publish(cfg, ig_url, cap)
            if results["instagram"].get("ok"):
                db.bump_stat(today, "published_ig")
        return results

    return await run_agent("publisher", "ceo", publish_fn,
                           job_id=news.get("job_id") or "",
                           message="પબ્લિશ કરો")
