from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

APP_DIR = ROOT / "newsroom"
TEMPLATES_DIR = ROOT / "templates"
FONTS_DIR = ROOT / "fonts"
WEB_DIR = ROOT / "web"
PROMPTS_DIR = ROOT / "prompts"

# 🔒 અપડેટમાં ક્યારેય ઓવરરાઈટ ન થાય
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"
STORAGE_DIR = ROOT / "storage"
POSTERS_DIR = STORAGE_DIR / "posters"
PHOTOS_DIR = STORAGE_DIR / "photos"
BACKUPS_DIR = ROOT / "backups"
LOGS_DIR = ROOT / "logs"

DB_PATH = DATA_DIR / "newsroom.db"
CONFIG_PATH = CONFIG_DIR / "config.json"
VERSION_PATH = DATA_DIR / "version.json"

for d in (DATA_DIR, CONFIG_DIR, STORAGE_DIR, POSTERS_DIR, PHOTOS_DIR,
          BACKUPS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)
