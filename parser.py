import gspread
from random import shuffle, choice
import datetime, string, json, time

limits = {"Продвинутый": 25, "Стандарт": 8, "Начальный": 4, "Пассивный": 9999}

def check_count_current_month(inn: int):
    with open('data3.json') as f:
        data3 = json.load(f)
    now = f'{str(datetime.datetime.now().month).rjust(2, "0")}.{datetime.datetime.now().year}'
    company = next((comp for comp in data3 if comp["Registration_number"] == inn), None)

    if not company:
        return False

    if now in company:
        if company["Status"] in limits:
            return company[now] < limits[company["Status"]]
        return True
    return False

def get_list_inn_companies_with_check_count():
    with open('data3.json') as f:
        data3 = json.load(f)
    output_list = []
    now = f'{str(datetime.datetime.now().month).rjust(2, "0")}.{datetime.datetime.now().year}'
    for comp in data3:
        if now in comp:
            if comp["Status"] in limits:
                if comp[now] < limits[comp["Status"]]:
                    output_list.append(comp['Registration_number'])
    return output_list



def add_count_current_month(companie: str):
    with open('data3.json') as f:
        data3 = json.load(f)
    now = f'{str(datetime.datetime.now().month).rjust(2, "0")}.{datetime.datetime.now().year}'
    for i, comp in enumerate(data3):
        if comp["Certification_body"] == companie and now in comp:
            string_letters = list(string.ascii_uppercase)
            for prefix in ["A", "B", "C", "D", "E", "F"]:
                string_letters.extend([f"{prefix}{letter}" for letter in string.ascii_uppercase])

            count = int(comp[now])
            column = string_letters[list(comp.keys()).index(now)]
            row = i + 2
            cell = f"{column}{row}"
            time.sleep(1)
            gc = gspread.service_account(filename="auth.json")
            sh = gc.open_by_url(
                "https://docs.google.com/spreadsheets/d/1dxqQccvwSka_dkYyNkcQPXnKWlvIDkjb2qfBwuJ92dQ/edit?pli=1&gid=719798611#gid=719798611"
            )
            worksheet3 = sh.get_worksheet(2)
            worksheet3.update_acell(cell, count + 1)
            break


def get_list_companies(standarts: list[str], region: str = "50"):
    with open('data3.json') as f:
        data3 = json.load(f)
    with open('data1.json') as f:
        data1 = json.load(f)
    list_inn_check_count = get_list_inn_companies_with_check_count()

    # Общий отбор
    list_all = [
        comp
        for comp in data1
        if all(comp.get(st) == "+" for st in standarts)
        and comp["Статус"].lower() != "бан" and comp["ИНН"] in list_inn_check_count
    ]

    # Отбор одной региональной компании
    list2 = [
        comp
        for comp in list_all
        if comp["Код региона"] == int(region)
    ]
    if list2:
        list2 = [choice(list2)]

    # Группы по статусу
    list1, list3, list4, list5 = [], [], [], []

    for comp in list_all:
        try:
            if comp in list2:
                continue
            status = comp["Статус"]
            if status == "Продвинутый":
                list1.append(comp)
            elif status == "Стандарт":
                list3.append(comp)
            elif status == "Начальный":
                list4.append(comp)
            elif status == "Пассивный":
                list5.append(comp)
        except Exception as e:
            print(f"ERROR {comp.get('Сокращенное наименование')}: {e}")

    # Перемешиваем списки
    for l in (list1, list3, list4, list5):
        shuffle(l)

    output_list = list1 + list2 + list3 + list4 + list5
    output_list2 = [f"{comp['Сокращенное наименование']}, {comp['Город']}" for comp in output_list]
    urls = get_urls([comp["Сокращенное наименование"] for comp in output_list])
    return [output_list2, urls]


def get_list_emails(list_companies):
    with open('data1.json') as f:
        data1 = json.load(f)
    list_emails = []
    for name in list_companies:
        for comp in data1:
            if comp["Сокращенное наименование"] == name:
                if ", " not in comp["Адрес эл. почты"]:
                    list_emails.append(comp["Адрес эл. почты"])
                else:
                    list_emails.extend(comp["Адрес эл. почты"].split(", "))
                break
    return list_emails


def get_url(companie: str):
    with open('data1.json') as f:
        data1 = json.load(f)
    for comp in data1:
        if comp["Сокращенное наименование"] == companie:
            return comp["Ссылка на сайт"]


def get_urls(list_companies: list):
    return [get_url(comp) for comp in list_companies]

l = get_list_companies(['9001'], '50')
print(len(l[0]))
print(*l[0], sep='\n')