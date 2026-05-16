import gspread

from config import GOOGLE_AUTH_PATH


def get_gspread_client():
    if not GOOGLE_AUTH_PATH.exists():
        raise RuntimeError(
            f"Google credentials file not found: {GOOGLE_AUTH_PATH}."
        )
    return gspread.service_account(filename=str(GOOGLE_AUTH_PATH))
