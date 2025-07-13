import gspread
from random import shuffle, choice
import datetime, string

gc = gspread.service_account(filename="auth.json")
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1dxqQccvwSka_dkYyNkcQPXnKWlvIDkjb2qfBwuJ92dQ/edit?pli=1&gid=719798611#gid=719798611")
worksheet1 = sh.get_worksheet(0)
worksheet3 = sh.get_worksheet(2)
data1 = worksheet1.get_all_records()
data3 = worksheet3.get_all_records()

def check_count_current_month(inn:int):
    now = f'{str(datetime.datetime.now().month).rjust(2, "0")}.{datetime.datetime.now().year}'
    for comp in data3:
        if comp['Registration_number']==inn:
            company = comp
            break
    limits = {'Продвинутый': 25,'Стандарт': 8,'Начальный': 4}
    if now in company:
        if company['Status'] in limits:
            return company[now]<limits[company['Status']]
        return True
    else:
        return False

def add_count_current_month(companie:str):
    now = f'{str(datetime.datetime.now().month).rjust(2, "0")}.{datetime.datetime.now().year}'
    for i in range(len(data3)):
        if data3[i]['Certification_body'] == companie:
            if now in data3[i]:
                string_letters = list(string.ascii_uppercase)
                string_letters.extend([f'A{letterA}' for letterA in string.ascii_uppercase])
                string_letters.extend([f'B{letterA}' for letterA in string.ascii_uppercase])
                string_letters.extend([f'C{letterA}' for letterA in string.ascii_uppercase])
                string_letters.extend([f'D{letterA}' for letterA in string.ascii_uppercase])
                string_letters.extend([f'E{letterA}' for letterA in string.ascii_uppercase])
                string_letters.extend([f'F{letterA}' for letterA in string.ascii_uppercase])
                count = int(data3[i][now])
                column = string_letters[list(data3[i].keys()).index(now)]
                row = i+2
                cell = f'{column}{row}'
                worksheet3.update_acell(cell, count+1)

def get_list_companies(standarts:list[str], region:str='50'):
    # Общий отбор
    list_all = [comp for comp in data1 if all([comp[st]=='+' for st in standarts]) and comp['Статус'].lower()!='бан']
    # Отбор одной региональной компании
    list2 = list(filter(lambda x: x['Код региона'] == int(region) and check_count_current_month(x['ИНН']), list_all))
    if len(list2):
        list2 = [choice(list2)]
    # Отбор продвинутых
    list1 = list(filter(lambda x: x['Статус']=='Продвинутый' and x not in list2 and check_count_current_month(x['ИНН']), list_all))
    shuffle(list1)

    # Отбор всех cтандартных
    list3 = list(filter(lambda x: x['Статус']=='Стандарт' and x not in list2 and check_count_current_month(x['ИНН']) , list_all))
    shuffle(list3)

    # Отбор всех начальных
    list4 = list(filter(lambda x: x['Статус'] == 'Начальный' and x not in list2 and check_count_current_month(x['ИНН']), list_all))
    shuffle(list4)

    # Отбор всех пассивных
    list5 = list(filter(lambda x: x['Статус'] == 'Пассивный' and x not in list2, list_all))
    shuffle(list5)

    output_list = list1 + list2 + list3 + list4 + list5
    output_list2 = [f"{comp['Сокращенное наименование']}, {comp['Город']}" for comp in output_list]
    urls = get_urls([comp['Сокращенное наименование'] for comp in output_list])
    return [output_list2, urls]

def get_list_emails(list_companies):
    list_emails = []
    for name in list_companies:
        for comp in data1:
            if comp['Сокращенное наименование']==name:
                if ', ' not in  comp['Адрес эл. почты']:
                    list_emails.append(comp['Адрес эл. почты'])
                else:
                    list_emails.extend(comp['Адрес эл. почты'].split(', '))
                break
    return  list_emails

def get_url(companie:str):
    global data1
    for comp in data1:
        if comp['Сокращенное наименование']==companie:
            return  comp['Ссылка на сайт']

def get_urls(list_companies:list):
    return [get_url(comp) for comp in list_companies]

