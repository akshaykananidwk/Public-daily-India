"""રોજ સવારે (દા.ત. 05:00) ઓટો રન — સેટિંગમાં ચાલુ/બંધ થાય."""
import asyncio
import json
from datetime import datetime, date

from .config import load_config
from .paths import DATA_DIR

LAST_RUN_FILE = DATA_DIR / "last_auto_run.json"


def _last_run_date() -> str:
    try:
        return json.loads(LAST_RUN_FILE.read_text())["date"]
    except Exception:
        return ""


async def scheduler_loop():
    from . import pipeline
    while True:
        try:
            cfg = load_config()
            if cfg.get("auto_run_enabled"):
                now = datetime.now().strftime("%H:%M")
                today = date.today().isoformat()
                if now >= cfg.get("auto_run_time", "05:00") and \
                        _last_run_date() != today and not pipeline.is_running():
                    LAST_RUN_FILE.write_text(json.dumps({"date": today}))
                    asyncio.create_task(pipeline.run_day())
        except Exception:
            pass
        await asyncio.sleep(30)
