import time

import gspread

from config import CACHE_RESTART_DELAY, GOOGLE_AUTH_PATH
from internal_api import sync_cache


def refresh_cache():
    gc = gspread.service_account(filename=str(GOOGLE_AUTH_PATH))
    sh = gc.open_by_url(
        "https://docs.google.com/spreadsheets/d/1dxqQccvwSka_dkYyNkcQPXnKWlvIDkjb2qfBwuJ92dQ/edit?pli=1&gid=719798611#gid=719798611"
    )
    worksheet1 = sh.get_worksheet(0)
    worksheet3 = sh.get_worksheet(2)
    data1 = worksheet1.get_all_records()
    data3 = worksheet3.get_all_records()
    sync_cache(data1, data3)
    print('Cache updated successfully')


if __name__ == '__main__':
    while True:
        refresh_cache()
        time.sleep(CACHE_RESTART_DELAY)
