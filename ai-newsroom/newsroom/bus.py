"""ઈવેન્ટ બસ — દરેક એજન્ટની ઘટના ડેશબોર્ડ (WebSocket) અને DB બંનેમાં જાય."""
import asyncio
import json
import time
from datetime import datetime

from . import db


class EventBus:
    def __init__(self):
        self.clients: set = set()          # WebSocket connections
        self.recent: list[dict] = []       # છેલ્લી 200 ઘટના (નવા ક્લાયન્ટ માટે)

    async def connect(self, ws):
        self.clients.add(ws)
        for ev in self.recent[-60:]:
            try:
                await ws.send_text(json.dumps(ev, ensure_ascii=False))
            except Exception:
                break

    def disconnect(self, ws):
        self.clients.discard(ws)

    async def emit(self, agent: str, parent: str, event: str, *,
                   job_id: str = "", status: str = "", message: str = "",
                   progress: int | None = None, detail: dict | None = None,
                   news_id: int | None = None, log_db: bool = False,
                   duration_ms: int | None = None, error: str = ""):
        payload = {
            "type": "agent:event",
            "job_id": job_id,
            "agent": agent,
            "parent": parent,
            "event": event,      # started|thinking|progress|completed|failed|dispatch
            "status": status,    # idle|thinking|working|waiting|done|error
            "message": message,
            "progress": progress,
            "detail": detail or {},
            "news_id": news_id,
            "ts": datetime.now().isoformat(timespec="seconds"),
        }
        self.recent.append(payload)
        self.recent = self.recent[-200:]
        text = json.dumps(payload, ensure_ascii=False)
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
        if log_db:
            db.execute(
                """INSERT INTO activity_log(job_id, agent, action, news_id,
                   status, duration_ms, message, error_message)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (job_id, agent, event, news_id,
                 "error" if event == "failed" else "success",
                 duration_ms, message, error))


    async def job_progress(self, percent: int, message: str, stage: str = ""):
        """આખા દિવસનું પ્રગતિ ટકા — ડેશબોર્ડ પ્રોગ્રેસ બાર માટે."""
        payload = {"type": "job:progress",
                   "percent": max(0, min(100, int(percent))),
                   "message": message, "stage": stage,
                   "ts": datetime.now().isoformat(timespec="seconds")}
        self.recent.append(payload)
        self.recent = self.recent[-200:]
        text = json.dumps(payload, ensure_ascii=False)
        for ws in list(self.clients):
            try:
                await ws.send_text(text)
            except Exception:
                self.disconnect(ws)


BUS = EventBus()


async def run_agent(name: str, parent: str, fn, *, job_id: str = "",
                    message: str = ""):
    """પ્લાનનો ફરજિયાત wrapper — ડેશબોર્ડ + રિપોર્ટ બંને આપોઆપ ભરાય."""
    t0 = time.time()
    if parent:
        await BUS.emit(parent, "", "dispatch", job_id=job_id,
                       detail={"to": name})
    await BUS.emit(name, parent, "started", job_id=job_id, status="working",
                   message=message, log_db=True)

    async def progress(msg: str, pct: int | None = None, detail: dict | None = None):
        await BUS.emit(name, parent, "progress", job_id=job_id,
                       status="working", message=msg, progress=pct,
                       detail=detail)

    try:
        result = await fn(progress)
        await BUS.emit(name, parent, "completed", job_id=job_id, status="done",
                       duration_ms=int((time.time() - t0) * 1000), log_db=True)
        return result
    except Exception as e:
        await BUS.emit(name, parent, "failed", job_id=job_id, status="error",
                       message=str(e)[:300], error=str(e)[:1000],
                       duration_ms=int((time.time() - t0) * 1000), log_db=True)
        raise
