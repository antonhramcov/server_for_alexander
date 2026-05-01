import gspread

from config import GOOGLE_AUTH_PATH, get_google_auth_info


def get_gspread_client():
    auth_info = get_google_auth_info()
    if auth_info is not None:
        return gspread.service_account_from_dict(auth_info)
    return gspread.service_account(filename=str(GOOGLE_AUTH_PATH))
