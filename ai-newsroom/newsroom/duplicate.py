"""ડુપ્લિકેટ ન્યુઝ પકડનાર — એક ઘટના = એક જ પોસ્ટર.

હેડલાઈન જુદી હોય તો પણ *એક જ ઘટના* હોય તો બીજું કાર્ડ ન બને.
ફોટો બન્યા પહેલાં જ ચેક થાય — એટલે નકામો AI ખર્ચ પણ બચે.
"""
import re

from . import db

# લગભગ દરેક વાક્યમાં આવતા શબ્દો — સરખામણીમાં ગણવા નહીં
STOP = {
    "અને", "માટે", "પર", "થી", "ના", "ની", "નું", "નો", "છે", "કે", "એક",
    "તથા", "સાથે", "બાદ", "થયું", "કર્યું", "થયો", "થઈ", "હતું", "હતો",
    "હતી", "માં", "તે", "પણ", "આ", "જે", "તો", "હવે", "આજે", "શરૂ",
    "the", "in", "of", "to", "and", "for", "on", "at", "is", "was", "news",
}

STEM = 5          # ગુજરાતી પ્રત્યય (નું/માં/ના) કાપવા — શબ્દના પહેલા 5 અક્ષર
SPLIT = re.compile(r"[\s,.:;–—\-|/()\[\]\"'!?૦-૯0-9]+")


def _place_words(cfg: dict) -> set:
    """ચેનલનું સ્થળ/જિલ્લા/નામ — આ લગભગ દરેક ન્યુઝમાં હોય, એટલે
    સરખામણીમાં ગણીએ તો બધા ન્યુઝ સરખા લાગે."""
    out = set()
    parts = [cfg.get("location", ""), cfg.get("channel_name", "")]
    parts += [d.get("name", "") for d in (cfg.get("districts") or [])]
    parts += [d.get("location", "") for d in (cfg.get("districts") or [])]
    for p in parts:
        for w in SPLIT.split((p or "").lower()):
            if len(w) >= 3:
                out.add(w[:STEM])
    out.update({"જિલ્લ", "તાલુક", "ગુજરા", "ભારત"})
    return out


def _stems(text: str, places: set) -> set:
    out = set()
    for w in SPLIT.split((text or "").lower()):
        if len(w) < 3 or w in STOP:
            continue
        s = w[:STEM]
        if s in places:
            continue
        out.add(s)
    return out


def similarity(a: str, b: str, places: set) -> tuple[float, int]:
    """(કેટલા ટકા મળતું આવે, કેટલા શબ્દ સરખા) — ટૂંકા લખાણના પ્રમાણમાં."""
    sa, sb = _stems(a, places), _stems(b, places)
    if not sa or not sb:
        return 0.0, 0
    common = sa & sb
    return len(common) / min(len(sa), len(sb)), len(common)


def _same_event(a: str, b: str, places: set) -> bool:
    ratio, shared = similarity(a, b, places)
    # મોટા ભાગના શબ્દ સરખા → એક જ ઘટના.
    # અથવા 3+ ખાસ શબ્દ સરખા હોય તો પણ (લાંબી vs ટૂંકી હેડલાઈન).
    return ratio >= 0.65 or (shared >= 3 and ratio >= 0.45)


def find_duplicate(cfg: dict, title: str, body: str,
                   day: str) -> dict | None:
    """આજે આ જ ઘટનાનો ન્યુઝ પહેલેથી બન્યો છે? હા તો એની વિગત પાછી આપે."""
    rows = db.query(
        "SELECT id, title FROM news "
        "WHERE date(created_at) = ? AND status != 'duplicate' "
        "ORDER BY id DESC LIMIT 60", (day,))
    if not rows:
        return None
    places = _place_words(cfg)
    full = f"{title} {body}"
    for r in rows:
        if _same_event(title, r["title"], places):
            return {"id": r["id"], "title": r["title"]}
        # હેડલાઈન બહુ ટૂંકી હોય તો આખા લખાણ સામે પણ જુઓ
        if len(title) < 30 and _same_event(full, r["title"], places):
            return {"id": r["id"], "title": r["title"]}
    return None
