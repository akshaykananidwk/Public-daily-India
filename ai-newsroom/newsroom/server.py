"""FastAPI સર્વર — UI, API, WebSocket બધું અહીંથી ચાલે."""
import asyncio
from datetime import date
from pathlib import Path

from fastapi import (FastAPI, WebSocket, WebSocketDisconnect, UploadFile,
                     Form, Body, File, Request, Depends, HTTPException)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import db, pipeline, updater, whatsapp, auth
from .bus import BUS
from .config import load_config, save_config
from .llm import LLM
from .paths import WEB_DIR, STORAGE_DIR, PHOTOS_DIR, FONTS_DIR
from .scheduler import scheduler_loop
from .updater import current_version

app = FastAPI(title="AI Newsroom — Public Day India")


@app.on_event("startup")
async def startup():
    db.run_migrations()
    asyncio.create_task(scheduler_loop())


@app.on_event("shutdown")
async def shutdown():
    from . import poster
    await poster.shutdown()


# ── ઓથ ─────────────────────────────────────────────────────────
def require_admin(request: Request):
    u = auth.current_user(request.cookies.get("session"))
    if u.get("role") != "admin":
        raise HTTPException(status_code=401, detail="એડમિન લોગિન જોઈએ")
    return u


@app.post("/api/login")
async def login(payload: dict = Body(...)):
    role = auth.verify(payload.get("username", ""), payload.get("password", ""))
    if not role:
        return JSONResponse({"error": "ખોટું નામ કે પાસવર્ડ"}, status_code=401)
    token = auth.make_token(payload["username"], role)
    resp = JSONResponse({"ok": True, "role": role})
    resp.set_cookie("session", token, httponly=True, max_age=86400 * 7)
    return resp


@app.post("/api/logout")
async def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("session")
    return resp


@app.get("/api/me")
async def me(request: Request):
    u = auth.current_user(request.cookies.get("session"))
    return {"auth_enabled": auth.enabled(),
            "role": u.get("role", ""), "username": u.get("username", "")}


# ── UI ──────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(WEB_DIR / "favicon.png")


app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")
app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")
app.mount("/fonts", StaticFiles(directory=FONTS_DIR), name="fonts")


# ── WebSocket (લાઈવ ડેશબોર્ડ) ──────────────────────────────────
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    await BUS.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        BUS.disconnect(ws)
    except Exception:
        BUS.disconnect(ws)


# ── સ્ટેટસ ──────────────────────────────────────────────────────
@app.get("/api/status")
async def status():
    cfg = load_config()
    today = date.today().isoformat()
    stats = db.query("SELECT * FROM daily_stats WHERE date=?", (today,))
    pending = db.query(
        "SELECT COUNT(*) n FROM news WHERE status='pending_approval'")
    return {
        "channel": cfg["channel_name"],
        "ollama": await LLM(cfg).available(),
        "running": pipeline.is_running(),
        "today": stats[0] if stats else {},
        "pending_approval": pending[0]["n"],
        "version": current_version().get("sha", "")[:7] or "dev",
    }


# ── રન ──────────────────────────────────────────────────────────
@app.post("/api/run-day")
async def run_day(payload: dict = Body(default={})):
    if pipeline.is_running():
        return JSONResponse({"error": "કામ પહેલેથી ચાલુ છે"}, status_code=409)
    news_count = payload.get("count")
    ai_limit = payload.get("ai_images")
    news_count = int(news_count) if news_count is not None else None
    ai_limit = int(ai_limit) if ai_limit is not None else None
    asyncio.create_task(pipeline.run_day(news_count=news_count,
                                         ai_limit=ai_limit))
    msg = "દિવસ શરૂ થયો 🚀"
    if news_count:
        msg += f" — {news_count} ન્યુઝ"
    if ai_limit is not None:
        msg += f", વધુમાં વધુ {ai_limit} AI તસવીર"
    return {"ok": True, "message": msg}


@app.post("/api/press-note")
async def press_note(text: str = Form(""), district: str = Form(""),
                     reporter: str = Form(""),
                     photos: list[UploadFile] = File(default=[])):
    from datetime import datetime
    note = (text or "").strip()
    overrides = {}
    if district:
        for d in load_config().get("districts", []):
            if d.get("name") == district:
                overrides = {"location": d.get("location"),
                             "contact_number": d.get("contact")}
                break
    photo_paths: list[str] = []
    for i, photo in enumerate(photos[:3]):     # વધુમાં વધુ 3 ફોટા
        if not photo.filename:
            continue
        safe = (f"{datetime.now():%Y%m%d_%H%M%S}_{i}_"
                f"{Path(photo.filename).name}")
        dest = PHOTOS_DIR / safe
        dest.write_bytes(await photo.read())
        photo_paths.append(str(dest))
    if not note and photo_paths:
        try:  # OCR — pytesseract હોય તો
            import pytesseract
            from PIL import Image
            note = pytesseract.image_to_string(
                Image.open(photo_paths[0]), lang="guj+eng")
        except Exception:
            return JSONResponse(
                {"error": "OCR ઉપલબ્ધ નથી — લખાણ પણ સાથે મોકલો "
                          "(pip install pytesseract pillow + Tesseract guj)"},
                status_code=400)
    if not note:
        return JSONResponse({"error": "પ્રેસ નોટનું લખાણ ખાલી છે"},
                            status_code=400)
    if pipeline.is_running():
        return JSONResponse({"error": "કામ પહેલેથી ચાલુ છે"}, status_code=409)
    asyncio.create_task(pipeline.run_day(press_note=note,
                                         photo_path=photo_paths,
                                         overrides=overrides,
                                         reporter=reporter))
    return {"ok": True, "message": "પ્રેસ નોટ પર કામ શરૂ 🚀"
            + (f" ({len(photo_paths)} ફોટા સાથે 📷)" if photo_paths else "")
            + (f" — {district}" if district else "")}


@app.get("/api/festivals")
async def festivals():
    from . import festivals as fest
    return fest.upcoming(3)


@app.get("/api/trending")
async def trending():
    """છેલ્લા 7 દિવસના ન્યુઝ ટાઈટલમાં સૌથી વધુ વપરાયેલા શબ્દો."""
    import re
    from collections import Counter
    stop = {"અને", "માટે", "પર", "થી", "ના", "ની", "નું", "છે", "કે",
            "એક", "આ", "તથા", "સાથે", "બાદ", "થયું", "કર્યું", "થયો",
            "news", "the", "in", "of", "-"}
    rows = db.query(
        "SELECT title FROM news WHERE created_at > date('now','-7 day')")
    words = Counter()
    for r in rows:
        for w in re.split(r"[\s,.:;–\-|/]+", r["title"]):
            w = w.strip()
            if len(w) >= 3 and w.lower() not in stop:
                words[w] += 1
    return [{"word": w, "count": c} for w, c in words.most_common(12)]


@app.post("/api/summarize")
async def summarize(payload: dict = Body(...)):
    llm = LLM(load_config())
    text = payload.get("text", "")
    if not text and payload.get("news_id"):
        rows = db.query("SELECT body FROM news WHERE id=?",
                        (payload["news_id"],))
        text = rows[0]["body"] if rows else ""
    return {"summary": await llm.summarize(text)}


# ── ન્યુઝ + અપ્રુવલ + સર્ચ ────────────────────────────────────
@app.get("/api/news")
async def list_news(status: str = "", limit: int = 50, q: str = "",
                    date_from: str = "", date_to: str = ""):
    where, params = [], []
    if status:
        where.append("status=?"); params.append(status)
    if q:
        where.append("(title LIKE ? OR body LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    if date_from:
        where.append("date(created_at) >= ?"); params.append(date_from)
    if date_to:
        where.append("date(created_at) <= ?"); params.append(date_to)
    sql = "SELECT * FROM news"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ?"; params.append(limit)
    rows = db.query(sql, tuple(params))
    for r in rows:
        posters = db.query(
            "SELECT file_path, size FROM poster_log WHERE news_id=? ORDER BY id",
            (r["id"],))
        for p in posters:
            rel = Path(p["file_path"])
            try:
                p["url"] = "/storage/" + str(rel.relative_to(STORAGE_DIR))
            except ValueError:
                p["url"] = ""
        r["posters"] = posters
    return rows


@app.post("/api/news/{news_id}/approve")
async def approve(news_id: int, _=Depends(require_admin)):
    db.execute("UPDATE news SET status='approved', "
               "updated_at=CURRENT_TIMESTAMP WHERE id=?", (news_id,))
    db.bump_stat(date.today().isoformat(), "approved")
    result = await pipeline.publish_news(news_id)
    return {"ok": True, "publish": result}


@app.post("/api/news/{news_id}/schedule")
async def schedule_news(news_id: int, payload: dict = Body(...)):
    """ન્યુઝ ભવિષ્યના સમયે આપોઆપ પબ્લિશ કરવા શેડ્યૂલ કરો."""
    at = payload.get("at", "")          # 'YYYY-MM-DDTHH:MM'
    if not at:
        db.execute("UPDATE news SET scheduled_at=NULL WHERE id=?", (news_id,))
        return {"ok": True, "cleared": True}
    db.execute("UPDATE news SET status='approved', scheduled_at=? WHERE id=?",
               (at.replace("T", " "), news_id))
    return {"ok": True, "at": at}


@app.get("/api/scheduled")
async def scheduled_list():
    return db.query(
        "SELECT id, title, scheduled_at, status FROM news "
        "WHERE scheduled_at IS NOT NULL AND status!='published' "
        "ORDER BY scheduled_at")


@app.post("/api/news/{news_id}/reject")
async def reject(news_id: int):
    db.execute("UPDATE news SET status='rejected', "
               "updated_at=CURRENT_TIMESTAMP WHERE id=?", (news_id,))
    db.bump_stat(date.today().isoformat(), "rejected")
    return {"ok": True}


@app.post("/api/news/{news_id}/edit")
async def edit_news(news_id: int, payload: dict = Body(...)):
    """હેડલાઈન/લખાણ સુધારો અને પોસ્ટર ફરી બનાવો."""
    fields, params = [], []
    for k in ("title", "body"):
        if k in payload:
            fields.append(f"{k}=?"); params.append(payload[k])
    if fields:
        params.append(news_id)
        db.execute(f"UPDATE news SET {','.join(fields)}, "
                   "updated_at=CURRENT_TIMESTAMP WHERE id=?", tuple(params))
    posters = await pipeline.render_news_posters(news_id)
    return {"ok": True, "posters": len(posters)}


@app.post("/api/news/{news_id}/regenerate")
async def regenerate_news(news_id: int):
    """પોસ્ટર ફરી બનાવો (થીમ/લોગો બદલ્યા પછી)."""
    posters = await pipeline.render_news_posters(news_id)
    return {"ok": True, "posters": len(posters)}


@app.post("/api/news/{news_id}/video")
async def make_video(news_id: int, payload: dict = Body(default={})):
    """પોસ્ટરમાંથી ટૂંકો વિડિયો (Reels/Shorts) — વૈકલ્પિક વોઈસ-ઓવર."""
    from . import video
    rows = db.query("SELECT * FROM news WHERE id=?", (news_id,))
    if not rows:
        return JSONResponse({"error": "ન્યુઝ મળ્યો નહીં"}, status_code=404)
    n = rows[0]
    posters = db.query(
        "SELECT file_path FROM poster_log WHERE news_id=? ORDER BY id",
        (news_id,))
    if not posters:
        return JSONResponse({"error": "પહેલા પોસ્ટર બનાવો"}, status_code=400)
    voice = ""
    if payload.get("voice"):
        voice = f"{n['title']}. {n['body']}"
    r = await video.make_video(posters[0]["file_path"],
                               duration=payload.get("duration", 8),
                               voice_text=voice)
    if r.get("ok"):
        try:
            rel = Path(r["file"]).relative_to(STORAGE_DIR)
            r["url"] = "/storage/" + rel.as_posix()
        except ValueError:
            pass
    return r


# ── રિપોર્ટ ─────────────────────────────────────────────────────
@app.get("/api/reports")
async def reports(month: str = ""):
    month = month or date.today().strftime("%Y-%m")
    rows = db.query(
        "SELECT * FROM daily_stats WHERE date LIKE ? ORDER BY date DESC",
        (month + "%",))
    totals = {}
    for col in ("news_collected", "news_selected", "news_written",
                "posters_created", "approved", "rejected", "published_fb",
                "errors"):
        totals[col] = sum(r.get(col) or 0 for r in rows)
    agent_perf = db.query(
        """SELECT agent, COUNT(*) runs,
           SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) errors,
           AVG(duration_ms) avg_ms
           FROM activity_log WHERE created_at LIKE ? AND action='completed'
           GROUP BY agent""", (month + "%",))
    return {"month": month, "days": rows, "totals": totals,
            "agents": agent_perf}


@app.get("/api/log")
async def activity_log(limit: int = 100):
    return db.query(
        "SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,))


@app.get("/api/accountant")
async def accountant_view(month: str = ""):
    from . import accountant
    return accountant.summary(month or None)


@app.post("/api/press-pdf")
async def press_pdf(pdf: UploadFile = File(...), reporter: str = Form("")):
    """PDF પ્રેસ નોટ → Vision AI થી દરેક પાનું જોઈ ન્યુઝ કાઢી બધા બનાવો."""
    from datetime import datetime
    if pipeline.is_running():
        return JSONResponse({"error": "કામ પહેલેથી ચાલુ છે"}, status_code=409)
    try:
        import fitz  # noqa
    except Exception:
        return JSONResponse(
            {"error": "PDF માટે PyMuPDF જોઈએ — pip install PyMuPDF"},
            status_code=400)
    cfg = load_config()
    if LLM(cfg).provider not in ("gemini", "openai") or not cfg.get("text_api_key"):
        return JSONResponse(
            {"error": "ઈમેજવાળી PDF વાંચવા Gemini/OpenAI key જોઈએ — "
                      "સેટિંગ → ન્યુઝ લેખન AI માં Gemini સેટ કરો"},
            status_code=400)
    data = await pdf.read()
    tmp = PHOTOS_DIR.parent / f"pressnote_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    tmp.write_bytes(data)
    asyncio.create_task(pipeline.run_from_pdf_file(str(tmp), reporter))
    return {"ok": True,
            "message": "PDF ના પાનાં જોઈ ન્યુઝ કાઢી રહ્યો છું 🚀 (Vision AI)"}


@app.get("/api/reports/cost")
async def report_cost(month: str = ""):
    from . import reports
    cfg = load_config()
    month = month or date.today().strftime("%Y-%m")
    provider = cfg.get("image_ai_provider", "pollinations")
    return {"month": month, "provider": provider,
            "cost": reports.month_cost(month, provider)}


@app.get("/api/reports/excel")
async def report_excel(month: str = ""):
    from fastapi.responses import Response
    from . import reports
    month = month or date.today().strftime("%Y-%m")
    data = reports.export_excel(month)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition":
                 f'attachment; filename="report_{month}.xlsx"'})


@app.post("/api/reports/whatsapp")
async def report_whatsapp():
    from . import reports
    cfg = load_config()
    if not whatsapp.is_configured(cfg):
        return JSONResponse({"error": "WhatsApp API ભરેલું નથી"},
                            status_code=400)
    r = await whatsapp.send(cfg, reports.daily_text())
    return {"ok": "error" not in r, "result": r}


# ── સેટિંગ ──────────────────────────────────────────────────────
MASKED_KEYS = ("update_token", "facebook_page_token", "whatsapp_api_key",
               "image_ai_key", "telegram_token", "text_api_key", "aiauto_key")


@app.get("/api/settings")
async def get_settings():
    cfg = load_config()
    for key in MASKED_KEYS:
        if cfg.get(key):
            cfg[key] = "••••" + cfg[key][-4:]
    return cfg


@app.post("/api/settings")
async def set_settings(payload: dict, _=Depends(require_admin)):
    # માસ્ક કરેલા ટોકન પાછા ન લખાય
    for key in MASKED_KEYS:
        if payload.get(key, "").startswith("••••"):
            payload.pop(key)
    save_config(payload)
    return {"ok": True}


# ── ન્યુઝ લેખન AI ટેસ્ટ (પસંદ કરેલા પ્રોવાઈડરનું જ) ──────────────
@app.post("/api/text-test")
async def text_test():
    cfg = load_config()
    llm = LLM(cfg)
    if not await llm.available():
        return JSONResponse(
            {"error": f"{llm.provider} ઉપલબ્ધ નથી — key/URL ચેક કરી સેવ કરો"},
            status_code=400)
    try:
        out = await llm.write_news(
            {"title": "દ્વારકામાં નવા બસ સ્ટેન્ડનું લોકાર્પણ"})
    except Exception as e:
        return JSONResponse({"error": str(e)[:300]}, status_code=500)
    if not out.get("body"):
        return JSONResponse({"error": "AI એ ખાલી જવાબ આપ્યો"}, status_code=500)
    return {"ok": True, "provider": llm.provider,
            "sample": (out.get("title", "") + "\n" + out.get("body", ""))[:400]}


# ── AI તસવીર ટેસ્ટ ──────────────────────────────────────────────
@app.post("/api/image-test")
async def image_test():
    from . import imagegen
    cfg = load_config()
    if not imagegen.is_configured(cfg):
        return JSONResponse(
            {"error": "પહેલા AI તસવીર ચાલુ કરી OpenAI API Key ભરી સેવ કરો"},
            status_code=400)
    try:
        path = await imagegen.generate(
            cfg, "દ્વારકાના દરિયાકિનારે સૂર્યાસ્તનું સુંદર દ્રશ્ય")
        rel = Path(path).relative_to(STORAGE_DIR)
        return {"ok": True, "url": "/storage/" + rel.as_posix()}
    except Exception as e:
        return JSONResponse({"error": str(e)[:400]}, status_code=500)


# ── Telegram ટેસ્ટ ──────────────────────────────────────────────
@app.post("/api/telegram-test")
async def telegram_test():
    from . import telegram
    cfg = load_config()
    if not telegram.is_configured(cfg):
        return JSONResponse({"error": "Telegram ટોકન + chat ભરો"},
                            status_code=400)
    r = await telegram.send_text(
        cfg, f"🧪 ટેસ્ટ — {cfg['channel_name']} Telegram જોડાયું! ✅")
    return {"ok": r.get("ok", False), "result": r}


# ── WhatsApp ટેસ્ટ ──────────────────────────────────────────────
@app.post("/api/whatsapp-test")
async def whatsapp_test():
    cfg = load_config()
    if not whatsapp.is_configured(cfg):
        return JSONResponse(
            {"error": "પહેલા WhatsApp API સેટિંગ ભરીને સેવ કરો"},
            status_code=400)
    result = await whatsapp.send(
        cfg, f"🧪 ટેસ્ટ મેસેજ — {cfg['channel_name']} AI Newsroom ચાલુ છે! "
             f"પબ્લિશ થાય એટલે અહીં જ જાણ આવશે. ✅")
    return {"ok": "error" not in result, "result": result}


# ── અપડેટ ───────────────────────────────────────────────────────
@app.post("/api/update/check")
async def update_check():
    return await updater.check_update(load_config())


@app.post("/api/update/apply")
async def update_apply():
    async def progress(msg):
        await BUS.emit("updater", "", "progress", status="working",
                       message=msg)
    return await updater.apply_update(load_config(), progress)


@app.post("/api/backup")
async def manual_backup():
    return {"ok": True, "file": updater.make_backup()}


@app.post("/api/restart")
async def restart_server():
    """આખું સર્વર રીસ્ટાર્ટ — નવો કોડ/ફીચર લોડ થાય, ફોનમાં પણ."""
    import os
    import sys

    async def do_restart():
        await asyncio.sleep(1)          # પહેલા જવાબ જવા દો
        from . import poster
        try:
            await poster.shutdown()
        except Exception:
            pass
        os.execv(sys.executable, [sys.executable] + sys.argv)

    asyncio.create_task(do_restart())
    return {"ok": True, "message": "સર્વર રીસ્ટાર્ટ થઈ રહ્યું છે..."}


# ── લોગો અપલોડ ──────────────────────────────────────────────────
@app.post("/api/logo")
async def upload_logo(logo: UploadFile = File(...)):
    from .paths import CONFIG_DIR
    ext = Path(logo.filename).suffix.lower() or ".png"
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        return JSONResponse({"error": "ફક્ત PNG/JPG લોગો"}, status_code=400)
    dest = CONFIG_DIR / f"logo{ext}"
    dest.write_bytes(await logo.read())
    save_config({"logo_path": str(dest)})
    return {"ok": True, "path": str(dest)}


@app.post("/api/logo/remove")
async def remove_logo():
    save_config({"logo_path": ""})
    return {"ok": True}
