"""બ્રાન્ડિંગ સહાયક — QR કોડ, કેપ્શન/હેશટેગ, હકીકત-તપાસ ચેતવણી."""
import io
import base64

import qrcode


def make_qr_datauri(data: str) -> str:
    """QR કોડ બનાવી data-URI પાછો આપે (પોસ્ટરમાં સીધો મુકાય)."""
    if not data:
        return ""
    qr = qrcode.QRCode(box_size=10, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#14295e", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def build_caption(title: str, body: str, cfg: dict) -> str:
    """સોશિયલ મીડિયા કેપ્શન + હેશટેગ."""
    tags = cfg.get("hashtags", "").strip()
    parts = [title.strip()]
    if body.strip():
        parts.append(body.strip()[:400])
    parts.append(f"— {cfg.get('channel_name', '')}")
    if cfg.get("contact_number"):
        parts.append(f"📞 {cfg['contact_number']}")
    if tags:
        parts.append(tags)
    return "\n\n".join(p for p in parts if p)


SUSPECT_WORDS = ("અફવા", "વાયરલ", "શેર કરો", "ફોરવર્ડ", "દાવો", "કહેવાય છે",
                 "સૂત્રોના જણાવ્યા", "અપુષ્ટ", "શંકા")


def fact_check_flag(title: str, body: str) -> str:
    """શંકાસ્પદ લખાણ હોય તો ચેતવણી (ખાલી = વાંધો નહીં)."""
    text = f"{title} {body}"
    hits = [w for w in SUSPECT_WORDS if w in text]
    if hits:
        return "⚠️ ચકાસો: " + ", ".join(hits) + " — પ્રકાશન પહેલા ખાતરી કરો"
    return ""
