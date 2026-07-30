import json

from .paths import CONFIG_PATH

DEFAULTS = {
    "channel_name": "PUBLIC DAY INDIA",
    "location": "દેવભૂમિ દ્વારકા",
    "ollama_url": "http://localhost:11434",
    "model_think": "gemma3:12b",       # CEO / રૂટિંગ / સ્કોરિંગ
    "model_write": "gemma3:27b",       # ગુજરાતી લેખન
    "model_translate": "",             # IndicTrans2 (ખાલી હોય તો model_write વાપરે)
    "writing_mode": "translate",       # direct | translate (બે-પગલાં)
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
    "tagline": "જ્યાં સત્ય છે, ત્યાં પબ્લિક ડે ઈન્ડિયા છે.",
    "editor_name": "",
    "contact_number": "",
    "facebook_page_token": "",
    "facebook_page_id": "",
    "instagram_account_id": "",
    "image_ai_enabled": False,
    "image_ai_provider": "pollinations",  # pollinations (મફત) | openai
    "image_ai_key": "",                # OpenAI API key (platform.openai.com)
    "image_ai_model": "gpt-image-1",
    "image_ai_quality": "medium",      # low | medium | high
    "image_ai_style": "",              # વધારાની સ્ટાઈલ સૂચના
    "whatsapp_api_url": "https://bulk.akdwk.in/api.php",
    "whatsapp_api_key": "",
    "whatsapp_session_id": "",
    "whatsapp_number": "",
    "public_base_url": "",
    "update_repo": "",                 # દા.ત. akshaykananidwk/Public-daily-India
    "update_branch": "main",
    "update_token": "",
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg.update(saved)
        except Exception:
            pass
    return cfg


def save_config(cfg: dict) -> dict:
    merged = load_config()
    for k, v in cfg.items():
        if k in DEFAULTS:
            merged[k] = v
    CONFIG_PATH.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged
