"""💰 એકાઉન્ટન્ટ — દરેક AI ખર્ચ નોંધે અને મહિનાનો હિસાબ રાખે."""
from datetime import date

from . import db

# અંદાજિત દર (₹)
IMAGE_RATE = {"local": 0.0, "pollinations": 0.0, "gemini": 3.0, "openai": 3.5}
TEXT_RATE = {"ollama": 0.0, "gemini": 0.3, "openai": 0.5}  # પ્રતિ ન્યુઝ અંદાજ


def record(kind: str, provider: str, detail: str = ""):
    rate = (IMAGE_RATE if kind == "image" else TEXT_RATE).get(provider, 0.0)
    db.execute(
        "INSERT INTO cost_log(kind, provider, amount, detail) VALUES(?,?,?,?)",
        (kind, provider, rate, detail))
    return rate


def summary(month: str | None = None) -> dict:
    month = month or date.today().strftime("%Y-%m")
    rows = db.query(
        """SELECT kind, provider, COUNT(*) n, SUM(amount) total
           FROM cost_log WHERE created_at LIKE ?
           GROUP BY kind, provider""", (month + "%",))
    total = sum((r["total"] or 0) for r in rows)
    by_day = db.query(
        """SELECT date(created_at) d, SUM(amount) total, COUNT(*) n
           FROM cost_log WHERE created_at LIKE ?
           GROUP BY date(created_at) ORDER BY d DESC""", (month + "%",))
    return {"month": month, "total": round(total, 2),
            "breakdown": rows, "by_day": by_day}
