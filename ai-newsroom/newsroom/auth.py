"""સાદું મલ્ટી-યુઝર લોગિન — એડમિન + રિપોર્ટર.

વૈકલ્પિક: config.auth_enabled=False હોય તો કોઈ લોગિન નહીં (ડિફોલ્ટ).
પાસવર્ડ pbkdf2 થી hash થાય; સેશન hmac-signed કૂકીથી.
"""
import hashlib
import hmac
import json
import os
import time
from base64 import urlsafe_b64encode, urlsafe_b64decode

from .paths import CONFIG_DIR
from .config import load_config

USERS_FILE = CONFIG_DIR / "users.json"
SECRET_FILE = CONFIG_DIR / "session_secret"


def _secret() -> bytes:
    if not SECRET_FILE.exists():
        SECRET_FILE.write_bytes(os.urandom(32))
    return SECRET_FILE.read_bytes()


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 120_000).hex()


def load_users() -> dict:
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    # પહેલી વાર — ડિફોલ્ટ એડમિન (admin / admin123). પછી બદલવો!
    salt = os.urandom(8).hex()
    users = {"admin": {"salt": salt, "hash": _hash("admin123", salt),
                       "role": "admin"}}
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
    return users


def save_users(users: dict):
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def add_user(username: str, password: str, role: str = "reporter"):
    users = load_users()
    salt = os.urandom(8).hex()
    users[username] = {"salt": salt, "hash": _hash(password, salt),
                       "role": role}
    save_users(users)


def verify(username: str, password: str) -> str | None:
    """સાચું હોય તો role પાછો, નહીંતર None."""
    u = load_users().get(username)
    if u and hmac.compare_digest(u["hash"], _hash(password, u["salt"])):
        return u["role"]
    return None


def make_token(username: str, role: str) -> str:
    payload = f"{username}:{role}:{int(time.time())}"
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()[:24]
    return urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()


def read_token(token: str) -> dict | None:
    try:
        raw = urlsafe_b64decode(token.encode()).decode()
        username, role, ts, sig = raw.rsplit(":", 3)
        payload = f"{username}:{role}:{ts}"
        good = hmac.new(_secret(), payload.encode(),
                        hashlib.sha256).hexdigest()[:24]
        if not hmac.compare_digest(good, sig):
            return None
        if time.time() - int(ts) > 86400 * 7:      # 7 દિવસ
            return None
        return {"username": username, "role": role}
    except Exception:
        return None


def enabled() -> bool:
    return bool(load_config().get("auth_enabled"))


def current_user(token: str | None) -> dict:
    """કૂકીમાંથી યુઝર. auth બંધ હોય તો admin ગણો."""
    if not enabled():
        return {"username": "guest", "role": "admin"}
    return read_token(token or "") or {}
