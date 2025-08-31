import gspread, time, json

time_sleep = 60

while True:
    gc = gspread.service_account(filename="auth.json")
    sh = gc.open_by_url(
        "https://docs.google.com/spreadsheets/d/1dxqQccvwSka_dkYyNkcQPXnKWlvIDkjb2qfBwuJ92dQ/edit?pli=1&gid=719798611#gid=719798611"
    )
    worksheet1 = sh.get_worksheet(0)
    worksheet3 = sh.get_worksheet(2)
    data1 = worksheet1.get_all_records()
    data3 = worksheet3.get_all_records()
    with open('data1.json', 'w') as f:
        json.dump(data1, f)
    with open('data3.json', 'w') as f:
        json.dump(data3, f)
    print(type(worksheet3))
    time.sleep(time_sleep)

