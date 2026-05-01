import gspread

from config import GOOGLE_AUTH_PATH


def get_gspread_client():
    if not GOOGLE_AUTH_PATH.exists():
        raise RuntimeError(
            f"Google credentials file not found: {GOOGLE_AUTH_PATH}. "
            "Container entrypoint should create it from GOOGLE_AUTH_JSON or GOOGLE_AUTH_JSON_BASE64."
        )
    return gspread.service_account(filename=str(GOOGLE_AUTH_PATH))
