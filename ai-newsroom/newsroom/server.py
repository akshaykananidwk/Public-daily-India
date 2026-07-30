"""FastAPI સર્વર — UI, API, WebSocket બધું અહીંથી ચાલે."""
import asyncio
from datetime import date
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import db, pipeline, updater
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


# ── UI ──────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "index.html")


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
async def run_day():
    if pipeline.is_running():
        return JSONResponse({"error": "કામ પહેલેથી ચાલુ છે"}, status_code=409)
    asyncio.create_task(pipeline.run_day())
    return {"ok": True, "message": "દિવસ શરૂ થયો 🚀"}


@app.post("/api/press-note")
async def press_note(text: str = Form(""), photo: UploadFile | None = None):
    note = (text or "").strip()
    if photo and photo.filename:
        dest = PHOTOS_DIR / photo.filename
        dest.write_bytes(await photo.read())
        if not note:
            try:  # OCR — pytesseract હોય તો
                import pytesseract
                from PIL import Image
                note = pytesseract.image_to_string(
                    Image.open(dest), lang="guj+eng")
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
    asyncio.create_task(pipeline.run_day(press_note=note))
    return {"ok": True, "message": "પ્રેસ નોટ પર કામ શરૂ 🚀"}


# ── ન્યુઝ + અપ્રુવલ ────────────────────────────────────────────
@app.get("/api/news")
async def list_news(status: str = "", limit: int = 50):
    if status:
        rows = db.query(
            "SELECT * FROM news WHERE status=? ORDER BY id DESC LIMIT ?",
            (status, limit))
    else:
        rows = db.query("SELECT * FROM news ORDER BY id DESC LIMIT ?", (limit,))
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
async def approve(news_id: int):
    db.execute("UPDATE news SET status='approved', "
               "updated_at=CURRENT_TIMESTAMP WHERE id=?", (news_id,))
    db.bump_stat(date.today().isoformat(), "approved")
    result = await pipeline.publish_news(news_id)
    return {"ok": True, "publish": result}


@app.post("/api/news/{news_id}/reject")
async def reject(news_id: int):
    db.execute("UPDATE news SET status='rejected', "
               "updated_at=CURRENT_TIMESTAMP WHERE id=?", (news_id,))
    db.bump_stat(date.today().isoformat(), "rejected")
    return {"ok": True}


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


# ── સેટિંગ ──────────────────────────────────────────────────────
@app.get("/api/settings")
async def get_settings():
    cfg = load_config()
    if cfg.get("update_token"):
        cfg["update_token"] = "••••" + cfg["update_token"][-4:]
    if cfg.get("facebook_page_token"):
        cfg["facebook_page_token"] = "••••" + cfg["facebook_page_token"][-4:]
    return cfg


@app.post("/api/settings")
async def set_settings(payload: dict):
    # માસ્ક કરેલા ટોકન પાછા ન લખાય
    for key in ("update_token", "facebook_page_token"):
        if payload.get(key, "").startswith("••••"):
            payload.pop(key)
    save_config(payload)
    return {"ok": True}


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
