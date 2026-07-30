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


def _norm(s: str) -> str:
    """સરખામણી માટે — જગ્યા/ચિહ્ન કાઢી નાની કરો."""
    return "".join(ch for ch in s.lower() if ch.isalnum())


async def fetch_news(feeds: list[str], keyword_filter: str = "",
                     seen_titles: set | None = None) -> list[dict]:
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
                    title, source = strip_source(raw)
                    items.append({"title": title, "url": link,
                                  "source": source})
        except Exception:
            continue
    if not items:
        items = [dict(d) for d in DEMO_ITEMS]

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
