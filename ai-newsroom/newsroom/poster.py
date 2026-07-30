"""પોસ્ટર એન્જિન — Chromium (Playwright) hidden window થી HTML → PNG.

ગુજરાતી shaping માટે ફોન્ટ પૂરો લોડ થાય પછી જ સ્ક્રીનશોટ લેવાય છે.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

from . import db
from .paths import TEMPLATES_DIR, POSTERS_DIR

_pw = None
_browser = None


def _find_chromium() -> str | None:
    """Playwright નું ડિફોલ્ટ Chromium ન મળે તો સિસ્ટમમાં શોધો."""
    candidates = [os.environ.get("CHROMIUM_PATH", ""),
                  "/opt/pw-browsers/chromium",
                  "/usr/bin/chromium", "/usr/bin/chromium-browser",
                  "/usr/bin/google-chrome",
                  r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


async def _get_browser():
    global _pw, _browser
    if _browser is None or not _browser.is_connected():
        _pw = await async_playwright().start()
        try:
            _browser = await _pw.chromium.launch()
        except Exception:
            exe = _find_chromium()
            if not exe:
                raise
            _browser = await _pw.chromium.launch(executable_path=exe)
    return _browser


async def render_poster(template: str, news: dict, size: dict) -> dict:
    """એક પોસ્ટર રેન્ડર કરે. news = {id,title,body,category,date}"""
    t0 = time.time()
    template_path = TEMPLATES_DIR / f"{template}.html"
    if not template_path.exists():
        template_path = TEMPLATES_DIR / "general.html"

    browser = await _get_browser()
    page = await browser.new_page(
        viewport={"width": size["w"], "height": size["h"]},
        device_scale_factor=2)  # HD — 1080 → ખરેખર 2160 રેન્ડર
    try:
        await page.goto(template_path.as_uri())
        await page.evaluate(
            f"window.renderNews({json.dumps(news, ensure_ascii=False)})")
        # ⭐ ફોન્ટ પૂરો લોડ થાય એની રાહ — નહીંતર અક્ષર તૂટે
        await page.evaluate("""
            document.fonts.ready.then(() =>
              new Promise(r => requestAnimationFrame(() =>
                requestAnimationFrame(r))))
        """)
        day_dir = POSTERS_DIR / datetime.now().strftime("%Y%m%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        out = day_dir / f"news{news.get('id', 0)}_{template}_{size['name']}.png"
        await page.screenshot(path=str(out))
    finally:
        await page.close()

    ms = int((time.time() - t0) * 1000)
    db.execute(
        """INSERT INTO poster_log(news_id, template, size, file_path, render_time_ms)
           VALUES(?,?,?,?,?)""",
        (news.get("id"), template, f"{size['w']}x{size['h']}",
         str(out), ms))
    return {"file": str(out), "ms": ms, "size": size["name"]}


async def shutdown():
    global _pw, _browser
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _pw is not None:
        await _pw.stop()
        _pw = None
