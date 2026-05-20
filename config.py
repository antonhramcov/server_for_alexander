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
TEMPLATES_DIR = Path(get_env("TEMPLATES_DIR", default=str(BASE_DIR / "templates")))
DATA1_PATH = Path(get_env("DATA1_PATH", default=str(BASE_DIR / "data1.json")))
DATA3_PATH = Path(get_env("DATA3_PATH", default=str(BASE_DIR / "data3.json")))
DATA_US_PATH = Path(get_env("DATA_US_PATH", default=str(BASE_DIR / "data_us.json")))
CACHE_SPREADSHEET_URL = get_env(
    "CACHE_SPREADSHEET_URL",
    default="https://docs.google.com/spreadsheets/d/1dxqQccvwSka_dkYyNkcQPXnKWlvIDkjb2qfBwuJ92dQ/edit?pli=1&gid=719798611#gid=719798611",
)
CACHE_RUSSIA_COMPANIES_SHEET = get_env("CACHE_RUSSIA_COMPANIES_SHEET")
CACHE_RUSSIA_LIMITS_SHEET = get_env("CACHE_RUSSIA_LIMITS_SHEET")
CACHE_USA_SHEET = get_env("CACHE_USA_SHEET")
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


def parse_moderator_ids() -> tuple[int, ...]:
    raw_ids = get_env("BOT_MODERATOR_IDS")
    raw_second_id = get_env("BOT_MODERATOR_ID_2")

    if not raw_ids:
        raw_ids = str(BOT_MODERATOR_ID)

    moderator_ids = []
    for raw_id in raw_ids.split(","):
        raw_id = raw_id.strip()
        if raw_id:
            moderator_ids.append(int(raw_id))

    if raw_second_id:
        moderator_ids.append(int(raw_second_id))

    moderator_ids = list(dict.fromkeys(moderator_ids))
    return tuple(moderator_ids) or (BOT_MODERATOR_ID,)


BOT_MODERATOR_IDS = parse_moderator_ids()
SMTP_HOST = get_env("SMTP_HOST", default="smtp.yandex.ru")
SMTP_PORT = int(get_env("SMTP_PORT", default="587"))

FLASK_HOST = get_env("FLASK_HOST", default="0.0.0.0")
FLASK_PORT = int(get_env("FLASK_PORT", default="5000"))
INTERNAL_API_URL = get_env("INTERNAL_API_URL", default="http://server:5000")
INTERNAL_API_TIMEOUT = int(get_env("INTERNAL_API_TIMEOUT", default="30"))
CACHE_RESTART_DELAY = int(get_env("CACHE_RESTART_DELAY", default="300"))


FILES_DIR.mkdir(parents=True, exist_ok=True)
REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
