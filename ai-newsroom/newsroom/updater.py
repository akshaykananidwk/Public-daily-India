"""GitHub One-Click અપડેટ — બેકઅપ → ડાઉનલોડ → કોપી → માઈગ્રેશન → હેલ્થ ચેક.
ભૂલ પડે તો ઓટો રોલબેક.
"""
import io
import json
import shutil
import zipfile
from datetime import datetime

import httpx

from . import db
from .paths import (ROOT, VERSION_PATH, BACKUPS_DIR, LOGS_DIR, DB_PATH,
                    CONFIG_DIR, TEMPLATES_DIR)

# 🔄 અપડેટ થાય તેવા ફોલ્ડર/ફાઈલ
UPDATABLE = ["newsroom", "templates", "web", "prompts", "fonts",
             "run.py", "requirements.txt", "start.bat"]
# 🔒 સુરક્ષિત — ક્યારેય ઓવરરાઈટ નહીં
PROTECTED = ["data", "config", "storage", "backups", "logs"]


def current_version() -> dict:
    if VERSION_PATH.exists():
        try:
            return json.loads(VERSION_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"sha": "", "updated_at": ""}


async def check_update(cfg: dict) -> dict:
    repo, branch = cfg.get("update_repo"), cfg.get("update_branch", "main")
    if not repo:
        return {"error": "સેટિંગમાં GitHub repo સેટ કરો"}
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "ai-newsroom"}
    if cfg.get("update_token"):
        headers["Authorization"] = f"Bearer {cfg['update_token']}"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(
            f"https://api.github.com/repos/{repo}/commits/{branch}",
            headers=headers)
        if r.status_code != 200:
            return {"error": f"GitHub ભૂલ {r.status_code}: {r.text[:200]}"}
        data = r.json()
    latest = data["sha"]
    cur = current_version().get("sha", "")
    return {
        "current": cur[:7] or "(પહેલી વાર)",
        "latest": latest[:7],
        "update_available": latest != cur,
        "message": data.get("commit", {}).get("message", "")[:300],
        "date": data.get("commit", {}).get("committer", {}).get("date", ""),
        "sha": latest,
    }


def make_backup() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = BACKUPS_DIR / f"backup_{stamp}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in UPDATABLE:
            p = ROOT / name
            if p.is_file():
                z.write(p, name)
            elif p.is_dir():
                for f in p.rglob("*"):
                    if f.is_file() and "__pycache__" not in f.parts:
                        z.write(f, f.relative_to(ROOT))
        if DB_PATH.exists():
            z.write(DB_PATH, DB_PATH.relative_to(ROOT))
        for f in CONFIG_DIR.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(ROOT))
    # ફક્ત છેલ્લા 5 બેકઅપ રાખો
    backups = sorted(BACKUPS_DIR.glob("backup_*.zip"))
    for old in backups[:-5]:
        old.unlink()
    return str(out)


def rollback(backup_path: str):
    with zipfile.ZipFile(backup_path) as z:
        z.extractall(ROOT)


def health_check() -> list[str]:
    problems = []
    try:
        db.query("SELECT 1")
    except Exception as e:
        problems.append(f"DB: {e}")
    if not (CONFIG_DIR / "config.json").exists():
        pass  # પહેલી વાર હોઈ શકે — ભૂલ નથી
    if not (TEMPLATES_DIR / "general.html").exists():
        problems.append("ટેમ્પ્લેટ ગુમ છે")
    return problems


async def apply_update(cfg: dict, progress=None) -> dict:
    async def report(step, msg):
        if progress:
            await progress(f"[{step}/7] {msg}")

    info = await check_update(cfg)
    if info.get("error"):
        return info
    if not info["update_available"]:
        return {"ok": True, "message": "પહેલેથી લેટેસ્ટ વર્ઝન છે ✅"}

    await report(1, "💾 બેકઅપ લેવાઈ રહ્યો છે...")
    backup = make_backup()
    try:
        await report(2, "⬇️ ડાઉનલોડ થઈ રહ્યું છે...")
        headers = {"User-Agent": "ai-newsroom"}
        if cfg.get("update_token"):
            headers["Authorization"] = f"Bearer {cfg['update_token']}"
        async with httpx.AsyncClient(timeout=300, follow_redirects=True) as c:
            r = await c.get(
                f"https://api.github.com/repos/{cfg['update_repo']}/zipball/"
                f"{cfg.get('update_branch', 'main')}", headers=headers)
            r.raise_for_status()

        await report(3, "📦 એક્સટ્રેક્ટ...")
        tmp = ROOT / "temp_update"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            z.extractall(tmp)
        # zipball માં ટોપ-લેવલ ફોલ્ડર હોય; ai-newsroom સબફોલ્ડર શોધો
        inner = next(tmp.iterdir())
        src = inner / "ai-newsroom" if (inner / "ai-newsroom").exists() else inner

        await report(4, "📋 ફાઈલો કોપી (સુરક્ષિત ફોલ્ડર છોડીને)...")
        copied = 0
        for name in UPDATABLE:
            s = src / name
            if not s.exists():
                continue
            d = ROOT / name
            if s.is_file():
                shutil.copy2(s, d)
                copied += 1
            else:
                for f in s.rglob("*"):
                    if f.is_file() and "__pycache__" not in f.parts:
                        rel = f.relative_to(src)
                        if any(str(rel).startswith(p) for p in PROTECTED):
                            continue
                        dest = ROOT / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, dest)
                        copied += 1
        shutil.rmtree(tmp)

        await report(5, "🗄️ DB માઈગ્રેશન...")
        db.run_migrations()

        await report(6, "✅ હેલ્થ ચેક...")
        problems = health_check()
        if problems:
            raise RuntimeError("હેલ્થ ચેક ફેલ: " + "; ".join(problems))

        await report(7, "વર્ઝન નોંધાઈ રહ્યું છે...")
        VERSION_PATH.write_text(json.dumps({
            "sha": info["sha"],
            "updated_at": datetime.now().isoformat()}), encoding="utf-8")
        return {"ok": True, "copied": copied,
                "message": f"અપડેટ પૂરું ✅ ({info['latest']}) — એપ રીસ્ટાર્ટ કરો"}
    except Exception as e:
        (LOGS_DIR / f"update_error_{datetime.now():%Y%m%d_%H%M%S}.log"
         ).write_text(str(e), encoding="utf-8")
        rollback(backup)
        return {"error": f"ભૂલ પડી, રોલબેક થઈ ગયું ↩️ — કંઈ ખોવાયું નથી. ({e})"}
