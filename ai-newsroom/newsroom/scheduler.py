"""રોજ સવારે (દા.ત. 05:00) ઓટો રન — સેટિંગમાં ચાલુ/બંધ થાય."""
import asyncio
import json
from datetime import datetime, date

from .config import load_config
from .paths import DATA_DIR

LAST_RUN_FILE = DATA_DIR / "last_auto_run.json"
LAST_REPORT_FILE = DATA_DIR / "last_report.json"


def _read_date(f) -> str:
    try:
        return json.loads(f.read_text())["date"]
    except Exception:
        return ""


async def scheduler_loop():
    from . import pipeline, whatsapp, reports
    while True:
        try:
            cfg = load_config()
            now = datetime.now().strftime("%H:%M")
            today = date.today().isoformat()

            # રોજ સવારે ઓટો રન
            if cfg.get("auto_run_enabled"):
                if now >= cfg.get("auto_run_time", "05:00") and \
                        _read_date(LAST_RUN_FILE) != today and \
                        not pipeline.is_running():
                    LAST_RUN_FILE.write_text(json.dumps({"date": today}))
                    asyncio.create_task(pipeline.run_day())

            # રાત્રે 9 વાગ્યે રોજનો રિપોર્ટ WhatsApp પર
            if cfg.get("daily_report_enabled") and \
                    whatsapp.is_configured(cfg):
                if now >= "21:00" and _read_date(LAST_REPORT_FILE) != today:
                    LAST_REPORT_FILE.write_text(json.dumps({"date": today}))
                    try:
                        await whatsapp.send(cfg, reports.daily_text())
                    except Exception:
                        pass
        except Exception:
            pass
        await asyncio.sleep(30)
