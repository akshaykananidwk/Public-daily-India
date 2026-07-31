"""સ્કાઉટ — RSS ફીડમાંથી ન્યુઝ ભેગા કરે. ઈન્ટરનેટ ન હોય તો ડેમો ન્યુઝ."""
import xml.etree.ElementTree as ET

import httpx

DEMO_ITEMS = [
    {"title": "દ્વારકામાં નવા બસ સ્ટેન્ડનું લોકાર્પણ", "url": ""},
    {"title": "જામનગર જિલ્લામાં વરસાદની આગાહી, ખેડૂતોમાં આનંદ", "url": ""},
    {"title": "દ્વારકાધીશ મંદિરમાં જન્માષ્ટમીની તૈયારીઓ શરૂ", "url": ""},
    {"title": "ઓખા બંદરે માછીમારી સીઝનનો પ્રારંભ", "url": ""},
    {"title": "ખંભાળિયામાં નવી પ્રાથમિક શાળાનું ઉદ્ઘાટન", "url": ""},
    {"title": "દેવભૂમિ દ્વારકા જિલ્લામાં આરોગ્ય કેમ્પનું આયોજન", "url": ""},
    {"title": "શિવરાજપુર બીચ પર પ્રવાસીઓની સંખ્યામાં વધારો", "url": ""},
    {"title": "ભાણવડ તાલુકામાં પાણી પુરવઠા યોજના મંજૂર", "url": ""},
]


def strip_source(title: str) -> tuple[str, str]:
    """Google News હેડલાઈન પાછળ '- ABP Asmita' જેવું સોર્સ નામ આવે છે —
    એ કાઢી નાખો (પોસ્ટરમાં બીજી ચેનલનું નામ ન દેખાય)."""
    for sep in (" - ", " – ", " | "):
        if sep in title:
            head, _, tail = title.rpartition(sep)
            # પાછળનો ભાગ ટૂંકો હોય તો જ એ સોર્સ નામ ગણાય
            if head and len(tail) <= 40:
                return head.strip(), tail.strip()
    return title.strip(), ""


def clean_title(title: str) -> str:
    """દ્વિભાષી/ક્લિકબેટ પૂંછડું કાઢો — ફક્ત મુખ્ય ગુજરાતી ભાગ રાખો.
    દા.ત. 'રાશિફળ । Read Horoscope...' → 'રાશિફળ'."""
    title = strip_source(title)[0]
    # '।' પછી અંગ્રેજી અનુવાદ હોય તો કાઢો
    for sep in ("। Read", "। read", " | Read", "। ", " Read "):
        if sep in title:
            title = title.split(sep)[0].strip()
            break
    return title.strip(" ।|-–").strip()


# ❌ કચરો — આ શબ્દવાળા ન્યુઝ ક્યારેય પોસ્ટ ન કરવા (પૈસા ન બગડે)
JUNK_WORDS = (
    "રાશિફળ", "રાશિ ", "ભવિષ્ય", "પંચાંગ", "જન્માક્ષર", "જ્યોતિષ",
    "લકી નંબર", "શુકન", "horoscope", "rashifal", "astrology", "zodiac",
    "panchang", "numerology", "vastu tips", "લોટરી", "સટ્ટા",
    "aaj nu rashifal", "aaj no",
    # ક્લિકબેટ / લિસ્ટિકલ
    "જુઓ વીડિયો", "વાયરલ વીડિયો", "જુઓ તસવીરો", "જુઓ ફોટા",
    "આ 5 ", "આ 7 ", "આ 10 ", "these ", "top 10", "viral video",
    "જાણો કેમ", "ચોંકાવનારો", "ધડાકો કરી",
)


def is_junk(title: str, block_words: list | None = None) -> bool:
    t = title.lower()
    for w in JUNK_WORDS:
        if w.lower() in t:
            return True
    for w in (block_words or []):
        if w.strip() and w.strip().lower() in t:
            return True
    return False


def _norm(s: str) -> str:
    """સરખામણી માટે — જગ્યા/ચિહ્ન કાઢી નાની કરો."""
    return "".join(ch for ch in s.lower() if ch.isalnum())


async def fetch_news(feeds: list[str], keyword_filter: str = "",
                     seen_titles: set | None = None,
                     block_words: list | None = None) -> list[dict]:
    items = []
    for feed in feeds:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
                r = await c.get(feed, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
            root = ET.fromstring(r.content)
            for it in root.iter("item"):
                raw = (it.findtext("title") or "").strip()
                link = (it.findtext("link") or "").strip()
                if raw:
                    source = strip_source(raw)[1]
                    title = clean_title(raw)
                    items.append({"title": title, "url": link,
                                  "source": source})
        except Exception:
            continue
    if not items:
        items = [dict(d) for d in DEMO_ITEMS]

    # ❌ કચરો કાઢો (રાશિફળ/જ્યોતિષ/ક્લિકબેટ) — CEO નું પહેલું કામ
    items = [it for it in items if not is_junk(it["title"], block_words)]

    # કીવર્ડ ફિલ્ટર — આપેલા શબ્દોમાંથી કોઈ એક હોય તો જ રાખો
    keywords = [k.strip() for k in keyword_filter.split(",") if k.strip()]
    if keywords:
        items = [it for it in items
                 if any(k.lower() in it["title"].lower() for k in keywords)]

    # ડુપ્લિકેટ કાઢો — આ રનમાં + પહેલા બનેલા ન્યુઝ સાથે (seen_titles)
    seen = set(seen_titles or ())
    unique = []
    for it in items:
        key = _norm(it["title"])
        if key and key not in seen:
            seen.add(key)
            unique.append(it)
    return unique
