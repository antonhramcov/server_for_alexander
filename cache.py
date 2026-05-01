import json

import gspread

from config import DATA1_PATH, DATA3_PATH, GOOGLE_AUTH_PATH


def refresh_cache():
    gc = gspread.service_account(filename=str(GOOGLE_AUTH_PATH))
    sh = gc.open_by_url(
        "https://docs.google.com/spreadsheets/d/1dxqQccvwSka_dkYyNkcQPXnKWlvIDkjb2qfBwuJ92dQ/edit?pli=1&gid=719798611#gid=719798611"
    )
    worksheet1 = sh.get_worksheet(0)
    worksheet3 = sh.get_worksheet(2)
    data1 = worksheet1.get_all_records()
    data3 = worksheet3.get_all_records()
    with open(DATA1_PATH, 'w') as f:
        json.dump(data1, f)
    with open(DATA3_PATH, 'w') as f:
        json.dump(data3, f)
    print('Cache updated successfully')


if __name__ == '__main__':
    refresh_cache()
