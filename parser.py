import datetime
import json
from random import choice, shuffle

from config import DATA1_PATH, DATA3_PATH


def load_json(path):
    with open(path) as f:
        return json.load(f)


def add_count_current_month(companie: str):
    data3 = load_json(DATA3_PATH)
    now = f'{str(datetime.datetime.now().month).rjust(2, "0")}.{datetime.datetime.now().year}'
    for comp in data3:
        if comp["Certification_body"] == companie:
            comp[now] = int(comp.get(now, 0)) + 1
            with open(DATA3_PATH, 'w') as f:
                json.dump(data3, f)
            break


def get_list_companies(standarts: list[str], region: str = "50"):
    data1 = load_json(DATA1_PATH)

    list_all = [
        comp
        for comp in data1
        if all(comp.get(st) == "+" for st in standarts)
        and comp["Статус"].lower() != "бан"
    ]

    list2 = [
        comp
        for comp in list_all
        if comp["Код региона"] == int(region)
    ]
    if list2:
        list2 = [choice(list2)]

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

    for current_list in (list1, list3, list4, list5):
        shuffle(current_list)

    output_list = list1 + list2 + list3 + list4 + list5
    output_names = [f"{comp['Сокращенное наименование']}, {comp['Город']}" for comp in output_list]
    urls = get_urls([comp["Сокращенное наименование"] for comp in output_list])
    return [output_names, urls]


def get_list_emails(list_companies):
    data1 = load_json(DATA1_PATH)
    list_emails = []
    for name in list_companies:
        clean_name = name.split(", ")[0]
        for comp in data1:
            if comp["Сокращенное наименование"] == clean_name:
                if ", " not in comp["Адрес эл. почты"]:
                    list_emails.append(comp["Адрес эл. почты"])
                else:
                    list_emails.extend(comp["Адрес эл. почты"].split(", "))
                break
    return list_emails


def get_url(companie: str):
    data1 = load_json(DATA1_PATH)
    for comp in data1:
        if comp["Сокращенное наименование"] == companie:
            return comp["Ссылка на сайт"]
    return None


def get_urls(list_companies: list):
    return [get_url(comp) for comp in list_companies]
