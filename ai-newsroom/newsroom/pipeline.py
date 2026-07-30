"""મુખ્ય પ્રવાહ — CEO કામ વહેંચે: સ્કાઉટ → લેખક → શુદ્ધિ → ડિઝાઈનર → અપ્રુવલ."""
import asyncio
from datetime import datetime, date

import httpx

from pathlib import Path

from . import db, scout, poster, whatsapp, imagegen, branding
from .bus import BUS, run_agent
from .config import load_config
from .llm import LLM

_running = False

BREAKING_WORDS = ("બ્રેકિંગ", "અકસ્માત", "મૃત્યુ", "આગ ", "ભૂકંપ", "હુમલો",
                  "હુમલા", "તાત્કાલિક", "દુર્ઘટના", "ધડાકો", "ચેતવણી")
BIRTHDAY_WORDS = ("જન્મદિવસ", "વર્ષગાંઠ", "શુભેચ્છા", "અભિનંદન")


def detect_category(title: str, body: str = "") -> str:
    text = f"{title} {body}"
    if any(w in text for w in BIRTHDAY_WORDS):
        return "birthday"
    if any(w in text for w in BREAKING_WORDS):
        return "breaking"
    return "general"


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
                  ai_limit: int | None = None):
    """આખા દિવસનો રન. press_note આપો તો ફક્ત એ એક ન્યુઝ બને.
    news_count = આજે કેટલા ન્યુઝ (ખાલી તો સેટિંગ મુજબ).
    ai_limit = આજે વધુમાં વધુ કેટલી AI તસવીર (ખર્ચ કંટ્રોલ; 0 = એક પણ નહીં)."""
    global _running
    if _running:
        return {"error": "કામ પહેલેથી ચાલુ છે"}
    _running = True
    cfg = load_config()
    llm = LLM(cfg)
    job_id = "job_" + datetime.now().strftime("%Y%m%d_%H%M")
    today = date.today().isoformat()
    t_start = datetime.now()

    try:
        await BUS.emit("ceo", "", "started", job_id=job_id, status="thinking",
                       message="દિવસ શરૂ — કામ વહેંચી રહ્યો છું...", log_db=True)

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
                found = await scout.fetch_news(cfg["rss_feeds"])
                await progress(f"{len(found)} ન્યુઝ મળ્યા",
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
        await BUS.emit("ceo", "", "progress", job_id=job_id, status="working",
                       message=f"લેખકને {len(selected)} ન્યુઝ સોંપ્યા")

        # ── 3. દરેક ન્યુઝ: લેખક → શુદ્ધિ → ડિઝાઈનર ─────────────
        done = 0
        ai_used = 0
        for idx, item in enumerate(selected, start=1):
            async def editor_fn(progress, item=item, idx=idx):
                await progress(f"ન્યુઝ #{idx} લખાઈ રહ્યો છે...",
                               pct=int(idx * 100 / len(selected)),
                               detail={"current": idx, "total": len(selected)})
                if item.get("press_note"):
                    return await llm.proofread(item["title"],
                                               item["press_note"]) | {"demo": False}
                return await llm.write_news(item)
            written = await run_agent("editor", "ceo", editor_fn,
                                      job_id=job_id, message="ન્યુઝ લખો")

            async def proof_fn(progress, written=written, idx=idx):
                await progress(f"ન્યુઝ #{idx} તપાસાઈ રહ્યો છે...")
                return await llm.proofread(written["title"], written["body"])
            clean = await run_agent("proofreader", "editor", proof_fn,
                                    job_id=job_id, message="તપાસો")

            category = detect_category(clean["title"], clean["body"])
            body = dedupe_body(clean["title"], clean["body"])
            photos = list(item.get("photos", []))
            image_ai = False

            # 📷 ફોટો એજન્ટ — સાચો ફોટો ન હોય તો AI તસવીર બનાવે
            # (જન્મદિવસમાં નહીં — વ્યક્તિનો AI ફોટો ન બનાવાય)
            # ai_limit થી ખર્ચ કંટ્રોલ: આજની મર્યાદા પૂરી થાય પછી નહીં
            if (not photos and category != "birthday"
                    and imagegen.is_configured(cfg)
                    and (ai_limit is None or ai_used < ai_limit)):
                async def photo_fn(progress, clean=clean, idx=idx):
                    await progress(
                        f"ન્યુઝ #{idx} માટે AI તસવીર બની રહી છે... (~30 સે)")
                    return await imagegen.generate(cfg, clean["title"])
                try:
                    p = await run_agent("photo", "ceo", photo_fn,
                                        job_id=job_id, message="AI તસવીર")
                    if p:
                        photos, image_ai = [p], True
                        ai_used += 1
                except Exception:
                    pass  # તસવીર ન બને તો પોસ્ટર ફોટા વગર બને — અટકવું નહીં

            news_id = db.execute(
                """INSERT INTO news(job_id, title, body, category, source_title,
                   source_url, status, photo) VALUES(?,?,?,?,?,?,?,?)""",
                (job_id, clean["title"], body, category,
                 item.get("source", "") or item.get("title", ""),
                 item.get("url", ""), "proofread", "|".join(photos)))
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
                        "contact": cfg.get("contact_number", ""),
                        "website": cfg.get("website_url", ""),
                        "theme_navy": cfg.get("theme_navy", ""),
                        "theme_accent": cfg.get("theme_accent", ""),
                        "theme_red": cfg.get("theme_red", ""),
                        "logo": logo_uri, "qr": qr,
                        "images": images,
                        "image": images[0] if images else "",
                        "image_ai": image_ai,
                        "date": datetime.now().strftime("%d/%m/%Y")}
                # બધા ન્યુઝ એક જ (રેફરન્સ) ડિઝાઈનમાં — ફક્ત જન્મદિવસ અલગ
                template = "birthday" if category == "birthday" else "general"
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

        await BUS.emit("ceo", "", "completed", job_id=job_id, status="done",
                       message=f"દિવસ પૂરો — {done} ન્યુઝ અપ્રુવલ માટે તૈયાર ✅",
                       log_db=True)
        return {"ok": True, "job_id": job_id, "news_ready": done}
    except Exception as e:
        db.bump_stat(today, "errors")
        await BUS.emit("ceo", "", "failed", job_id=job_id, status="error",
                       message=str(e)[:300], error=str(e)[:1000], log_db=True)
        raise
    finally:
        _running = False


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
            msg = (f"✅ પબ્લિશ થઈ ગયું!\n\n📰 {news['title']}\n\n"
                   f"{news['body'][:200]}\n\n— {cfg['channel_name']}")
            results["whatsapp"] = await whatsapp.send(cfg, msg, media_url)
            db.bump_stat(today, "published_wa")
        return results

    return await run_agent("publisher", "ceo", publish_fn,
                           job_id=news.get("job_id") or "",
                           message="પબ્લિશ કરો")
