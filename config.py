import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def get_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


FILES_DIR = Path(get_env("FILES_DIR", default=str(BASE_DIR / "files")))
REQUESTS_DIR = Path(get_env("REQUESTS_DIR", default=str(BASE_DIR / "requests")))
DATA1_PATH = Path(get_env("DATA1_PATH", default=str(BASE_DIR / "data1.json")))
DATA3_PATH = Path(get_env("DATA3_PATH", default=str(BASE_DIR / "data3.json")))
GOOGLE_AUTH_PATH = Path(
    get_env(
        "GOOGLE_AUTH_PATH",
        default=str(BASE_DIR / "auth.json"),
    )
)

BOT_TOKEN = get_env("BOT_TOKEN", "bot_token")
SMTP_EMAIL = get_env("SMTP_EMAIL", "EMAIL_LOGIN", "email")
SMTP_PASSWORD = get_env("SMTP_PASSWORD", "email_pass")

BOT_MODERATOR_ID = int(get_env("BOT_MODERATOR_ID", default="1111111111"))
SMTP_HOST = get_env("SMTP_HOST", default="smtp.yandex.ru")
SMTP_PORT = int(get_env("SMTP_PORT", default="587"))

FLASK_HOST = get_env("FLASK_HOST", default="0.0.0.0")
FLASK_PORT = int(get_env("FLASK_PORT", default="5000"))
INTERNAL_API_URL = get_env("INTERNAL_API_URL", default="http://server:5000")
INTERNAL_API_TIMEOUT = int(get_env("INTERNAL_API_TIMEOUT", default="30"))
CACHE_RESTART_DELAY = int(get_env("CACHE_RESTART_DELAY", default="300"))


FILES_DIR.mkdir(parents=True, exist_ok=True)
REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
