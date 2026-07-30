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


async def fetch_news(feeds: list[str]) -> list[dict]:
    items = []
    for feed in feeds:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
                r = await c.get(feed, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
            root = ET.fromstring(r.content)
            for it in root.iter("item"):
                title = (it.findtext("title") or "").strip()
                link = (it.findtext("link") or "").strip()
                if title:
                    items.append({"title": title, "url": link})
        except Exception:
            continue
    if not items:
        items = [dict(d) for d in DEMO_ITEMS]
    # ડુપ્લિકેટ કાઢો
    seen, unique = set(), []
    for it in items:
        if it["title"] not in seen:
            seen.add(it["title"])
            unique.append(it)
    return unique
