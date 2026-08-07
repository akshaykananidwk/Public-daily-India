import json

from .paths import CONFIG_PATH

DEFAULTS = {
    "channel_name": "PUBLIC DAILY INDIA",
    "location": "દેવભૂમિ દ્વારકા",
    "ollama_url": "http://localhost:11434",
    "model_think": "gemma3:12b",       # CEO / રૂટિંગ / સ્કોરિંગ
    "model_write": "gemma3:27b",       # ગુજરાતી લેખન
    "model_translate": "",             # IndicTrans2 (ખાલી હોય તો model_write વાપરે)
    "writing_mode": "translate",       # direct | translate (બે-પગલાં)
    "text_provider": "ollama",         # ollama | gemini | openai (ન્યુઝ લખવા)
    "text_api_key": "",                # Gemini/OpenAI key (ટેક્સ્ટ માટે)
    "text_model": "",                  # ખાલી = gemini-2.0-flash / gpt-4o-mini
    "daily_news_count": 12,
    "auto_run_time": "05:00",          # રોજ સવારે ઓટો રન
    "auto_run_enabled": False,
    "rss_feeds": [
        "https://news.google.com/rss?hl=gu&gl=IN&ceid=IN:gu",
    ],
    "poster_sizes": [
        {"name": "post", "w": 1080, "h": 1080},
        {"name": "portrait", "w": 1080, "h": 1350},
        {"name": "story", "w": 1080, "h": 1920},
    ],
    "tagline": "જ્યાં સત્ય છે, ત્યાં પબ્લિક ડેઈલી ઈન્ડિયા છે.",
    "editor_name": "",
    "contact_number": "",
    # 🎨 બ્રાન્ડિંગ / ડિઝાઈન
    "logo_path": "",                   # સાચો લોગો (અપલોડ થાય તો PD બોક્સ બદલે)
    "theme_navy": "#14295e",           # પોસ્ટરનો મુખ્ય રંગ
    "theme_accent": "#ffc400",         # પીળો accent
    "theme_red": "#e11b22",            # લાલ પટ્ટી
    "website_url": "www.publicdayindia.com",
    "qr_enabled": False,               # પોસ્ટર પર QR કોડ
    "qr_data": "",                     # QR માં શું (ખાલી તો website/whatsapp)
    "poster_font": "AnekGuj",          # પોસ્ટર ફોન્ટ (નીચે યાદી)
    "watermark_enabled": True,         # ફોટા પર ચેનલ વોટરમાર્ક
    "districts": [],                   # મલ્ટી-જિલ્લા [{name,location,contact}]
    "hashtags": "#PublicDailyIndia #Dwarka #Gujarat #GujaratiNews",
    "keyword_filter": "",              # RSS ફિલ્ટર (અલ્પવિરામથી અલગ)
    "block_words": "",                 # આ શબ્દવાળા ન્યુઝ કાઢી નાખો (કચરો)
    # 📱 WhatsApp બ્રોડકાસ્ટ (અલ્પવિરામથી અલગ નંબર, 91 સાથે)
    "whatsapp_broadcast": "",
    "daily_report_enabled": False,     # રાત્રે રિપોર્ટ WhatsApp પર
    "error_alert_enabled": False,      # ભૂલ પડે તો WhatsApp એલર્ટ
    "facebook_page_token": "",
    "facebook_page_id": "",
    "instagram_account_id": "",
    "image_ai_enabled": False,
    "image_ai_provider": "aiauto",     # aiauto | gemini
    "image_ai_key": "",                # Gemini API key
    "image_ai_model": "gemini-2.5-flash-image",
    "image_ai_style": "",              # વધારાની સ્ટાઈલ સૂચના
    # 🤖 ઓટો પ્રોમ્પ્ટ બિલ્ડર — admin એ પ્રોમ્પ્ટ ન લખવો પડે
    "image_quality_tags": ("ultra realistic, 8K, highly detailed, sharp focus, "
                           "cinematic lighting, HDR, professional photography, "
                           "volumetric lighting, beautiful composition, masterpiece"),
    "image_negative": ("low quality, blurry, duplicate, cropped, bad anatomy, "
                       "deformed face, extra fingers, watermark, text, letters, "
                       "logo, noise, low resolution"),
    # ☁️ AIAuto પ્લેટફોર્મ (તમારું પોતાનું async job API)
    "aiauto_url": "http://127.0.0.1:8000/api/public/v1",
    "aiauto_key": "",                  # ak_... (X-API-Key)
    "telegram_token": "",              # @BotFather થી બોટ ટોકન
    "telegram_chat": "",               # @channel કે -100... chat id
    "whatsapp_api_url": "https://bulk.akdwk.in/api.php",
    "whatsapp_api_key": "",
    "whatsapp_session_id": "",
    "whatsapp_number": "",
    # ⚡ ન્યુઝ બનતાં જ (અપ્રુવલ પહેલાં) અહીં પોસ્ટર મોકલો —
    #    કોમન નંબર (919978123146) કે ગ્રુપ ID (1203...@g.us)
    "whatsapp_instant_enabled": False,
    "whatsapp_instant_to": "",
    "public_base_url": "",
    "update_repo": "",                 # દા.ત. akshaykananidwk/Public-daily-India
    "update_branch": "main",
    "update_token": "",
    "auth_enabled": False,             # મલ્ટી-યુઝર લોગિન (ડિફોલ્ટ બંધ)
}


def clean_key(raw: str) -> str:
    """API key ને HTTP header માં મૂકતાં પહેલાં સાફ કરે.
    કોપી-પેસ્ટ સાથે ✅, ઈમોજી, space કે newline આવી જાય તો httpx
    'ascii codec can't encode' ભૂલ આપે — એ અહીં જ અટકાવીએ."""
    s = (raw or "").strip()
    # ઈમોજી/ગુજરાતી/કોઈ પણ non-ASCII અક્ષર કાઢી નાખો
    s = "".join(ch for ch in s if 32 < ord(ch) < 127)
    return s


# ઈમેજ માટે હવે ફક્ત આ બે — જૂની સેટિંગ (pollinations/local/openai) આપોઆપ બદલાય
IMAGE_PROVIDERS = ("aiauto", "gemini")


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg.update(saved)
        except Exception:
            pass
    if cfg.get("image_ai_provider") not in IMAGE_PROVIDERS:
        cfg["image_ai_provider"] = "aiauto"
    return cfg


def save_config(cfg: dict) -> dict:
    merged = load_config()
    for k, v in cfg.items():
        if k in DEFAULTS:
            # key/token વાળા ખાનામાં કોપી-પેસ્ટનો કચરો સેવ કરતાં જ સાફ કરો
            if isinstance(v, str) and (k.endswith("_key") or k.endswith("_token")):
                v = clean_key(v)
            merged[k] = v
    CONFIG_PATH.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged
