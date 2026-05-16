import gspread
import json

from config import GOOGLE_AUTH_PATH


def get_gspread_client():
    if not GOOGLE_AUTH_PATH.exists():
        raise RuntimeError(
            f"Google credentials file not found: {GOOGLE_AUTH_PATH}. "
            "Container entrypoint should create it from GOOGLE_AUTH_JSON or GOOGLE_AUTH_JSON_BASE64."
        )
    data = json.loads(GOOGLE_AUTH_PATH.read_text(encoding="utf-8"))
    print(
        "Using Google credentials file",
        str(GOOGLE_AUTH_PATH),
        "client_email=",
        data.get("client_email"),
        "private_key_id=",
        data.get("private_key_id"),
    )
    return gspread.service_account(filename=str(GOOGLE_AUTH_PATH))
