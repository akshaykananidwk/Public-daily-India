"""રિપોર્ટ સહાયક — ખર્ચ ગણતરી, રોજનો WhatsApp રિપોર્ટ, Excel એક્સપોર્ટ."""
import io
from datetime import date

from . import db

# પ્રતિ AI તસવીર અંદાજિત ખર્ચ (₹)
IMG_RATE = {"local": 0, "pollinations": 0, "gemini": 3, "openai": 3.5}


def month_cost(month: str, provider: str) -> float:
    rows = db.query(
        "SELECT SUM(ai_images) n FROM daily_stats WHERE date LIKE ?",
        (month + "%",))
    n = (rows[0]["n"] if rows else 0) or 0
    return n * IMG_RATE.get(provider, 0)


def daily_text(d: str | None = None) -> str:
    d = d or date.today().isoformat()
    rows = db.query("SELECT * FROM daily_stats WHERE date=?", (d,))
    if not rows:
        return f"📊 {d}: આજે કોઈ પ્રવૃત્તિ નથી."
    s = rows[0]
    return (f"📊 આજનો રિપોર્ટ ({d})\n\n"
            f"📥 ભેગા કર્યા: {s['news_collected']}\n"
            f"✍️ લખાયા: {s['news_written']}\n"
            f"🖼️ પોસ્ટર: {s['posters_created']}\n"
            f"✅ મંજૂર: {s['approved']}   ❌ રદ: {s['rejected']}\n"
            f"📤 પબ્લિશ: {s['published_fb']}\n"
            f"🎨 AI તસવીર: {s['ai_images']}\n"
            f"⚠️ ભૂલ: {s['errors']}")


def export_excel(month: str) -> bytes:
    """મહિનાનો ડેટા Excel (.xlsx) માં."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = month
    headers = ["તારીખ", "ભેગા", "પસંદ", "લખાયા", "પોસ્ટર", "મંજૂર",
               "રદ", "પબ્લિશ", "AI તસવીર", "ભૂલ"]
    ws.append(headers)
    rows = db.query(
        "SELECT * FROM daily_stats WHERE date LIKE ? ORDER BY date",
        (month + "%",))
    for r in rows:
        ws.append([r["date"], r["news_collected"], r["news_selected"],
                   r["news_written"], r["posters_created"], r["approved"],
                   r["rejected"], r["published_fb"], r["ai_images"],
                   r["errors"]])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
