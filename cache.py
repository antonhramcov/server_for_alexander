import time

from config import CACHE_RESTART_DELAY
from google_client import get_gspread_client
from models import save_cache_data


def refresh_cache():
    gc = get_gspread_client()
    sh = gc.open_by_url(
        "https://docs.google.com/spreadsheets/d/1dxqQccvwSka_dkYyNkcQPXnKWlvIDkjb2qfBwuJ92dQ/edit?pli=1&gid=719798611#gid=719798611"
    )
    worksheet1 = sh.get_worksheet(0)
    worksheet3 = sh.get_worksheet(2)
    data1 = worksheet1.get_all_records()
    data3 = worksheet3.get_all_records()
    save_cache_data(data1, data3)
    print('Cache updated successfully')


if __name__ == '__main__':
    refresh_cache()
